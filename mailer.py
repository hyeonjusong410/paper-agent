import sqlite3
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

def get_weekly_papers():
    conn = sqlite3.connect("papers.db")
    df = pd.read_sql("""
        SELECT title, authors, category, citations, url
        FROM papers
        WHERE published >= date('now', '-7 days')
        ORDER BY citations DESC
        LIMIT 5
    """, conn)
    conn.close()
    return df

def build_email_html():
    df = get_weekly_papers()
    now = datetime.now()
    week = (now.day - 1) // 7 + 1

    rows = ""
    for i, row in df.iterrows():
        rows += f"""
        <tr>
            <td style="padding:8px;border-bottom:1px solid #eee;">{i+1}</td>
            <td style="padding:8px;border-bottom:1px solid #eee;">
                <a href="{row['url']}" style="color:#185FA5;">{row['title'][:60]}...</a>
            </td>
            <td style="padding:8px;border-bottom:1px solid #eee;">{row['authors'][:30]}</td>
            <td style="padding:8px;border-bottom:1px solid #eee;">{row['citations']}</td>
        </tr>"""

    html = f"""
    <html><body style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:20px;">
        <h2 style="color:#185FA5;">📡 PaperAgent 주간 AI 논문 트렌드</h2>
        <p style="color:#888;">{now.year}년 {now.month}월 {week}주차</p>
        <hr>
        <h3>🔥 이주의 논문 TOP 5</h3>
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
            <tr style="background:#f0f0f0;">
                <th style="padding:8px;">#</th>
                <th style="padding:8px;">제목</th>
                <th style="padding:8px;">저자</th>
                <th style="padding:8px;">인용수</th>
            </tr>
            {rows}
        </table>
        <br>
        <p style="color:#888;font-size:12px;">PaperAgent · 매주 월요일 자동 발송</p>
    </body></html>
    """
    return html

def send_email(to_email: str, gmail_address: str, gmail_password: str):
    html = build_email_html()
    now = datetime.now()
    week = (now.day - 1) // 7 + 1

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📡 PaperAgent 주간 AI 트렌드 — {now.year}년 {now.month}월 {week}주차"
    msg["From"] = gmail_address
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, gmail_password)
        server.sendmail(gmail_address, to_email, msg.as_string())

    print(f"✅ 메일 발송 완료 → {to_email}")

if __name__ == "__main__":
    send_email(
        to_email="받는사람@gmail.com",
        gmail_address="내gmail@gmail.com",
        gmail_password="앱비밀번호"
    )