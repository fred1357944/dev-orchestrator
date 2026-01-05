# 5 分鐘快速開始

## 步驟 1: 安裝與設定 (1 分鐘)

```bash
# Clone 專案
git clone https://github.com/your-username/dev-orchestrator.git
cd dev-orchestrator

# 建立虛擬環境
python3 -m venv .venv
source .venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 初始化資料檔案
cp data/projects.template.json data/projects.json

# 確認 PM2 已安裝（如果沒有）
npm install -g pm2
```

## 步驟 2: 啟動 Dashboard (30 秒)

```bash
# 確保在虛擬環境中
source .venv/bin/activate

# 啟動 Dashboard
.venv/bin/streamlit run src/dashboard/app.py --server.port 8500
```

瀏覽器會自動開啟 http://localhost:8500

## 步驟 3: 新增你的第一個專案 (2 分鐘)

1. 在 Dashboard 左側點擊「新增專案」
2. 填寫表單：
   - **專案名稱**: `my-first-project`
   - **專案路徑**: `/path/to/your/project`
   - **後端啟動指令**: `python main.py` (或你的指令)
3. 點擊「註冊專案」

系統會自動分配端口（例如 Backend: 8001）

## 步驟 4: 啟動專案 (30 秒)

1. 回到「專案列表」
2. 找到你的專案，點擊「啟動」
3. 看到 [ON] 表示成功！

## 步驟 5: 查看 Log (1 分鐘)

1. 點擊左側「Log 監控」
2. 選擇你的專案
3. 即可看到運行日誌

---

## 下一步

### 設定 Claude 整合

讓你可以用自然語言操作專案：

```bash
claude mcp add dev-orchestrator -s user -- /path/to/dev-orchestrator/.venv/bin/python -m src.mcp_server.server
```

然後對 Claude 說：「幫我啟動 my-first-project」

### 讓 Dashboard 開機自動啟動

```bash
# 用 PM2 管理 Dashboard
pm2 start ".venv/bin/streamlit run src/dashboard/app.py --server.port 8500" --name "dev-dashboard"

# 設定開機自動啟動
pm2 save
pm2 startup
```

這樣每次開機，Dashboard 就會自動在 http://localhost:8500 運行！
