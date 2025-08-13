import streamlit as st
import pandas as pd
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.sheets_loader import load_sheets_data
from backend.diagnostics import add_health_scores

import google.generativeai as genai
from sentence_transformers import SentenceTransformer, util
import json
from dotenv import load_dotenv

# ---------- Load Gemini API Key ----------
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    raise ValueError("GOOGLE_API_KEY not found in .env")

# ---------- Helper: Generate Gemini Response ----------
def generate_gemini_response(prompt, model_name="gemini-2.0-flash"):
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return response.text

# ---------- Cache Embedding Model ----------
@st.cache_resource
def load_embedding_model():
    return SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

# ---------- Chunk DataFrame ----------
def chunk_dataframe(df, chunk_size=200):
    return [df.iloc[i:i+chunk_size] for i in range(0, len(df), chunk_size)]

# ---------- Embed and Select Most Relevant Chunks ----------
def get_most_relevant_chunks(df_chunks, query, model, top_k=2):
    json_chunks = []
    for chunk in df_chunks:
        chunk = chunk.copy()
        chunk = chunk.applymap(lambda x: str(x) if pd.isna(x) or isinstance(x, pd.Timestamp) else x)
        json_str = json.dumps(chunk.to_dict(orient="records"), indent=2)
        json_chunks.append(json_str)
    query_embedding = model.encode(query, convert_to_tensor=True)
    chunk_embeddings = model.encode(json_chunks, convert_to_tensor=True)
    scores = util.cos_sim(query_embedding, chunk_embeddings)[0]
    top_indices = scores.argsort(descending=True)[:top_k]
    return [json_chunks[i] for i in top_indices]

# ---------- Main Chatbot UI ----------
def show():
    st.header("🤖 Meet Daby! Your virtual assistant bot!")

    df = load_sheets_data()
    df['ZVS_status'] = df['ZVS_status'].apply(lambda x: str(x).lower() in ['true', '1'])  # Ensure boolean
    df = add_health_scores(df)

    user_query = st.text_area("Ask about DAB converter health, trends, or anomalies...")

    if st.button("Generate Analysis"):
        if not user_query.strip():
            st.warning("Please enter a question.")
            return

        model = load_embedding_model()
        df_chunks = chunk_dataframe(df)
        relevant_chunks = get_most_relevant_chunks(df_chunks, user_query, model)
        structured_data = "\n\n".join(relevant_chunks)

        # You can adjust this for your DAB dataset columns!
        column_description_text = """
You are analyzing DAB converter data with fields like:
- V_dc1, V_dc2, I_dc1, I_dc2, delta_1, delta_2, phi, L_total, R_total,
- efficiency_percent, temperature_C, ZVS_status, input_power, power_loss, switching_loss, conduction_loss, health_score
Each record is a JSON object with these fields and values.
"""

        structured_prompt = f"""
You are a power electronics expert reviewing DAB converter operational data (in JSON format).

{column_description_text}

Here are the most relevant records:
{structured_data}

User Question:
{user_query}

Instructions:
- Adapt your response to the user's question. If the question is simple or asks only for a value, answer briefly and to the point.
- If the question asks about health, trends, maintenance, or needs recommendations, provide a structured answer:
Recommendations:
(What should the user do, if anything? If all is well, say so.)

Health Estimation:
(Your assessment of system health, e.g. “Healthy”, “Degraded”, “Needs Attention”, with reasoning)
- Analyze the efficiency values for the given period and state whether there was a significant drop or unusual pattern.
- Explain what you observe (stable? fluctuating? declining?).
- Provide a short summary with your reasoning, then show the daily values.
- Do NOT list every value from a column. Instead, only summarize, highlight outliers, or show up to 3 most relevant data points for any field.
- For questions about highest/lowest or unusual values, only show the top 3 and explain their significance.
- If a user asks for a summary or stats, only return aggregated results, not all raw values.
- Do NOT invent data.
"""

        with st.spinner("Gemini Flash 2.0 is analyzing your data..."):
            response = generate_gemini_response(structured_prompt)
        st.subheader("📊 AI Analysis")
        st.write(response)
