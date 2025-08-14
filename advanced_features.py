# ================== FUNCIONALIDADES AVANÇADAS PARA DR_C ==================
# Arquivo: advanced_features.py

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from collections import Counter
import streamlit as st
from datetime import datetime
import json

def create_biodiversity_metrics_dashboard(meta):
    """Cria dashboard de métricas da base de conhecimento"""
    if not meta:
        return
    
    st.subheader("📊 Análise da Base de Conhecimento")
    
    # Métricas básicas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Chunks", len(meta))
    
    with col2:
        sources = [m.get('source', 'Unknown') for m in meta]
        unique_sources = len(set(sources))
        st.metric("Documentos", unique_sources)
    
    with col3:
        total_chars = sum(len(m.get('snippet', '')) for m in meta)
        st.metric("Caracteres Totais", f"{total_chars:,}")
    
    with col4:
        avg_chunk_size = total_chars / len(meta) if meta else 0
        st.metric("Tamanho Médio/Chunk", f"{avg_chunk_size:.0f}")
    
    # Distribuição por fonte
    if len(set(sources)) > 1:
        source_counts = Counter(sources)
        df_sources = pd.DataFrame([
            {"Documento": doc, "Chunks": count} 
            for doc, count in source_counts.items()
        ])
        
        fig_pie = px.pie(
            df_sources, 
            values='Chunks', 
            names='Documento',
            title="Distribuição de Conteúdo por Documento"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

def generate_topic_analysis(meta):
    """Análise de tópicos na base de conhecimento"""
    if not meta:
        return
    
    st.subheader("🔍 Análise de Tópicos")
    
    # Palavras-chave relacionadas à biodiversidade
    biodiversity_keywords = {
        'floresta': ['floresta', 'árvore', 'árvores', 'mata', 'vegetação'],
        'biodiversidade': ['biodiversidade', 'espécie', 'espécies', 'fauna', 'flora'],
        'conservação': ['conservação', 'preservação', 'sustentável', 'manejo'],
        'economia': ['economia', 'econômico', 'lucro', 'rentabilidade', 'viabilidade'],
        'amazônia': ['amazônia', 'amazônica', 'amazônico'],
        'tecnologia': ['tecnologia', 'blockchain', 'inteligência', 'artificial']
    }
    
    # Conta ocorrências
    topic_counts = {}
    all_text = ' '.join([m.get('snippet', '').lower() for m in meta])
    
    for topic, keywords in biodiversity_keywords.items():
        count = sum(all_text.count(keyword) for keyword in keywords)
        topic_counts[topic] = count
    
    # Visualização
    if topic_counts:
        df_topics = pd.DataFrame([
            {"Tópico": topic.title(), "Menções": count}
            for topic, count in topic_counts.items()
        ])
        
        fig_bar = px.bar(
            df_topics.sort_values('Menções', ascending=True),
            x='Menções',
            y='Tópico',
            orientation='h',
            title="Frequência de Tópicos na Base de Conhecimento",
            color='Menções',
            color_continuous_scale='Greens'
        )
        st.plotly_chart(fig_bar, use_container_width=True)

def create_conversation_analytics(chat_history):
    """Analytics das conversas com Dr_C"""
    if not chat_history:
        return
    
    st.subheader("📈 Analytics de Conversas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Evolução temporal
        questions = [len(chat.get('question', '').split()) for chat in chat_history]
        
        df_time = pd.DataFrame({
            'Conversa': range(1, len(chat_history) + 1),
            'Palavras_Pergunta': questions
        })
        
        fig_line = px.line(
            df_time,
            x='Conversa',
            y='Palavras_Pergunta',
            title="Complexidade das Perguntas ao Longo do Tempo",
            markers=True
        )
        st.plotly_chart(fig_line, use_container_width=True)
    
    with col2:
        # Qualidade das respostas (baseada no número de fontes)
        source_counts = [len(chat.get('sources', [])) for chat in chat_history]
        
        df_quality = pd.DataFrame({
            'Conversa': range(1, len(chat_history) + 1),
            'Fontes_Utilizadas': source_counts
        })
        
        fig_quality = px.bar(
            df_quality,
            x='Conversa',
            y='Fontes_Utilizadas',
            title="Número de Fontes por Resposta",
            color='Fontes_Utilizadas',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_quality, use_container_width=True)

def create_dr_c_persona_metrics(chat_history):
    """Métricas sobre como o Dr_C está respondendo (tom, estilo)"""
    if not chat_history:
        return
    
    st.subheader("🎭 Análise da Persona Dr_C")
    
    # Palavras-chave características do Dr_C
    persona_indicators = {
        'experiência_pessoal': ['minha', 'meu', 'vi', 'aprendi', 'presenciei'],
        'tom_pragmático': ['prático', 'viável', 'econômico', 'lucro', 'rentável'],
        'conservação': ['floresta', 'preservar', 'conservar', 'sustentável'],
        'amazônia': ['amazônia', 'amazônica', 'região'],
        'visão_estratégica': ['longo prazo', 'futuro', 'estratégia', 'planejamento'],
        'storytelling': ['história', 'exemplo', 'caso', 'experiência']
    }
    
    # Analisa respostas
    all_answers = ' '.join([chat.get('answer', '').lower() for chat in chat_history])
    
    persona_scores = {}
    for aspect, keywords in persona_indicators.items():
        score = sum(all_answers.count(keyword) for keyword in keywords)
        persona_scores[aspect] = score
    
    if persona_scores:
        df_persona = pd.DataFrame([
            {"Aspecto": aspect.replace('_', ' ').title(), "Pontuação": score}
            for aspect, score in persona_scores.items()
        ])
        
        fig_radar = go.Figure()
        
        fig_radar.add_trace(go.Scatterpolar(
            r=list(persona_scores.values()),
            theta=list(df_persona['Aspecto']),
            fill='toself',
            name='Dr_C Persona',
            line_color='green'
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(persona_scores.values()) if persona_scores.values() else 1]
                )),
            showlegend=True,
            title="Análise da Consistência da Persona Dr_C"
        )
        
        st.plotly_chart(fig_radar, use_container_width=True)

