import os
import pickle
import faiss
import numpy as np
import tiktoken
import streamlit as st
from pypdf import PdfReader

# ================== CONFIGURAÇÃO ==================
st.set_page_config(page_title="Dr_C • MVP RAG", page_icon="🌿", layout="wide")

# Idioma
DEFAULT_LANG = (st.secrets.get("APP_LANG", "pt") or "pt").strip().lower()
lang = st.sidebar.radio("Idioma Language", ["pt", "en"], index=0 if DEFAULT_LANG == "pt" else 1)
def T(pt, en): return pt if lang == "pt" else en

st.title("🌿 Dr_C — MVP Fase 1")
st.caption(T(
    "Responde com base no acervo interno enviado.",
    "Answers based on the uploaded internal corpus."
))

# ================== CLIENTE OPENAI ROBUSTO ==================
# Lê chave dos Secrets e tenta SDK v1. Em caso de falha, usa SDK v0.
api_key = (st.secrets.get("OPENAI_API_KEY", "") or "").strip()
if not api_key:
    st.error("OPENAI_API_KEY ausente em Settings Secrets.")
    st.stop()
os.environ["OPENAI_API_KEY"] = api_key  # para libs que leem do ambiente

USE_V1 = False
client_v1 = None
openai_v0 = None

try:
    # Tentativa v1
    from openai import OpenAI
    try:
        client_v1 = OpenAI(api_key=api_key)
        USE_V1 = True
    except Exception:
        USE_V1 = False
except Exception:
    USE_V1 = False

if not USE_V1:
    # Fallback v0
    import openai as openai_v0  # type: ignore
    openai_v0.api_key = api_key

# Wrappers unificados
def create_embeddings(texts):
    if USE_V1:
        resp = client_v1.embeddings.create(model="text-embedding-3-small", input=texts)
        return [d.embedding for d in resp.data]
    else:
        resp = openai_v0.Embedding.create(model="text-embedding-3-small", input=texts)
        return [d["embedding"] for d in resp["data"]]

def chat_completion(messages, temperature=0.2, model="gpt-4o-mini"):
    if USE_V1:
        resp = client_v1.chat.completions.create(model=model, messages=messages, temperature=temperature)
        return resp.choices[0].message.content
    else:
        resp = openai_v0.ChatCompletion.create(model=model, messages=messages, temperature=temperature)
        return resp["choices"][0]["message"]["content"]

# ================== EMBEDDINGS E CHUNKING ==================
EMBED_DIM = 1536  # text-embedding-3-small
ENCODER = tiktoken.get_encoding("cl100k_base")

def chunk_text(text: str, max_tokens: int = 500, overlap_tokens: int = 50):
    toks = ENCODER.encode(text or "")
    chunks, start = [], 0
    while start < len(toks):
        end = min(start + max_tokens, len(toks))
        chunks.append(ENCODER.decode(toks[start:end]))
        start = end - overlap_tokens
        if start < 0:
            start = 0
        if start >= len(toks):
            break
    return chunks

def embed_texts(texts):
    vecs = np.array(create_embeddings(texts), dtype="float32")
    norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12
    return vecs / norms

# ================== EXTRAÇÃO PDF ==================
def extract_text_from_pdf(file) -> str:
    reader = PdfReader(file)
    return "\n".join((page.extract_text() or "") for page in reader.pages)

# ================== FAISS STORE ==================
INDEX_PATH, META_PATH = "faiss.index", "meta.pkl"

@st.cache_resource(show_spinner=False)
def load_store():
    if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
        index = faiss.read_index(INDEX_PATH)
        with open(META_PATH, "rb") as f:
            meta = pickle.load(f)
        return index, meta
    index = faiss.IndexFlatIP(EMBED_DIM)
    meta = []
    return index, meta

@st.cache_resource(show_spinner=False)
def save_store(index, meta):
    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump(meta, f)

index, meta = load_store()

# ================== UPLOAD E INDEXAÇÃO ==================
st.subheader(T("1) Suba o conteúdo", "1) Upload your content"))
uploaded = st.file_uploader(T("Arraste PDFs ou artigos", "Drag and drop PDFs or articles"),
                            type=["pdf"], accept_multiple_files=True)

