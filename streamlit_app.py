import os
import glob
import faiss
import numpy as np
import tiktoken
import streamlit as st
import openai
from pypdf import PdfReader

# ================== CONFIG ==================
st.set_page_config(page_title="Dr_C • MVP (RAG sem upload)", page_icon="🌿", layout="wide")

OPENAI_KEY = (st.secrets.get("OPENAI_API_KEY", "") or "").strip()
if not OPENAI_KEY:
    st.error("OPENAI_API_KEY ausente em Settings → Secrets.")
    st.stop()
openai.api_key = OPENAI_KEY

DEFAULT_LANG = (st.secrets.get("APP_LANG", "pt") or "pt").strip().lower()
lang = st.sidebar.radio("Idioma / Language", ["pt", "en"], index=0 if DEFAULT_LANG == "pt" else 1)
def T(pt, en): return pt if lang == "pt" else en

st.title("🌿 Dr_C — MVP (Fase 1, sem upload)")
st.caption(T("Responde com base no PDF do repositório.", "Answers based on the repository PDF."))

# ================== FONTE DOS DADOS ==================
# Ajuste aqui caso mude o nome/locais dos PDFs
PDF_PATHS = [
    "Arquivo 1 FAISS.pdf",                 # nome exato
    "Arquivo*FAISS*.pdf",                  # fallback por padrão
]

def find_existing_pdfs(patterns):
    files = []
    for p in patterns:
        files.extend(glob.glob(p))
    # remove duplicatas preservando ordem
    seen, out = set(), []
    for f in files:
        if f not in seen and os.path.isfile(f):
            seen.add(f); out.append(f)
    return out

# ================== EMBEDDINGS & CHUNKING ==================
EMBED_MODEL = "text-embedding-3-small"   # compatível com openai==0.28.1
EMBED_DIM   = 1536
ENCODER     = tiktoken.get_encoding("cl100k_base")

def chunk_text(text: str, max_tokens: int = 500, overlap_tokens: int = 50):
    toks = ENCODER.encode(text or "")
    chunks, start = [], 0
    while start < len(toks):
        end = min(start + max_tokens, len(toks))
        chunks.append(ENCODER.decode(toks[start:end]))
        start = end - overlap_tokens
        if start < 0: start = 0
        if start >= len(toks): break
    return chunks

def embed_texts(texts: list[str]) -> np.ndarray:
    resp = openai.Embedding.create(model=EMBED_MODEL, input=texts)
    vecs = np.array([d["embedding"] for d in resp["data"]], dtype="float32")
    norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12
    return vecs / norms

def extract_text_from_pdf(path: str) -> str:
    try:
        with open(path, "rb") as f:
            reader = PdfReader(f)
            return "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception as e:
        return ""

# ================== INDEX (CACHE) ==================
@st.cache_resource(show_spinner=True)
def build_corpus_and_index():
    pdfs = find_existing_pdfs(PDF_PATHS)
    if not pdfs:
        return None, None, []

    chunks, meta = [], []
    for pdf in pdfs:
        txt = extract_text_from_pdf(pdf)
        for ch in chunk_text(txt, max_tokens=520, overlap_tokens=60):
            chs = ch.strip()
            if chs:
                chunks.append(chs)
                meta.append({"source": os.path.basename(pdf), "snippet": chs[:200].replace("\n", " ")})

    if not chunks:
        return None, None, []

    vecs = embed_texts(chunks)
    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(vecs)
    return index, meta, pdfs

index, meta, used_pdfs = build_corpus_and_index()

if not used_pdfs:
    st.error(T("Nenhum PDF encontrado. Coloque 'Arquivo 1 FAISS.pdf' na raiz do repositório.",
               "No PDF found. Put 'Arquivo 1 FAISS.pdf' at the repo root."))
    st.stop()

st.success(T(f"Base carregada a partir de: {', '.join(used_pdfs)}",
             f"Corpus loaded from: {', '.join(used_pdfs)}"))

# ================== SEARCH & ANSWER ==================
def search(query: str, k: int = 4):
    if index is None: return []
    qvec = embed_texts([query])
    D, I = index.search(qvec, k)
    results = []
    for idx in I[0]:
        if 0 <= idx < len(meta):
            results.append(meta[idx])
    return results

SYSTEM_PT = (
    "Você é o Dr_C, especialista em biodiversidade. "
    "Mantenha o foco em conservação e soluções baseadas na natureza. "
    "Responda estritamente com base nas fontes fornecidas. "
    "Se estiver incerto, diga e peça mais contexto. "
    "No final, cite as fontes (arquivo e pequeno trecho)."
)
SYSTEM_EN = (
    "You are Dr_C, a biodiversity expert. "
    "Keep the focus on conservation and nature-based solutions. "
    "Ground your answer strictly in the provided sources. "
    "If uncertain, say so and ask for more context. "
    "At the end, cite sources (file and small snippet)."
)

def answer_with_sources(query: str, sources: list[dict]) -> str:
    system_msg = SYSTEM_PT if lang == "pt" else SYSTEM_EN
    ctx = "\n\n".join(f"[{s.get('source','?')}]\n{s.get('snippet','')}" for s in sources)
    user_msg = (
        f"Pergunta: {query}\n\nContexto (trechos relevantes):\n{ctx}\n\n"
        f"Responda de forma didática e objetiva. Cite as fontes ao final."
        if lang == "pt"
        else
        f"Question: {query}\n\nContext (relevant snippets):\n{ctx}\n\n"
        f"Answer clearly and concisely. Cite sources at the end."
    )
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":system_msg},
                  {"role":"user","content":user_msg}],
        temperature=0.2
    )
    return resp["choices"][0]["message"]["content"]

st.subheader(T("Faça sua pergunta", "Ask your question"))
q = st.text_input(T("Sua pergunta", "Your question"),
                  placeholder=T("Ex.: Como provar economicamente o valor da floresta?",
                                "e.g., How to economically prove the value of the forest?"))
top_k = st.slider(T("Fontes (top_k)", "Sources (top_k)"), 2, 8, 4)

if st.button(T("Responder", "Answer"), type="primary", use_container_width=True) and q:
    with st.spinner(T("Buscando e respondendo...", "Retrieving and generating...")):
        srcs = search(q, k=top_k)
        if not srcs:
            st.warning(T("Base vazia ou sem trechos indexados.", "Empty corpus or no indexed snippets."))
        else:
            ans = answer_with_sources(q, srcs)
            st.markdown("### " + T("Resposta", "Answer"))
            st.write(ans)
            with st.expander(T("Fontes usadas", "Sources used")):
                for s in srcs:
                    st.write(f"- **{s.get('source','?')}** — “{s.get('snippet','')[:200]}...”")
