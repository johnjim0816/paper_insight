import httpx

from app.schemas import PaperResponse


def _fallback_summary(paper: PaperResponse, reason: str) -> str:
    return f"摘要生成失败，已保留元数据：{paper.title}。原因：{reason}"


async def summarize_paper(
    paper: PaperResponse,
    api_key: str | None,
    base_url: str,
    model: str,
    client: httpx.AsyncClient | None = None,
) -> str:
    if not api_key:
        return _fallback_summary(paper, "OPENAI_API_KEY is missing")

    prompt = (
        "请用中文总结这篇论文，包含一句话结论、研究问题、方法亮点、"
        "以及它为什么匹配用户关注方向。控制在 180 字以内。\n\n"
        f"Title: {paper.title}\n"
        f"Abstract: {paper.abstract or 'No abstract'}\n"
        f"Venue: {paper.venue or 'Unknown'}\n"
        f"Match reasons: {', '.join(paper.match_reasons)}"
    )
    close_client = client is None
    active_client = client or httpx.AsyncClient(timeout=40.0)
    try:
        response = await active_client.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You summarize academic papers for a Chinese research daily report."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        return _fallback_summary(paper, str(exc))
    finally:
        if close_client:
            await active_client.aclose()
