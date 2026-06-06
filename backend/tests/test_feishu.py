import pytest

from app.services.feishu import FeishuClient, FeishuSettings


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeHttpClient:
    def __init__(self):
        self.posts = []

    async def post(self, url, json=None, headers=None):
        self.posts.append((url, json, headers))
        if "tenant_access_token" in url:
            return FakeResponse({"code": 0, "tenant_access_token": "token-1"})
        return FakeResponse({"code": 0, "data": {"message_id": "msg-1"}})


@pytest.mark.asyncio
async def test_feishu_sends_message():
    http_client = FakeHttpClient()
    client = FeishuClient(
        FeishuSettings(
            app_id="cli_x",
            app_secret="secret",
            recipient_id="me@example.com",
            recipient_id_type="email",
        ),
        http_client=http_client,
    )

    result = await client.send_report("hello")

    assert result == "msg-1"
    assert len(http_client.posts) == 2
    assert http_client.posts[1][1]["receive_id"] == "me@example.com"
