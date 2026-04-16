from flask import Flask, jsonify, render_template, request
import sqlite3
import pandas as pd
from collections import Counter
import re
from agent import run_agent

app = Flask(__name__)

def get_df(days=7):
    conn = sqlite3.connect("papers.db")
    df = pd.read_sql("SELECT * FROM papers", conn)
    conn.close()
    df["published"] = pd.to_datetime(df["published"])
    if days != 9999:
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
        df = df[df["published"] >= cutoff]
    return df

def extract_keywords(texts, top_n=6):
    stopwords = {"the","a","an","of","in","to","and","for","with","on","is",
                 "are","was","were","we","our","by","from","that","this","which",
                 "be","as","at","it","its","or","can","has","have","not","also",
                 "but","using","based","via","show","shows","paper","propose",
                 "proposed","results","data","approach","task","tasks","large",
                 "high","new","two","one","used","train","trained","performance"}
    words = []
    for text in texts:
        tokens = re.findall(r'\b[a-z]{4,}\b', text.lower())
        words += [w for w in tokens if w not in stopwords]
    return Counter(words).most_common(top_n)

def extract_authors(df, top_n=5):
    author_count = Counter()
    for authors in df["authors"]:
        for a in str(authors).split(","):
            a = a.strip()
            if a:
                author_count[a] += 1
    return author_count.most_common(top_n)

def extract_orgs(df):
    orgs = {
        "Google/DeepMind": ["google", "deepmind"],
        "OpenAI": ["openai"],
        "Meta AI": ["meta", "facebook"],
        "Microsoft": ["microsoft"],
        "Anthropic": ["anthropic"],
        "DeepSeek": ["deepseek"],
        "Stanford/MIT": ["stanford", "mit"],
    }
    counts = {k: 0 for k in orgs}
    for authors in df["authors"]:
        text = str(authors).lower()
        for org, keywords in orgs.items():
            if any(k in text for k in keywords):
                counts[org] += 1
    return counts

def build_heatmap(df, keywords=["reasoning","learning","model","agent","safety"]):
    result = {}
    df2 = df.copy()
    df2["month"] = df2["published"].dt.strftime("%Y-%m")
    months = sorted(df2["month"].unique())[-12:]
    for kw in keywords:
        result[kw] = {}
        for m in months:
            month_df = df2[df2["month"] == m]
            count = month_df["abstract"].str.lower().str.count(kw).sum()
            result[kw][m] = int(count)
    return result

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/stats")
def stats():
    range_map = {"7d": 7, "1m": 30, "3m": 90, "all": 9999}
    days = range_map.get(request.args.get("range", "7d"), 7)
    df = get_df(days)

    if df.empty:
        return jsonify({"total": 0, "error": "데이터 없음"})

    daily = df.groupby(df["published"].dt.strftime("%Y-%m-%d")).size().to_dict()
    categories = df["category"].value_counts().head(6).to_dict()
    keywords = extract_keywords(df["abstract"].dropna().tolist())
    top_papers = df.nlargest(10, "citations")[
        ["title","authors","category","citations","url","published"]
    ].to_dict("records")
    for p in top_papers:
        p["published"] = str(p["published"])[:10]

    unique_authors = set()
    for a in df["authors"]:
        for name in str(a).split(","):
            unique_authors.add(name.strip())

    return jsonify({
        "total": len(df),
        "avg_citations": round(float(df["citations"].mean()), 1),
        "hot_papers": int(len(df[df["citations"] > 10])),
        "unique_authors": len(unique_authors),
        "daily": daily,
        "categories": categories,
        "keywords": keywords,
        "top_papers": top_papers,
        "orgs": extract_orgs(df),
        "authors": extract_authors(df),
        "heatmap": build_heatmap(get_df(9999))
    })

@app.route("/api/agent", methods=["POST"])
def agent():
    query = request.json.get("query", "")
    answer = run_agent(query)
    return jsonify({"answer": answer})

@app.route("/api/collect", methods=["POST"])
def collect():
    from collector import fetch_arxiv_papers, save_papers
    papers = fetch_arxiv_papers(max_results=100)
    save_papers(papers)
    return jsonify({"message": "수집 완료"})

@app.route("/api/send_email", methods=["POST"])
def send_email():
    return jsonify({"message": "메일 발송 기능은 곧 추가됩니다!"})

if __name__ == "__main__":
    app.run(debug=True)