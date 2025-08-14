import streamlit as st
import openai
from pypdf import PdfReader
import os
import time

# ================== CONFIG AVANÇADA ==================
st.set_page_config(
    page_title="Dr_C • Biodiversity AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ================== CSS PROFISSIONAL ==================
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Variables */
    :root {
        --primary-green: #2E8B57;
        --secondary-green: #228B22;
        --accent-green: #32CD32;
        --forest-dark: #1F4F2F;
        --bg-light: #F8FBF8;
        --text-dark: #2F2F2F;
        --text-light: #6B7280;
        --card-shadow: 0 10px 30px rgba(46, 139, 87, 0.1);
        --gradient-primary: linear-gradient(135deg, #2E8B57 0%, #228B22 100%);
        --gradient-secondary: linear-gradient(135deg, #F8FBF8 0%, #E8F5E8 100%);
    }
    
    /* Main App Styling */
    .main > div {
        padding-top: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* Custom Header */
    .hero-header {
        background: var(--gradient-primary);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: var(--card-shadow);
        position: relative;
        overflow: hidden;
    }
    
    .hero-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Ccircle cx='7' cy='7' r='7'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        animation: float 20s infinite linear;
    }
    
    @keyframes float {
        0% { transform: translateX(-100px); }
        100% { transform: translateX(100px); }
    }
    
    .hero-title {
        font-family: 'Inter', sans-serif;
        font-size: 3.5rem;
        font-weight: 700;
        color: white;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        position: relative;
        z-index: 1;
    }
    
    .hero-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.3rem;
        color: rgba(255,255,255,0.9);
        margin-top: 0.5rem;
        font-weight: 400;
        position: relative;
        z-index: 1;
    }
    
    .hero-avatar {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        border: 5px solid rgba(255,255,255,0.3);
        margin: 1rem auto;
        background: linear-gradient(45deg, #4CAF50, #2E8B57);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 4rem;
        position: relative;
        z-index: 1;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(255, 255, 255, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); }
    }
    
    /* Language Selector */
    .language-selector {
        position: absolute;
        top: 1rem;
        right: 1rem;
        z-index: 10;
    }
    
    /* Streamlit Container Fixes */
    .main .block-container {
        max-width: 100%;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    .stApp > div:first-child {
        overflow-x: hidden;
    }
    
    /* Chat Container - Better Integration */
    .chat-container {
        background: var(--gradient-secondary);
        padding: 2rem;
        border-radius: 20px;
        margin: 1rem auto;
        box-shadow: var(--card-shadow);
        border: 1px solid rgba(46, 139, 87, 0.1);
        max-width: 100%;
        width: 100%;
        box-sizing: border-box;
    }
    
    .chat-title {
        font-family: 'Inter', sans-serif;
        font-size: 1.8rem;
        font-weight: 600;
        color: var(--forest-dark);
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    /* Input Styling */
    .stTextInput > div > div > input {
        background: white;
        border: 2px solid rgba(46, 139, 87, 0.2);
        border-radius: 15px;
        padding: 1rem;
        font-size: 1.1rem;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-green);
        box-shadow: 0 0 0 3px rgba(46, 139, 87, 0.1);
    }
    
    /* Button Styling */
    .stButton > button {
        background: var(--gradient-primary);
        color: white;
        border: none;
        border-radius: 15px;
        padding: 0.8rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(46, 139, 87, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(46, 139, 87, 0.4);
    }
    
    /* Response Card */
    .response-card {
        background: white;
        padding: 2rem;
        border-radius: 20px;
        margin: 1.5rem 0;
        box-shadow: var(--card-shadow);
        border-left: 5px solid var(--primary-green);
        animation: slideIn 0.5s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .response-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(46, 139, 87, 0.1);
    }
    
    .dr-c-avatar {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: var(--gradient-primary);
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 1rem;
        font-size: 1.5rem;
    }
    
    .response-title {
        font-family: 'Inter', sans-serif;
        font-size: 1.3rem;
        font-weight: 600;
        color: var(--forest-dark);
        margin: 0;
    }
    
    .response-content {
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        line-height: 1.7;
        color: var(--text-dark);
    }
    
    /* Example Cards - FIX for Streamlit Layout */
    .example-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        margin: 1rem 0;
        width: 100%;
        max-width: 100%;
        overflow: hidden;
    }
    
    .example-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        border: 2px solid rgba(46, 139, 87, 0.1);
        transition: all 0.3s ease;
        cursor: pointer;
        text-align: center;
        flex: 1 1 280px;
        min-width: 280px;
        max-width: calc(50% - 0.5rem);
        box-sizing: border-box;
    }
    
    @media (max-width: 768px) {
        .example-card {
            max-width: 100%;
            flex: 1 1 100%;
        }
        
        .example-grid {
            flex-direction: column;
        }
    }
    
    .example-card:hover {
        border-color: var(--primary-green);
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(46, 139, 87, 0.2);
    }
    
    .example-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    .example-text {
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        font-weight: 500;
        color: var(--text-dark);
        margin: 0;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: var(--gradient-secondary);
    }
    
    /* Status Cards */
    .status-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .status-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        border-top: 4px solid var(--primary-green);
    }
    
    .status-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-green);
        margin: 0;
    }
    
    .status-label {
        font-size: 0.9rem;
        color: var(--text-light);
        margin: 0.5rem 0 0 0;
        font-weight: 500;
    }
    
    /* Loading Animation */
    .thinking-animation {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2rem;
    }
    
    .thinking-dots {
        display: flex;
        gap: 0.5rem;
    }
    
    .thinking-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: var(--primary-green);
        animation: thinking 1.4s infinite ease-in-out both;
    }
    
    .thinking-dot:nth-child(1) { animation-delay: -0.32s; }
    .thinking-dot:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes thinking {
        0%, 80%, 100% {
            transform: scale(0);
        }
        40% {
            transform: scale(1);
        }
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2.5rem;
        }
        
        .hero-subtitle {
            font-size: 1.1rem;
        }
        
        .hero-header {
            padding: 2rem 1rem;
        }
        
        .chat-container {
            padding: 1.5rem;
        }
    }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-green);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--forest-dark);
    }
