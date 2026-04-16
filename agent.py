import time
import google.generativeai as genai
import sqlite3
import pandas as pd

def get_papers_for_analysis():
    conn = sqlite3.connect("papers.db")
    df = pd.read_sql("""
        SELECT title, authors, abstract, category, citations
        FROM papers
        ORDER BY citations DESC
        LIMIT 3
    """, conn)
    conn.close()
    return df

def run_agent(user_query: str) -> str:
    genai.configure(api_key="GEMINI_API_KEY")
    model = genai.GenerativeModel("gemini-2.0-flash-lite")

    df = get_papers_for_analysis()
    papers_text = ""
    for _, row in df.iterrows():
        papers_text += f"제목: {row['title']}\n초록: {row['abstract'][:100]}\n---\n"

    prompt = f"""AI 논문 트렌드 분석 에이전트야. 한국어로 답해줘.
논문: {papers_text}
질문: {user_query}"""

    time.sleep(3)
    response = model.generate_content(prompt)
    return response.text