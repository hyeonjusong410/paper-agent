import arxiv
import sqlite3
import requests
from datetime import datetime

def init_db():
    conn = sqlite3.connect("papers.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id TEXT PRIMARY KEY,
            title TEXT,
            authors TEXT,
            abstract TEXT,
            category TEXT,
            published DATE,
            citations INTEGER DEFAULT 0,
            url TEXT
        )
    """)
    conn.commit()
    return conn

def fetch_arxiv_papers(max_results=3000):
    client = arxiv.Client()
    search = arxiv.Search(
    query="cat:cs.AI OR cat:cs.LG OR cat:cs.CL",
    max_results=3000,  
    sort_by=arxiv.SortCriterion.SubmittedDate
)
    papers = []
    for result in client.results(search):
        papers.append({
            "id": result.entry_id.split("/")[-1],
            "title": result.title,
            "authors": ", ".join([a.name for a in result.authors[:3]]),
            "abstract": result.summary,
            "category": result.primary_category,
            "published": result.published.date(),
            "url": result.entry_id
        })
    return papers

def get_citation_count(arxiv_id):
    url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}"
    try:
        res = requests.get(url, params={"fields": "citationCount"}, timeout=5)
        return res.json().get("citationCount", 0)
    except:
        return 0

def save_papers(papers):
    conn = init_db()
    for p in papers:
        citations = get_citation_count(p["id"])
        conn.execute("""
            INSERT OR REPLACE INTO papers
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (p["id"], p["title"], p["authors"], p["abstract"],
              p["category"], p["published"], citations, p["url"]))
    conn.commit()
    conn.close()
    print(f"✅ {len(papers)}편 저장 완료")

if __name__ == "__main__":
    print("논문 수집 시작...")
    papers = fetch_arxiv_papers()
    save_papers(papers)