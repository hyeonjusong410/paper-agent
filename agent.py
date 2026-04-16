import time
import os
import google.generativeai as genai
import psycopg2
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def get_papers_for_analysis():
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    df = pd.read_sql("""
        SELECT title, authors, abstract, category, citations
        FROM papers
        ORDER BY citations DESC
        LIMIT 5
    """, conn)
    conn.close()
    return df

def run_agent(user_query: str) -> str:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-2.0-flash")

    df = get_papers_for_analysis()
    papers_text = ""
    for _, row in df.iterrows():
        papers_text += f"제목: {row['title']}\n초록: {row['abstract'][:100]}\n---\n"

    prompt = f"""AI 논문 트렌드 분석 에이전트야. 한국어로 답해줘.
논문: {papers_text}
질문: {user_query}"""

    time.sleep(2)
    response = model.generate_content(prompt)
    return response.text