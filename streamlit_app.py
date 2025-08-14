import streamlit as st
import openai
from pypdf import PdfReader
import os

# ================== CONFIG BÁSICA ==================
st.set_page_config(page_title="Dr_C", page_icon="🌿")

# API Key
try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    st.sidebar.success("✅ API configurada")
except:
    st.error("❌ Configure OPENAI_API_KEY nos secrets")
    st.stop()

# ================== TÍTULO ==================
st.title("🌿 Dr_C Avatar")
st.write("Chat simples com Charles Frewen sobre biodiversidade")

# ================== CARREGAR PDF ==================
@st.cache_data
def load_pdf():
    pdf_path = "Arquivo 1 FAISS.pdf"
    
    if not os.path.exists(pdf_path):
        return None, "❌ Arquivo 'Arquivo 1 FAISS.pdf' não encontrado"
    
    try:
        with open(pdf_path, "rb") as file:
            reader = PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        
        return text, f"✅ PDF carregado: {len(text)} caracteres"
    except Exception as e:
        return None, f"❌ Erro ao carregar PDF: {str(e)}"

# Carregar conteúdo
pdf_content, status = load_pdf()
st.sidebar.write(status)

if pdf_content is None:
    st.error("Não foi possível carregar o PDF. Verifique se 'Arquivo 1 FAISS.pdf' está na raiz do repositório.")
    st.stop()

# ================== FUNÇÃO PRINCIPAL ==================
def ask_dr_c(question, context):
    """Função simples para gerar resposta do Dr_C"""
    
    # Prompt super simples
    system_prompt = """Você é Charles Frewen (Dr_C), especialista em biodiversidade da Amazônia.
    
    Características:
    - Formado no Eton College
    - Mais de 30 anos de experiência na Amazônia
    - Defende que conservação deve ser economicamente viável
    - Tom prático e inspirador
    
    Responda baseado APENAS no contexto fornecido.
    Se não souber, diga que não tem essa informação."""
    
    # Usar apenas os primeiros 3000 caracteres do PDF para evitar limite de tokens
    context_short = context[:3000] + "..."
    
    user_prompt = f"""Contexto: {context_short}

Pergunta: {question}

Responda como Charles Frewen, de forma objetiva e prática:"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Erro: {str(e)}"

# ================== INTERFACE ==================
st.subheader("💬 Faça sua pergunta")

# Campo de pergunta
question = st.text_input(
    "Digite sua pergunta:",
    placeholder="Ex: Como a floresta pode gerar lucro sustentável?"
)

# Botão para perguntar
if st.button("🌿 Perguntar", type="primary"):
    if question.strip():
        with st.spinner("Pensando..."):
            answer = ask_dr_c(question, pdf_content)
            
            st.markdown("### 🌿 Resposta do Dr_C:")
            st.write(answer)
    else:
        st.warning("Digite uma pergunta primeiro!")

# ================== EXEMPLOS ==================
st.subheader("💡 Perguntas de exemplo")

examples = [
    "Como provar o valor econômico da floresta?",
    "Quais projetos desenvolveu na Amazônia?",
    "Como funciona o manejo sustentável?",
    "Que espécies descobriu?"
]

for i, example in enumerate(examples):
    if st.button(example, key=f"ex_{i}"):
        # Simular clique com exemplo
        with st.spinner("Pensando..."):
            answer = ask_dr_c(example, pdf_content)
            
            st.markdown("### 🌿 Resposta do Dr_C:")
            st.write(answer)

# ================== INFORMAÇÕES ==================
st.sidebar.markdown("---")
st.sidebar.markdown("### 🌿 Sobre")
st.sidebar.write("Charles Frewen - Especialista em biodiversidade amazônica")

if pdf_content:
    word_count = len(pdf_content.split())
    st.sidebar.write(f"📄 Palavras no PDF: {word_count}")

st.sidebar.markdown("---")
st.sidebar.write("🔧 Versão ultra-simples para teste")
