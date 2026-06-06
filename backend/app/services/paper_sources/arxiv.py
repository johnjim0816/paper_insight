from datetime import datetime, timedelta, timezone
import re
from xml.etree import ElementTree

import httpx

from app.services.paper_sources.base import PaperCandidate, PaperQuery

ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"


class ArxivSource:
    base_url = "https://export.arxiv.org/api/query"

    async def search(self, query: PaperQuery) -> list[PaperCandidate]:
        terms = [f'all:"{term}"' for term in query.keywords + query.venues if term.strip()]
        search_query = " OR ".join(terms) or "all:machine learning"

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                self.base_url,
                params={
                    "search_query": search_query,
                    "start": 0,
                    "max_results": query.max_results,
                    "sortBy": "submittedDate",
                    "sortOrder": "descending",
                },
            )
            response.raise_for_status()

        cutoff = datetime.now(timezone.utc) - timedelta(days=query.lookback_days)
        root = ElementTree.fromstring(response.text)
        papers: list[PaperCandidate] = []

        for entry in root.findall(f"{ATOM}entry"):
            published_text = entry.findtext(f"{ATOM}published")
            published_at = published_text[:10] if published_text else None
            if published_text:
                published_dt = datetime.fromisoformat(published_text.replace("Z", "+00:00"))
                if published_dt < cutoff:
                    continue

            entry_id = entry.findtext(f"{ATOM}id") or ""
            raw_arxiv_id = entry_id.rsplit("/", 1)[-1]
            arxiv_id = re.sub(r"v\d+$", "", raw_arxiv_id)
            authors = [node.findtext(f"{ATOM}name") or "" for node in entry.findall(f"{ATOM}author")]
            link_node = entry.find(f"{ATOM}link")
            url = link_node.attrib.get("href") if link_node is not None else entry_id

            papers.append(
                PaperCandidate(
                    source="arxiv",
                    source_id=arxiv_id,
                    title=" ".join((entry.findtext(f"{ATOM}title") or "").split()),
                    abstract=" ".join((entry.findtext(f"{ATOM}summary") or "").split()),
                    authors=[author for author in authors if author],
                    venue=None,
                    published_at=published_at,
                    url=url,
                    doi=entry.findtext(f"{ARXIV}doi"),
                    arxiv_id=arxiv_id,
                    semantic_scholar_id=None,
                    citation_count=None,
                )
            )

        return papers
