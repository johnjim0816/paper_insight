import httpx

from app.services.paper_sources.base import PaperCandidate, PaperQuery


class SemanticScholarSource:
    base_url = "https://api.semanticscholar.org/graph/v1/paper/search"

    async def search(self, query: PaperQuery) -> list[PaperCandidate]:
        text_query = " ".join(query.keywords + query.venues).strip() or "machine learning"
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                self.base_url,
                params={
                    "query": text_query,
                    "limit": query.max_results,
                    "fields": "paperId,title,abstract,authors,venue,year,url,citationCount,externalIds",
                },
            )
            response.raise_for_status()

        papers: list[PaperCandidate] = []
        for item in response.json().get("data", []):
            external_ids = item.get("externalIds") or {}
            paper_id = item["paperId"]
            papers.append(
                PaperCandidate(
                    source="semantic_scholar",
                    source_id=paper_id,
                    title=item.get("title") or "Untitled",
                    abstract=item.get("abstract"),
                    authors=[author.get("name", "") for author in item.get("authors", []) if author.get("name")],
                    venue=item.get("venue"),
                    published_at=str(item["year"]) if item.get("year") else None,
                    url=item.get("url") or f"https://www.semanticscholar.org/paper/{paper_id}",
                    doi=external_ids.get("DOI"),
                    arxiv_id=external_ids.get("ArXiv"),
                    semantic_scholar_id=paper_id,
                    citation_count=item.get("citationCount"),
                )
            )
        return papers
