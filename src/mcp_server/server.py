"""MCP Server for Dev Orchestrator - Claude AI Integration"""

import asyncio
import json
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.project_registry import ProjectRegistry, ProjectExistsError, ProjectNotFoundError
from src.core.process_controller import ProcessController
from src.core.port_manager import PortManager

# Initialize server
server = Server("dev-orchestrator")

# Data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data"


def get_registry() -> ProjectRegistry:
    """Get a fresh ProjectRegistry instance"""
    return ProjectRegistry(DATA_DIR)


def get_controller() -> ProcessController:
    """Get a fresh ProcessController instance"""
    return ProcessController(DATA_DIR)


def get_port_manager() -> PortManager:
    """Get a fresh PortManager instance"""
    return PortManager(DATA_DIR / "projects.json")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="list_projects",
            description="列出所有已註冊的開發專案及其運行狀態",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_stopped": {
                        "type": "boolean",
                        "description": "是否包含已停止的專案",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="start_project",
            description="啟動指定的開發專案（前端和後端服務）",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "專案名稱"
                    },
                    "services": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["frontend", "backend"]},
                        "description": "要啟動的服務，預設全部"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="stop_project",
            description="停止指定的開發專案",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "專案名稱"
                    },
                    "services": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["frontend", "backend"]},
                        "description": "要停止的服務，預設全部"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="restart_project",
            description="重啟指定的開發專案",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "專案名稱"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="allocate_project",
            description="為新專案分配端口並註冊到系統",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "專案名稱（英文小寫，可用連字號）"
                    },
                    "path": {
                        "type": "string",
                        "description": "專案根目錄的絕對路徑"
                    },
                    "display_name": {
                        "type": "string",
                        "description": "顯示名稱（可含中文）"
                    },
                    "frontend_command": {
                        "type": "string",
                        "description": "前端啟動指令，如 'npm run dev' 或 'streamlit run app.py'"
                    },
                    "backend_command": {
                        "type": "string",
                        "description": "後端啟動指令，如 'python main.py' 或 'uvicorn main:app'"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "分類標籤"
                    }
                },
                "required": ["name", "path"]
            }
        ),
        Tool(
            name="remove_project",
            description="從系統移除專案（不會刪除實際檔案）",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "專案名稱"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="get_project_logs",
            description="取得指定專案的運行日誌",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "專案名稱"
                    },
                    "service": {
                        "type": "string",
                        "enum": ["frontend", "backend", "both"],
                        "description": "要查看的服務",
                        "default": "backend"
                    },
                    "lines": {
                        "type": "integer",
                        "description": "回傳行數",
                        "default": 50
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="get_port_status",
            description="查看端口使用情況和可用端口",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="start_all_projects",
            description="啟動所有已註冊的專案",
            inputSchema={
                "type": "object",
                "properties": {
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "只啟動有這些標籤的專案"
                    }
                }
            }
        ),
        Tool(
            name="stop_all_projects",
            description="停止所有已註冊的專案",
            inputSchema={
                "type": "object",
                "properties": {
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "只停止有這些標籤的專案"
                    }
                }
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""

    try:
        if name == "list_projects":
            return await handle_list_projects(arguments)

        elif name == "start_project":
            return await handle_start_project(arguments)

        elif name == "stop_project":
            return await handle_stop_project(arguments)

        elif name == "restart_project":
            return await handle_restart_project(arguments)

        elif name == "allocate_project":
            return await handle_allocate_project(arguments)

        elif name == "remove_project":
            return await handle_remove_project(arguments)

        elif name == "get_project_logs":
            return await handle_get_logs(arguments)

        elif name == "get_port_status":
            return await handle_port_status(arguments)

        elif name == "start_all_projects":
            return await handle_start_all(arguments)

        elif name == "stop_all_projects":
            return await handle_stop_all(arguments)

        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False)
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, ensure_ascii=False)
        )]


async def handle_list_projects(arguments: dict) -> list[TextContent]:
    """Handle list_projects tool"""
    controller = get_controller()
    statuses = controller.get_all_status()

    projects = []
    running = 0
    stopped = 0

    for status in statuses:
        proj = {
            "name": status.name,
            "display_name": status.display_name,
            "status": status.overall_status
        }

        if status.frontend:
            proj["frontend"] = {
                "port": status.frontend.port,
                "status": status.frontend.status,
                "url": status.frontend.url
            }

        if status.backend:
            proj["backend"] = {
                "port": status.backend.port,
                "status": status.backend.status,
                "url": status.backend.url
            }

        projects.append(proj)

        if status.overall_status == "running":
            running += 1
        else:
            stopped += 1

    result = {
        "projects": projects,
        "summary": f"{len(projects)} 專案，{running} 運行中，{stopped} 已停止"
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, ensure_ascii=False, indent=2)
    )]


async def handle_start_project(arguments: dict) -> list[TextContent]:
    """Handle start_project tool"""
    controller = get_controller()
    name = arguments["name"]
    services = arguments.get("services")

    result = controller.start_project(name, services)

    response = {
        "success": result.success,
        "message": result.message,
        "services": {}
    }

    if result.frontend:
        response["services"]["frontend"] = {
            "status": result.frontend.status,
            "url": result.frontend.url
        }

    if result.backend:
        response["services"]["backend"] = {
            "status": result.backend.status,
            "url": result.backend.url
        }

    return [TextContent(
        type="text",
        text=json.dumps(response, ensure_ascii=False, indent=2)
    )]


