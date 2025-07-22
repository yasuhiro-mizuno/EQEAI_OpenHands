import os
import streamlit as st
from dotenv import load_dotenv
import openai
from docx import Document
import fitz
import csv
from io import StringIO

# Load environment variables
load_dotenv()
openai.api_type = "azure"
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = os.getenv("AZURE_OPENAI_VERSION")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "o4-mini")

# 表現品質ルール定義
RULES = {
    "簡潔な文": "能動的な表現で記述し、受動態、二重否定、部分否定、使役表現を使用しない",
    "必要な語の欠落": "主語、述語、目的語など必要な要素が欠落していない",
    "曖昧語の回避": "「適切に」「可能な限り」など曖昧な語句を使用しない",
    "誤字脱字": "誤字脱字がない",
    "係り受け": "係り受けが一意に解釈できる"
}

st.set_page_config(page_title="EQEAI 表現品質評価AI", layout="wide")
st.title("表現品質評価AI")

# ファイルアップロードとルール選択
uploaded_file = st.file_uploader("Word(.docx)またはPDF(.pdf)をアップロード", type=["docx","pdf"])
selected_rules = st.multiselect("評価するルールを選択", list(RULES.keys()), default=list(RULES.keys()))

if st.button("評価"):
    # 入力チェック
    if not uploaded_file:
        st.error("ファイルをアップロードしてください。")
        st.stop()
    if not selected_rules:
        st.error("少なくとも1つのルールを選択してください。")
        st.stop()

    # テキスト抽出
    try:
        if uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(uploaded_file)
            text = "\n".join(p.text for p in doc.paragraphs).strip()
        else:
            pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            text = "\n".join(page.get_text() for page in pdf).strip()
    except Exception as e:
        st.error(f"ファイル読み込みエラー: {e}")
        st.stop()

    # ステップ1: 要求文抽出
    st.subheader("ステップ1: 要求文抽出")
    with st.spinner("要求文を抽出中..."):
        prompt_ext = f"""
あなたはソフトウェア要求文抽出AIです。
以下の手順に従い、文書からソフトウェア要求文を抽出してください。\n
1. 文書を1文単位に分割し、文とみなせないものを除外する
2. ソフトウェア要求文に該当する文のみ抽出する
3. 各文に章番号と章名を推定し、Markdown表形式で出力する。表ヘッダは |章番号・章名|文| とする\n
文書内容:\n{text}
"""
        try:
            res_ext = openai.ChatCompletion.create(
                engine=deployment_name,
                messages=[
                    {"role":"system","content":"あなたは表現品質評価AIです。"},
                    {"role":"user","content":prompt_ext}
                ],
                max_tokens=2048
            )
            ext_output = res_ext.choices[0].message.content
        except Exception as e:
            st.error(f"抽出APIエラー: {e}")
            st.stop()
    st.markdown(ext_output)

    # 抽出結果パース
    requirements = []
    for line in ext_output.splitlines():
        if line.startswith("|") and not line.startswith("|---"):
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 2:
                requirements.append((cols[0], cols[1]))
    if not requirements:
        st.warning("ソフトウェア要求文が見つかりませんでした。")
        st.stop()

    # ステップ2: 表現品質評価
    st.subheader("ステップ2: 表現品質評価")
    with st.spinner("評価中..."):
        rules_md = "\n".join(f"- {r}: {RULES[r]}" for r in selected_rules)
        req_list_md = "\n".join(f"- {chap} | {sen}" for chap, sen in requirements)
        prompt_eval = f"""
あなたは表現品質評価AIです。
以下のルールに基づき、抽出されたソフトウェア要求文を評価してください。\n
選択されたルール:\n{rules_md}\n
抽出された要求文と章情報:\n{req_list_md}\n
該当する文のみ、Markdown表形式で出力する。表ヘッダは |章番号・章名|元の記述|指摘理由|改善案| とする
"""
        try:
            res_eval = openai.ChatCompletion.create(
                engine=deployment_name,
                messages=[
                    {"role":"system","content":"あなたは表現品質評価AIです。"},
                    {"role":"user","content":prompt_eval}
                ],
                max_tokens=2048
            )
            eval_output = res_eval.choices[0].message.content
        except Exception as e:
            st.error(f"評価APIエラー: {e}")
            st.stop()
    st.markdown(eval_output)

    # ダウンロード
    st.download_button("Markdownダウンロード", eval_output, "evaluation.md", "text/markdown")
    rows = [l for l in eval_output.splitlines() if l.startswith("|") and not l.startswith("|---")]
    if rows:
        sio = StringIO()
        writer = csv.writer(sio)
        writer.writerow([h.strip() for h in rows[0].strip("|").split("|")])
        for r in rows[1:]:
            writer.writerow([c.strip() for c in r.strip("|").split("|")])
        st.download_button("CSVダウンロード", sio.getvalue(), "evaluation.csv", "text/csv")
EOF