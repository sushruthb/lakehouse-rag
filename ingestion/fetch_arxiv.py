import feedparser
from tenacity import retry, stop_after_attempt, wait_exponential


ARXIV_BASE_URL = "http://export.arxiv.org/api/query"


def _parse_paper_id(entry_id: str) -> str:
    return entry_id.split("/abs/")[-1].split("v")[0]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_papers(category: str = "cs.AI", max_results: int = 500) -> list[dict]:
    url = f"{ARXIV_BASE_URL}?search_query=cat:{category}&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
    feed = feedparser.parse(url)
    papers = []
    for entry in feed.entries:
        papers.append({
            "paper_id": _parse_paper_id(entry.id),
            "title": entry.title.strip(),
            "abstract": entry.summary.strip(),
            "authors": [a.name for a in entry.authors],
            "category": entry.tags[0].term if entry.tags else category,
            "published_date": entry.published[:10],
        })
    return papers


if __name__ == "__main__":
    import os
    from bronze_writer import write_bronze

    papers = fetch_papers(category="cs.AI", max_results=500)
    print(f"Fetched {len(papers)} papers")
    write_bronze(
        papers,
        minio_endpoint=os.environ["MINIO_ENDPOINT"],
        access_key=os.environ["MINIO_ACCESS_KEY"],
        secret_key=os.environ["MINIO_SECRET_KEY"],
    )
    print("Bronze write complete")