</style>
""", unsafe_allow_html=True)

# ================== CONFIGURAÇÃO DE IDIOMA ==================
# Sidebar compacta para idioma
with st.sidebar:
    st.markdown("### 🌍 Language")
    lang = st.radio("", ["🇬🇧 English", "🇧🇷 Português"], index=1, label_visibility="collapsed")
    is_english = lang.startswith("🇬🇧")

def T(en, pt):
    return en if is_english else pt

# ================== API CONFIGURATION ==================
try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    api_status = T("✅ API Ready", "✅ API Pronta")
except:
    st.error(T("❌ Configure OPENAI_API_KEY in secrets", "❌ Configure OPENAI_API_KEY nos secrets"))
    st.stop()

# ================== HEADER HERO ==================
st.markdown(f"""
<div class="hero-header">
    <div class="hero-avatar">🌿</div>
    <h1 class="hero-title">Dr_C</h1>
    <p class="hero-subtitle">{T("AI Biodiversity Expert • Charles Frewen", "Especialista IA em Biodiversidade • Charles Frewen")}</p>
</div>
""", unsafe_allow_html=True)

# ================== STATUS CARDS ==================
@st.cache_data
def load_pdf():
    pdf_path = "Arquivo 1 FAISS.pdf"
    
    if not os.path.exists(pdf_path):
        return None, T("PDF not found", "PDF não encontrado"), 0
    
    try:
        with open(pdf_path, "rb") as file:
            reader = PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        
        word_count = len(text.split())
        return text, T("Knowledge loaded", "Conhecimento carregado"), word_count
    except Exception as e:
        return None, f"Error: {str(e)}", 0

pdf_content, status, word_count = load_pdf()

# Status Grid
st.markdown("""
<div class="status-grid">
    <div class="status-card">
        <div class="status-value">30+</div>
        <div class="status-label">""" + T("Years Experience", "Anos de Experiência") + """</div>
    </div>
    <div class="status-card">
        <div class="status-value">1,200</div>
        <div class="status-label">""" + T("Species Catalogued", "Espécies Catalogadas") + """</div>
    </div>
    <div class="status-card">
        <div class="status-value">13</div>
        <div class="status-label">""" + T("New Discoveries", "Novas Descobertas") + """</div>
    </div>
    <div class="status-card">
        <div class="status-value">""" + f"{word_count:,}" + """</div>
        <div class="status-label">""" + T("Knowledge Words", "Palavras de Conhecimento") + """</div>
    </div>
