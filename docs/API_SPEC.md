# Dev Orchestrator API 規格

## 概述

本文件定義 Dev Orchestrator 的所有 API 介面，包括：
1. **Core Services API** - Python 內部模組介面
2. **MCP Tools API** - 暴露給 Claude 的工具介面
3. **Dashboard API** - Streamlit 內部呼叫介面

---

## 1. Core Services API

### 1.1 PortManager

端口管理模組，負責分配和檢查端口。

#### `PortManager.find_available_port()`

尋找指定範圍內的可用端口。

```python
def find_available_port(
    start: int = 3000,
    end: int = 3099,
    exclude: list[int] = None
) -> int | None
```

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| start | int | 3000 | 起始端口 |
| end | int | 3099 | 結束端口 |
| exclude | list[int] | None | 排除的端口列表 |

| 回傳 | 說明 |
|------|------|
| int | 找到的可用端口 |
| None | 範圍內無可用端口 |

---

#### `PortManager.is_port_in_use()`

檢查端口是否被系統佔用。

```python
def is_port_in_use(port: int) -> bool
```

| 參數 | 類型 | 說明 |
|------|------|------|
| port | int | 要檢查的端口 |

| 回傳 | 說明 |
|------|------|
| True | 端口被佔用 |
| False | 端口可用 |

---

#### `PortManager.allocate_ports()`

為專案分配前後端端口。

```python
def allocate_ports(
    project_name: str,
    need_frontend: bool = True,
    need_backend: bool = True
) -> dict
```

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| project_name | str | 必填 | 專案名稱 |
| need_frontend | bool | True | 是否需要前端端口 |
| need_backend | bool | True | 是否需要後端端口 |

| 回傳結構 | 說明 |
|----------|------|
| `{ "frontend": 3001, "backend": 8001 }` | 分配的端口 |

| 例外 | 說明 |
|------|------|
| PortExhaustedError | 無可用端口 |

---

#### `PortManager.release_ports()`

釋放專案佔用的端口。

```python
def release_ports(project_name: str) -> bool
```

---

### 1.2 ProjectRegistry

專案註冊表模組，管理專案配置。

#### `ProjectRegistry.list_projects()`

列出所有專案。

```python
def list_projects(
    filter_tags: list[str] = None,
    include_status: bool = True
) -> list[ProjectInfo]
```

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| filter_tags | list[str] | None | 按標籤篩選 |
| include_status | bool | True | 是否包含運行狀態 |

| 回傳 | 說明 |
|------|------|
| list[ProjectInfo] | 專案資訊列表 |

---

#### `ProjectRegistry.get_project()`

取得單一專案詳情。

```python
def get_project(name: str) -> ProjectInfo | None
```

---

#### `ProjectRegistry.register_project()`

註冊新專案。

```python
def register_project(config: ProjectConfig) -> ProjectInfo
```

**ProjectConfig 結構**：

```python
@dataclass
class ProjectConfig:
    name: str                    # 專案名稱（唯一識別符）
    path: str                    # 專案根目錄絕對路徑
    frontend: ServiceConfig | None  # 前端服務配置
    backend: ServiceConfig | None   # 後端服務配置
    env_vars: dict[str, str] = None # 環境變數
    tags: list[str] = None       # 分類標籤

@dataclass
class ServiceConfig:
    command: str                 # 啟動指令
    port: int | None = None      # 端口（None 表示自動分配）
    cwd: str | None = None       # 工作目錄（預設為專案 path）
    enabled: bool = True         # 是否啟用
```

| 例外 | 說明 |
|------|------|
| ProjectExistsError | 專案名稱已存在 |
| InvalidPathError | 專案路徑不存在 |

---

#### `ProjectRegistry.update_project()`

更新專案配置。

```python
def update_project(name: str, updates: dict) -> ProjectInfo
```

---

#### `ProjectRegistry.remove_project()`

移除專案（不會刪除實際檔案）。

```python
def remove_project(name: str, stop_if_running: bool = True) -> bool
```

---

### 1.3 ProcessController

進程控制模組，與 PM2 互動。

#### `ProcessController.start_project()`

啟動專案服務。

