from app import extract_keywords, get_df

df = get_df(9999)
keywords = extract_keywords(df["abstract"].dropna().tolist(), top_n=100)
for kw, cnt in keywords:
    print(f"{kw}: {cnt}회")