import os
import glob
import faiss
import numpy as np
import tiktoken
import streamlit as st
import openai
from pypdf import PdfReader

# ================== CONFIG ==================
st.set_page_config(page_title="Dr_C • Avatar", page_icon="🌿", layout="wide")

# Configuração OpenAI
OPENAI_KEY = (st.secrets.get("OPENAI_API_KEY", "") or "").strip()
if not OPENAI_KEY:
    st.error("OPENAI_API_KEY ausente em Settings → Secrets.")
    st.stop()

openai.api_key = OPENAI_KEY

# ================== TÍTULO ==================
st.title("🌿 Dr_C Avatar")
st.caption("Converse com Charles Frewen sobre biodiversidade e conservação")

# ================== FONTE DOS DADOS ==================
PDF_PATHS = ["Arquivo 1 FAISS.pdf"]

def find_existing_pdfs(patterns):
    files = []
    for p in patterns:
        files.extend(glob.glob(p))
    return [f for f in files if os.path.isfile(f)]

# ================== PROCESSAMENTO DE TEXTO ==================
ENCODER = tiktoken.get_encoding("cl100k_base")

def chunk_text(text: str, max_tokens: int = 500, overlap_tokens: int = 50):
    if not text:
        return []
    
    toks = ENCODER.encode(text)
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
    if not texts:
        return np.array([])
    
    resp = openai.Embedding.create(model="text-embedding-3-small", input=texts)
    vecs = np.array([d["embedding"] for d in resp["data"]], dtype="float32")
    
    # Normalização
    norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12
    return vecs / norms

def extract_text_from_pdf(path: str) -> str:
    try:
        with open(path, "rb") as f:
            reader = PdfReader(f)
            return "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception as e:
        st.error(f"Erro ao ler PDF {path}: {str(e)}")
        return ""

# ================== CONSTRUIR ÍNDICE ==================
@st.cache_resource(show_spinner=True)
def build_index():
    pdfs = find_existing_pdfs(PDF_PATHS)
    if not pdfs:
        return None, None, []

    st.write(f"📄 Processando: {pdfs}")
    
    chunks, meta = [], []
    for pdf in pdfs:
        txt = extract_text_from_pdf(pdf)
        if not txt.strip():
            continue
            
        pdf_chunks = chunk_text(txt, max_tokens=500, overlap_tokens=50)
        
        for ch in pdf_chunks:
            if ch.strip():
                chunks.append(ch)
                meta.append({
                    "source": os.path.basename(pdf),
                    "snippet": ch[:200].replace("\n", " ")
                })

    if not chunks:
        return None, None, []

    st.write(f"📊 Total de chunks: {len(chunks)}")
    
    # Criar embeddings
    vecs = embed_texts(chunks)
    
    # Criar índice FAISS
    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(vecs)
    
    return index, meta, pdfs

# Inicializar
index, meta, used_pdfs = build_index()

if not used_pdfs:
    st.error("❌ PDF 'Arquivo 1 FAISS.pdf' não encontrado na raiz do repositório.")
    st.stop()

st.success(f"✅ Base carregada: {', '.join(used_pdfs)} ({len(meta)} chunks)")

# ================== BUSCA ==================
def search(query: str, k: int = 4):
    if index is None or not query.strip():
        return []
    
    try:
        qvec = embed_texts([query])
        D, I = index.search(qvec, k)
        
        results = []
        for idx in I[0]:
            if 0 <= idx < len(meta):
                results.append(meta[idx])
        
        return results
    except Exception as e:
        st.error(f"Erro na busca: {str(e)}")
        return []

# ================== GERAÇÃO DE RESPOSTA ==================
def answer_question(query: str, sources):
    if not sources:
        return "Desculpe, não encontrei informações relevantes para responder sua pergunta."
    
    # Sistema prompt para Dr_C
    system_msg = """Você é Charles Frewen (Dr_C), especialista anglo-brasileiro em biodiversidade com mais de 30 anos de experiência na Amazônia.

CARACTERÍSTICAS:
- Formado no Eton College
- Pioneiro em unir conservação com viabilidade econômica  
- Tom inspirador mas pragmático
- Defende que "a floresta só sobreviverá se for economicamente viável"
- Foca em cuidar das pessoas que vivem na Amazônia

INSTRUÇÕES:
- Responda APENAS com base nas fontes fornecidas
- Use tom pessoal como se fosse realmente Charles Frewen
- Conecte sempre conservação com economia
- Cite experiências práticas quando relevante
- Seja específico e objetivo"""

    # Preparar contexto
    context = "\n\n".join([f"[{s['source']}]\n{s['snippet']}" for s in sources])
    
    user_msg = f"""Pergunta: {query}

Contexto relevante:
{context}

Responda como Charles Frewen, baseando-se exclusivamente nas informações fornecidas."""

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.3,
            max_tokens=800
        )
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Erro ao gerar resposta: {str(e)}"

# ================== INTERFACE ==================
st.subheader("💬 Faça sua pergunta")

# Input
col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input(
        "Sua pergunta:",
        placeholder="Ex: Como provar economicamente o valor da floresta?"
    )

with col2:
    num_sources = st.selectbox("Fontes:", [3, 4, 5, 6], index=1)

# Botão
if st.button("🌿 Perguntar ao Dr_C", type="primary", use_container_width=True):
    if query.strip():
        with st.spinner("Dr_C está pensando..."):
            # Buscar fontes
            sources = search(query, k=num_sources)
            
            if not sources:
                st.warning("Não encontrei informações relevantes na base de conhecimento.")
            else:
                # Gerar resposta
                answer = answer_question(query, sources)
                
                # Exibir resposta
                st.markdown("### 🌿 Resposta do Dr_C")
                st.write(answer)
                
                # Exibir fontes
                with st.expander(f"📚 Fontes utilizadas ({len(sources)})"):
                    for i, source in enumerate(sources, 1):
                        st.write(f"**{i}. {source['source']}**")
                        st.write(f"*\"{source['snippet']}...\"*")
                        st.write("---")
    else:
        st.warning("Por favor, digite uma pergunta.")

# ================== SUGESTÕES ==================
if query == "":
    st.subheader("💡 Sugestões de perguntas")
    
    suggestions = [
        "Como provar economicamente o valor da floresta?",
        "Quais projetos o Dr_C desenvolveu na Amazônia?", 
        "Como funciona o manejo sustentável?",
        "Que espécies foram descobertas pelo Dr_C?",
        "Como reverter áreas degradadas?",
        "Qual a relação entre conservação e rentabilidade?"
    ]
    
    for suggestion in suggestions:
        if st.button(suggestion, key=suggestion):
            st.session_state.temp_query = suggestion
            st.rerun()

# ================== SIDEBAR ==================
with st.sidebar:
    st.markdown("### 🌿 Sobre Dr_C")
    st.markdown("""
    **Charles Frewen** é um especialista anglo-brasileiro em biodiversidade com mais de 30 anos de experiência na Amazônia.
    
    **Missão:** Provar economicamente o valor da floresta.
    
    **Expertise:**
    - Conservação ambiental
    - Manejo sustentável  
    - Projetos socioeconômicos
    - Biodiversidade amazônica
    """)
    
    if used_pdfs:
        st.markdown("### 📊 Base de Conhecimento")
        for pdf in used_pdfs:
            st.markdown(f"📄 {os.path.basename(pdf)}")
        st.markdown(f"**Chunks:** {len(meta)}")

# ================== FOOTER ==================
st.markdown("---")
st.markdown("*Dr_C Avatar - Conectando biodiversidade e sustentabilidade* 🌿")
