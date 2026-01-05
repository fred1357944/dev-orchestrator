# Dev Orchestrator MCP Server 設定指南

## 快速設定

將以下配置加入你的 Claude 設定檔：

### 方法一：透過 Claude Code 指令

```bash
claude mcp add dev-orchestrator -s user -- /path/to/dev-orchestrator/.venv/bin/python -m src.mcp_server.server
```

請將 `/path/to/dev-orchestrator` 替換為你的實際安裝路徑。

### 方法二：手動編輯設定檔

編輯 `~/.claude.json`，在 `mcpServers` 區段加入：

```json
{
  "mcpServers": {
    "dev-orchestrator": {
      "type": "stdio",
      "command": "/path/to/dev-orchestrator/.venv/bin/python",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "/path/to/dev-orchestrator",
      "env": {
        "PYTHONPATH": "/path/to/dev-orchestrator"
      }
    }
  }
}
```

請將所有 `/path/to/dev-orchestrator` 替換為你的實際安裝路徑。

## 可用的 Tools

設定完成後，Claude 可以使用以下工具：

| Tool | 功能 |
|------|------|
| `list_projects` | 列出所有專案和狀態 |
| `start_project` | 啟動指定專案 |
| `stop_project` | 停止指定專案 |
| `restart_project` | 重啟專案 |
| `allocate_project` | 註冊新專案並分配端口 |
| `remove_project` | 移除專案 |
| `get_project_logs` | 查看專案 Log |
| `get_port_status` | 查看端口使用情況 |
| `start_all_projects` | 啟動所有專案 |
| `stop_all_projects` | 停止所有專案 |

## 使用範例

設定完成後，你可以對 Claude 說：

```
「幫我列出所有專案」
「啟動 my-project 專案」
「幫我新增一個專案叫 my-api，路徑是 /path/to/project」
「停止所有專案」
「查看 my-project 的 Log」
```

## 驗證設定

重新啟動 Claude Code 後，執行：

```bash
claude mcp list
```

應該可以看到 `dev-orchestrator` 出現在列表中。

## 故障排除

### MCP Server 無法啟動

1. 確認 Python 路徑正確
2. 確認依賴已安裝：`pip install mcp pydantic`
3. 確認 PYTHONPATH 設定正確

### 工具無法呼叫

1. 確認 `cwd` 路徑正確
2. 檢查 `data/projects.json` 是否存在
3. 查看 Claude Code 的 MCP 日誌
