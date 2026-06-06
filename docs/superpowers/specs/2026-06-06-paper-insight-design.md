# Paper Insight Design

Date: 2026-06-06

## Goal

Paper Insight is a local-first paper monitoring tool. The first version lets the user configure research keywords and reference venues, search recent papers, generate a GPT-assisted daily report, review report history in a web UI, and send the report to the user's own Feishu account.

The first release prioritizes a reliable local workflow over cloud deployment:

1. Configure topics, keywords, venues, and exclusions in the web UI.
2. Search papers from selected sources.
3. Deduplicate and store paper metadata locally.
4. Generate Chinese daily summaries with an OpenAI-compatible GPT API.
5. Send the final report to the user through a Feishu custom app bot private message.
6. Let Codex automation or any external scheduler call a backend endpoint daily.

## Non-Goals For V1

- No multi-user account system.
- No production cloud deployment.
- No Celery, Redis, or distributed worker queue.
- No full OpenReview, DBLP, or Crossref integration in the first implementation.
- No Feishu event subscription, WebSocket bot chat, or interactive Feishu command handling.
- No automatic model fine-tuning from user feedback.

## Recommended Stack

- Frontend: React + Vite + TypeScript.
- Backend: FastAPI + Python.
- Database: SQLite for local persistence.
- ORM and schema setup: SQLAlchemy with local `create_all` for V1.
- HTTP client: httpx.
- Paper sources in V1: arXiv and Semantic Scholar.
- Summary provider: OpenAI-compatible chat completion API.
- Delivery provider in V1: Feishu custom app bot private message.

React + FastAPI is a good fit because the frontend can stay focused on configuration and report review, while the Python backend handles paper APIs, summarization, persistence, and Feishu delivery.

## Repository Layout

```text
paper_insight/
  frontend/
    src/
      components/
      pages/
      api/
      types/
  backend/
    app/
      api/
        config.py
        papers.py
        reports.py
        delivery.py
      core/
        config.py
        logging.py
      db/
        models.py
        session.py
      jobs/
        generate_report.py
      services/
        paper_sources/
          base.py
          arxiv.py
          semantic_scholar.py
        summarizer.py
        report_builder.py
        feishu.py
      main.py
  docs/
    superpowers/
      specs/
  .env.example
  README.md
```

## Configuration Model

The app stores user-editable monitoring configuration in SQLite and keeps secrets in environment variables.

Example logical configuration:

```yaml
topics:
  - name: llm_agents
    keywords:
      - LLM agent
      - tool use
      - autonomous agents
    venues:
      - NeurIPS
      - ICML
      - ICLR
      - ACL
      - EMNLP
    exclude_keywords:
      - survey
search:
  lookback_days: 7
  max_results_per_source: 30
summary:
  language: zh
delivery:
  provider: feishu
  mode: app_bot
  recipient_id_type: email
```

Secrets:

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL=
FEISHU_APP_ID=
FEISHU_APP_SECRET=
FEISHU_RECIPIENT_ID=
FEISHU_RECIPIENT_ID_TYPE=email
```

`FEISHU_RECIPIENT_ID_TYPE` supports `email`, `open_id`, or `user_id`. V1 should default to `email` because it is easier to configure manually. If Feishu rejects email delivery in a given tenant setup, the user can switch to `open_id` or `user_id`.

## Data Model

Minimum tables:

- `topics`: named monitoring profiles.
- `topic_keywords`: included keywords per topic.
- `topic_venues`: reference conference and journal names per topic.
- `topic_exclusions`: excluded keywords per topic.
- `papers`: deduplicated paper metadata.
- `paper_matches`: which topic matched which paper and why.
- `reports`: generated daily report records.
- `report_items`: papers included in each report.
- `delivery_logs`: Feishu send attempts and errors.

Paper deduplication should prefer stable IDs in this order:

1. DOI.
2. arXiv ID.
3. Semantic Scholar paper ID.
4. Normalized title hash.

## Paper Search

V1 source adapters implement one internal interface:

```python
class PaperSource:
    async def search(self, query: PaperQuery) -> list[PaperCandidate]:
        raise NotImplementedError