```python
def start_project(
    name: str,
    services: list[str] = None  # ["frontend", "backend"] 或 None 表示全部
) -> StartResult
```

**StartResult 結構**：

```python
@dataclass
class StartResult:
    success: bool
    frontend: ServiceStatus | None
    backend: ServiceStatus | None
    message: str

@dataclass
class ServiceStatus:
    name: str           # PM2 進程名稱
    status: str         # "online" | "stopped" | "errored"
    pid: int | None     # 進程 ID
    port: int           # 服務端口
    url: str            # 訪問 URL
```

---

#### `ProcessController.stop_project()`

停止專案服務。

```python
def stop_project(
    name: str,
    services: list[str] = None
) -> StopResult
```

---

#### `ProcessController.restart_project()`

重啟專案服務。

```python
def restart_project(name: str) -> StartResult
```

---

#### `ProcessController.get_status()`

取得專案運行狀態。

```python
def get_status(name: str = None) -> dict | list[dict]
```

| 參數 | 回傳 |
|------|------|
| 指定 name | 該專案的狀態 dict |
| name=None | 所有專案的狀態列表 |

**狀態 dict 結構**：

```python
{
    "name": "krush",
    "frontend": {
        "status": "online",  # online | stopped | errored | not_started
        "pid": 12345,
        "port": 3001,
        "uptime": "2h 30m",
        "memory": "45.2 MB",
        "cpu": "0.1%"
    },
    "backend": {
        "status": "online",
        "pid": 12346,
        "port": 8001,
        "uptime": "2h 30m",
        "memory": "120.5 MB",
        "cpu": "0.3%"
    }
}
```

---

#### `ProcessController.get_logs()`

取得專案 Log。

```python
def get_logs(
    name: str,
    service: str = "backend",  # "frontend" | "backend" | "both"
    lines: int = 100,
    follow: bool = False
) -> str | Generator[str, None, None]
```

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| name | str | 必填 | 專案名稱 |
| service | str | "backend" | 哪個服務的 Log |
| lines | int | 100 | 回傳行數 |
| follow | bool | False | 是否持續追蹤 |

---

#### `ProcessController.start_all()` / `stop_all()`

批次操作。

```python
def start_all(filter_tags: list[str] = None) -> list[StartResult]
def stop_all(filter_tags: list[str] = None) -> list[StopResult]
```

---

## 2. MCP Tools API

暴露給 Claude 的工具介面，遵循 MCP 協議。

### 2.1 list_projects

列出所有專案和狀態。

```json
{
  "name": "list_projects",
  "description": "列出所有已註冊的開發專案及其運行狀態",
  "inputSchema": {
    "type": "object",
    "properties": {
      "include_stopped": {
        "type": "boolean",
        "description": "是否包含已停止的專案",
        "default": true
      }
    }
  }
}
```

**回傳範例**：

```json
{
  "projects": [
    {
      "name": "krush",
      "status": "running",
      "frontend": { "port": 3001, "url": "http://localhost:3001" },
      "backend": { "port": 8001, "url": "http://localhost:8001" },
      "tags": ["dashboard", "python"]
    },
    {
      "name": "food-map",
      "status": "stopped",
      "frontend": { "port": 3002 },
      "backend": { "port": 8002 },
      "tags": ["map", "react"]
    }
  ],
  "summary": "2 專案，1 運行中，1 已停止"
}
```

---

### 2.2 start_project

啟動指定專案。

```json
{
  "name": "start_project",
  "description": "啟動指定的開發專案（前端和後端服務）",
  "inputSchema": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "description": "專案名稱"
      },
      "services": {
        "type": "array",
        "items": { "type": "string", "enum": ["frontend", "backend"] },
        "description": "要啟動的服務，預設全部"
      }
    },
    "required": ["name"]
  }
}
```

**回傳範例**：

```json
{
  "success": true,
  "message": "KRUSH 專案已啟動",
  "services": {
    "frontend": {
      "status": "online",
      "url": "http://localhost:3001"
    },
    "backend": {
      "status": "online",
      "url": "http://localhost:8001"
    }
  }
}
```

---

### 2.3 stop_project

停止指定專案。

