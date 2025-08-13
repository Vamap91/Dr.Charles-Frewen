import os
import pickle
import faiss
import numpy as np
import tiktoken
import streamlit as st
from pypdf import PdfReader
from openai import OpenAI

# ================== CONFIGURAÇÃO ==================
st.set_page_config(page_title="Dr_C • MVP RAG", page_icon="🌿", layout="wide")

# Cliente OpenAI (lendo a chave de Settings → Secrets)
api_key = st.secrets["OPENAI_API_KEY"].strip()
os.environ["OPENAI_API_KEY"] = api_key
client = OpenAI(api_key=api_key)

# Idioma inicial (lido de Secrets ou padrão pt)
DEFAULT_LANG = st.secrets.get("APP_LANG", "pt").strip().lower()
lang = st.sidebar.radio("Idioma / Language", ["pt", "en"], index=0 if DEFAULT_LANG == "pt" else 1)
def T(pt, en): return pt if lang == "pt" else en

# ================== INTERFACE ==================
st.title("🌿 Dr_C — MVP (Fase 1)")
st.caption(T(
    "Avatar de biodiversidade (MVP): responde com base no acervo interno enviado.",
    "Biodiversity avatar (MVP): answers based on the uploaded internal corpus."
))

# ================== EMBEDDINGS ==================
EMBED_MODEL = "text-embedding-3-small"
ENCODER = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(ENCODER.encode(text))

def chunk_text(text: str, max_tokens: int = 500, overlap_tokens: int = 50):
    toks = ENCODER.encode(text)
    chunks, start = [], 0
    while start < len(toks):
        end = min(start + max_tokens, len(toks))
        chunks.append(ENCODER.decode(toks[start:end]))
        start = end - overlap_tokens
        if start < 0: start = 0
        if start >= len(toks): break
    return chunks

def embed_texts(texts: list[str]) -> np.ndarray:
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    vecs = np.array([d.embedding for d in resp.data], dtype="float32")
    return vecs

def normalize(vecs: np.ndarray) -> np.ndarray:
    return vecs / (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12)

# ================== PDF EXTRACTION ==================
def extract_text_from_pdf(file) -> str:
    reader = PdfReader(file)
    return "\n".join(page.extract_text() or "" for page in reader.pages)

# ================== FAISS STORE ==================
INDEX_PATH, META_PATH = "faiss.index", "meta.pkl"

@st.cache_resource(show_spinner=False)
def load_store():
    if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
        index = faiss.read_index(INDEX_PATH)
        with open(META_PATH, "rb") as f: meta = pickle.load(f)
        return index, meta
    d = 1536
    return faiss.IndexFlatIP(d), []

@st.cache_resource(show_spinner=False)
def save_store(index, meta):
    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "wb") as f: pickle.dump(meta, f)

index, meta = load_store()

# ================== UPLOAD & INDEX ==================
st.subheader(T("1) Suba o conteúdo", "1) Upload your content"))
uploaded = st.file_uploader(T("Arraste PDFs/artigos", "Drag & drop PDFs/articles"),
                             type=["pdf"], accept_multiple_files=True)

colA, colB = st.columns(2)
with colA:
    if st.button(T("Indexar arquivos enviados", "Index uploaded files"), use_container_width=True):
        if not uploaded:
            st.warning(T("Envie ao menos 1 PDF.", "Please upload at least one PDF."))
        else:
            new_chunks, new_meta = [], []
            with st.spinner(T("Processando documentos...", "Processing documents...")):
                for f in uploaded:
                    raw = extract_text_from_pdf(f)
                    chunks = chunk_text(raw, max_tokens=520, overlap_tokens=60)
                    for ch in chunks:
                        if ch.strip():
                            new_chunks.append(ch)
                            new_meta.append({"source": f.name, "snippet": ch[:180].replace("\n", " ")})
            if new_chunks:
                vecs = normalize(embed_texts(new_chunks))
                if index.ntotal == 0:
                    d = vecs.shape[1]
                    index = faiss.IndexFlatIP(d)
                index.add(vecs)
                meta.extend(new_meta)
                save_store(index, meta)
                st.success(T("Indexação concluída.", "Indexing complete."))
            else:
                st.error(T("Nada para indexar.", "Nothing to index."))

with colB:
    if st.button(T("Limpar base", "Clear corpus"), type="secondary", use_container_width=True):
        if os.path.exists(INDEX_PATH): os.remove(INDEX_PATH)
        if os.path.exists(META_PATH): os.remove(META_PATH)
        st.success(T("Base limpa. Recarregue a página.", "Corpus cleared. Reload the page."))

# ================== SEARCH & ANSWER ==================
st.subheader(T("2) Pergunte ao Dr_C", "2) Ask Dr_C"))
q = st.text_input(T("Sua pergunta", "Your question"))
top_k = st.slider(T("Fontes (top_k)", "Sources (top_k)"), 2, 8, 4)

def search(query, k=4):
    if index.ntotal == 0: return []
    qvec = normalize(embed_texts([query]))
    D, I = index.search(qvec, k)
    return [meta[idx] for idx in I[0] if 0 <= idx < len(meta)]

SYSTEM_PT = ("Você é o Dr_C, especialista em biodiversidade. "
             "Responda sempre trazendo o foco para conservação e soluções baseadas na natureza, "
             "usando apenas as fontes fornecidas e citando-as no final.")
SYSTEM_EN = ("You are Dr_C, a biodiversity expert. "
             "Always bring the focus to conservation and nature-based solutions, "
             "using only the provided sources and citing them at the end.")

def answer_with_sources(query, sources):
    system_msg = SYSTEM_PT if lang == "pt" else SYSTEM_EN
    context = "\n\n".join(f"[{s['source']}]\n{s['snippet']}" for s in sources)
    user_prompt = f"{query}\n\n{context}"
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":system_msg},
                  {"role":"user","content":user_prompt}],
        temperature=0.2
    )
    return resp.choices[0].message.content

if st.button(T("Responder", "Answer"), type="primary", use_container_width=True) and q:
    if index.ntotal == 0:
        st.warning(T("Base vazia. Faça upload e indexe antes.", "Corpus empty. Upload & index first."))
    else:
        with st.spinner(T("Buscando e respondendo...", "Searching and answering...")):
            srcs = search(q, k=top_k)
            ans = answer_with_sources(q, srcs)
        st.markdown("### " + T("Resposta", "Answer"))
        st.write(ans)
        with st.expander(T("Fontes usadas", "Sources used")):
            for s in srcs:
                st.write(f"- **{s['source']}** — “{s['snippet'][:200]}...”")
