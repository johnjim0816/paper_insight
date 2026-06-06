from collections import defaultdict

from app.schemas import PaperResponse


def build_report_markdown(report_date: str, papers: list[PaperResponse], summaries: dict[int, str]) -> str:
    lines = [
        f"# Paper Insight Daily Report - {report_date}",
        "",
        "## Worth Reading First",
        "",
    ]

    if not papers:
        lines.append("No matching papers were found for this report.")

    for paper in papers[:3]:
        lines.extend(
            [
                f"- [{paper.title}]({paper.url})",
                f"  - {summaries.get(paper.id, '暂无摘要')}",
            ]
        )

    grouped: dict[str, list[PaperResponse]] = defaultdict(list)
    for paper in papers:
        for topic in paper.topic_names or ["unclassified"]:
            grouped[topic].append(paper)

    lines.extend(["", "## Papers By Topic", ""])
    for topic, topic_papers in grouped.items():
        lines.extend([f"### {topic}", ""])
        for paper in topic_papers:
            meta = " | ".join(item for item in [paper.venue, paper.published_at, paper.source] if item)
            lines.extend(
                [
                    f"- **[{paper.title}]({paper.url})**",
                    f"  - Metadata: {meta or 'unknown'}",
                    f"  - Match: {', '.join(paper.match_reasons) or 'matched'}",
                    f"  - Summary: {summaries.get(paper.id, '暂无摘要')}",
                ]
            )

    return "\n".join(lines).strip() + "\n"
