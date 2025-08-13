import os
import io
import time
import pickle
import faiss
import numpy as np
import tiktoken
import streamlit as st
from pypdf import PdfReader
from openai import OpenAI

# ------------- Config básica -------------
st.set_page_config(page_title="Dr_C • MVP RAG", page_icon="🌿", layout="wide")
APP_LANG = os.getenv("APP_LANG", "pt")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ------------- UI helpers -------------
def T(pt, en):
    return pt if APP_LANG == "pt" else en

st.title("🌿 Dr_C — MVP (Fase 1)")
st.caption(T(
    "Avatar de biodiversidade (MVP): responde com base no seu acervo interno.",
    "Biodiversity avatar (MVP): answers based on your internal corpus."
))

# ------------- Chunking & Embeddings -------------
EMBED_MODEL = "text-embedding-3-small"   # custo baixo e bom p/ RAG
ENCODER = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(ENCODER.encode(text))

def chunk_text(text: str, max_tokens: int = 500, overlap_tokens: int = 50):
    """
    Divide texto em blocos ~max_tokens com leve overlap.
    """
    toks = ENCODER.encode(text)
    chunks = []
    start = 0
    while start < len(toks):
        end = min(start + max_tokens, len(toks))
        chunk = ENCODER.decode(toks[start:end])
        chunks.append(chunk)
        start = end - overlap_tokens
        if start < 0:
            start = 0
        if start >= len(toks):
            break
    return chunks

def embed_texts(texts: list[str]) -> np.ndarray:
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    vecs = np.array([d.embedding for d in resp.data], dtype="float32")
    return vecs

# ------------- PDF/Text ingestion -------------
def extract_text_from_pdf(file) -> str:
    reader = PdfReader(file)
    all_text = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        all_text.append(txt)
    return "\n".join(all_text)

# ------------- FAISS store -------------
INDEX_PATH = "faiss.index"
META_PATH  = "meta.pkl"

@st.cache_resource(show_spinner=False)
def load_store():
    if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
        index = faiss.read_index(INDEX_PATH)
        with open(META_PATH, "rb") as f:
            meta = pickle.load(f)
        return index, meta
    # store vazio
    d = 1536  # dim do text-embedding-3-small
    index = faiss.IndexFlatIP(d)  # cosine via inner product com vetores normalizados
    meta = []
    return index, meta

@st.cache_resource(show_spinner=False)
def save_store(index, meta):
    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump(meta, f)

