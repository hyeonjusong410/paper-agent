import arxiv
import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
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
    cur.close()
    conn.close()

def fetch_arxiv_papers(max_results=100):
    client = arxiv.Client()
    search = arxiv.Search(
        query="cat:cs.AI OR cat:cs.LG OR cat:cs.CL",
        max_results=max_results,
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

def save_papers(papers):
    conn = get_conn()
    cur = conn.cursor()
    for p in papers:
        cur.execute("""
            INSERT INTO papers (id, title, authors, abstract, category, published, citations, url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (p["id"], p["title"], p["authors"], p["abstract"],
              p["category"], p["published"], 0, p["url"]))
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ {len(papers)}편 저장 완료")

if __name__ == "__main__":
    init_db()
    papers = fetch_arxiv_papers()
    save_papers(papers)