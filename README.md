# Zero-LLM ML Digest

Zero-LLM ML Digest 是一個無需生成式 AI 的 MVP，會在每個週期選出 3 篇 paper（Trending / Quality / Exploration），並透過 SMTP 寄送 HTML + Text Digest 給自己。資料來源包含 arXiv、OpenReview、Hugging Face Papers 公開端點。

## 安裝方式

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 設定檔說明

範例設定檔位於 `config/config.example.yaml`，可以複製成自己的設定檔並修改：

- `schedule.mode`: `biweekly` 或 `monthly`
- `schedule.window_days`: 資料抓取時間窗（biweekly 預設 14 天）
- `sources.arxiv.categories`: arXiv 分類
- `sources.hf.queries`: Hugging Face Papers 搜尋關鍵字
- `sources.openreview.venues`: OpenReview venue（可替換為其他年份/會議）
- `topics.buckets`: 規則化主題關鍵字
- `email`: SMTP 設定（請勿直接寫入密碼）

> Gmail 使用者請申請 App Password，並透過環境變數 `SMTP_PASSWORD` 提供密碼，請勿使用一般登入密碼。

## 執行方式

Dry-run（不寄信，只產出 artifacts）：

```bash
python -m mldigest.run --config config/config.example.yaml --dry-run --print
```

執行後會在 `runs/` 產生 JSON/HTML/Text 產物：

- `digest_YYYYMMDD_HHMMSS.json`
- `digest_YYYYMMDD_HHMMSS.html`
- `digest_YYYYMMDD_HHMMSS.txt`

## 常見問題

### Hugging Face 端點變動

HF 端點若失效，系統會自動忽略 HF 命中，Trending 角色會降級到 `arXiv 近期 + 主題命中` 方案，仍可選出 3 篇。

### OpenReview venue 調整

OpenReview 的 venue 名稱會因年度而不同，請修改 `sources.openreview.venues`，例如：

```yaml
sources:
  openreview:
    venues: ["ICLR.cc/2024/Conference"]
```

如果 OpenReview 端點失效，Quality 角色會降級到 arXiv 近期 fallback，流程仍可完成。
