from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.delivery import _feishu_client
from app.db.models import DeliveryLog, Report
from app.db.session import get_db
from app.jobs.generate_report import generate_report
from app.schemas import DeliveryResponse, ReportResponse

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _to_response(report: Report) -> ReportResponse:
    return ReportResponse(id=report.id, report_date=report.report_date, title=report.title, markdown=report.markdown)


def _record_delivery(db: Session, report_id: int | None, status: str, response: str) -> None:
    db.add(DeliveryLog(provider="feishu", report_id=report_id, status=status, response=response))
    db.commit()


@router.post("/generate", response_model=ReportResponse)
async def generate(db: Session = Depends(get_db)) -> ReportResponse:
    return await generate_report(db)


@router.post("/generate-and-send", response_model=DeliveryResponse)
async def generate_and_send(db: Session = Depends(get_db)) -> DeliveryResponse:
    report = await generate_report(db)
    try:
        message_id = await _feishu_client().send_report(report.markdown)
    except Exception as exc:
        _record_delivery(db, report.id, "failed", str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    _record_delivery(db, report.id, "sent", message_id)
    return DeliveryResponse(status="sent", message_id=message_id)


@router.get("", response_model=list[ReportResponse])
def list_reports(db: Session = Depends(get_db)) -> list[ReportResponse]:
    reports = db.scalars(select(Report).order_by(Report.created_at.desc())).all()
    return [_to_response(report) for report in reports]


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db)) -> ReportResponse:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return _to_response(report)


@router.post("/{report_id}/send", response_model=DeliveryResponse)
async def send_report(report_id: int, db: Session = Depends(get_db)) -> DeliveryResponse:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    try:
        message_id = await _feishu_client().send_report(report.markdown)
    except Exception as exc:
        _record_delivery(db, report_id, "failed", str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    _record_delivery(db, report_id, "sent", message_id)
    return DeliveryResponse(status="sent", message_id=message_id)
