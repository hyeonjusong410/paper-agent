import pandas as pd
import smtplib
from google import genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TREND_KEYWORDS = [
    "transformer","attention","llm","gpt","bert","finetuning","alignment","rlhf",
    "agent","agentic","reasoning","planning","autonomous","multiagent",
    "diffusion","multimodal","vision","video","generation",
    "reinforcement","reward","policy","robot",
    "safety","hallucination","bias","robustness","jailbreak",
    "quantum","mamba","mixture","retrieval","rag","embodied","scaling",
]
MAJOR_ORGS = ["google","deepmind","openai","meta","microsoft","anthropic","deepseek","stanford","mit","berkeley"]

def get_weekly_papers():
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    df = pd.read_sql("""
        SELECT title, authors, abstract, category, citations, url
        FROM papers
        WHERE published >= CURRENT_DATE - INTERVAL '7 days'
    """, conn)
    conn.close()
    return df

def keyword_score(abstract):
    if not abstract:
        return 0
    text = abstract.lower()
    return sum(text.count(kw) for kw in TREND_KEYWORDS)

def is_major_org(authors):
    text = str(authors).lower()
    return any(org in text for org in MAJOR_ORGS)

def summarize_with_gemini(title, abstract):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = f"다음 논문을 한국어로 2문장으로 요약해줘.\n제목: {title}\n초록: {abstract[:500]}"
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text.strip()
    except:
        return "요약을 불러올 수 없습니다."

def generate_weekly_summary(trend_papers, major_papers):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        papers_text = ""
        for p in trend_papers + major_papers:
            papers_text += f"- {p['title']} ({p['authors']})\n"
        prompt = f"""다음 논문들을 바탕으로 이번 주 AI 연구 동향을 한국어로 3~4문장으로 요약해줘.
전문적이지만 읽기 쉽게 작성해줘.

논문 목록:
{papers_text}"""
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text.strip()
    except:
        return "이번 주 동향 요약을 불러올 수 없습니다."

def build_email_html():
    df = get_weekly_papers()
    now = datetime.now()
    week = (now.day - 1) // 7 + 1

    df["score"] = df["abstract"].apply(keyword_score)
    trend_papers = df.nlargest(3, "score").to_dict("records")

    df_major = df[df["authors"].apply(is_major_org)]
    major_papers = df_major.nlargest(3, "citations").to_dict("records") if len(df_major) > 0 else []

    weekly_summary = generate_weekly_summary(trend_papers, major_papers)

    trend_rows = ""
    for i, p in enumerate(trend_papers):
        summary = summarize_with_gemini(p["title"], p["abstract"])
        trend_rows += f"""
        <div style="margin-bottom:16px;padding-bottom:16px;border-bottom:1px solid #eee;">
            <div style="font-size:13px;font-weight:600;margin-bottom:4px;">
                {i+1}. <a href="{p['url']}" style="color:#185FA5;">{p['title'][:70]}...</a>
            </div>
            <div style="font-size:11px;color:#888;margin-bottom:6px;">{p['authors'][:50]} · {p['category']}</div>
            <div style="font-size:12px;color:#444;background:#f8f8f6;padding:8px;border-radius:6px;">{summary}</div>
        </div>"""

    major_rows = ""
    if major_papers:
        for i, p in enumerate(major_papers):
            summary = summarize_with_gemini(p["title"], p["abstract"])
            major_rows += f"""
            <div style="margin-bottom:16px;padding-bottom:16px;border-bottom:1px solid #eee;">
                <div style="font-size:13px;font-weight:600;margin-bottom:4px;">
                    {i+1}. <a href="{p['url']}" style="color:#185FA5;">{p['title'][:70]}...</a>
                </div>
                <div style="font-size:11px;color:#888;margin-bottom:6px;">{p['authors'][:50]} · {p['category']}</div>
                <div style="font-size:12px;color:#444;background:#f8f8f6;padding:8px;border-radius:6px;">{summary}</div>
            </div>"""
    else:
        major_rows = "<div style='font-size:12px;color:#888;'>이번 주 주요 기관 논문 없음</div>"

    html = f"""
    <html><body style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:20px;color:#1a1a1a;">
        <h2 style="color:#185FA5;margin-bottom:4px;">📡 PaperAgent 주간 AI 논문 트렌드</h2>
        <p style="color:#888;font-size:12px;margin-bottom:20px;">{now.year}년 {now.month}월 {week}주차</p>
        <div style="background:#E6F1FB;border-radius:8px;padding:14px;margin-bottom:24px;">
            <div style="font-size:11px;color:#185FA5;font-weight:600;margin-bottom:6px;">💡 이번 주 동향 요약</div>
            <div style="font-size:13px;color:#0C447C;line-height:1.6;">{weekly_summary}</div>
        </div>
        <h3 style="font-size:14px;margin-bottom:12px;">🔥 트렌드 논문