# Dev Orchestrator 實作計畫

## 概述

本文件定義 Dev Orchestrator 的分階段實作計畫，包含具體任務、預估時間和驗收標準。

---

## 實作階段總覽

```
┌─────────────────────────────────────────────────────────────────┐
│                        實作時程                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1: 基礎建設        ████████░░░░░░░░░░░░  (4 tasks)       │
│  Phase 2: 進程控制        ░░░░░░░░████████░░░░  (4 tasks)       │
│  Phase 3: MCP 整合        ░░░░░░░░░░░░░░██████  (5 tasks)       │
│  Phase 4: Dashboard UI    ░░░░░░░░░░░░░░░░████  (5 tasks)       │
│  Phase 5: 整合優化        ░░░░░░░░░░░░░░░░░░██  (3 tasks)       │
│                                                                 │
│  總計：21 tasks                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: 基礎建設 (Foundation)

**目標**：建立專案骨架、資料結構、核心邏輯

### Task 1.1: 建立專案目錄結構

**描述**：建立完整的目錄結構和基礎檔案

**產出**：
```
.dev-orchestrator/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   └── __init__.py
│   ├── mcp_server/
│   │   └── __init__.py
│   └── dashboard/
│       └── __init__.py
├── data/
│   └── .gitkeep
├── logs/
│   └── .gitkeep
├── tests/
│   └── __init__.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

**驗收標準**：
- [ ] 所有目錄和基礎檔案已建立
- [ ] Python 套件結構正確（可 import）
- [ ] requirements.txt 包含基本依賴

---

### Task 1.2: 定義資料結構和初始化 projects.json

**描述**：根據 DATA_SCHEMA.md 建立初始資料檔

**產出**：
- `data/projects.json` - 空的初始結構
- `src/core/models.py` - Python dataclass 定義

**驗收標準**：
- [ ] projects.json 符合 Schema 定義
- [ ] Python models 可序列化/反序列化 JSON
- [ ] 包含驗證邏輯

---

### Task 1.3: 實作 PortManager 類別

**描述**：實作端口分配和檢查邏輯

**產出**：
- `src/core/port_manager.py`

**核心方法**：
- `find_available_port(start, end, exclude)`
- `is_port_in_use(port)` - Socket 檢查
- `allocate_ports(project_name)`
- `release_ports(project_name)`

**驗收標準**：
- [ ] Socket 檢查正確偵測端口佔用
- [ ] 分配邏輯避免衝突
- [ ] 單元測試覆蓋率 > 80%

---

### Task 1.4: 實作 ProjectRegistry 類別

**描述**：實作專案配置的 CRUD 操作

**產出**：
- `src/core/project_registry.py`

**核心方法**：
- `list_projects()`
- `get_project(name)`
- `register_project(config)`
- `update_project(name, updates)`
- `remove_project(name)`
- `_load()` / `_save()` - JSON 讀寫

**驗收標準**：
- [ ] CRUD 操作正確
- [ ] 自動備份機制運作
- [ ] 路徑和名稱驗證正確
- [ ] 單元測試覆蓋率 > 80%

---

## Phase 2: 進程控制 (Process Control)

**目標**：整合 PM2，實現專案啟動/停止功能

### Task 2.1: 安裝和配置 PM2

**描述**：確保 PM2 正確安裝並可從 Python 呼叫

**前置條件**：Node.js 已安裝

**步驟**：
1. 安裝 PM2: `npm install -g pm2`
2. 驗證安裝: `pm2 --version`
3. 測試 JSON 輸出: `pm2 jlist`

**驗收標準**：
- [ ] `pm2` 指令可用
- [ ] `pm2 jlist` 回傳有效 JSON
- [ ] Python subprocess 可呼叫 PM2

---

### Task 2.2: 實作 ProcessController 類別

**描述**：封裝 PM2 操作

**產出**：
- `src/core/process_controller.py`

**核心方法**：
- `start_project(name)` - 啟動專案
- `stop_project(name)` - 停止專案
- `restart_project(name)` - 重啟專案
- `get_status(name)` - 取得狀態
- `_run_pm2_command(args)` - 底層 PM2 呼叫

**驗收標準**：
- [ ] 可正確啟動/停止測試專案
- [ ] 狀態解析正確
- [ ] 錯誤處理完善

---

### Task 2.3: 建立 PM2 ecosystem 配置生成器

**描述**：根據 projects.json 自動生成 PM2 配置

**產出**：
- `src/core/ecosystem_generator.py`
- 生成的 `ecosystem.config.js`

**驗收標準**：
- [ ] 配置檔符合 PM2 格式
- [ ] 可用 `pm2 start ecosystem.config.js` 啟動
- [ ] 環境變數正確注入

---

### Task 2.4: 實作 Log 讀取功能

**描述**：讀取 PM2 Log 檔案

**產出**：
- `ProcessController.get_logs(name, lines)`

**Log 位置**：`~/.pm2/logs/`

**驗收標準**：
- [ ] 可讀取指定行數的 Log
- [ ] 支援 stdout 和 stderr
- [ ] 處理 Log 檔不存在的情況

---

## Phase 3: MCP 整合 (AI Integration)

**目標**：建立 MCP Server，讓 Claude 可以操作系統

### Task 3.1: 建立 MCP Server 框架

**描述**：使用 MCP Python SDK 建立基礎 Server

**產出**：
- `src/mcp_server/server.py`

**依賴**：
```
mcp
```

**驗收標準**：
- [ ] Server 可啟動且不報錯
- [ ] Claude Desktop 可連線

---

### Task 3.2: 實作 list_projects Tool

