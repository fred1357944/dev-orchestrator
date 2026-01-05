"""Tests for Dev Orchestrator core modules"""

import pytest
import tempfile
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.models import Project, ServiceConfig, ProjectRegistry as RegistryModel
from src.core.port_manager import PortManager, PortExhaustedError
from src.core.project_registry import ProjectRegistry, ProjectExistsError, ProjectNotFoundError


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        (data_dir / "projects.json").write_text(json.dumps({
            "version": "1.0.0",
            "projects": {},
            "port_allocation": {
                "frontend_range": {"start": 3000, "end": 3010, "reserved": []},
                "backend_range": {"start": 8000, "end": 8010, "reserved": []},
                "allocated": {}
            },
            "settings": {
                "auto_generate_env": False,
                "default_tags": ["test"]
            },
            "metadata": {}
        }))
        yield data_dir


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestProject:
    """Tests for Project model"""

    def test_create_valid_project(self, temp_project_dir):
        """Test creating a valid project"""
        project = Project(
            name="test-project",
            path=str(temp_project_dir)
        )
        assert project.name == "test-project"
        assert project.display_name == "Test Project"

    def test_invalid_project_name(self, temp_project_dir):
        """Test that invalid project names raise an error"""
        with pytest.raises(ValueError):
            Project(name="Test Project", path=str(temp_project_dir))

        with pytest.raises(ValueError):
            Project(name="123-project", path=str(temp_project_dir))

    def test_project_serialization(self, temp_project_dir):
        """Test project serialization to dict"""
        project = Project(
            name="test-project",
            path=str(temp_project_dir),
            frontend=ServiceConfig(port=3001, command="npm run dev"),
            backend=ServiceConfig(port=8001, command="python main.py")
        )

        data = project.to_dict()
        assert data["name"] == "test-project"
        assert data["frontend"]["port"] == 3001
        assert data["backend"]["port"] == 8001


class TestPortManager:
    """Tests for PortManager"""

    def test_find_available_port(self, temp_data_dir):
        """Test finding an available port"""
        pm = PortManager(temp_data_dir / "projects.json")

        port = pm.find_available_frontend_port()
        assert 3000 <= port <= 3010

    def test_allocate_ports(self, temp_data_dir):
        """Test port allocation"""
        pm = PortManager(temp_data_dir / "projects.json")

        ports = pm.allocate_ports("test-project")
        assert "frontend" in ports
        assert "backend" in ports
        assert 3000 <= ports["frontend"] <= 3010
        assert 8000 <= ports["backend"] <= 8010

    def test_release_ports(self, temp_data_dir):
        """Test releasing ports"""
        pm = PortManager(temp_data_dir / "projects.json")

        pm.allocate_ports("test-project")
        released = pm.release_ports("test-project")
        assert len(released) == 2

    def test_port_status(self, temp_data_dir):
        """Test getting port status"""
        pm = PortManager(temp_data_dir / "projects.json")

        status = pm.get_port_status()
        assert "frontend_range" in status
        assert "backend_range" in status
        assert "used_ports" in status


class TestProjectRegistry:
    """Tests for ProjectRegistry"""

    def test_register_project(self, temp_data_dir, temp_project_dir):
        """Test registering a project"""
        registry = ProjectRegistry(temp_data_dir)

        project = registry.register_project(
            name="test-project",
            path=str(temp_project_dir),
            frontend_command="npm run dev",
            backend_command="python main.py"
        )

        assert project.name == "test-project"
        assert project.frontend.port is not None
        assert project.backend.port is not None

    def test_register_duplicate_project(self, temp_data_dir, temp_project_dir):
        """Test that registering a duplicate project raises an error"""
        registry = ProjectRegistry(temp_data_dir)

        registry.register_project(
            name="test-project",
            path=str(temp_project_dir),
            backend_command="python main.py"
        )

        with pytest.raises(ProjectExistsError):
            registry.register_project(
                name="test-project",
                path=str(temp_project_dir),
                backend_command="python main.py"
            )

    def test_get_project(self, temp_data_dir, temp_project_dir):
        """Test getting a project"""
        registry = ProjectRegistry(temp_data_dir)

        registry.register_project(
            name="test-project",
            path=str(temp_project_dir),
            backend_command="python main.py"
        )

        project = registry.get_project("test-project")
        assert project is not None
        assert project.name == "test-project"

    def test_remove_project(self, temp_data_dir, temp_project_dir):
        """Test removing a project"""
        registry = ProjectRegistry(temp_data_dir)

        registry.register_project(
            name="test-project",
            path=str(temp_project_dir),
            backend_command="python main.py"
        )

        result = registry.remove_project("test-project")
        assert result is True

        project = registry.get_project("test-project")
        assert project is None

    def test_list_projects(self, temp_data_dir, temp_project_dir):
        """Test listing projects"""
        registry = ProjectRegistry(temp_data_dir)

        registry.register_project(
            name="project-a",
            path=str(temp_project_dir),
            backend_command="python main.py",
            tags=["api"]
        )

        with tempfile.TemporaryDirectory() as tmpdir2:
            registry.register_project(
                name="project-b",
                path=tmpdir2,
                backend_command="python main.py",
                tags=["web"]
            )

            all_projects = registry.list_projects()
            assert len(all_projects) == 2

            api_projects = registry.list_projects(filter_tags=["api"])
            assert len(api_projects) == 1
            assert api_projects[0].name == "project-a"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