```json
{
  "name": "stop_project",
  "description": "停止指定的開發專案",
  "inputSchema": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "description": "專案名稱"
      }
    },
    "required": ["name"]
  }
}
```

---

### 2.4 allocate_project

為新專案分配端口並註冊。

```json
{
  "name": "allocate_project",
  "description": "為新專案分配端口並註冊到系統",
  "inputSchema": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "description": "專案名稱（英文，用於識別）"
      },
      "path": {
        "type": "string",
        "description": "專案根目錄的絕對路徑"
      },
      "frontend_command": {
        "type": "string",
        "description": "前端啟動指令，如 'npm run dev'"
      },
      "backend_command": {
        "type": "string",
        "description": "後端啟動指令，如 'python main.py'"
      },
      "tags": {
        "type": "array",
        "items": { "type": "string" },
        "description": "分類標籤"
      }
    },
    "required": ["name", "path"]
  }
}
```

**回傳範例**：

```json
{
  "success": true,
  "message": "專案 analyze_v2 已註冊",
  "allocated_ports": {
    "frontend": 3004,
    "backend": 8004
  },
  "env_file_created": true,
  "next_steps": [
    "執行 'start_project(\"analyze_v2\")' 啟動專案",
    "或在 Dashboard 中點擊啟動按鈕"
  ]
}
```

---

### 2.5 get_project_logs

取得專案 Log。

```json
{
  "name": "get_project_logs",
  "description": "取得指定專案的運行日誌",
  "inputSchema": {
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
}
```

---

### 2.6 get_port_status

查看端口使用情況。

```json
{
  "name": "get_port_status",
  "description": "查看端口使用情況和可用端口",
  "inputSchema": {
    "type": "object",
    "properties": {
      "range": {
        "type": "string",
        "enum": ["frontend", "backend", "all"],
        "description": "查看的端口範圍",
        "default": "all"
      }
    }
  }
}
```

**回傳範例**：

```json
{
  "frontend_range": "3000-3099",
  "backend_range": "8000-8099",
  "used_ports": {
    "frontend": [3001, 3002, 3003],
    "backend": [8001, 8002, 8003]
  },
  "next_available": {
    "frontend": 3004,
    "backend": 8004
  },
  "utilization": {
    "frontend": "3%",
    "backend": "3%"
  }
}
```

---

## 3. 錯誤處理

### 錯誤碼定義

| 錯誤碼 | 名稱 | 說明 |
|--------|------|------|
| E001 | ProjectNotFoundError | 專案不存在 |
| E002 | ProjectExistsError | 專案名稱已存在 |
| E003 | InvalidPathError | 專案路徑無效 |
| E004 | PortExhaustedError | 無可用端口 |
| E005 | PortInUseError | 指定端口被佔用 |
| E006 | PM2Error | PM2 操作失敗 |
| E007 | ServiceNotRunningError | 服務未運行 |
| E008 | ConfigError | 配置檔案錯誤 |

### 錯誤回傳格式

```python
@dataclass
class OperationError:
    code: str           # 錯誤碼
    message: str        # 人類可讀訊息
    details: dict       # 詳細資訊
    suggestions: list   # 建議的解決方案
```

**MCP 錯誤回傳範例**：

```json
{
  "success": false,
  "error": {
    "code": "E001",
    "message": "找不到專案 'unknown_project'",
    "suggestions": [
      "使用 list_projects 查看所有可用專案",
      "檢查專案名稱是否正確"
    ]
  }
}
```

---

## 4. 事件與通知

### 系統事件

| 事件 | 觸發時機 | 資料 |
|------|---------|------|
| project.started | 專案啟動完成 | project_name, services |
| project.stopped | 專案停止完成 | project_name |
| project.error | 專案發生錯誤 | project_name, error |
| project.registered | 新專案註冊 | project_config |
| port.allocated | 端口分配 | project_name, ports |
| port.exhausted | 端口耗盡警告 | range, utilization |

### 未來擴展：Webhook 通知

```python
# 配置範例（未來實作）
notifications:
  webhook:
    url: "https://your-webhook.com/notify"
    events: ["project.error", "port.exhausted"]
```
