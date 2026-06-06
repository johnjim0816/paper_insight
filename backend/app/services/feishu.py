from dataclasses import dataclass
import json

import httpx


@dataclass(frozen=True)
class FeishuSettings:
    app_id: str
    app_secret: str
    recipient_id: str
    recipient_id_type: str


class FeishuClient:
    token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    message_url = "https://open.feishu.cn/open-apis/im/v1/messages"

    def __init__(self, settings: FeishuSettings, http_client: httpx.AsyncClient | None = None):
        self.settings = settings
        self.http_client = http_client

    async def _post(self, url: str, json_body: dict, headers: dict | None = None):
        if self.http_client is not None:
            return await self.http_client.post(url, json=json_body, headers=headers)
        async with httpx.AsyncClient(timeout=20.0) as client:
            return await client.post(url, json=json_body, headers=headers)

    async def tenant_access_token(self) -> str:
        response = await self._post(
            self.token_url,
            json_body={"app_id": self.settings.app_id, "app_secret": self.settings.app_secret},
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != 0:
            raise RuntimeError(str(payload))
        return payload["tenant_access_token"]

    async def send_report(self, markdown: str) -> str:
        token = await self.tenant_access_token()
        response = await self._post(
            f"{self.message_url}?receive_id_type={self.settings.recipient_id_type}",
            headers={"Authorization": f"Bearer {token}"},
            json_body={
                "receive_id": self.settings.recipient_id,
                "msg_type": "post",
                "content": _markdown_to_post(markdown),
            },
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != 0:
            raise RuntimeError(str(payload))
        return payload["data"]["message_id"]


def _markdown_to_post(markdown: str) -> str:
    lines = []
    for line in markdown.splitlines():
        if not line.strip():
            continue
        lines.append([{"tag": "text", "text": line}])
    return json.dumps(
        {
            "zh_cn": {
                "title": "Paper Insight Daily Report",
                "content": lines[:80],
            }
        },
        ensure_ascii=False,
    )
