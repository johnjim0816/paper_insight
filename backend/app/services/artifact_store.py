import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings
from app.schemas import PaperResponse, ReportResponse
from app.services.paper_sources.base import PaperQuery


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _model_dump(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return model.dict()


def save_paper_search_artifacts(
    papers: list[PaperResponse],
    warnings: list[str],
    query: PaperQuery,
    settings: Settings | None = None,
) -> None:
    settings = settings or get_settings()
    paper_dir = settings.data_dir / "papers"
    retrieved_at = _now_iso()

    _write_json(
        paper_dir / "papers.json",
        {
            "retrieved_at": retrieved_at,
            "count": len(papers),
            "papers": [_model_dump(paper) for paper in papers],
            "warnings": warnings,
        },
    )
    _write_json(
        paper_dir / "sources.json",
        {
            "retrieved_at": retrieved_at,
            "query": asdict(query),
            "warnings": warnings,
        },
    )


def save_report_artifacts(
    report: ReportResponse,
    paper_count: int,
    settings: Settings | None = None,
) -> None:
    settings = settings or get_settings()
    reports_dir = settings.data_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_path = reports_dir / f"{report.report_date}.md"
    report_path.write_text(report.markdown, encoding="utf-8")
    _write_json(
        reports_dir / f"{report.report_date}.json",
        {
            "retrieved_at": _now_iso(),
            "id": report.id,
            "report_date": report.report_date,
            "title": report.title,
            "paper_count": paper_count,
            "markdown_path": str(report_path),
        },
    )
