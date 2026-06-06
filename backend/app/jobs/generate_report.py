from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Paper, Report, ReportItem
from app.schemas import ReportResponse
from app.services.artifact_store import save_report_artifacts
from app.services.paper_repository import paper_to_response
from app.services.report_builder import build_report_markdown
from app.services.summarizer import summarize_paper


async def generate_report(db: Session, report_date: str | None = None) -> ReportResponse:
    settings = get_settings()
    target_date = report_date or date.today().isoformat()
    papers = db.scalars(select(Paper).order_by(Paper.created_at.desc()).limit(20)).all()
    paper_responses = [paper_to_response(db, paper) for paper in papers]

    summaries: dict[int, str] = {}
    for paper in paper_responses:
        summaries[paper.id] = await summarize_paper(
            paper,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
        )

    markdown = build_report_markdown(target_date, paper_responses, summaries)
    report = db.scalar(select(Report).where(Report.report_date == target_date))
    if report is not None:
        db.execute(delete(ReportItem).where(ReportItem.report_id == report.id))
    else:
        report = Report(report_date=target_date, title=f"Paper Insight Daily Report - {target_date}", markdown="")

    report.title = f"Paper Insight Daily Report - {target_date}"
    report.markdown = markdown
    db.add(report)
    db.flush()

    for paper in paper_responses:
        db.add(ReportItem(report_id=report.id, paper_id=paper.id, summary=summaries[paper.id]))

    db.commit()
    db.refresh(report)
    response = ReportResponse(id=report.id, report_date=report.report_date, title=report.title, markdown=report.markdown)
    save_report_artifacts(response, paper_count=len(paper_responses), settings=settings)
    return response
