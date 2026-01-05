# 故障排除指南

## 常見問題

### 1. PM2 找不到

**症狀**：
```
PM2Error: PM2 is not installed
```

**解決方案**：
```bash
# 安裝 PM2
npm install -g pm2

# 驗證安裝
pm2 --version
```

### 2. 端口被佔用

**症狀**：
- 專案無法啟動
- 錯誤訊息提到 "address already in use"

**解決方案**：
```bash
# 查看佔用端口的進程
lsof -i :3001

# 終止進程
kill -9 <PID>

# 或者讓系統分配新端口
# 在 Dashboard 移除專案後重新註冊
```

### 3. 專案啟動失敗

**症狀**：
- 點擊啟動後狀態仍為停止
- PM2 顯示 errored 狀態

**排查步驟**：

1. 檢查 PM2 Log：
```bash
pm2 logs <project-name>-be
```

2. 確認專案路徑正確：
```bash
ls /path/to/project
```

3. 確認啟動指令正確：
```bash
cd /path/to/project
python main.py  # 或你的指令
```

4. 確認虛擬環境路徑正確（如果使用）：
```bash
/path/to/project/.venv/bin/python --version
```

### 4. 虛擬環境模組找不到

**症狀**：
```
ModuleNotFoundError: No module named 'xxx'
```

**原因**：
啟動指令沒有使用專案的虛擬環境

**解決方案**：
確保啟動指令使用**絕對路徑**指向虛擬環境：

```bash
# 錯誤
streamlit run main.py

# 正確
/full/path/to/project/.venv/bin/streamlit run main.py
```

### 5. Dashboard 無法啟動

**症狀**：
- Streamlit 報錯
- 瀏覽器無法開啟 8500

**解決方案**：
```bash
# 確認 Streamlit 已安裝
pip install streamlit

# 檢查端口是否被佔用
lsof -i :8500

# 使用其他端口
streamlit run src/dashboard/app.py --server.port 8502
```

### 6. MCP Server 無法連線

**症狀**：
- Claude 看不到 dev-orchestrator tools
- MCP 連線失敗

**排查步驟**：

1. 驗證 MCP Server 可以獨立運行：
```bash
cd /path/to/dev-orchestrator
python -m src.mcp_server.server
# 應該不報錯並等待輸入
```

2. 檢查配置路徑：
- 確認 `cwd` 路徑正確
- 確認 `PYTHONPATH` 設定正確

3. 重新啟動 Claude Code：
```bash
# 完全關閉後重新開啟
```

4. 確認 MCP 已註冊：
```bash
claude mcp list
```

### 7. projects.json 損壞

**症狀**：
- JSON 解析錯誤
- 專案列表顯示異常

**解決方案**：

1. 檢查備份：
```bash
ls data/backups/
```

2. 恢復最近的備份：
```bash
cp data/backups/projects_YYYYMMDD_HHMMSS.json data/projects.json
```

3. 如果沒有備份，重置：
```bash
cp data/projects.template.json data/projects.json
```

### 8. 休眠後服務沒有恢復

**症狀**：
- 蓋上電腦再打開後服務停止
- PM2 顯示 stopped 狀態

**解決方案**：

PM2 管理的服務通常會自動恢復。如果沒有：

```bash
# 手動重啟所有
pm2 restart all

# 或在 Dashboard 點擊「全部啟動」
```

如果經常發生，可以設定開機自動恢復：
```bash
pm2 save
pm2 startup
```

## 日誌位置

- **PM2 日誌**: `~/.pm2/logs/`
- **專案備份**: `data/backups/`

## 取得更多幫助

1. 檢查 PM2 狀態：`pm2 status`
2. 檢查 PM2 日誌：`pm2 logs --lines 50`
3. 檢查專案配置：`cat data/projects.json`