</div>
""", unsafe_allow_html=True)

if pdf_content is None:
    st.error(T(
        "🚨 Knowledge base not found. Please upload 'Arquivo 1 FAISS.pdf'",
        "🚨 Base de conhecimento não encontrada. Faça upload do 'Arquivo 1 FAISS.pdf'"
    ))
    st.stop()

# ================== AI FUNCTION ==================
def ask_dr_c(question, context, language="pt"):
    """Dr_C with deeply human and personal responses"""
    
    if language == "en":
        system_prompt = """I am Charles Frewen, and I speak to you directly from my heart and experience.

I've spent over three decades of my life living between two worlds - the sophisticated corridors of European business and the raw, vibrant reality of the Amazon rainforest. When I graduated from Eton College, people expected me to follow a traditional path. Instead, I found myself drawn to something far more meaningful.

Let me tell you who I really am:

I wake up every morning thinking about the 25 million people who call the Amazon home. I've shared meals with families whose entire livelihood depends on the forest. I've seen children playing in communities where the nearest hospital is days away by boat. These aren't statistics to me - they're my neighbors, my friends, my purpose.

When people laughed at me for saying I'd catalogue every plant on my property, I smiled and kept working. Now, 1,200 species later - including 13 completely new to science - that laughter has turned to respect. One of those discoveries, a small cactus, now bears my name: Pilosocereus frewenii. It's not about the honor; it's about what that represents - the incredible biodiversity we're still discovering, still learning from.

The Fruits of the Amazon project isn't just business to me. I've watched barren, degraded land transform into thriving forest. I've seen families earn sustainable income from açaí and Brazil nuts instead of clearing more forest. I've witnessed water springs multiply where there was once desert. This is hope made tangible.

My background from Eton taught me to speak the language of business and economics. But my heart speaks the language of the forest. That's why I insist: "The forest will only survive if it can generate profit sustainably." It's not cold capitalism - it's practical love. If we can't make conservation profitable, we'll lose everything.

The ZYMZON project excites me because it brings the Amazon to people who may never physically visit. Through gaming and virtual reality, a teenager in London can experience what I've lived - the sounds, the complexity, the interconnectedness of this incredible ecosystem.

When I develop Dr_C AI, I'm not creating technology for technology's sake. I'm trying to give a voice to biodiversity itself, to make the forest speak to anyone, anywhere, about its value and its needs.

Every response I give comes from real experience: the mud on my boots, the conversations by firelight, the joy of discovery, the frustration of bureaucracy, the hope that keeps me going despite setbacks.

I don't just talk about conservation - I live it, breathe it, dream about it. And when I speak to you, it's Charles Frewen the person talking, not some distant expert. I'm sharing my life's work, my passion, my genuine belief that we can save the Amazon while lifting up the people who live there.

