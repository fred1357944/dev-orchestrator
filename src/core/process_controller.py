"""Process Controller - Manages project processes via PM2"""

import json
import subprocess
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from .project_registry import ProjectRegistry


@dataclass
class ServiceStatus:
    """Status of a single service"""
    name: str
    status: str  # online, stopped, errored, not_started
    pid: Optional[int]
    port: Optional[int]
    uptime: Optional[str]
    memory: Optional[str]
    cpu: Optional[str]
    url: Optional[str]


@dataclass
class ProjectStatus:
    """Status of a project"""
    name: str
    display_name: str
    frontend: Optional[ServiceStatus]
    backend: Optional[ServiceStatus]
    overall_status: str  # running, stopped, partial, error


@dataclass
class OperationResult:
    """Result of a start/stop operation"""
    success: bool
    message: str
    project_name: str
    frontend: Optional[ServiceStatus]
    backend: Optional[ServiceStatus]


class PM2Error(Exception):
    """Raised when PM2 operation fails"""
    pass


class ProcessController:
    """Controls project processes via PM2"""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.registry = ProjectRegistry(self.data_dir)
        self.pm2_log_dir = Path.home() / ".pm2" / "logs"

    def _run_pm2_command(
        self,
        args: List[str],
        capture_output: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Run a PM2 command.

        Args:
            args: Command arguments (without 'pm2' prefix)
            capture_output: Whether to capture stdout/stderr

        Returns:
            CompletedProcess result
        """
        cmd = ["pm2"] + args

        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                timeout=30
            )
            return result
        except subprocess.TimeoutExpired:
            raise PM2Error(f"PM2 command timed out: {' '.join(cmd)}")
        except FileNotFoundError:
            raise PM2Error("PM2 is not installed. Run: npm install -g pm2")

    def _get_pm2_list(self) -> List[Dict[str, Any]]:
        """Get list of all PM2 processes as JSON"""
        result = self._run_pm2_command(["jlist"])
        if result.returncode != 0:
            return []

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return []

    def _get_pm2_process(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific PM2 process by name"""
        processes = self._get_pm2_list()
        for proc in processes:
            if proc.get("name") == name:
                return proc
        return None

    def _format_uptime(self, uptime_ms: Optional[int]) -> Optional[str]:
        """Format uptime from milliseconds to human readable"""
        if uptime_ms is None:
            return None

        seconds = uptime_ms // 1000
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h {minutes % 60}m"
        days = hours // 24
        return f"{days}d {hours % 24}h"

    def _format_memory(self, memory_bytes: Optional[int]) -> Optional[str]:
        """Format memory from bytes to human readable"""
        if memory_bytes is None:
            return None

        mb = memory_bytes / (1024 * 1024)
        return f"{mb:.1f} MB"

    def _get_service_status(
        self,
        pm2_name: str,
        port: Optional[int]
    ) -> ServiceStatus:
        """Get status of a service from PM2"""
        proc = self._get_pm2_process(pm2_name)

        if proc is None:
            return ServiceStatus(
                name=pm2_name,
                status="not_started",
                pid=None,
                port=port,
                uptime=None,
                memory=None,
                cpu=None,
                url=f"http://localhost:{port}" if port else None
            )

        pm2_env = proc.get("pm2_env", {})
        monit = proc.get("monit", {})

        status = pm2_env.get("status", "unknown")
        if status == "online":
            status_str = "online"
        elif status == "stopped":
            status_str = "stopped"
        else:
            status_str = "errored"

        return ServiceStatus(
            name=pm2_name,
            status=status_str,
            pid=proc.get("pid"),
            port=port,
            uptime=self._format_uptime(pm2_env.get("pm_uptime")),
            memory=self._format_memory(monit.get("memory")),
            cpu=f"{monit.get('cpu', 0):.1f}%",
            url=f"http://localhost:{port}" if port else None
        )

    def get_project_status(self, project_name: str) -> Optional[ProjectStatus]:
        """
        Get status of a project.

        Args:
            project_name: Name of the project

        Returns:
            ProjectStatus object or None if project not found
        """
        project = self.registry.get_project(project_name)
        if not project:
            return None

        frontend_status = None
        backend_status = None

        if project.frontend and project.frontend.enabled:
            pm2_name = f"{project_name}-fe"
            frontend_status = self._get_service_status(
                pm2_name,
                project.frontend.port
            )

        if project.backend and project.backend.enabled:
            pm2_name = f"{project_name}-be"
            backend_status = self._get_service_status(
                pm2_name,
                project.backend.port
            )

        # Determine overall status
        statuses = []
        if frontend_status:
            statuses.append(frontend_status.status)
        if backend_status:
            statuses.append(backend_status.status)

        if not statuses:
            overall = "stopped"
        elif all(s == "online" for s in statuses):
            overall = "running"
        elif all(s in ["stopped", "not_started"] for s in statuses):
            overall = "stopped"
        elif any(s == "errored" for s in statuses):
            overall = "error"
        else:
            overall = "partial"

        return ProjectStatus(
            name=project_name,
            display_name=project.display_name or project_name,
            frontend=frontend_status,
            backend=backend_status,
            overall_status=overall
        )

    def get_all_status(self) -> List[ProjectStatus]:
        """Get status of all projects"""
        statuses = []
        for project in self.registry.list_projects():
            status = self.get_project_status(project.name)
            if status:
                statuses.append(status)
        return statuses

    def start_project(
        self,
        project_name: str,
        services: List[str] = None
    ) -> OperationResult:
        """
        Start a project.

        Args:
            project_name: Name of the project
            services: List of services to start ["frontend", "backend"] or None for all

        Returns:
            OperationResult
        """
        project = self.registry.get_project(project_name)
        if not project:
            return OperationResult(
                success=False,
                message=f"Project '{project_name}' not found",
                project_name=project_name,
                frontend=None,
                backend=None
            )

        services = services or ["frontend", "backend"]
        errors = []
        frontend_status = None
        backend_status = None

        # Start frontend
        if "frontend" in services and project.frontend and project.frontend.enabled:
            try:
                self._start_service(
                    project_name=project_name,
                    service_type="fe",
                    command=project.frontend.command,
                    port=project.frontend.port,
                    cwd=project.frontend.cwd,
                    project_path=project.path,
                    env=project.frontend.env
                )
                frontend_status = self._get_service_status(
                    f"{project_name}-fe",
                    project.frontend.port
                )
            except PM2Error as e:
                errors.append(f"Frontend: {e}")

        # Start backend
        if "backend" in services and project.backend and project.backend.enabled:
            try:
                self._start_service(
                    project_name=project_name,
                    service_type="be",
                    command=project.backend.command,
                    port=project.backend.port,
                    cwd=project.backend.cwd,
                    project_path=project.path,
                    env=project.backend.env
                )
                backend_status = self._get_service_status(
                    f"{project_name}-be",
                    project.backend.port
                )
            except PM2Error as e:
                errors.append(f"Backend: {e}")

        if errors:
            return OperationResult(
                success=False,
                message=f"Errors: {'; '.join(errors)}",
                project_name=project_name,
                frontend=frontend_status,
                backend=backend_status
            )

        # Build success message
        urls = []
        if frontend_status and frontend_status.url:
            urls.append(f"Frontend: {frontend_status.url}")
        if backend_status and backend_status.url:
            urls.append(f"Backend: {backend_status.url}")

        message = f"Project '{project_name}' started successfully"
        if urls:
            message += f". {', '.join(urls)}"

        return OperationResult(
            success=True,
            message=message,
            project_name=project_name,
            frontend=frontend_status,
            backend=backend_status
        )

    def _start_service(
        self,
        project_name: str,
        service_type: str,
        command: str,
        port: Optional[int],
        cwd: Optional[str],
        project_path: str,
        env: dict
    ) -> None:
        """Start a single service via PM2"""
        pm2_name = f"{project_name}-{service_type}"

        # Determine working directory
        work_dir = project_path
        if cwd:
            work_dir = os.path.join(project_path, cwd)

        # Build environment variables
        full_env = os.environ.copy()
        full_env.update(env)
        if port:
            full_env["PORT"] = str(port)

        # Check if already running
        existing = self._get_pm2_process(pm2_name)
        if existing and existing.get("pm2_env", {}).get("status") == "online":
            return  # Already running

        # Stop if exists but not running
        if existing:
            self._run_pm2_command(["delete", pm2_name])

        # Build PM2 start command using bash interpreter
        # This ensures Python/npm commands are executed correctly
        pm2_args = [
            "start",
            "bash",
            "--name", pm2_name,
            "--cwd", work_dir,
            "--interpreter", "none",
            "--",
            "-c",
            command  # Execute the full command as a bash script
        ]

        result = self._run_pm2_command(pm2_args)
        if result.returncode != 0:
            raise PM2Error(f"Failed to start: {result.stderr}")

    def stop_project(
        self,
        project_name: str,
        services: List[str] = None
    ) -> OperationResult:
        """
        Stop a project.

        Args:
            project_name: Name of the project
            services: List of services to stop or None for all

        Returns:
            OperationResult
        """
        project = self.registry.get_project(project_name)
        if not project:
            return OperationResult(
                success=False,
                message=f"Project '{project_name}' not found",
                project_name=project_name,
                frontend=None,
                backend=None
            )

        services = services or ["frontend", "backend"]
        errors = []

        # Stop frontend
        if "frontend" in services:
            pm2_name = f"{project_name}-fe"
            result = self._run_pm2_command(["stop", pm2_name])
            if result.returncode != 0 and "not found" not in result.stderr.lower():
                errors.append(f"Frontend: {result.stderr}")

        # Stop backend
        if "backend" in services:
            pm2_name = f"{project_name}-be"
            result = self._run_pm2_command(["stop", pm2_name])
            if result.returncode != 0 and "not found" not in result.stderr.lower():
                errors.append(f"Backend: {result.stderr}")

        # Get updated status
        status = self.get_project_status(project_name)

        if errors:
            return OperationResult(
                success=False,
                message=f"Errors: {'; '.join(errors)}",
                project_name=project_name,
                frontend=status.frontend if status else None,
                backend=status.backend if status else None
            )

        return OperationResult(
            success=True,
            message=f"Project '{project_name}' stopped",
            project_name=project_name,
            frontend=status.frontend if status else None,
            backend=status.backend if status else None
        )

    def restart_project(self, project_name: str) -> OperationResult:
        """Restart a project"""
        stop_result = self.stop_project(project_name)
        if not stop_result.success:
            return stop_result

        return self.start_project(project_name)

    def start_all(self, filter_tags: List[str] = None) -> List[OperationResult]:
        """Start all projects"""
        results = []
        for project in self.registry.list_projects(filter_tags=filter_tags):
            result = self.start_project(project.name)
            results.append(result)
        return results

    def stop_all(self, filter_tags: List[str] = None) -> List[OperationResult]:
        """Stop all projects"""
        results = []
        for project in self.registry.list_projects(filter_tags=filter_tags):
            result = self.stop_project(project.name)
            results.append(result)
        return results

    def get_logs(
        self,
        project_name: str,
        service: str = "backend",
        lines: int = 100
    ) -> str:
        """
        Get logs for a project service.

        Args:
            project_name: Name of the project
            service: "frontend", "backend", or "both"
            lines: Number of lines to return

        Returns:
            Log content as string
        """
        project = self.registry.get_project(project_name)
        if not project:
            return f"Project '{project_name}' not found"

        logs = []

        if service in ["backend", "both"]:
            pm2_name = f"{project_name}-be"
            log_file = self.pm2_log_dir / f"{pm2_name}-out.log"
            error_file = self.pm2_log_dir / f"{pm2_name}-error.log"

            if log_file.exists():
                logs.append(f"=== {pm2_name} stdout ===")
                logs.append(self._tail_file(log_file, lines))

            if error_file.exists():
                error_content = self._tail_file(error_file, lines // 2)
                if error_content.strip():
                    logs.append(f"\n=== {pm2_name} stderr ===")
                    logs.append(error_content)

        if service in ["frontend", "both"]:
            pm2_name = f"{project_name}-fe"
            log_file = self.pm2_log_dir / f"{pm2_name}-out.log"
            error_file = self.pm2_log_dir / f"{pm2_name}-error.log"

            if log_file.exists():
                logs.append(f"=== {pm2_name} stdout ===")
                logs.append(self._tail_file(log_file, lines))

            if error_file.exists():
                error_content = self._tail_file(error_file, lines // 2)
                if error_content.strip():
                    logs.append(f"\n=== {pm2_name} stderr ===")
                    logs.append(error_content)

        if not logs:
            return "No logs found"

        return "\n".join(logs)

    def _tail_file(self, path: Path, lines: int) -> str:
        """Get last N lines from a file"""
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                all_lines = f.readlines()
                return "".join(all_lines[-lines:])
        except Exception as e:
            return f"Error reading log: {e}"

    def generate_ecosystem_config(self) -> str:
        """
        Generate PM2 ecosystem config file.

        Returns:
            Path to generated config file
        """
        apps = []

        for project in self.registry.list_projects():
            if project.frontend and project.frontend.enabled:
                cmd_parts = project.frontend.command.split()
                work_dir = project.path
                if project.frontend.cwd:
                    work_dir = os.path.join(project.path, project.frontend.cwd)

                apps.append({
                    "name": f"{project.name}-fe",
                    "script": cmd_parts[0],
                    "args": " ".join(cmd_parts[1:]) if len(cmd_parts) > 1 else "",
                    "cwd": work_dir,
                    "env": {
                        "PORT": str(project.frontend.port),
                        **project.frontend.env
                    }
                })

            if project.backend and project.backend.enabled:
                cmd_parts = project.backend.command.split()
                work_dir = project.path
                if project.backend.cwd:
                    work_dir = os.path.join(project.path, project.backend.cwd)

                apps.append({
                    "name": f"{project.name}-be",
                    "script": cmd_parts[0],
                    "args": " ".join(cmd_parts[1:]) if len(cmd_parts) > 1 else "",
                    "cwd": work_dir,
                    "env": {
                        "PORT": str(project.backend.port),
                        **project.backend.env
                    }
                })

        config = {
            "apps": apps
        }

        # Write config file
        config_path = self.data_dir.parent / "ecosystem.config.js"
        config_content = f"// Auto-generated by Dev Orchestrator\n// Do not edit manually\n\nmodule.exports = {json.dumps(config, indent=2)};\n"
        config_path.write_text(config_content)

        return str(config_path)