def create_educational_mode():
    """Modo educacional com explicações detalhadas"""
    st.subheader("🎓 Modo Educacional")
    
    educational_topics = {
        "Biodiversidade": {
            "conceito": "A variedade de vida em todas as suas formas e níveis de organização",
            "importancia": "Essencial para estabilidade dos ecossistemas e bem-estar humano",
            "ameacas": "Desmatamento, mudanças climáticas, poluição, urbanização"
        },
        "Manejo Sustentável": {
            "conceito": "Uso dos recursos naturais de forma que se mantenham para gerações futuras",
            "principios": "Planejamento, monitoramento, adaptação, participação comunitária",
            "beneficios": "Conservação + desenvolvimento econômico + bem-estar social"
        },
        "Economia Verde": {
            "conceito": "Modelo econômico que considera o capital natural como fator de produção",
            "exemplos": "Pagamento por serviços ambientais, ecoturismo, produtos sustentáveis",
            "desafios": "Mensuração de valor, políticas públicas, mudança cultural"
        }
    }
    
    selected_topic = st.selectbox(
        "Escolha um tópico para aprender:",
        list(educational_topics.keys())
    )
    
    if selected_topic:
        topic_info = educational_topics[selected_topic]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Conceito:**")
            st.write(topic_info.get("conceito", ""))
            
            if "principios" in topic_info:
                st.markdown("**Princípios:**")
                st.write(topic_info["principios"])
            elif "importancia" in topic_info:
                st.markdown("**Importância:**")
                st.write(topic_info["importancia"])
        
        with col2:
            if "exemplos" in topic_info:
                st.markdown("**Exemplos:**")
                st.write(topic_info["exemplos"])
            elif "beneficios" in topic_info:
                st.markdown("**Benefícios:**")
                st.write(topic_info["beneficios"])
            
            if "ameacas" in topic_info:
                st.markdown("**Principais Ameaças:**")
                st.write(topic_info["ameacas"])
            elif "desafios" in topic_info:
                st.markdown("**Desafios:**")
                st.write(topic_info["desafios"])

def create_interactive_timeline():
    """Timeline interativa da jornada do Dr_C"""
    st.subheader("📅 Jornada do Dr_C")
    
    timeline_events = [
        {"ano": 1990, "evento": "Início dos estudos na Amazônia", "tipo": "educação"},
        {"ano": 2000, "evento": "Primeiros investimentos em agronegócios sustentáveis", "tipo": "negócios"},
        {"ano": 2010, "evento": "Criação do projeto Fruits of the Amazon", "tipo": "conservação"},
        {"ano": 2015, "evento": "Parceria com Royal Botanic Gardens, Kew", "tipo": "pesquisa"},
        {"ano": 2020, "evento": "Descoberta de 13 novas espécies", "tipo": "ciência"},
        {"ano": 2023, "evento": "Desenvolvimento do Dr_C AI", "tipo": "tecnologia"},
        {"ano": 2024, "evento": "Lançamento do projeto ZYMZON", "tipo": "inovação"}
    ]
    
    df_timeline = pd.DataFrame(timeline_events)
    
    fig_timeline = px.scatter(
        df_timeline,
        x='ano',
        y=[1]*len(df_timeline),
        color='tipo',
        size=[10]*len(df_timeline),
        hover_data=['evento'],
        title="Linha do Tempo - Marcos na Carreira do Dr_C"
    )
    
    fig_timeline.update_layout(
        showlegend=True,
        yaxis_visible=False,
        height=300
    )
    
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Detalhes do evento selecionado
    selected_year = st.selectbox("Explore um marco:", df_timeline['ano'].tolist())
    
    if selected_year:
        event = df_timeline[df_timeline['ano'] == selected_year].iloc[0]
        st.info(f"**{event['ano']}:** {event['evento']}")