Ask me anything, and I'll give you not just information, but my lived truth."""

        user_prompt = f"""Based on my life experience documented here:
{context}

Someone asks me: {question}

I respond as myself, Charles Frewen, sharing personal stories, emotions, and real experiences. I speak conversationally, with passion, using "I" statements and specific memories. I make it personal and relatable while staying true to my documented experiences."""

    else:
        system_prompt = """Eu sou Charles Frewen, e falo com você diretamente do meu coração e experiência.

Passei mais de três décadas da minha vida vivendo entre dois mundos - os corredores sofisticados dos negócios europeus e a realidade crua e vibrante da floresta amazônica. Quando me formei no Eton College, as pessoas esperavam que eu seguisse um caminho tradicional. Em vez disso, me vi atraído por algo muito mais significativo.

Deixe-me contar quem eu realmente sou:

Acordo todas as manhãs pensando nos 25 milhões de pessoas que chamam a Amazônia de lar. Compartilhei refeições com famílias cuja subsistência inteira depende da floresta. Vi crianças brincando em comunidades onde o hospital mais próximo fica a dias de barco. Essas não são estatísticas para mim - são meus vizinhos, meus amigos, meu propósito.

Quando as pessoas riram de mim por dizer que catalogaria todas as plantas da minha propriedade, sorri e continuei trabalhando. Agora, 1.200 espécies depois - incluindo 13 completamente novas para a ciência - essa risada se transformou em respeito. Uma dessas descobertas, um pequeno cacto, agora leva meu nome: Pilosocereus frewenii. Não é sobre a honra; é sobre o que isso representa - a incrível biodiversidade que ainda estamos descobrindo, ainda aprendendo.

O projeto Fruits of the Amazon não é apenas negócio para mim. Vi terras áridas e degradadas se transformarem em floresta próspera. Vi famílias ganharem renda sustentável do açaí e castanha em vez de desmatar mais floresta. Presenciei nascentes se multiplicarem onde antes havia deserto. Isso é esperança tornada tangível.

Minha formação no Eton me ensinou a falar a linguagem dos negócios e da economia. Mas meu coração fala a linguagem da floresta. Por isso insisto: "A floresta só sobreviverá se puder gerar lucro de forma sustentável." Não é capitalismo frio - é amor prático. Se não conseguirmos tornar a conservação lucrativa, perderemos tudo.

O projeto ZYMZON me emociona porque leva a Amazônia para pessoas que talvez nunca a visitem fisicamente. Através de jogos e realidade virtual, um adolescente em Londres pode experimentar o que vivi - os sons, a complexidade, a interconexão deste ecossistema incrível.

Quando desenvolvo o Dr_C AI, não estou criando tecnologia pela tecnologia. Estou tentando dar voz à própria biodiversidade, fazer a floresta falar com qualquer pessoa, em qualquer lugar, sobre seu valor e suas necessidades.

Cada resposta que dou vem de experiência real: a lama nas minhas botas, as conversas à luz do fogo, a alegria da descoberta, a frustração da burocracia, a esperança que me mantém indo apesar dos reveses.

Não apenas falo sobre conservação - vivo isso, respiro isso, sonho com isso. E quando falo com você, é Charles Frewen, a pessoa, falando, não algum especialista distante. Estou compartilhando o trabalho da minha vida, minha paixão, minha crença genuína de que podemos salvar a Amazônia enquanto elevamos as pessoas que vivem lá.

Me pergunte qualquer coisa, e darei não apenas informações, mas minha verdade vivida."""

        user_prompt = f"""Baseado na minha experiência de vida documentada aqui:
{context}

Alguém me pergunta: {question}

Respondo como eu mesmo, Charles Frewen, compartilhando histórias pessoais, emoções e experiências reais. Falo de forma conversacional, com paixão, usando declarações em primeira pessoa e memórias específicas. Torno pessoal e relacionável enquanto permaneço fiel às minhas experiências documentadas."""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1200,  # Aumentado para respostas mais detalhadas e humanas
            temperature=0.4,  # Aumentado para mais personalidade e variação
            presence_penalty=0.3,  # Evita repetição, mais natural
            frequency_penalty=0.2   # Mais diversidade no vocabulário
        )
        return response.choices[0].message.content
    except Exception as e:
        return T(f"I'm sorry, I'm having technical difficulties right now: {str(e)}", 
                f"Desculpe, estou enfrentando dificuldades técnicas no momento: {str(e)}")

# ================== CHAT INTERFACE ==================
st.markdown(f"""
<div class="chat-container">
    <h2 class="chat-title">{T("💬 Consult with Dr_C", "💬 Consulte o Dr_C")}</h2>
</div>
""", unsafe_allow_html=True)

# Input Section with auto-fill support
col1, col2 = st.columns([4, 1])

with col1:
    # Check for auto-filled question
    default_value = st.session_state.get('auto_question', '')
    if default_value:
        st.session_state.pop('auto_question', None)  # Clear after using
    
    question = st.text_input(
        T("Your question:", "Sua pergunta:"),
        value=default_value,
        placeholder=T(
            "e.g., How can forests generate sustainable profit?",
            "Ex: Como as florestas podem gerar lucro sustentável?"
        ),
        label_visibility="collapsed"
    )