```

`PaperQuery` includes keywords, venues, exclusions, date range, and result limits.

arXiv should be used for recent preprints. Semantic Scholar should supplement metadata such as authors, abstract, citation count, venue, year, and external IDs.

Filtering rules:

- A paper is relevant when its title, abstract, venue, or source metadata matches at least one configured keyword or venue.
- Exclusion keywords remove a paper when they appear in the title or abstract, even if other metadata also matches.
- V1 should keep the filtering understandable and visible in the UI by storing match reasons.

## GPT Summary

The report builder sends a compact paper payload to the summarizer. Each included paper should receive:

- Chinese one-sentence takeaway.
- Research problem.
- Method highlight.
- Why it matched the user's configured interests.
- Links and metadata.

The daily report should include:

- Date and configured topic names.
- Top paper highlights.
- Grouped paper list by topic.
- A short "worth reading first" section.
- Source links for each paper.

The summarizer must handle missing abstracts and API failures gracefully. If summarization fails for one paper, the report should still be generated with metadata-only fallback text for that item.

## Feishu Delivery

V1 uses a Feishu custom app bot private message flow:

1. Use `FEISHU_APP_ID` and `FEISHU_APP_SECRET` to get a `tenant_access_token`.
2. Send the report with Feishu's message creation API.
3. Use `FEISHU_RECIPIENT_ID_TYPE` and `FEISHU_RECIPIENT_ID` to identify the recipient.

The backend should support:

- `POST /api/delivery/feishu/test`: send a short test message.
- `POST /api/reports/{report_id}/send`: send an existing report.
- `POST /api/reports/generate-and-send`: generate today's report and send it.

V1 sends a Feishu rich text post message, with plain text as a fallback if rich text creation fails. Interactive cards are deferred until basic delivery is stable.

Feishu references:

- Send message API: https://open.feishu.cn/document/server-docs/im-v1/message/create?lang=zh-CN
- Get tenant access token for custom apps: https://open.feishu.cn/document/server-docs/authentication-management/access-token/tenant_access_token_internal?lang=zh-CN

## Backend API

Initial endpoints:

- `GET /api/health`
- `GET /api/config`
- `PUT /api/config`
- `POST /api/papers/search`
- `GET /api/papers`
- `POST /api/reports/generate`
- `POST /api/reports/generate-and-send`
- `GET /api/reports`
- `GET /api/reports/{report_id}`
- `POST /api/reports/{report_id}/send`
- `POST /api/delivery/feishu/test`

The report generation endpoints should be idempotent for the same date and configuration snapshot. Re-running the same day can update or replace the report, but it should not create confusing duplicate reports unless explicitly requested.

## Frontend UX

V1 screens:

- Dashboard: latest report, last run status, and primary actions.
- Configuration: topics, keywords, venues, exclusions, search window, limits, and delivery settings.
- Papers: recent matched papers with source, date, venue, and match reason.
- Reports: report history and report detail page.
- Delivery test: visible status for Feishu configuration and a test send action.

The UI should be utilitarian and dense enough for repeated use. It should not be a marketing landing page.

## External Scheduling

The app does not own scheduling in V1. Codex automation, cron, launchd, or a manual script can call:

```bash
curl -X POST http://localhost:8000/api/reports/generate-and-send
```

This keeps the app local-first and avoids worker infrastructure.

## Error Handling

- Paper source failure: log the source error, continue with other sources, show partial-result warning.
- GPT summary failure: keep the paper in the report with metadata-only fallback.
- Feishu token failure: store failed delivery log with status and response body.
- Feishu send failure: keep the generated report and show retry action in the UI.
- Missing secrets: block send actions with clear backend validation errors.
- Duplicate papers: deduplicate before summarization to avoid repeated cost.

## Testing Strategy

Backend:

- Unit tests for config validation.
- Unit tests for paper deduplication.
- Unit tests for filtering and match reasons.
- Unit tests for report builder fallback behavior.
- Mocked tests for Feishu token and message APIs.
- Mocked tests for paper source adapters.

Frontend:

- Component tests for configuration editing.
- Component tests for report and paper list rendering.
- API-client tests for expected request and response shapes.

End-to-end local smoke test:

1. Start backend and frontend.
2. Save one topic with keywords and venues.
3. Run a search.
4. Generate a report.
5. Send a Feishu test message.
6. Send the generated report.

## Implementation Phases

Phase 1: local skeleton

- Initialize React + Vite frontend and FastAPI backend.
- Add `.env.example`, README, and local run instructions.
- Add SQLite connection and initial models.

Phase 2: configuration and search

- Build topic configuration UI and API.
- Implement arXiv source adapter.
- Implement Semantic Scholar source adapter.
- Store papers and match reasons.

Phase 3: report generation

- Implement GPT summarizer.
- Implement report builder.
- Add report history UI.

Phase 4: Feishu private delivery

- Implement token retrieval.
- Implement send message API.
- Add test-send endpoint and UI action.
- Add generate-and-send endpoint for Codex automation.

Phase 5: verification and polish

- Add targeted backend tests.
- Add frontend smoke tests.
- Validate local run instructions.
- Verify one full local workflow.

## V1 Implementation Decisions

- Feishu report delivery uses rich text post first and plain text fallback.
- SQLite schema setup uses SQLAlchemy `create_all`; Alembic is deferred until schema migration is useful.
- OpenReview and DBLP are not included in V1. The source adapter boundary remains ready for them later.