c1, c2 = st.columns(2)
with c1:
    if st.button(T("Indexar arquivos enviados", "Index uploaded files"), use_container_width=True):
        if not uploaded:
            st.warning(T("Envie ao menos um PDF.", "Please upload at least one PDF."))
        else:
            new_chunks, new_meta = [], []
            with st.spinner(T("Lendo e preparando documentos...", "Reading and preparing documents...")):
                for f in uploaded:
                    raw = extract_text_from_pdf(f)
                    chunks = chunk_text(raw, max_tokens=520, overlap_tokens=60)
                    for ch in chunks:
                        chs = ch.strip()
                        if chs:
                            new_chunks.append(chs)
                            new_meta.append({
                                "source": f.name,
                                "snippet": chs[:180].replace("\n", " ")
                            })
            if not new_chunks:
                st.error(T("Nada para indexar.", "Nothing to index."))
            else:
                with st.spinner(T("Gerando embeddings e atualizando índice...", "Embedding and updating index...")):
                    vecs = embed_texts(new_chunks)
                    if index.ntotal == 0 and vecs.shape[1] != EMBED_DIM:
                        # Recria com dimensão correta, por segurança
                        index = faiss.IndexFlatIP(vecs.shape[1])
                    index.add(vecs)
                    meta.extend(new_meta)
                    save_store(index, meta)
                st.success(T("Indexação concluída.", "Indexing complete."))

with c2:
    if st.button(T("Limpar base", "Clear corpus"), type="secondary", use_container_width=True):
        try:
            if os.path.exists(INDEX_PATH): os.remove(INDEX_PATH)
            if os.path.exists(META_PATH): os.remove(META_PATH)
            st.success(T("Base limpa. Recarregue a página.", "Corpus cleared. Reload the page."))
        except Exception as e:
            st.error(str(e))

st.caption(T(
    "Sugestão inicial: 3 a 5 PDFs representativos. Depois amplie.",
    "Start with 3 to 5 representative PDFs. Expand later."
))

# ================== BUSCA E RESPOSTA ==================
st.subheader(T("2) Pergunte ao Dr_C", "2) Ask Dr_C"))
q = st.text_input(T("Sua pergunta", "Your question"),
                  placeholder=T("Exemplo: Soluções baseadas na natureza para restauração de matas ciliares",
                                "Example: Nature based solutions for riparian forest restoration"))
top_k = st.slider(T("Fontes top_k", "Sources top_k"), 2, 8, 4)

def search(query, k=4):
    if index.ntotal == 0:
        return []
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
    "Em caso de incerteza, informe e solicite mais contexto. "
    "No final, cite as fontes usadas."
)
SYSTEM_EN = (
    "You are Dr_C, a biodiversity expert. "
    "Keep the focus on conservation and nature based solutions. "
    "Ground your answer strictly on the provided sources. "
    "If uncertain, say so and ask for more context. "
    "At the end, cite the sources used."
)

def answer_with_sources(query, sources):
    system_msg = SYSTEM_PT if lang == "pt" else SYSTEM_EN
    ctx = "\n\n".join(f"[Source: {s.get('source','?')}]\n{s.get('snippet','')}" for s in sources)
    user_msg = (
        f"Pergunta: {query}\n\nContexto:\n{ctx}\n\nResponda de forma didática e objetiva. Cite as fontes ao final."
        if lang == "pt" else
        f"Question: {query}\n\nContext:\n{ctx}\n\nAnswer clearly and concisely. Cite sources at the end."
    )
    return chat_completion(
        messages=[{"role": "system", "content": system_msg},
                  {"role": "user", "content": user_msg}],
        temperature=0.2
    )

if st.button(T("Responder", "Answer"), type="primary", use_container_width=True) and q:
    if index.ntotal == 0:
        st.warning(T("Base vazia. Faça upload e indexe antes.", "Corpus empty. Upload and index first."))
    else:
        with st.spinner(T("Buscando e respondendo...", "Retrieving and generating...")):
            srcs = search(q, k=top_k)
            ans = answer_with_sources(q, srcs)
        st.markdown("### " + T("Resposta", "Answer"))
        st.write(ans)
        with st.expander(T("Fontes usadas", "Sources used")):
            for s in srcs:
                st.write(f"- **{s.get('source','?')}** — “{s.get('snippet','')[:200]}...”")
