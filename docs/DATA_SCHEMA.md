# Dev Orchestrator 資料結構定義

## 概述

本文件定義 Dev Orchestrator 使用的所有資料結構，主要是 `projects.json` 的 Schema。

---

## projects.json

專案註冊表，是整個系統的**單一真實來源（Single Source of Truth）**。

### 檔案位置

```
.dev-orchestrator/data/projects.json
```

### 完整 Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Dev Orchestrator Projects Registry",
  "type": "object",
  "required": ["version", "projects", "port_allocation"],
  "properties": {
    "version": {
      "type": "string",
      "description": "Schema 版本",
      "example": "1.0.0"
    },
    "projects": {
      "type": "object",
      "description": "專案配置，key 為專案名稱",
      "additionalProperties": { "$ref": "#/definitions/Project" }
    },
    "port_allocation": {
      "$ref": "#/definitions/PortAllocation"
    },
    "settings": {
      "$ref": "#/definitions/Settings"
    },
    "metadata": {
      "$ref": "#/definitions/Metadata"
    }
  },
  "definitions": {
    "Project": { "...見下方..." },
    "PortAllocation": { "...見下方..." },
    "Settings": { "...見下方..." },
    "Metadata": { "...見下方..." }
  }
}
```

---

## 資料結構詳解

### 1. Project（專案配置）

每個專案的完整配置。

```json
{
  "name": "krush",
  "display_name": "KRUSH 舞蹈教室",
  "path": "/path/to/your/project",
  "description": "KRUSH 舞蹈教室的營運數據分析儀表板",

  "frontend": {
    "enabled": true,
    "port": 3001,
    "command": "streamlit run app.py",
    "cwd": null,
    "env": {
      "STREAMLIT_SERVER_PORT": "3001"
    },
    "health_check": {
      "path": "/",
      "timeout": 30
    }
  },

  "backend": {
    "enabled": true,
    "port": 8001,
    "command": "python -m uvicorn main:app --host 0.0.0.0",
    "cwd": "api",
    "env": {
      "DATABASE_URL": "sqlite:///./data.db"
    },
    "health_check": {
      "path": "/health",
      "timeout": 30
    }
  },

  "env_vars": {
    "API_URL": "http://localhost:8001",
    "DEBUG": "true"
  },

  "dependencies": [],
  "tags": ["dashboard", "python", "streamlit"],

  "created_at": "2024-01-05T10:30:00Z",
  "updated_at": "2024-01-05T14:20:00Z",

  "notes": "主要分析專案，每週一使用"
}
```

#### 欄位說明

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| name | string | ✅ | 專案唯一識別符（英文、小寫、連字號） |
| display_name | string | ❌ | 顯示名稱（可含中文） |
| path | string | ✅ | 專案根目錄絕對路徑 |
| description | string | ❌ | 專案描述 |
| frontend | ServiceConfig | ❌ | 前端服務配置 |
| backend | ServiceConfig | ❌ | 後端服務配置 |
| env_vars | object | ❌ | 共用環境變數 |
| dependencies | string[] | ❌ | 依賴的其他專案名稱 |
| tags | string[] | ❌ | 分類標籤 |
| created_at | ISO8601 | ✅ | 建立時間 |
| updated_at | ISO8601 | ✅ | 最後更新時間 |
| notes | string | ❌ | 備註 |

---

### 2. ServiceConfig（服務配置）

前端或後端服務的配置。

```json
{
  "enabled": true,
  "port": 3001,
  "command": "npm run dev",
  "cwd": null,
  "env": {},
  "health_check": {
    "path": "/",
    "timeout": 30
  }
}
```

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| enabled | boolean | ✅ | 是否啟用此服務 |
| port | integer | ✅ | 服務端口 |
| command | string | ✅ | 啟動指令 |
| cwd | string | ❌ | 工作目錄（相對於專案 path），null 表示專案根目錄 |
| env | object | ❌ | 服務專用環境變數 |
| health_check | HealthCheck | ❌ | 健康檢查配置 |

---

### 3. PortAllocation（端口分配記錄）

記錄端口分配狀態。

```json
{
  "frontend_range": {
    "start": 3000,
    "end": 3099,
    "reserved": [3000]
  },
  "backend_range": {
    "start": 8000,
    "end": 8099,
    "reserved": [8501]
  },
  "allocated": {
    "3001": "krush",
    "3002": "food-map",
    "8001": "krush",
    "8002": "food-map"
  }
}
```

| 欄位 | 說明 |
|------|------|
| frontend_range | 前端端口範圍和保留端口 |
| backend_range | 後端端口範圍和保留端口 |
| allocated | 已分配端口 → 專案名稱對應 |

---

### 4. Settings（全域設定）

系統層級設定。

```json
{
  "auto_generate_env": true,
  "env_file_name": ".env.local",
  "pm2_ecosystem_path": "./ecosystem.config.js",
  "log_retention_days": 7,
  "health_check_interval": 60,
  "dashboard_port": 8501,
  "default_tags": ["local"]
}
```

| 欄位 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| auto_generate_env | boolean | true | 註冊專案時自動生成 .env 檔 |
| env_file_name | string | ".env.local" | 生成的環境變數檔案名稱 |
| pm2_ecosystem_path | string | "./ecosystem.config.js" | PM2 配置檔路徑 |
| log_retention_days | integer | 7 | Log 保留天數 |
| health_check_interval | integer | 60 | 健康檢查間隔（秒） |
| dashboard_port | integer | 8501 | Dashboard 使用的端口 |
| default_tags | string[] | ["local"] | 新專案預設標籤 |

---

### 5. Metadata（元資料）

檔案元資料。

```json
{
  "created_at": "2024-01-01T00:00:00Z",
  "last_modified": "2024-01-05T14:30:00Z",
  "last_modified_by": "dashboard",
  "total_projects": 5,
  "active_projects": 2
}
```

---

## 完整範例

```json
{
  "version": "1.0.0",

  "projects": {
    "krush": {
      "name": "krush",
      "display_name": "KRUSH 舞蹈教室",
      "path": "/path/to/your/project",
      "description": "KRUSH 舞蹈教室營運分析",
      "frontend": {
        "enabled": true,
        "port": 3001,
        "command": "streamlit run app.py --server.port 3001",
        "cwd": null,
        "env": {}
      },
      "backend": {
        "enabled": true,
        "port": 8001,
        "command": "python -m uvicorn api.main:app --port 8001",
        "cwd": null,
        "env": {}
      },
      "env_vars": {
        "API_URL": "http://localhost:8001"
      },
      "dependencies": [],
      "tags": ["dashboard", "streamlit", "active"],
      "created_at": "2024-01-05T10:00:00Z",
      "updated_at": "2024-01-05T10:00:00Z",
      "notes": null
    },

    "food-map": {
      "name": "food-map",
      "display_name": "美食地圖",
      "path": "/path/to/another/project",
      "description": "外送美食地圖視覺化專案",
      "frontend": {
        "enabled": true,
        "port": 3002,
        "command": "npm run dev -- --port 3002",
        "cwd": "frontend",
        "env": {}
      },
      "backend": {
        "enabled": true,
        "port": 8002,
        "command": "python main.py --port 8002",
        "cwd": "backend",
        "env": {
          "DATABASE_URL": "postgresql://localhost/foodmap"
        }
      },
      "env_vars": {},
      "dependencies": [],
      "tags": ["map", "react", "python"],
      "created_at": "2024-01-03T15:00:00Z",
      "updated_at": "2024-01-04T09:30:00Z",
      "notes": null
    }
  },

  "port_allocation": {
    "frontend_range": {
      "start": 3000,
      "end": 3099,
      "reserved": [3000]
    },
    "backend_range": {
      "start": 8000,
      "end": 8099,
      "reserved": [8501]
    },
    "allocated": {
      "3001": "krush",
      "3002": "food-map",
      "8001": "krush",
      "8002": "food-map"
    }
  },

  "settings": {
    "auto_generate_env": true,
    "env_file_name": ".env.local",
    "pm2_ecosystem_path": "./ecosystem.config.js",
    "log_retention_days": 7,
    "health_check_interval": 60,
    "dashboard_port": 8501,
    "default_tags": ["local"]
  },

  "metadata": {
    "created_at": "2024-01-01T00:00:00Z",
    "last_modified": "2024-01-05T14:30:00Z",
    "last_modified_by": "mcp_server",
    "total_projects": 2,
    "active_projects": 1
  }
}
```

---

## 資料驗證規則

### 專案名稱規則

```
^[a-z][a-z0-9-]*$
```

- 必須以小寫字母開頭
- 只能包含小寫字母、數字、連字號
- 長度 2-50 字元
- 不可重複

### 路徑驗證

- 必須是絕對路徑
- 路徑必須存在且是目錄
- 必須有讀取權限

### 端口驗證

- Frontend: 3000-3099
- Backend: 8000-8099
- 不可與 reserved 重複
- 不可與其他專案重複

---

## 資料遷移

### 版本升級

當 Schema 版本升級時，系統會自動執行遷移：

```python
# 遷移腳本位置
.dev-orchestrator/migrations/
├── v1_0_0_to_v1_1_0.py
├── v1_1_0_to_v1_2_0.py
└── ...
```

### 備份策略

- 每次修改前自動備份
- 備份位置：`.dev-orchestrator/data/backups/`
- 命名格式：`projects_YYYYMMDD_HHMMSS.json`
- 保留最近 10 個備份

---

## 與其他檔案的關係

### ecosystem.config.js（PM2 配置）

由系統根據 `projects.json` 自動生成，不應手動編輯。

```javascript
// 自動生成，請勿手動編輯
module.exports = {
  apps: [
    {
      name: 'krush-fe',
      script: 'streamlit',
      args: 'run app.py --server.port 3001',
      cwd: '/path/to/your/project',
      env: { ... }
    },
    {
      name: 'krush-be',
      script: 'python',
      args: '-m uvicorn api.main:app --port 8001',
      cwd: '/path/to/your/project',
      env: { ... }
    }
  ]
};
```

### .env.local（專案環境變數）

在專案目錄下自動生成：

```bash
# Auto-generated by Dev Orchestrator
# Do not edit manually - changes will be overwritten

FRONTEND_PORT=3001
BACKEND_PORT=8001
API_URL=http://localhost:8001
DEBUG=true
```