def normalize(vecs: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12
    return vecs / norms

# ------------- Ingest UI -------------
st.subheader(T("1) Suba o conteúdo", "1) Upload your content"))
uploaded = st.file_uploader(
    T("Arraste PDFs/artigos do Charles", "Drag & drop Charles' PDFs/articles"),
    type=["pdf"], accept_multiple_files=True
)

index, meta = load_store()
colA, colB = st.columns([1,1])
with colA:
    if st.button(T("Indexar arquivos enviados", "Index uploaded files"), use_container_width=True):
        if not uploaded:
            st.warning(T("Envie ao menos 1 PDF.", "Please upload at least one PDF."))
        else:
            new_chunks, new_meta = [], []
            with st.spinner(T("Lendo e chunkando documentos...", "Reading & chunking documents...")):
                for f in uploaded:
                    raw = extract_text_from_pdf(f)
                    chunks = chunk_text(raw, max_tokens=520, overlap_tokens=60)
                    for ch in chunks:
                        if ch.strip():
                            new_chunks.append(ch)
                            new_meta.append({"source": f.name, "snippet": ch[:180].replace("\n"," ")})
            if not new_chunks:
                st.error(T("Nada para indexar.", "Nothing to index."))
            else:
                with st.spinner(T("Gerando embeddings e atualizando índice...", "Embedding & updating index...")):
                    vecs = embed_texts(new_chunks)
                    vecs = normalize(vecs)
                    # se index vazio, recria com a dimensão correta
                    if index.ntotal == 0:
                        d = vecs.shape[1]
                        new_index = faiss.IndexFlatIP(d)
                        index = new_index
                    index.add(vecs)
                    meta.extend(new_meta)
                    save_store(index, meta)
                st.success(T("Indexação concluída.", "Indexing complete."))

with colB:
    if st.button(T("Limpar base (reset)", "Clear corpus (reset)"), type="secondary", use_container_width=True):
        try:
            if os.path.exists(INDEX_PATH): os.remove(INDEX_PATH)
            if os.path.exists(META_PATH):  os.remove(META_PATH)
            st.success(T("Base limpa. Recarregue a página.", "Corpus cleared. Reload the page."))
        except Exception as e:
            st.error(str(e))

st.caption(T(
    "Dica: comece por 3–5 PDFs mais representativos. Depois amplia.",
    "Tip: start with 3–5 representative PDFs. Expand later."
))

# ------------- Retrieval + Answering -------------
st.subheader(T("2) Pergunte ao Dr_C", "2) Ask Dr_C"))
q = st.text_input(T("Sua pergunta", "Your question"), placeholder=T(
    "Ex.: Quais soluções baseadas na natureza para restauração de matas ciliares?",
    "e.g., Which nature-based solutions support riparian forest restoration?"
))
top_k = st.slider(T("Fontes (top_k)", "Sources (top_k)"), 2, 8, 4)

def search(query, k=4):
    if index.ntotal == 0:
        return []
    qvec = embed_texts([query])
    qvec = normalize(qvec)
    D, I = index.search(qvec, k)
    results = []
    for idx in I[0]:
        if 0 <= idx < len(meta):
            results.append(meta[idx])
    return results

SYSTEM_PT = (
    "Você é o Dr_C, um especialista em biodiversidade. "
    "Sempre responda trazendo o tema para natureza, conservação e soluções baseadas na biodiversidade. "
    "Baseie-se estritamente nas fontes fornecidas (trechos e PDFs indexados). "
    "Quando houver incerteza, declare e peça mais contexto. "
    "Cite as fontes ao final (arquivo e breve trecho)."
)
SYSTEM_EN = (
    "You are Dr_C, a biodiversity expert. "
    "Always bring the discussion back to nature, conservation, and biodiversity-based solutions. "
    "Ground answers strictly in the provided sources (snippets and indexed PDFs). "
    "When uncertain, say so and ask for more context. "
    "Cite sources at the end (file and brief snippet)."
)

def answer_with_sources(query, sources, lang="pt"):
    system_msg = SYSTEM_PT if lang == "pt" else SYSTEM_EN
    context_blocks = []
    for s in sources:
        block = f"[Source: {s.get('source','?')}]\n{ s.get('snippet','') }\n"
        context_blocks.append(block)
    context = "\n\n".join(context_blocks)

    user_prompt = (
        f"Pergunta: {query}\n\n"
        f"Contexto (trechos relevantes):\n{context}\n\n"
        "Responda de modo didático e objetivo. No final, liste as fontes usadas."
        if lang == "pt"
        else
        f"Question: {query}\n\n"
        f"Context (relevant snippets):\n{context}\n\n"
        "Answer clearly and concisely. At the end, list the sources used."
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system", "content": system_msg},
            {"role":"user", "content": user_prompt}
        ],
        temperature=0.2
    )
    return resp.choices[0].message.content

if st.button(T("Responder", "Answer"), type="primary", use_container_width=True) and q:
    if index.ntotal == 0:
        st.warning(T("Base vazia. Faça upload e indexe antes.", "Corpus empty. Upload & index first."))
    else:
        with st.spinner(T("Buscando fontes e gerando resposta...", "Retrieving & generating...")):
            srcs = search(q, k=top_k)
            ans = answer_with_sources(q, srcs, lang=APP_LANG)
        st.markdown("### " + T("Resposta", "Answer"))
        st.write(ans)
        with st.expander(T("Fontes usadas", "Sources used")):
            for s in srcs:
                st.write(f"- **{s.get('source','?')}** — “{s.get('snippet','')[:200]}...”")
        st.caption(T(
            "Observação: este é um MVP. O agente responde apenas com base no acervo enviado.",
            "Note: this is an MVP. The agent only answers from uploaded corpus."
        ))
