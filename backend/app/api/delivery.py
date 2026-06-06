from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.schemas import DeliveryResponse
from app.services.feishu import FeishuClient, FeishuSettings

router = APIRouter(prefix="/api/delivery", tags=["delivery"])


def _feishu_client() -> FeishuClient:
    settings = get_settings()
    missing = [
        name
        for name, value in {
            "FEISHU_APP_ID": settings.feishu_app_id,
            "FEISHU_APP_SECRET": settings.feishu_app_secret,
            "FEISHU_RECIPIENT_ID": settings.feishu_recipient_id,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing Feishu settings: {', '.join(missing)}")
    return FeishuClient(
        FeishuSettings(
            app_id=settings.feishu_app_id or "",
            app_secret=settings.feishu_app_secret or "",
            recipient_id=settings.feishu_recipient_id or "",
            recipient_id_type=settings.feishu_recipient_id_type,
        )
    )


@router.post("/feishu/test", response_model=DeliveryResponse)
async def test_feishu() -> DeliveryResponse:
    try:
        message_id = await _feishu_client().send_report("# Paper Insight\nFeishu test message")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return DeliveryResponse(status="sent", message_id=message_id)
