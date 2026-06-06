# Paper Insight

Paper Insight is a local-first paper monitoring app. It lets you configure research keywords and venues, search recent papers, generate a Chinese daily report with GPT, and send the report to yourself through a Feishu custom app bot.

## Local Setup

### One-command start

```bash
./start.sh
```

Open `http://127.0.0.1:5173`. Press `Ctrl-C` in the terminal to stop both the backend and frontend.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp ../.env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Configuration

Use the Config page to set:

- topic name
- keywords, one per line
- conference or journal names, one per line
- exclusion keywords, one per line
- search lookback window
- max results per source

Secrets stay in `backend/.env`, not in the browser.

## Feishu Setup

Create a Feishu custom app, enable bot capability, and make sure your account is in the app availability scope. Configure:

```env
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
FEISHU_RECIPIENT_ID=your_email@example.com
FEISHU_RECIPIENT_ID_TYPE=email
```

If email delivery fails in your tenant, switch `FEISHU_RECIPIENT_ID_TYPE` to `open_id` or `user_id` and set `FEISHU_RECIPIENT_ID` accordingly.

## OpenAI Setup

Configure an OpenAI-compatible chat completion endpoint:

```env
OPENAI_API_KEY=sk_xxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
```

If `OPENAI_API_KEY` is missing or the request fails, reports are still generated with metadata-only fallback summaries.

## Codex Automation Command

Run the full daily workflow:

```bash
curl -X POST http://127.0.0.1:8000/api/reports/generate-and-send
```

For a manual local smoke path:

```bash
curl http://127.0.0.1:8000/api/health
curl -X POST http://127.0.0.1:8000/api/papers/search
curl -X POST http://127.0.0.1:8000/api/reports/generate
```

## Tests

```bash
cd backend
source .venv/bin/activate
python -m pytest -v

cd ../frontend
npm test
npm run build
npm audit --omit=dev
```
