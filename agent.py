import google.generativeai as genai
import sqlite3
import pandas as pd

def get_papers_for_analysis():
    conn = sqlite3.connect("papers.db")
    df = pd.read_sql("""
        SELECT title, authors, abstract, category, citations
        FROM papers
        ORDER BY citations DESC
        LIMIT 20
    """, conn)
    conn.close()
    return df

def run_agent(user_query: str) -> str:
    genai.configure(api_key="AQ.Ab8RN6IXgPu5tJtrKLaz2A7lUcjtdoErM4xI_s5i9lDn7EZJ_A")
    model = genai.GenerativeModel("gemini-1.5-flash")

    df = get_papers_for_analysis()
    papers_text = ""
    for _, row in df.iterrows():
        papers_text += f"""
제목: {row['title']}
저자: {row['authors']}
카테고리: {row['category']}
인용수: {row['citations']}
초록: {row['abstract'][:200]}
---"""

    prompt = f"""너는 AI 논문 트렌드 분석 에이전트야.
사용자가 질문하면 제공된 논문 데이터를 바탕으로 인사이트를 제공해.
항상 한국어로 답변하고, 구체적인 논문을 근거로 들어서 설명해.

논문 데이터:
{papers_text}

질문: {user_query}"""

    response = model.generate_content(prompt)
    return response.text