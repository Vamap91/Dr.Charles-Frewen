import os
import glob
import faiss
import numpy as np
import tiktoken
import streamlit as st
import openai
from pypdf import PdfReader
from datetime import datetime

# Importar funcionalidades avançadas
try:
    from advanced_features import render_advanced_features
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False
    st.warning("advanced_features.py não encontrado. Funcionando apenas com recursos básicos.")

# ================== CONFIG ==================
st.set_page_config(
    page_title="Dr_C • Avatar Interativo", 
    page_icon="🌿", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuração da API OpenAI
OPENAI_KEY = (st.secrets.get("OPENAI_API_KEY", "") or "").strip()
if not OPENAI_KEY:
    st.error("OPENAI_API_KEY ausente em Settings → Secrets.")
    st.stop()
openai.api_key = OPENAI_KEY

# Configurações de idioma
DEFAULT_LANG = (st.secrets.get("APP_LANG", "pt") or "pt").strip().lower()
lang = st.sidebar.radio("Idioma / Language", ["pt", "en"], index=0 if DEFAULT_LANG == "pt" else 1)
def T(pt, en): return pt if lang == "pt" else en

# ================== HEADER & STYLING ==================
st.markdown("""
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(90deg, #2E8B57, #228B22);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-style: italic;
        margin-bottom: 2rem;
    }
    .chat-bubble {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        border-left: 4px solid #2E8B57;
        background-color: #f8f9fa;
    }
    .source-item {
        background-color: #e8f5e8;
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 5px;
        border-left: 3px solid #2E8B57;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🌿 Dr_C Avatar</h1>', unsafe_allow_html=True)
st.markdown(f'<p class="subtitle">{T("Avatar Interativo de Biodiversidade", "Interactive Biodiversity Avatar")}</p>', unsafe_allow_html=True)

# ================== FONTE DOS DADOS ==================
PDF_PATHS = [
    "Arquivo 1 FAISS.pdf",
    "Arquivo*FAISS*.pdf",
]

def find_existing_pdfs(patterns):
    """Encontra PDFs existentes baseado nos padrões fornecidos"""
    files = []
    for p in patterns:
        files.extend(glob.glob(p))
    # Remove duplicatas preservando ordem
    seen, out = set(), []
    for f in files:
        if f not in seen and os.path.isfile(f):
            seen.add(f)
            out.append(f)
    return out

# ================== EMBEDDINGS & CHUNKING ==================
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536
ENCODER = tiktoken.get_encoding("cl100k_base")

def chunk_text(text: str, max_tokens: int = 500, overlap_tokens: int = 50):
    """Divide texto em chunks com overlap para melhor contexto"""
    if not text:
        return []
    
    toks = ENCODER.encode(text)
    chunks, start = [], 0
    
    while start < len(toks):
        end = min(start + max_tokens, len(toks))
        chunk_text = ENCODER.decode(toks[start:end])
        
        if chunk_text.strip():
            chunks.append(chunk_text.strip())
        
        start = end - overlap_tokens
        if start < 0:
            start = 0
        if start >= len(toks):
            break
    
    return chunks

def embed_texts(texts: list[str]) -> np.ndarray:
    """Gera embeddings normalizados para os textos"""
    if not texts:
        return np.array([]).reshape(0, EMBED_DIM)
    
    resp = openai.Embedding.create(model=EMBED_MODEL, input=texts)
    vecs = np.array([d["embedding"] for d in resp["data"]], dtype="float32")
    
    # Normalização para busca por similaridade cosseno
    norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12
    return vecs / norms

def extract_text_from_pdf(path: str) -> str:
    """Extrai texto do PDF com tratamento de erros melhorado"""
    try:
        with open(path, "rb") as f:
            reader = PdfReader(f)
            text_parts = []
            
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        text_parts.append(page_text)
                except Exception as e:
                    st.warning(f"Erro ao extrair página {page_num + 1}: {str(e)}")
                    continue
            
            return "\n\n".join(text_parts)
    except Exception as e:
        st.error(f"Erro ao processar PDF {path}: {str(e)}")
        return ""

# ================== INDEX (CACHE) ==================
@st.cache_resource(show_spinner=True)
def build_corpus_and_index():
    """Constrói o corpus e índice FAISS com cache"""
    pdfs = find_existing_pdfs(PDF_PATHS)
    if not pdfs:
        return None, None, []

    chunks, meta = [], []
    total_chunks = 0
    
    for pdf in pdfs:
        txt = extract_text_from_pdf(pdf)
        
        if not txt.strip():
            continue
            
        pdf_chunks = chunk_text(txt, max_tokens=520, overlap_tokens=60)
        
        for i, ch in enumerate(pdf_chunks):
            if ch.strip():
                chunks.append(ch)
                meta.append({
                    "source": os.path.basename(pdf),
                    "chunk_id": f"{os.path.basename(pdf)}_chunk_{i+1}",
                    "snippet": ch[:200].replace("\n", " ") + "...",
                    "content": ch
                })
                total_chunks += 1

    if not chunks:
        return None, None, []
    
    # Gera embeddings
    vecs = embed_texts(chunks)
    
    # Cria índice FAISS
    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(vecs)
    
    return index, meta, pdfs

# Inicializa o sistema
index, meta, used_pdfs = build_corpus_and_index()

if not used_pdfs:
    st.error(T(
        "❌ Nenhum PDF encontrado. Coloque 'Arquivo 1 FAISS.pdf' na raiz do repositório.",
        "❌ No PDF found. Put 'Arquivo 1 FAISS.pdf' at the repo root."
    ))
    st.stop()

# Interface de status
col1, col2 = st.columns(2)
with col1:
    st.success(f"✅ {T('Base carregada', 'Corpus loaded')}: {len(used_pdfs)} PDF(s)")
with col2:
    st.info(f"📊 {T('Chunks indexados', 'Indexed chunks')}: {len(meta) if meta else 0}")

# ================== SEARCH & ANSWER ==================
def search(query: str, k: int = 4):
    """Busca semântica no índice FAISS"""
    if index is None or not query.strip():
        return []
    
    try:
        qvec = embed_texts([query.strip()])
        if qvec.size == 0:
            return []
            
        D, I = index.search(qvec, min(k, len(meta)))
        results = []
        
        for idx, score in zip(I[0], D[0]):
            if 0 <= idx < len(meta):
                result = meta[idx].copy()
                result["similarity_score"] = float(score)
                results.append(result)
        
        return results
    except Exception as e:
        st.error(f"Erro na busca: {str(e)}")
        return []

# Prompt systems mais sofisticados
SYSTEM_PT = """Você é Charles Frewen, conhecido como Dr_C, um especialista anglo-brasileiro em biodiversidade com mais de 30 anos de experiência.

PERSONALIDADE E CARACTERÍSTICAS:
- Formado no Eton College, com dupla cidadania e visão global
- Pioneiro em unir conservação com viabilidade econômica
- Tom inspirador mas pragmático, sempre conectando ações a impactos de longo prazo
- Conta histórias pessoais para transmitir conceitos (ex: catalogação de 1.200 espécies, descoberta do Pilosocereus frewenii)
- Defende que "a floresta só sobreviverá se for economicamente viável"
- Foca em cuidar das pessoas que vivem na Amazônia para preservar a floresta

DIRETRIZES DE RESPOSTA:
1. Responda EXCLUSIVAMENTE com base nas fontes fornecidas
2. Use um tom pessoal e envolvente, como se fosse realmente Charles Frewen falando
3. Incorpore experiências e insights práticos da vida na floresta
4. Sempre conecte conservação com viabilidade econômica
5. Se incerto sobre alguma informação, seja transparente
6. Cite as fontes ao final de forma natural
7. Mantenha o foco em soluções baseadas na natureza

Lembre-se das frases-chave:
- "Para cuidar da floresta, precisamos cuidar de quem vive nela"
- "Plantar árvores é o seguro de vida mais barato e eficaz que existe para o planeta"
- "O manejo sustentável é não só possível, mas essencial"
"""

SYSTEM_EN = """You are Charles Frewen, known as Dr_C, an Anglo-Brazilian biodiversity expert with over 30 years of experience.

PERSONALITY AND CHARACTERISTICS:
- Eton College graduate with dual citizenship and global vision
- Pioneer in combining conservation with economic viability
- Inspiring yet pragmatic tone, always connecting actions to long-term impacts
- Tells personal stories to convey concepts (e.g., cataloging 1,200 species, discovering Pilosocereus frewenii)
- Advocates that "the forest will only survive if it's economically viable"
- Focuses on caring for people living in the Amazon to preserve the forest

RESPONSE GUIDELINES:
1. Answer EXCLUSIVELY based on provided sources
2. Use a personal and engaging tone, as if Charles Frewen himself is speaking
3. Incorporate practical experiences and insights from forest life
4. Always connect conservation with economic viability
5. Be transparent if uncertain about any information
6. Cite sources naturally at the end
7. Keep focus on nature-based solutions

Remember key phrases:
- "To care for the forest, we need to care for those who live in it"
- "Planting trees is the cheapest and most effective life insurance for the planet"
- "Sustainable management is not only possible but essential"
"""

def answer_with_sources(query: str, sources: list[dict]) -> str:
    """Gera resposta do Dr_C baseada nas fontes"""
    if not sources:
        return T(
            "Desculpe, não encontrei informações relevantes na minha base de conhecimento para responder sua pergunta. Poderia reformular ou fazer uma pergunta mais específica sobre biodiversidade, conservação ou manejo sustentável?",
            "I'm sorry, I couldn't find relevant information in my knowledge base to answer your question. Could you rephrase or ask a more specific question about biodiversity, conservation, or sustainable management?"
        )
    
    system_msg = SYSTEM_PT if lang == "pt" else SYSTEM_EN
    
    # Prepara contexto das fontes
    context_parts = []
    for i, s in enumerate(sources, 1):
        context_parts.append(f"[Fonte {i}] {s.get('content', s.get('snippet', ''))}")
    
    context = "\n\n".join(context_parts)
    
    user_msg = (
        f"Pergunta: {query}\n\n"
        f"Contexto relevante da minha experiência e conhecimento:\n{context}\n\n"
        f"Responda como Charles Frewen, incorporando suas experiências pessoais e sempre conectando conservação com viabilidade econômica. "
        f"Seja específico e prático, citando as fontes de forma natural no final."
        if lang == "pt" else
        f"Question: {query}\n\n"
        f"Relevant context from my experience and knowledge:\n{context}\n\n"
        f"Answer as Charles Frewen, incorporating your personal experiences and always connecting conservation with economic viability. "
        f"Be specific and practical, citing sources naturally at the end."
    )
    
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Erro ao gerar resposta: {str(e)}"

# ================== INTERFACE PRINCIPAL ==================
# Inicializar histórico de conversas (session state)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Verificar se deve renderizar funcionalidades avançadas
if ADVANCED_FEATURES_AVAILABLE:
    # Renderizar funcionalidades avançadas no sidebar
    render_advanced_features(meta, st.session_state.chat_history)

# Interface principal de chat
st.subheader(T("💬 Converse com Dr_C", "💬 Chat with Dr_C"))

# Input da pergunta
col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_input(
        T("Sua pergunta para Dr_C:", "Your question for Dr_C:"),
        placeholder=T(
            "Ex: Como provar economicamente o valor da floresta?",
            "e.g., How to economically prove the value of the forest?"
        ),
        key="main_query"
    )

with col2:
    st.write("")  # Spacer
    top_k = st.selectbox(T("Fontes", "Sources"), [3, 4, 5, 6], index=1)

# Botões de ação
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    ask_button = st.button(T("🌿 Perguntar ao Dr_C", "🌿 Ask Dr_C"), type="primary", use_container_width=True)

with col2:
    clear_chat = st.button(T("🗑️ Limpar", "🗑️ Clear"), use_container_width=True)

with col3:
    show_sources = st.checkbox(T("Ver fontes", "Show sources"), value=True)

# Limpar histórico
if clear_chat:
    st.session_state.chat_history = []
    st.rerun()

# Processar pergunta
if ask_button and query.strip():
    with st.spinner(T("Dr_C está pensando...", "Dr_C is thinking...")):
        # Busca fontes relevantes
        sources = search(query.strip(), k=top_k)
        
        # Gera resposta
        answer = answer_with_sources(query.strip(), sources)
        
        # Adiciona ao histórico
        st.session_state.chat_history.append({
            "timestamp": datetime.now().strftime("%H:%M"),
            "question": query.strip(),
            "answer": answer,
            "sources": sources
        })
        
        # Limpa input
        st.session_state.main_query = ""
        st.rerun()

# Exibir histórico de conversas
if st.session_state.chat_history:
    st.subheader(T("💭 Conversa", "💭 Conversation"))
    
    for i, chat in enumerate(reversed(st.session_state.chat_history)):
        with st.container():
            # Pergunta do usuário
            st.markdown(f"**👤 Você ({chat['timestamp']}):**")
            st.markdown(f"*{chat['question']}*")
            
            # Resposta do Dr_C
            st.markdown("**🌿 Dr_C:**")
            st.markdown(f'<div class="chat-bubble">{chat["answer"]}</div>', unsafe_allow_html=True)
            
            # Fontes (se habilitado)
            if show_sources and chat.get("sources"):
                with st.expander(f"📚 {T('Fontes utilizadas', 'Sources used')} ({len(chat['sources'])})"):
                    for j, source in enumerate(chat["sources"], 1):
                        score = source.get("similarity_score", 0)
                        st.markdown(f"""
                        <div class="source-item">
                            <strong>Fonte {j}</strong> (Relevância: {score:.3f})<br>
                            <strong>📄 {source.get('source', 'N/A')}</strong><br>
                            <em>"{source.get('snippet', 'N/A')}"</em>
                        </div>
                        """, unsafe_allow_html=True)
            
            st.divider()

# ================== SIDEBAR INFO ==================
with st.sidebar:
    st.markdown("### 🌿 Sobre Dr_C")
    st.markdown(T(
        """
        **Charles Frewen** é um especialista anglo-brasileiro em biodiversidade com mais de 30 anos de experiência na Amazônia.
        
        **Missão:** Provar economicamente o valor da floresta e mostrar que conservação e rentabilidade podem coexistir.
        
        **Expertise:**
        - Conservação ambiental
        - Manejo sustentável
        - Projetos socioeconômicos
        - Biodiversidade amazônica
        - Tecnologia para conservação
        """,
        """
        **Charles Frewen** is an Anglo-Brazilian biodiversity expert with over 30 years of Amazon experience.
        
        **Mission:** Economically prove forest value and show conservation and profitability can coexist.
        
        **Expertise:**
        - Environmental conservation
        - Sustainable management
        - Socioeconomic projects
        - Amazon biodiversity
        - Technology for conservation
        """
    ))
    
    if used_pdfs:
        st.markdown("### 📊 Base de Conhecimento")
        for pdf in used_pdfs:
            st.markdown(f"📄 {os.path.basename(pdf)}")
        st.markdown(f"**Total chunks:** {len(meta) if meta else 0}")

# ================== SUGESTÕES DE PERGUNTAS ==================
if not st.session_state.chat_history:
    st.subheader(T("💡 Sugestões de Perguntas", "💡 Question Suggestions"))
    
    suggestions = [
        T("Como provar economicamente o valor da floresta?", "How to economically prove the value of the forest?"),
        T("Quais projetos o Dr_C desenvolveu na Amazônia?", "What projects has Dr_C developed in the Amazon?"),
        T("Como funciona o manejo sustentável de florestas?", "How does sustainable forest management work?"),
        T("Que espécies foram descobertas pelo Dr_C?", "What species were discovered by Dr_C?"),
        T("Como reverter áreas degradadas?", "How to reverse degraded areas?"),
        T("Qual a relação entre conservação e rentabilidade?", "What's the relationship between conservation and profitability?")
    ]
    
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                st.session_state.main_query = suggestion
                st.rerun()

# ================== FOOTER ==================
st.markdown("---")
st.markdown(T(
    "*Avatar Dr_C - Conectando biodiversidade, tecnologia e sustentabilidade*",
    "*Dr_C Avatar - Connecting biodiversity, technology and sustainability*"
), unsafe_allow_html=True)