def create_impact_calculator():
    """Calculadora de impacto ambiental"""
    st.subheader("🌱 Calculadora de Impacto")
    
    st.write("Calcule o impacto potencial de projetos de reflorestamento:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        area_hectares = st.number_input("Área para reflorestamento (hectares):", min_value=0.1, value=10.0)
        tree_density = st.number_input("Densidade de árvores (por hectare):", min_value=100, value=500)
        
    with col2:
        co2_per_tree_year = st.number_input("CO₂ absorvido por árvore/ano (kg):", min_value=1.0, value=22.0)
        project_years = st.number_input("Duração do projeto (anos):", min_value=1, value=20)
    
    if st.button("Calcular Impacto"):
        total_trees = area_hectares * tree_density
        annual_co2 = total_trees * co2_per_tree_year
        total_co2 = annual_co2 * project_years
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Árvores Plantadas", f"{total_trees:,.0f}")
        
        with col2:
            st.metric("CO₂/Ano", f"{annual_co2:,.0f} kg")
        
        with col3:
            st.metric("CO₂ Total", f"{total_co2:,.0f} kg")
        
        with col4:
            equivalent_cars = total_co2 / 4600  # média anual de emissão por carro
            st.metric("Equiv. Carros/Ano", f"{equivalent_cars:.0f}")
        
        # Visualização do crescimento
        years = list(range(1, project_years + 1))
        co2_cumulative = [annual_co2 * year for year in years]
        
        df_growth = pd.DataFrame({
            'Ano': years,
            'CO₂ Acumulado (kg)': co2_cumulative
        })
        
        fig_growth = px.area(
            df_growth,
            x='Ano',
            y='CO₂ Acumulado (kg)',
            title="Projeção de Absorção de CO₂ ao Longo do Tempo"
        )
        
        st.plotly_chart(fig_growth, use_container_width=True)

def add_feedback_system():
    """Sistema de feedback para melhorar as respostas"""
    st.subheader("📝 Feedback sobre Dr_C")
    
    with st.form("feedback_form"):
        rating = st.slider("Como você avalia as respostas do Dr_C?", 1, 5, 3)
        
        feedback_type = st.selectbox(
            "Tipo de feedback:",
            ["Geral", "Precisão técnica", "Tom de resposta", "Relevância", "Sugestão de melhoria"]
        )
        
        feedback_text = st.text_area(
            "Seu feedback (opcional):",
            placeholder="Compartilhe sua experiência ou sugestões..."
        )
        
        submitted = st.form_submit_button("Enviar Feedback")
        
        if submitted:
            st.success("Obrigado pelo seu feedback! Ele nos ajuda a melhorar o Dr_C.")
            
            # Exibe métricas de feedback (simulado)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Avaliação Média", "4.2/5.0")
            with col2:
                st.metric("Total de Feedbacks", "47")
            with col3:
                st.metric("Satisfação", "89%")

def render_advanced_features(meta=None, chat_history=None):
    """Função principal para renderizar todas as funcionalidades avançadas"""
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🚀 Funcionalidades Avançadas")
    
    features = {
        "📊 Analytics": "analytics",
        "🎓 Modo Educacional": "educational",
        "📅 Timeline": "timeline", 
        "🌱 Calculadora de Impacto": "calculator",
        "📝 Feedback": "feedback"
    }
    
    selected_feature = st.sidebar.selectbox(
        "Escolha uma funcionalidade:",
        list(features.keys())
    )
    
    # Renderiza a funcionalidade selecionada
    feature_key = features[selected_feature]
    
    if feature_key == "analytics" and (meta or chat_history):
        if meta:
            create_biodiversity_metrics_dashboard(meta)
            generate_topic_analysis(meta)
        if chat_history:
            create_conversation_analytics(chat_history)
            create_dr_c_persona_metrics(chat_history)
    
    elif feature_key == "educational":
        create_educational_mode()
    
    elif feature_key == "timeline":
        create_interactive_timeline()
    
    elif feature_key == "calculator":
        create_impact_calculator()
    
    elif feature_key == "feedback":
        add_feedback_system()
    
    else:
        st.info("Selecione uma funcionalidade avançada no menu lateral.")
