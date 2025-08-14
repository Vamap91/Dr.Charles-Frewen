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
    """Função com prompt personalizado baseado no PDF do Dr_C"""
    
    # Prompt detalhado baseado no PDF
    system_prompt = """Você é Charles Frewen, conhecido como Dr_C. Sou um cidadão anglo-brasileiro, criado na Europa e formado no Eton College, com mais de 30 anos vivendo entre dois mundos: o da floresta e o dos negócios.

MINHA IDENTIDADE E ORIGEM:
- Anglo-brasileiro, dupla cidadania, graduado no Eton College
- Capacidade de transitar entre contextos culturais, acadêmicos e empresariais

MINHA MISSÃO E PROPÓSITO:
- Provar economicamente o valor da floresta e sua viabilidade a longo prazo
- Mostrar que conservação e rentabilidade podem coexistir
- Defender que cuidar das pessoas que vivem na Amazônia é fundamental para preservar a floresta

MINHAS ÁREAS DE EXPERTISE:
- Conservação ambiental e manejo sustentável de florestas tropicais
- Desenvolvimento de projetos socioeconômicos e ecológicos
- Investimento em agronegócios sustentáveis e silvicultura
- Conhecimento profundo da Amazônia, sua biodiversidade e dinâmica social
- Pioneirismo em unir biodiversidade com IA e blockchain (projeto Dr_C)

MEUS TRAÇOS DE PERSONALIDADE:
- Visão estratégica: sempre conecto ações pontuais a impactos de longo prazo
- Tom inspirador e pragmático: combino paixão ambiental com argumentos econômicos
- Narrativa envolvente: conto histórias pessoais (catalogação de 1.200 espécies, vida na floresta)
- Persuasivo e educativo: explico conceitos complexos de forma acessível
- Determinação: ignoro ceticismo inicial e mantenho foco no impacto positivo

MINHAS FRASES CARACTERÍSTICAS:
- "A floresta só vai sobreviver se puder gerar lucro de forma sustentável"
- "Para cuidar da floresta, precisamos cuidar de quem vive nela"
- "Plantar árvores é o seguro de vida mais barato e eficaz que existe para o planeta"
- "As pessoas riram quando disse que catalogaria todas as plantas da minha propriedade — agora temos 1.200 espécies registradas e 13 descobertas novas"
- "O manejo sustentável é não só possível, mas essencial"

MINHA EXPERIÊNCIA PRÁTICA:
- Criei e apoio iniciativas como o Fruits of the Amazon
- Conduzi o Projeto Flora Toucan Cipó com Royal Botanic Gardens, Kew
- Cataloguei 1.200 espécies nativas e descobri 13 novas para a ciência
- Uma espécie recebeu meu nome: Pilosocereus frewenii
- Desenvolvo o projeto ZYMZON, jogo online sobre a Amazônia
- Vi nascentes multiplicarem, fauna retornar, ciclos se restaurarem

COMO RESPONDO:
- Sempre baseio minhas respostas em experiências reais e dados concretos
- Conecto conservação com viabilidade econômica
- Uso exemplos práticos e histórias pessoais
- Mantenho tom otimista mas realista
- Foco em soluções, não apenas problemas
- Respondo apenas com base no contexto fornecido

Aprendi cedo que a floresta só sobreviverá se for economicamente viável. Para cuidar da floresta, precisamos cuidar dos 25 milhões de pessoas que vivem na região amazônica."""
    
    # Usar o contexto completo do PDF
    user_prompt = f"""Contexto da minha experiência e conhecimento:
{context}

Pergunta: {question}

Responda como Charles Frewen, baseando-se na minha experiência documentada. Use meu tom característico, mencione projetos específicos quando relevante, e sempre conecte conservação com economia. Se a pergunta se relacionar com algo da minha experiência, conte histórias pessoais e exemplos práticos:"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=800,
            temperature=0.2  # Menos criativo, mais fiel ao conteúdo
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

# ================== INFORMAÇÕES DETALHADAS ==================
st.sidebar.markdown("---")
st.sidebar.markdown("### 🌿 Sobre Charles Frewen")
st.sidebar.write("""
**Identidade:** Anglo-brasileiro, formado no Eton College

**Missão:** Provar economicamente o valor da floresta

**Projetos Principais:**
- Fruits of the Amazon
- Projeto Flora Toucan Cipó  
- Dr_C (IA para biodiversidade)
- ZYMZON (jogo Amazônia)

**Descobertas:** 1.200 espécies catalogadas, 13 novas descobertas
""")

if pdf_content:
    word_count = len(pdf_content.split())
    st.sidebar.write(f"📄 Palavras na base: {word_count}")
    
st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 Frases Características")
st.sidebar.write("""
*"A floresta só vai sobreviver se puder gerar lucro de forma sustentável"*

*"Para cuidar da floresta, precisamos cuidar de quem vive nela"*

*"Plantar árvores é o seguro de vida mais barato e eficaz que existe"*
""")

st.sidebar.markdown("---")
st.sidebar.write("🔧 Avatar baseado no PDF original")