**描述**：第一個 MCP Tool，列出專案

**產出**：
- `list_projects` tool 定義和實作

**驗收標準**：
- [ ] Claude 可呼叫並取得專案列表
- [ ] 回傳格式清晰易讀

---

### Task 3.3: 實作 start/stop_project Tools

**描述**：專案啟動/停止 Tools

**產出**：
- `start_project` tool
- `stop_project` tool

**驗收標準**：
- [ ] Claude 可成功啟動/停止專案
- [ ] 回傳狀態和 URL

---

### Task 3.4: 實作 allocate_project Tool

**描述**：新專案註冊 Tool

**產出**：
- `allocate_project` tool

**驗收標準**：
- [ ] Claude 可註冊新專案
- [ ] 端口自動分配
- [ ] .env 檔自動生成（如啟用）

---

### Task 3.5: 註冊到 Claude 配置

**描述**：將 MCP Server 加入 Claude 配置

**產出**：
- 更新 `~/.claude/claude_desktop_config.json`

**配置範例**：
```json
{
  "mcpServers": {
    "dev-orchestrator": {
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "/path/to/.dev-orchestrator"
    }
  }
}
```

**驗收標準**：
- [ ] Claude Code 可看到 dev-orchestrator tools
- [ ] 所有 tools 可正常呼叫

---

## Phase 4: Dashboard UI

**目標**：建立 Streamlit 視覺化介面

### Task 4.1: 建立 Streamlit 應用框架

**描述**：基礎 Dashboard 骨架

**產出**：
- `src/dashboard/app.py`
- `src/dashboard/components/`

**驗收標準**：
- [ ] `streamlit run app.py` 可啟動
- [ ] 基本頁面結構完成

---

### Task 4.2: 實作專案列表頁面

**描述**：顯示所有專案和狀態

**功能**：
- 專案卡片展示
- 狀態燈（綠/灰/紅）
- 啟動/停止按鈕
- 篩選和搜尋

**驗收標準**：
- [ ] 專案列表正確顯示
- [ ] 狀態即時更新
- [ ] 按鈕操作有效

---

### Task 4.3: 實作 Log 查看功能

**描述**：Log 即時查看介面

**功能**：
- 選擇專案和服務
- Log 內容展示
- 自動刷新
- 搜尋/過濾

**驗收標準**：
- [ ] Log 正確顯示
- [ ] 可選擇 frontend/backend
- [ ] 刷新功能運作

---

### Task 4.4: 實作新增專案表單

**描述**：新專案註冊介面

**欄位**：
- 專案名稱
- 專案路徑（檔案瀏覽器）
- 前端指令
- 後端指令
- 標籤

**驗收標準**：
- [ ] 表單驗證正確
- [ ] 可成功註冊新專案
- [ ] 端口自動分配並顯示

---

### Task 4.5: 加入批次操作和系統狀態

**描述**：全域操作和監控

**功能**：
- Start All / Stop All 按鈕
- 端口使用概覽
- 系統狀態（PM2、MCP Server）

**驗收標準**：
- [ ] 批次操作正確
- [ ] 狀態概覽準確

---

## Phase 5: 整合與優化

**目標**：端到端測試、錯誤處理、文件完善

### Task 5.1: 端到端測試

**描述**：完整流程測試

**測試情境**：
1. 新增專案 → 啟動 → 查看 Log → 停止 → 移除
2. 用 Claude 操作完整流程
3. Dashboard 操作完整流程
4. 休眠/喚醒後服務恢復測試

**驗收標準**：
- [ ] 所有情境通過
- [ ] 無記憶體洩漏
- [ ] 錯誤處理完善

---

### Task 5.2: 錯誤處理和邊界情況

**描述**：強化錯誤處理

**情境**：
- 專案路徑不存在
- 端口被外部程式佔用
- PM2 未安裝
- JSON 檔案損壞
- 網路斷線

**驗收標準**：
- [ ] 所有錯誤有清晰提示
- [ ] 系統不會崩潰
- [ ] 自動恢復機制

---

### Task 5.3: 使用說明和快速開始指南

**描述**：完善文件

**產出**：
- `README.md` - 完整使用說明
- `docs/QUICKSTART.md` - 5 分鐘快速開始
- `docs/TROUBLESHOOTING.md` - 常見問題

**驗收標準**：
- [ ] 新使用者可按文件完成設定
- [ ] 常見問題有解答

---

## 依賴清單

### Python 依賴 (requirements.txt)

```
# Core
pydantic>=2.0
python-dotenv>=1.0

# MCP Server
mcp>=0.1.0

# Dashboard
streamlit>=1.28

# Process Management (optional, for direct PM2 communication)
# psutil>=5.9

# Development
pytest>=7.0
pytest-cov>=4.0
black>=23.0
ruff>=0.1
```

### 系統依賴

```bash
# Node.js (for PM2)
brew install node  # macOS

# PM2
npm install -g pm2
```

---

## 風險與緩解

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| PM2 版本不相容 | 低 | 中 | 鎖定測試過的版本 |
| MCP SDK 變更 | 中 | 高 | 關注更新日誌，及時調整 |
| 端口耗盡 | 低 | 低 | 提供清理功能和警告 |
| JSON 檔損壞 | 低 | 高 | 自動備份機制 |

---

## 成功指標

1. **功能完整性**：所有 Phase 1-4 功能正常運作
2. **穩定性**：連續運行 7 天無崩潰
3. **易用性**：5 分鐘內可完成首次設定
4. **Claude 整合**：所有 MCP Tools 可用
5. **效能**：Dashboard 響應時間 < 1 秒
