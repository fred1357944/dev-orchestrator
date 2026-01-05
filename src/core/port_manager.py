"""Port Manager - Handles port allocation and conflict detection"""

import socket
from pathlib import Path
from typing import Optional, Tuple
from .models import ProjectRegistry, PortAllocation


class PortExhaustedError(Exception):
    """Raised when no available ports in the specified range"""
    pass


class PortInUseError(Exception):
    """Raised when a specific port is already in use"""
    pass


class PortManager:
    """Manages port allocation for development projects"""

    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self._registry: Optional[ProjectRegistry] = None

    @property
    def registry(self) -> ProjectRegistry:
        """Lazy load registry"""
        if self._registry is None:
            self._registry = ProjectRegistry.load(self.registry_path)
        return self._registry

    def reload(self) -> None:
        """Reload registry from disk"""
        self._registry = ProjectRegistry.load(self.registry_path)

    def save(self) -> None:
        """Save registry to disk"""
        self.registry.save(self.registry_path)

    @staticmethod
    def is_port_in_use(port: int, host: str = "localhost") -> bool:
        """
        Check if a port is currently in use by the system.

        Uses socket connection to test if port is occupied.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result == 0

    def is_port_allocated(self, port: int) -> Optional[str]:
        """
        Check if a port is allocated in our registry.

        Returns project name if allocated, None otherwise.
        """
        allocated = self.registry.port_allocation.allocated
        return allocated.get(str(port))

    def is_port_reserved(self, port: int) -> bool:
        """Check if a port is in the reserved list"""
        fe_reserved = self.registry.port_allocation.frontend_range.reserved
        be_reserved = self.registry.port_allocation.backend_range.reserved
        return port in fe_reserved or port in be_reserved

    def find_available_port(
        self,
        start: int,
        end: int,
        exclude: list[int] = None
    ) -> Optional[int]:
        """
        Find an available port in the specified range.

        Checks both:
        1. Our internal allocation registry
        2. Actual system port usage via socket

        Args:
            start: Start of port range (inclusive)
            end: End of port range (inclusive)
            exclude: List of ports to exclude

        Returns:
            Available port number or None if no port available
        """
        exclude = exclude or []
        allocated = self.registry.port_allocation.allocated

        for port in range(start, end + 1):
            # Skip excluded ports
            if port in exclude:
                continue

            # Skip reserved ports
            if self.is_port_reserved(port):
                continue

            # Skip already allocated ports
            if str(port) in allocated:
                continue

            # Check if port is actually in use by system
            if self.is_port_in_use(port):
                continue

            return port

        return None

    def find_available_frontend_port(self, exclude: list[int] = None) -> Optional[int]:
        """Find available port in frontend range (3000-3099)"""
        fe_range = self.registry.port_allocation.frontend_range
        return self.find_available_port(fe_range.start, fe_range.end, exclude)

    def find_available_backend_port(self, exclude: list[int] = None) -> Optional[int]:
        """Find available port in backend range (8000-8099)"""
        be_range = self.registry.port_allocation.backend_range
        return self.find_available_port(be_range.start, be_range.end, exclude)

    def allocate_ports(
        self,
        project_name: str,
        need_frontend: bool = True,
        need_backend: bool = True
    ) -> dict:
        """
        Allocate ports for a project.

        Args:
            project_name: Name of the project
            need_frontend: Whether to allocate a frontend port
            need_backend: Whether to allocate a backend port

        Returns:
            Dict with allocated ports: {"frontend": 3001, "backend": 8001}

        Raises:
            PortExhaustedError: If no available ports in range
        """
        result = {}
        allocated_ports = []

        try:
            if need_frontend:
                fe_port = self.find_available_frontend_port()
                if fe_port is None:
                    raise PortExhaustedError("No available frontend ports in range 3000-3099")
                result["frontend"] = fe_port
                allocated_ports.append(fe_port)
                # Temporarily mark as allocated to avoid backend getting same port
                self.registry.port_allocation.allocated[str(fe_port)] = project_name

            if need_backend:
                be_port = self.find_available_backend_port()
                if be_port is None:
                    raise PortExhaustedError("No available backend ports in range 8000-8099")
                result["backend"] = be_port
                allocated_ports.append(be_port)
                self.registry.port_allocation.allocated[str(be_port)] = project_name

            # Save to disk
            self.save()

        except Exception as e:
            # Rollback on failure
            for port in allocated_ports:
                self.registry.port_allocation.allocated.pop(str(port), None)
            raise e

        return result

    def release_ports(self, project_name: str) -> list[int]:
        """
        Release all ports allocated to a project.

        Args:
            project_name: Name of the project

        Returns:
            List of released port numbers
        """
        released = []
        allocated = self.registry.port_allocation.allocated

        # Find all ports allocated to this project
        ports_to_release = [
            port for port, name in allocated.items()
            if name == project_name
        ]

        # Remove them
        for port in ports_to_release:
            del allocated[port]
            released.append(int(port))

        if released:
            self.save()

        return released

    def get_port_status(self) -> dict:
        """
        Get overview of port usage.

        Returns:
            Dict with port usage statistics
        """
        fe_range = self.registry.port_allocation.frontend_range
        be_range = self.registry.port_allocation.backend_range
        allocated = self.registry.port_allocation.allocated

        # Count allocated ports by range
        fe_allocated = []
        be_allocated = []
        for port_str, project in allocated.items():
            port = int(port_str)
            if fe_range.start <= port <= fe_range.end:
                fe_allocated.append(port)
            elif be_range.start <= port <= be_range.end:
                be_allocated.append(port)

        fe_total = fe_range.end - fe_range.start + 1 - len(fe_range.reserved)
        be_total = be_range.end - be_range.start + 1 - len(be_range.reserved)

        return {
            "frontend_range": f"{fe_range.start}-{fe_range.end}",
            "backend_range": f"{be_range.start}-{be_range.end}",
            "used_ports": {
                "frontend": sorted(fe_allocated),
                "backend": sorted(be_allocated)
            },
            "next_available": {
                "frontend": self.find_available_frontend_port(),
                "backend": self.find_available_backend_port()
            },
            "utilization": {
                "frontend": f"{len(fe_allocated) / fe_total * 100:.1f}%",
                "backend": f"{len(be_allocated) / be_total * 100:.1f}%"
            }
        }

    def validate_port(self, port: int, port_type: str = "any") -> Tuple[bool, str]:
        """
        Validate if a port can be used.

        Args:
            port: Port number to validate
            port_type: "frontend", "backend", or "any"

        Returns:
            Tuple of (is_valid, message)
        """
        fe_range = self.registry.port_allocation.frontend_range
        be_range = self.registry.port_allocation.backend_range

        # Check range
        if port_type == "frontend":
            if not (fe_range.start <= port <= fe_range.end):
                return False, f"Port {port} is outside frontend range ({fe_range.start}-{fe_range.end})"
        elif port_type == "backend":
            if not (be_range.start <= port <= be_range.end):
                return False, f"Port {port} is outside backend range ({be_range.start}-{be_range.end})"

        # Check reserved
        if self.is_port_reserved(port):
            return False, f"Port {port} is reserved"

        # Check allocated
        project = self.is_port_allocated(port)
        if project:
            return False, f"Port {port} is allocated to project '{project}'"

        # Check system usage
        if self.is_port_in_use(port):
            return False, f"Port {port} is currently in use by the system"

        return True, "Port is available"
