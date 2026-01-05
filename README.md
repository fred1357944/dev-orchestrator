# Dev Orchestrator

本地開發環境管理工具，統一管理多個開發專案的端口分配、進程控制和狀態監控。支援 Claude AI 協作。

## 功能特色

- **端口自動分配**：避免端口衝突，自動追蹤使用狀態
- **一鍵啟動/停止**：透過 Dashboard 或 Claude 指令控制專案
- **Log 即時監控**：集中查看所有專案的運行日誌
- **Claude AI 整合**：使用自然語言管理專案（MCP 協議）
- **虛擬環境支援**：自動使用專案的 venv/`.venv` 執行指令
- **休眠友好**：蓋上電腦再打開，PM2 自動恢復服務

## 快速開始

### 1. Clone 並設定

```bash
git clone https://github.com/your-username/dev-orchestrator.git
cd dev-orchestrator

# 建立虛擬環境
python3 -m venv .venv
source .venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 初始化資料檔案
cp data/projects.template.json data/projects.json
```

### 2. 確保 PM2 已安裝

```bash
npm install -g pm2
pm2 --version
```

### 3. 啟動 Dashboard

```bash
.venv/bin/streamlit run src/dashboard/app.py --server.port 8500
```

瀏覽器開啟 http://localhost:8500

### 4. 設定 MCP Server（Claude 整合）

```bash
claude mcp add dev-orchestrator -s user -- \
  /path/to/dev-orchestrator/.venv/bin/python \
  -m src.mcp_server.server
```

詳細說明請參考 `docs/MCP_SETUP.md`

## 使用指南

### 透過 Dashboard

1. 開啟 Dashboard (http://localhost:8500)
2. 點擊「新增專案」填寫專案資訊
3. 在專案列表點擊「啟動」

### 透過 Claude MCP

重啟 Claude Code 後，可使用自然語言：

```
「幫我啟動 my-project」
「列出所有專案」
「查看端口分配」
「停止所有專案」
「幫我新增一個專案叫 my-api，路徑是 /path/to/project」
```

### MCP 可用工具

| 工具 | 功能 |
|------|------|
| `list_projects` | 列出所有專案及運行狀態 |
| `start_project` | 啟動指定專案 |
| `stop_project` | 停止指定專案 |
| `restart_project` | 重啟專案 |
| `allocate_project` | 註冊新專案並分配端口 |
| `remove_project` | 移除專案（不刪除檔案） |
| `get_project_logs` | 查看專案日誌 |
| `get_port_status` | 查看端口使用情況 |
| `start_all_projects` | 啟動所有專案 |
| `stop_all_projects` | 停止所有專案 |

## 目錄結構

```
dev-orchestrator/
├── .venv/                    # Python 虛擬環境
├── src/
│   ├── core/                 # 核心邏輯
│   │   ├── models.py         # 資料模型
│   │   ├── port_manager.py   # 端口管理
│   │   ├── project_registry.py  # 專案註冊
│   │   └── process_controller.py # PM2 進程控制
│   ├── mcp_server/           # MCP Server
│   │   └── server.py
│   └── dashboard/            # Streamlit UI
│       └── app.py
├── data/
│   ├── projects.json         # 專案配置（單一數據源，gitignore）
│   ├── projects.template.json # 專案配置模板
│   └── backups/              # 自動備份
├── docs/                     # 設計文件
├── tests/                    # 測試
├── requirements.txt
└── README.md
```

## 配置

### 端口範圍

| 類型 | 範圍 | 說明 |
|------|------|------|
| Frontend | 3001-3099 | Vite, Streamlit, React 等 |
| Backend | 8001-8099 | FastAPI, Flask, Chainlit 等 |
| Dashboard | 8500 | Dev Orchestrator UI |
| Reserved | 3000, 8501 | 系統保留 |

### 專案啟動指令格式

使用虛擬環境的專案需要指定**絕對路徑**：

```bash
# Streamlit (使用專案 venv)
/full/path/to/project/.venv/bin/streamlit run main.py --server.port 3004

# FastAPI/Uvicorn
/full/path/to/project/venv/bin/uvicorn main:app --port 8005

# Chainlit
/full/path/to/project/venv/bin/chainlit run app.py --port 8006

# Node.js (不需要 venv)
npm run dev -- --port 3001
```

### 環境變數

註冊專案時會自動在專案目錄生成 `.env.local`：

```
FRONTEND_PORT=3001
BACKEND_PORT=8001
API_URL=http://localhost:8001
```

## PM2 命令參考

```bash
# 查看所有進程
pm2 list

# 查看 Log
pm2 logs

# 查看特定專案 Log
pm2 logs my-project-fe --lines 50

# 停止所有
pm2 stop all

# 重啟所有
pm2 restart all

# 清除 Log
pm2 flush

# 設定開機自動啟動
pm2 save
pm2 startup
```

## 故障排除

### 專案啟動失敗

1. 檢查 PM2 Log：`pm2 logs <project>-fe --lines 50`
2. 確認虛擬環境路徑正確
3. 確認依賴已安裝：`pip install -r requirements.txt`

### 端口被佔用

```bash
# 查看佔用端口的進程
lsof -i :3004

# 終止進程
kill -9 <PID>
```

### MCP Server 無法連線

1. 確認已加入 Claude 設定：`claude mcp list`
2. 重啟 Claude Code
3. 檢查 Python 路徑是否正確

詳細故障排除請參考 `docs/TROUBLESHOOTING.md`

## 測試

```bash
source .venv/bin/activate
pytest tests/ -v
```

## License

MIT