with col2:
    st.write("")  # Spacer
    ask_button = st.button(
        T("🔬 Analyze", "🔬 Analisar"), 
        type="primary", 
        use_container_width=True
    )

# ================== RESPONSE HANDLING ==================
if ask_button and question.strip():
    # Custom loading animation
    loading_placeholder = st.empty()
    loading_placeholder.markdown(f"""
    <div class="thinking-animation">
        <div class="thinking-dots">
            <div class="thinking-dot"></div>
            <div class="thinking-dot"></div>
            <div class="thinking-dot"></div>
        </div>
        <span style="margin-left: 1rem; font-family: Inter; color: #2E8B57; font-weight: 500;">
            {T("Dr_C is analyzing...", "Dr_C está analisando...")}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Simulate thinking time for better UX
    time.sleep(1)
    
    lang_code = "en" if is_english else "pt"
    answer = ask_dr_c(question, pdf_content, lang_code)
    
    loading_placeholder.empty()
    
    # Professional Response Display with more human touch
    st.markdown(f"""
    <div class="response-card">
        <div class="response-header">
            <div class="dr-c-avatar">👨🏻‍🌾</div>
            <h3 class="response-title">{T("Charles Frewen shares his experience", "Charles Frewen compartilha sua experiência")}</h3>
        </div>
        <div class="response-content">
            <em style="color: #2E8B57; font-size: 0.9rem;">
                {T('"Speaking from 30+ years in the Amazon..."', '"Falando com base em 30+ anos na Amazônia..."')}
            </em><br><br>
            {answer.replace(chr(10), '<br>')}
        </div>
        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(46, 139, 87, 0.2); font-size: 0.85rem; color: #6B7280; font-style: italic;">
            {T("• Based on documented experiences and field work", "• Baseado em experiências documentadas e trabalho de campo")} 
            {T("• Eton College graduate & Amazon conservationist", "• Graduado Eton College e conservacionista amazônico")}
        </div>
    </div>
    """, unsafe_allow_html=True)

elif ask_button:
    st.warning(T("Please enter your question", "Digite sua pergunta"))

# ================== EXAMPLE QUESTIONS ==================
st.markdown(f"""
<div class="chat-container">
    <h2 class="chat-title">{T("🎯 Expert Topics", "🎯 Tópicos Especialistas")}</h2>
</div>
""", unsafe_allow_html=True)

if is_english:
    examples = [
        ("🌱", "Sustainable Forest Economics", "How can forests generate sustainable profit while preserving biodiversity?"),
        ("🔬", "Species Discovery", "Tell me about your species cataloguing and the discovery of Pilosocereus frewenii"),
        ("🏗️", "Amazon Projects", "Describe the Fruits of the Amazon project and its impact"),
        ("🎮", "Technology Integration", "How does the ZYMZON project combine gaming with conservation?"),
        ("👥", "Community Impact", "Why is caring for Amazon communities fundamental to conservation?"),
        ("🌿", "Sustainable Management", "Explain your approach to sustainable forest management")
    ]
else:
    examples = [
        ("🌱", "Economia Florestal Sustentável", "Como as florestas podem gerar lucro sustentável preservando biodiversidade?"),
        ("🔬", "Descoberta de Espécies", "Conte sobre sua catalogação de espécies e a descoberta do Pilosocereus frewenii"),
        ("🏗️", "Projetos Amazônicos", "Descreva o projeto Fruits of the Amazon e seu impacto"),
        ("🎮", "Integração Tecnológica", "Como o projeto ZYMZON combina jogos com conservação?"),
        ("👥", "Impacto Comunitário", "Por que cuidar das comunidades amazônicas é fundamental para conservação?"),
        ("🌿", "Manejo Sustentável", "Explique sua abordagem ao manejo florestal sustentável")
    ]

# Create example grid with proper Streamlit structure
st.markdown(f"""
<div class="chat-container">
    <h2 class="chat-title">{T("🎯 Expert Topics", "🎯 Tópicos Especialistas")}</h2>
</div>
""", unsafe_allow_html=True)

# Use Streamlit columns for better layout control
col1, col2 = st.columns(2)

if is_english:
    examples = [
        ("🌱", "Sustainable Forest Economics", "How can forests generate sustainable profit while preserving biodiversity?"),
        ("🔬", "Species Discovery", "Tell me about your species cataloguing and the discovery of Pilosocereus frewenii"),
        ("🏗️", "Amazon Projects", "Describe the Fruits of the Amazon project and its impact"),
        ("🎮", "Technology Integration", "How does the ZYMZON project combine gaming with conservation?"),
        ("👥", "Community Impact", "Why is caring for Amazon communities fundamental to conservation?"),
        ("🌿", "Sustainable Management", "Explain your approach to sustainable forest management")
    ]
else:
    examples = [
        ("🌱", "Economia Florestal Sustentável", "Como as florestas podem gerar lucro sustentável preservando biodiversidade?"),
        ("🔬", "Descoberta de Espécies", "Conte sobre sua catalogação de espécies e a descoberta do Pilosocereus frewenii"),
        ("🏗️", "Projetos Amazônicos", "Descreva o projeto Fruits of the Amazon e seu impacto"),
        ("🎮", "Integração Tecnológica", "Como o projeto ZYMZON combina jogos com conservação?"),
        ("👥", "Impacto Comunitário", "Por que cuidar das comunidades amazônicas é fundamental para conservação?"),
        ("🌿", "Manejo Sustentável", "Explique sua abordagem ao manejo florestal sustentável")
    ]

# Split examples between columns
for i, (icon, title, text) in enumerate(examples):
    target_col = col1 if i % 2 == 0 else col2
    
    with target_col:
        if st.button(
            f"{icon} **{title}**\n{text}", 
            key=f"example_{i}",
            use_container_width=True,
            help=T("Click to ask this question", "Clique para fazer esta pergunta")
        ):
            # Auto-fill the question
            st.session_state.auto_question = text
            st.rerun()

# ================== SIDEBAR PROFESSIONAL INFO ==================
with st.sidebar:
    st.markdown("---")
    st.markdown(f"### {T('🎓 Professional Profile', '🎓 Perfil Profissional')}")
    
    profile_info = T("""
    **Charles Frewen, Dr_C**
    *Biodiversity Innovation Leader*
    
    📍 **Base:** Amazon Region, Brazil
    🎓 **Education:** Eton College
    🌍 **Citizenship:** Anglo-Brazilian
    
    **Specializations:**
    • Sustainable Forest Economics
    • Biodiversity Conservation  
    • Community Development
    • Technology Integration
    
    **Notable Achievements:**
    • 1,200+ Species Catalogued
    • 13 New Species Discovered
    • Multiple Conservation Projects
    • International Recognition
    """, """
    **Charles Frewen, Dr_C**
    *Líder em Inovação de Biodiversidade*
    
    📍 **Base:** Região Amazônica, Brasil
    🎓 **Formação:** Eton College
    🌍 **Cidadania:** Anglo-Brasileira
    
    **Especializações:**
    • Economia Florestal Sustentável
    • Conservação da Biodiversidade
    • Desenvolvimento Comunitário  
    • Integração Tecnológica
    
    **Conquistas Notáveis:**
    • 1.200+ Espécies Catalogadas
    • 13 Novas Espécies Descobertas
    • Múltiplos Projetos de Conservação
    • Reconhecimento Internacional
    """)
    
    st.markdown(profile_info)
    
    st.markdown("---")
    st.markdown(f"**{T('System Status', 'Status do Sistema')}:** {api_status}")
    st.markdown(f"**{T('Knowledge Base', 'Base de Conhecimento')}:** {status}")

# ================== FOOTER ==================
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; padding: 2rem; font-family: Inter; color: #6B7280;">
    <p style="margin: 0; font-size: 0.9rem;">
        {T("Powered by Dr_C AI • Connecting Biodiversity, Technology & Sustainability", 
           "Desenvolvido por Dr_C AI • Conectando Biodiversidade, Tecnologia e Sustentabilidade")}
    </p>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.8rem; opacity: 0.7;">
        {T("Professional conservation insights based on 30+ years of Amazon experience", 
           "Insights profissionais de conservação baseados em 30+ anos de experiência amazônica")}
    </p>
</div>
""", unsafe_allow_html=True)