async def handle_stop_project(arguments: dict) -> list[TextContent]:
    """Handle stop_project tool"""
    controller = get_controller()
    name = arguments["name"]
    services = arguments.get("services")

    result = controller.stop_project(name, services)

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": result.success,
            "message": result.message
        }, ensure_ascii=False, indent=2)
    )]


async def handle_restart_project(arguments: dict) -> list[TextContent]:
    """Handle restart_project tool"""
    controller = get_controller()
    name = arguments["name"]

    result = controller.restart_project(name)

    response = {
        "success": result.success,
        "message": result.message,
        "services": {}
    }

    if result.frontend:
        response["services"]["frontend"] = {
            "status": result.frontend.status,
            "url": result.frontend.url
        }

    if result.backend:
        response["services"]["backend"] = {
            "status": result.backend.status,
            "url": result.backend.url
        }

    return [TextContent(
        type="text",
        text=json.dumps(response, ensure_ascii=False, indent=2)
    )]


async def handle_allocate_project(arguments: dict) -> list[TextContent]:
    """Handle allocate_project tool"""
    registry = get_registry()

    try:
        project = registry.register_project(
            name=arguments["name"],
            path=arguments["path"],
            display_name=arguments.get("display_name"),
            frontend_command=arguments.get("frontend_command"),
            backend_command=arguments.get("backend_command"),
            tags=arguments.get("tags")
        )

        response = {
            "success": True,
            "message": f"專案 '{project.name}' 已註冊",
            "allocated_ports": {
                "frontend": project.frontend.port if project.frontend else None,
                "backend": project.backend.port if project.backend else None
            },
            "next_steps": [
                f"執行 start_project(\"{project.name}\") 啟動專案",
                "或在 Dashboard 中點擊啟動按鈕"
            ]
        }

    except ProjectExistsError as e:
        response = {
            "success": False,
            "error": str(e),
            "suggestions": ["使用不同的專案名稱", "或先移除現有專案"]
        }

    except Exception as e:
        response = {
            "success": False,
            "error": str(e)
        }

    return [TextContent(
        type="text",
        text=json.dumps(response, ensure_ascii=False, indent=2)
    )]


async def handle_remove_project(arguments: dict) -> list[TextContent]:
    """Handle remove_project tool"""
    registry = get_registry()
    controller = get_controller()
    name = arguments["name"]

    try:
        # Stop project first
        controller.stop_project(name)

        # Remove from registry
        registry.remove_project(name)

        response = {
            "success": True,
            "message": f"專案 '{name}' 已從系統移除（實際檔案未刪除）"
        }

    except ProjectNotFoundError as e:
        response = {
            "success": False,
            "error": str(e)
        }

    return [TextContent(
        type="text",
        text=json.dumps(response, ensure_ascii=False, indent=2)
    )]


async def handle_get_logs(arguments: dict) -> list[TextContent]:
    """Handle get_project_logs tool"""
    controller = get_controller()
    name = arguments["name"]
    service = arguments.get("service", "backend")
    lines = arguments.get("lines", 50)

    logs = controller.get_logs(name, service, lines)

    return [TextContent(
        type="text",
        text=logs
    )]


async def handle_port_status(arguments: dict) -> list[TextContent]:
    """Handle get_port_status tool"""
    port_manager = get_port_manager()
    status = port_manager.get_port_status()

    return [TextContent(
        type="text",
        text=json.dumps(status, ensure_ascii=False, indent=2)
    )]


async def handle_start_all(arguments: dict) -> list[TextContent]:
    """Handle start_all_projects tool"""
    controller = get_controller()
    tags = arguments.get("tags")

    results = controller.start_all(filter_tags=tags)

    started = sum(1 for r in results if r.success)
    failed = len(results) - started

    response = {
        "success": failed == 0,
        "message": f"啟動了 {started} 個專案" + (f"，{failed} 個失敗" if failed else ""),
        "results": [
            {"name": r.project_name, "success": r.success, "message": r.message}
            for r in results
        ]
    }

    return [TextContent(
        type="text",
        text=json.dumps(response, ensure_ascii=False, indent=2)
    )]


async def handle_stop_all(arguments: dict) -> list[TextContent]:
    """Handle stop_all_projects tool"""
    controller = get_controller()
    tags = arguments.get("tags")

    results = controller.stop_all(filter_tags=tags)

    stopped = sum(1 for r in results if r.success)
    failed = len(results) - stopped

    response = {
        "success": failed == 0,
        "message": f"停止了 {stopped} 個專案" + (f"，{failed} 個失敗" if failed else ""),
        "results": [
            {"name": r.project_name, "success": r.success}
            for r in results
        ]
    }

    return [TextContent(
        type="text",
        text=json.dumps(response, ensure_ascii=False, indent=2)
    )]


def main():
    """Main entry point"""
    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )

    asyncio.run(run())


if __name__ == "__main__":
    main()
