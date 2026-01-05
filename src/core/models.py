"""Data models for Dev Orchestrator"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from pathlib import Path
import json
import re


@dataclass
class HealthCheck:
    """Health check configuration for a service"""
    path: str = "/"
    timeout: int = 30


@dataclass
class ServiceConfig:
    """Configuration for a frontend or backend service"""
    enabled: bool = True
    port: Optional[int] = None
    command: str = ""
    cwd: Optional[str] = None
    env: dict = field(default_factory=dict)
    health_check: Optional[HealthCheck] = None

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "port": self.port,
            "command": self.command,
            "cwd": self.cwd,
            "env": self.env,
            "health_check": {
                "path": self.health_check.path,
                "timeout": self.health_check.timeout
            } if self.health_check else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ServiceConfig":
        health_check = None
        if data.get("health_check"):
            health_check = HealthCheck(**data["health_check"])
        return cls(
            enabled=data.get("enabled", True),
            port=data.get("port"),
            command=data.get("command", ""),
            cwd=data.get("cwd"),
            env=data.get("env", {}),
            health_check=health_check
        )


@dataclass
class Project:
    """Project configuration"""
    name: str
    path: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    frontend: Optional[ServiceConfig] = None
    backend: Optional[ServiceConfig] = None
    env_vars: dict = field(default_factory=dict)
    dependencies: list = field(default_factory=list)
    tags: list = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: Optional[str] = None

    def __post_init__(self):
        # Validate project name
        if not re.match(r'^[a-z][a-z0-9-]*$', self.name):
            raise ValueError(
                f"Invalid project name '{self.name}'. "
                "Must start with lowercase letter and contain only lowercase letters, numbers, and hyphens."
            )

        # Set display_name if not provided
        if not self.display_name:
            self.display_name = self.name.replace("-", " ").title()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "path": self.path,
            "description": self.description,
            "frontend": self.frontend.to_dict() if self.frontend else None,
            "backend": self.backend.to_dict() if self.backend else None,
            "env_vars": self.env_vars,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        frontend = None
        backend = None
        if data.get("frontend"):
            frontend = ServiceConfig.from_dict(data["frontend"])
        if data.get("backend"):
            backend = ServiceConfig.from_dict(data["backend"])

        return cls(
            name=data["name"],
            path=data["path"],
            display_name=data.get("display_name"),
            description=data.get("description"),
            frontend=frontend,
            backend=backend,
            env_vars=data.get("env_vars", {}),
            dependencies=data.get("dependencies", []),
            tags=data.get("tags", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            notes=data.get("notes")
        )


@dataclass
class PortRange:
    """Port range configuration"""
    start: int
    end: int
    reserved: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "start": self.start,
            "end": self.end,
            "reserved": self.reserved
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PortRange":
        return cls(
            start=data["start"],
            end=data["end"],
            reserved=data.get("reserved", [])
        )


@dataclass
class PortAllocation:
    """Port allocation tracking"""
    frontend_range: PortRange = field(default_factory=lambda: PortRange(3000, 3099, [3000]))
    backend_range: PortRange = field(default_factory=lambda: PortRange(8000, 8099, [8501]))
    allocated: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "frontend_range": self.frontend_range.to_dict(),
            "backend_range": self.backend_range.to_dict(),
            "allocated": self.allocated
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PortAllocation":
        return cls(
            frontend_range=PortRange.from_dict(data.get("frontend_range", {"start": 3000, "end": 3099, "reserved": [3000]})),
            backend_range=PortRange.from_dict(data.get("backend_range", {"start": 8000, "end": 8099, "reserved": [8501]})),
            allocated=data.get("allocated", {})
        )


@dataclass
class Settings:
    """Global settings"""
    auto_generate_env: bool = True
    env_file_name: str = ".env.local"
    pm2_ecosystem_path: str = "./ecosystem.config.js"
    log_retention_days: int = 7
    health_check_interval: int = 60
    dashboard_port: int = 8501
    default_tags: list = field(default_factory=lambda: ["local"])

    def to_dict(self) -> dict:
        return {
            "auto_generate_env": self.auto_generate_env,
            "env_file_name": self.env_file_name,
            "pm2_ecosystem_path": self.pm2_ecosystem_path,
            "log_retention_days": self.log_retention_days,
            "health_check_interval": self.health_check_interval,
            "dashboard_port": self.dashboard_port,
            "default_tags": self.default_tags
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        return cls(
            auto_generate_env=data.get("auto_generate_env", True),
            env_file_name=data.get("env_file_name", ".env.local"),
            pm2_ecosystem_path=data.get("pm2_ecosystem_path", "./ecosystem.config.js"),
            log_retention_days=data.get("log_retention_days", 7),
            health_check_interval=data.get("health_check_interval", 60),
            dashboard_port=data.get("dashboard_port", 8501),
            default_tags=data.get("default_tags", ["local"])
        )


@dataclass
class Metadata:
    """Registry metadata"""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())
    last_modified_by: str = "system"
    total_projects: int = 0
    active_projects: int = 0

    def to_dict(self) -> dict:
        return {
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "last_modified_by": self.last_modified_by,
            "total_projects": self.total_projects,
            "active_projects": self.active_projects
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Metadata":
        return cls(
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_modified=data.get("last_modified", datetime.now().isoformat()),
            last_modified_by=data.get("last_modified_by", "system"),
            total_projects=data.get("total_projects", 0),
            active_projects=data.get("active_projects", 0)
        )


@dataclass
class ProjectRegistry:
    """Complete project registry structure"""
    version: str = "1.0.0"
    projects: dict = field(default_factory=dict)
    port_allocation: PortAllocation = field(default_factory=PortAllocation)
    settings: Settings = field(default_factory=Settings)
    metadata: Metadata = field(default_factory=Metadata)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "projects": {name: proj.to_dict() for name, proj in self.projects.items()},
            "port_allocation": self.port_allocation.to_dict(),
            "settings": self.settings.to_dict(),
            "metadata": self.metadata.to_dict()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectRegistry":
        projects = {}
        for name, proj_data in data.get("projects", {}).items():
            projects[name] = Project.from_dict(proj_data)

        return cls(
            version=data.get("version", "1.0.0"),
            projects=projects,
            port_allocation=PortAllocation.from_dict(data.get("port_allocation", {})),
            settings=Settings.from_dict(data.get("settings", {})),
            metadata=Metadata.from_dict(data.get("metadata", {}))
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "ProjectRegistry":
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def load(cls, path: Path) -> "ProjectRegistry":
        if not path.exists():
            return cls()
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
