from flask import Flask, jsonify, render_template, request
import pandas as pd
from collections import Counter
from collector import fetch_arxiv_papers, save_papers
from agent import run_agent
import os
from mailer import send_email
from apscheduler.schedulers.background import BackgroundScheduler
import psycopg2

app = Flask(__name__)

# DB 초기화
from collector import init_db
init_db()

def get_conn():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

def get_df(days=7):
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM papers", conn)
    conn.close()
    df["published"] = pd.to_datetime(df["published"])
    if days != 9999:
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
        df = df[df["published"] >= cutoff]
    return df

TREND_KEYWORDS = [
    # LLM / 언어모델
    "transformer","attention","llm","gpt","bert","finetuning","alignment","rlhf",
    "instruct","prompt","context","tokenizer","embedding","pretraining",
    # 에이전트
    "agent","agentic","reasoning","planning","tool","autonomous","workflow",
    "multiagent","reflection","memory","action",
    # 비전
    "diffusion","multimodal","vision","image","video","generation","stable",
    "controlnet","inpainting","segmentation","detection","recognition",
    # 강화학습
    "reinforcement","reward","policy","environment","simulation","robot",
    # 안전성
    "safety","hallucination","bias","robustness","jailbreak","watermark",
    # 최신 트렌드
    "quantum","mamba","mixture","experts","retrieval","rag","embodied",
    "knowledge","graph","reasoning","chain","thought","inference","scaling",
    "efficient","compression","distillation","pruning","quantization",
    # 멀티모달
    "audio","speech","3d","depth","point","cloud","lidar",
]

def extract_keywords(texts, top_n=6):
    counts = {kw: 0 for kw in TREND_KEYWORDS}
    for text in texts:
        text_lower = text.lower()
        for kw in TREND_KEYWORDS:
            counts[kw] += text_lower.count(kw)
    sorted_kw = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return [(kw, cnt) for kw, cnt in sorted_kw if cnt > 0][:top_n]
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

    def keyword_score(abstract):
        if not abstract:
            return 0, []
        text = abstract.lower()
        matched = []
        score = 0
        for kw in TREND_KEYWORDS:
            cnt = text.count(kw)
            if cnt > 0:
                score += cnt
                matched.append(kw)
        return score, matched[:3]

    daily = df.groupby(df["published"].dt.strftime("%Y-%m-%d")).size().to_dict()
    categories = df["category"].value_counts().head(6).to_dict()
    keywords = extract_keywords(df["abstract"].dropna().tolist())

    df["score"] = df["abstract"].apply(lambda x: keyword_score(x)[0])
    df["matched_kw"] = df["abstract"].apply(lambda x: keyword_score(x)[1])

    top_papers = df[df["score"] > 0].nlargest(20, "score")[
        ["title","authors","category","citations","url","published","score","matched_kw"]
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
def send_email_route():
    try:
        from mailer import send_email
        send_email(
            to_email=os.environ.get("MAIL_TO"),
            gmail_address=os.environ.get("GMAIL_ADDRESS"),
            gmail_password=os.environ.get("GMAIL_PASSWORD")
        )
        return jsonify({"message": "✅ 메일 발송 완료!"})
    except Exception as e:
        return jsonify({"message": f"❌ 오류: {str(e)}"})

scheduler = BackgroundScheduler()

# 매일 오전 0시 논문 자동 수집
scheduler.add_job(
    lambda: save_papers(fetch_arxiv_papers()),
    trigger="cron",
    hour=0,
    minute=0
)

scheduler.add_job(
    lambda: send_email(
        to_email=os.environ.get("MAIL_TO"),
        gmail_address=os.environ.get("GMAIL_ADDRESS"),
        gmail_password=os.environ.get("GMAIL_PASSWORD")
    ),
    trigger="cron",
    day_of_week="fri",
    hour=6, 
    minute=0
)

scheduler.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)