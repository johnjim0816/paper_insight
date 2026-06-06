import json

from app.core.config import get_settings
from app.db.models import Paper, PaperMatch


def seed_paper(db):
    paper = Paper(
        dedup_key="doi:10.1000/report",
        source="fake",
        source_id="fake-1",
        title="Tool Use for Agents",
        abstract="Agent abstract",
        authors='["Alice"]',
        venue="ICLR",
        published_at="2026-06-05",
        url="https://example.com",
        doi="10.1000/report",
        arxiv_id=None,
        semantic_scholar_id=None,
        citation_count=1,
    )
    db.add(paper)
    db.flush()
    db.add(PaperMatch(paper_id=paper.id, topic_name="agents", reasons='["keyword: agents"]'))
    db.commit()


def test_generate_and_read_report(client, monkeypatch):
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        seed_paper(db)

    async def fake_summary(paper, api_key, base_url, model):
        return "一句话结论：值得阅读。"

    monkeypatch.setattr("app.jobs.generate_report.summarize_paper", fake_summary)

    response = client.post("/api/reports/generate")

    assert response.status_code == 200
    report = response.json()
    assert "Paper Insight Daily Report" in report["markdown"]

    list_response = client.get("/api/reports")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_generate_report_writes_markdown_to_configured_data_dir(client, monkeypatch, tmp_path):
    from app.db.session import SessionLocal

    get_settings.cache_clear()
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    with SessionLocal() as db:
        seed_paper(db)

    async def fake_summary(paper, api_key, base_url, model):
        return "一句话结论：值得阅读。"

    monkeypatch.setattr("app.jobs.generate_report.summarize_paper", fake_summary)

    response = client.post("/api/reports/generate")

    assert response.status_code == 200
    report = response.json()
    report_file = tmp_path / "reports" / f"{report['report_date']}.md"
    manifest_file = tmp_path / "reports" / f"{report['report_date']}.json"
    assert report_file.read_text(encoding="utf-8") == report["markdown"]

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest["title"] == report["title"]
    assert manifest["paper_count"] == 1
    get_settings.cache_clear()
