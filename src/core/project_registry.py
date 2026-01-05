"""Project Registry - Manages project configurations"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from .models import Project, ServiceConfig, ProjectRegistry as RegistryModel
from .port_manager import PortManager


class ProjectExistsError(Exception):
    """Raised when trying to register a project that already exists"""
    pass


class ProjectNotFoundError(Exception):
    """Raised when project is not found"""
    pass


class InvalidPathError(Exception):
    """Raised when project path is invalid"""
    pass


class ProjectRegistry:
    """Manages project configurations and registration"""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.registry_path = self.data_dir / "projects.json"
        self.backup_dir = self.data_dir / "backups"
        self.port_manager = PortManager(self.registry_path)
        self._registry: Optional[RegistryModel] = None

    @property
    def registry(self) -> RegistryModel:
        """Lazy load registry"""
        if self._registry is None:
            self._registry = RegistryModel.load(self.registry_path)
        return self._registry

    def reload(self) -> None:
        """Reload registry from disk"""
        self._registry = RegistryModel.load(self.registry_path)
        self.port_manager.reload()

    def save(self, modified_by: str = "system") -> None:
        """Save registry to disk with backup"""
        # Update metadata
        self.registry.metadata.last_modified = datetime.now().isoformat()
        self.registry.metadata.last_modified_by = modified_by
        self.registry.metadata.total_projects = len(self.registry.projects)

        # Create backup before saving
        self._create_backup()

        # Save
        self.registry.save(self.registry_path)

    def _create_backup(self) -> None:
        """Create a backup of the current registry"""
        if not self.registry_path.exists():
            return

        self.backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"projects_{timestamp}.json"

        shutil.copy2(self.registry_path, backup_path)

        # Keep only last 10 backups
        backups = sorted(self.backup_dir.glob("projects_*.json"))
        for old_backup in backups[:-10]:
            old_backup.unlink()

    def list_projects(
        self,
        filter_tags: List[str] = None,
        include_stopped: bool = True
    ) -> List[Project]:
        """
        List all registered projects.

        Args:
            filter_tags: Only return projects with these tags
            include_stopped: Include stopped projects (always True for now)

        Returns:
            List of Project objects
        """
        projects = list(self.registry.projects.values())

        if filter_tags:
            projects = [
                p for p in projects
                if any(tag in p.tags for tag in filter_tags)
            ]

        return projects

    def get_project(self, name: str) -> Optional[Project]:
        """
        Get a project by name.

        Args:
            name: Project name

        Returns:
            Project object or None if not found
        """
        return self.registry.projects.get(name)

    def register_project(
        self,
        name: str,
        path: str,
        display_name: str = None,
        description: str = None,
        frontend_command: str = None,
        backend_command: str = None,
        frontend_cwd: str = None,
        backend_cwd: str = None,
        env_vars: dict = None,
        tags: List[str] = None,
        auto_allocate_ports: bool = True
    ) -> Project:
        """
        Register a new project.

        Args:
            name: Project name (lowercase, alphanumeric with hyphens)
            path: Absolute path to project root
            display_name: Display name (optional)
            description: Project description (optional)
            frontend_command: Command to start frontend (optional)
            backend_command: Command to start backend (optional)
            frontend_cwd: Frontend working directory relative to path (optional)
            backend_cwd: Backend working directory relative to path (optional)
            env_vars: Environment variables (optional)
            tags: Project tags (optional)
            auto_allocate_ports: Whether to auto-allocate ports

        Returns:
            Registered Project object

        Raises:
            ProjectExistsError: If project name already exists
            InvalidPathError: If path doesn't exist or isn't a directory
        """
        # Validate name doesn't exist
        if name in self.registry.projects:
            raise ProjectExistsError(f"Project '{name}' already exists")

        # Validate path
        project_path = Path(path)
        if not project_path.exists():
            raise InvalidPathError(f"Path '{path}' does not exist")
        if not project_path.is_dir():
            raise InvalidPathError(f"Path '{path}' is not a directory")

        # Allocate ports if needed
        ports = {"frontend": None, "backend": None}
        if auto_allocate_ports:
            need_frontend = frontend_command is not None
            need_backend = backend_command is not None
            if need_frontend or need_backend:
                ports = self.port_manager.allocate_ports(
                    name,
                    need_frontend=need_frontend,
                    need_backend=need_backend
                )

        # Create service configs
        frontend = None
        backend = None

        if frontend_command:
            frontend = ServiceConfig(
                enabled=True,
                port=ports.get("frontend"),
                command=frontend_command,
                cwd=frontend_cwd,
                env={}
            )

        if backend_command:
            backend = ServiceConfig(
                enabled=True,
                port=ports.get("backend"),
                command=backend_command,
                cwd=backend_cwd,
                env={}
            )

        # Merge default tags
        project_tags = list(self.registry.settings.default_tags)
        if tags:
            project_tags.extend(tags)
        project_tags = list(set(project_tags))  # Remove duplicates

        # Create project
        project = Project(
            name=name,
            path=str(project_path.absolute()),
            display_name=display_name,
            description=description,
            frontend=frontend,
            backend=backend,
            env_vars=env_vars or {},
            tags=project_tags
        )

        # Add to registry
        self.registry.projects[name] = project
        self.save(modified_by="register_project")

        # Generate .env file if enabled
        if self.registry.settings.auto_generate_env:
            self._generate_env_file(project)

        return project

    def update_project(self, name: str, updates: dict) -> Project:
        """
        Update a project's configuration.

        Args:
            name: Project name
            updates: Dictionary of fields to update

        Returns:
            Updated Project object

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        project = self.get_project(name)
        if not project:
            raise ProjectNotFoundError(f"Project '{name}' not found")

        # Apply updates
        for key, value in updates.items():
            if hasattr(project, key):
                setattr(project, key, value)

        # Update timestamp
        project.updated_at = datetime.now().isoformat()

        self.save(modified_by="update_project")

        return project

    def remove_project(self, name: str, release_ports: bool = True) -> bool:
        """
        Remove a project from the registry.

        Args:
            name: Project name
            release_ports: Whether to release allocated ports

        Returns:
            True if removed successfully

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        if name not in self.registry.projects:
            raise ProjectNotFoundError(f"Project '{name}' not found")

        # Release ports
        if release_ports:
            self.port_manager.release_ports(name)

        # Remove from registry
        del self.registry.projects[name]
        self.save(modified_by="remove_project")

        return True

    def _generate_env_file(self, project: Project) -> Path:
        """
        Generate .env file for a project.

        Args:
            project: Project object

        Returns:
            Path to generated .env file
        """
        env_content = [
            "# Auto-generated by Dev Orchestrator",
            "# Do not edit manually - changes may be overwritten",
            ""
        ]

        # Add port variables
        if project.frontend and project.frontend.port:
            env_content.append(f"FRONTEND_PORT={project.frontend.port}")

        if project.backend and project.backend.port:
            env_content.append(f"BACKEND_PORT={project.backend.port}")
            env_content.append(f"API_URL=http://localhost:{project.backend.port}")

        # Add custom env vars
        for key, value in project.env_vars.items():
            env_content.append(f"{key}={value}")

        # Write file
        env_path = Path(project.path) / self.registry.settings.env_file_name
        env_path.write_text("\n".join(env_content) + "\n")

        return env_path

    def get_project_info(self, name: str) -> dict:
        """
        Get detailed project information including status.

        Args:
            name: Project name

        Returns:
            Dictionary with project details
        """
        project = self.get_project(name)
        if not project:
            return None

        return {
            "name": project.name,
            "display_name": project.display_name,
            "path": project.path,
            "description": project.description,
            "frontend": {
                "port": project.frontend.port if project.frontend else None,
                "command": project.frontend.command if project.frontend else None,
                "enabled": project.frontend.enabled if project.frontend else False,
                "url": f"http://localhost:{project.frontend.port}" if project.frontend and project.frontend.port else None
            },
            "backend": {
                "port": project.backend.port if project.backend else None,
                "command": project.backend.command if project.backend else None,
                "enabled": project.backend.enabled if project.backend else False,
                "url": f"http://localhost:{project.backend.port}" if project.backend and project.backend.port else None
            },
            "tags": project.tags,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "notes": project.notes
        }

    def search_projects(self, query: str) -> List[Project]:
        """
        Search projects by name, display name, or tags.

        Args:
            query: Search query

        Returns:
            List of matching projects
        """
        query = query.lower()
        results = []

        for project in self.registry.projects.values():
            # Search in name
            if query in project.name.lower():
                results.append(project)
                continue

            # Search in display name
            if project.display_name and query in project.display_name.lower():
                results.append(project)
                continue

            # Search in tags
            if any(query in tag.lower() for tag in project.tags):
                results.append(project)
                continue

            # Search in description
            if project.description and query in project.description.lower():
                results.append(project)

        return results
