import streamlit as st
import pickle
import pandas as pd
import numpy as np
from sentence_transformers import util
import plotly.express as px
import plotly.graph_objects as go
import math
import re
import gdown
import os
from PIL import Image
import base64
import io
import streamlit_nested_layout


# Configuração da página
st.set_page_config(
    page_title="Decision Recruiter - Recomendação de Candidatos",
    page_icon="",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Função para detectar o tema do Streamlit
def get_streamlit_theme():
    """Detecta se o tema é dark ou light baseado nas configurações do Streamlit"""
    try:
        # Tenta acessar as configurações de tema do Streamlit
        if hasattr(st, '_config') and st._config.get_option('theme.base') == 'dark':
            return 'dark'
        elif hasattr(st, '_config') and st._config.get_option('theme.base') == 'light':
            return 'light'
        else:
            # Fallback: usar JavaScript para detectar o tema
            return 'auto'
    except:
        return 'auto'

# CSS dinâmico baseado no tema
def get_dynamic_css():
    """Retorna CSS adaptado para tema claro e escuro"""
    return """
<style>
    /* Variáveis CSS para tema claro e escuro */
    :root {
        --primary: #4F46E5;
        --primary-light: #6366F1;
        --secondary: #10B981;
        --link-color: #6d97b2;
        --link-hover: #5a8399;
    }
    
    /* Tema claro (padrão) */
    [data-theme="light"], .stApp {
        --background: #F9FAFB;
        --surface: #FFFFFF;
        --surface-alt: #F3F4F6;
        --text-primary: #111827;
        --text-secondary: #4B5563;
        --text-muted: #6B7280;
        --border: #E5E7EB;
        --border-selected: #4F46E5;
        --shadow: rgba(0, 0, 0, 0.1);
        --shadow-selected: rgba(79, 70, 229, 0.2);
        --card-bg: #FFFFFF;
        --card-bg-selected: #EEF2FF;
        --header-bg: #4F46E5;
        --header-text: #FFFFFF;
        --skill-tag-bg: #F3F4F6;
        --skill-tag-text: #374151;
        --progress-bg: #F3F4F6;
    }
    
    /* Tema escuro */
    @media (prefers-color-scheme: dark) {
        :root, .stApp {
            --background: #0F172A;
            --surface: #1E293B;
            --surface-alt: #334155;
            --text-primary: #F1F5F9;
            --text-secondary: #CBD5E1;
            --text-muted: #94A3B8;
            --border: #334155;
            --border-selected: #6366F1;
            --shadow: rgba(0, 0, 0, 0.3);
            --shadow-selected: rgba(99, 102, 241, 0.3);
            --card-bg: #1E293B;
            --card-bg-selected: #312E81;
            --header-bg: #312E81;
            --header-text: #F1F5F9;
            --skill-tag-bg: #334155;
            --skill-tag-text: #CBD5E1;
            --progress-bg: #334155;
        }
    }
    
    /* Força tema escuro quando detectado via Streamlit */
    .stApp[data-theme="dark"] {
        --background: #0F172A !important;
        --surface: #1E293B !important;
        --surface-alt: #334155 !important;
        --text-primary: #F1F5F9 !important;
        --text-secondary: #CBD5E1 !important;
        --text-muted: #94A3B8 !important;
        --border: #334155 !important;
        --border-selected: #6366F1 !important;
        --shadow: rgba(0, 0, 0, 0.3) !important;
        --shadow-selected: rgba(99, 102, 241, 0.3) !important;
        --card-bg: #1E293B !important;
        --card-bg-selected: #312E81 !important;
        --header-bg: #312E81 !important;
        --header-text: #F1F5F9 !important;
        --skill-tag-bg: #334155 !important;
        --skill-tag-text: #CBD5E1 !important;
        --progress-bg: #334155 !important;
    }
    
    /* Estilos globais usando variáveis CSS */
    .main {
        background-color: var(--background);
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
    }
    
    p, div, span {
        color: var(--text-secondary) !important;
    }
    
    /* Links personalizados */
    a {
        color: var(--link-color) !important;
    }
    
    a:hover {
        color: var(--link-hover) !important;
    }
    
    /* Elementos interativos - texto em hover e estados ativos */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: var(--link-color) !important;
        border-bottom-color: var(--link-color) !important;
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] div {
        border-bottom: 2px solid var(--link-color) !important;
    }
    
    .stTabs [data-baseweb="tab-list"] button:hover {
        color: var(--link-color) !important;
    }
    
    .stTabs [data-baseweb="tab-list"] button {
        color: var(--text-secondary) !important;
    }
    
    .stExpander summary:hover {
        color: var(--link-color) !important;
    }
    
    .stSelectbox label {
        color: var(--link-color) !important;
    }
    
    .stButton > button {
        color: var(--link-color) !important;
        border-color: var(--link-color) !important;
        background-color: var(--surface) !important;
    }
    
    .stButton > button:hover {
        color: var(--header-text) !important;
        background-color: var(--link-color) !important;
    }
    
    .stDownloadButton > button {
        color: var(--link-color) !important;
        border-color: var(--link-color) !important;
        background-color: var(--surface) !important;
    }
    
    .stDownloadButton > button:hover {
        color: var(--header-text) !important;
        background-color: var(--link-color) !important;
    }
    
    /* Status e progress */
    .stProgress > div > div {
        background-color: var(--link-color) !important;
    }
    
    .stStatus {
        color: var(--link-color) !important;
    }
    
    /* Containers e surfaces */
    .stContainer {
        background-color: var(--surface) !important;
    }
    
    /* Info, success, warning elements */
    .stInfo {
        border-left-color: var(--link-color) !important;
        background-color: var(--surface) !important;
    }
    
    .stSuccess {
        border-left-color: var(--secondary) !important;
        background-color: var(--surface) !important;
    }
    
    .stWarning {
        background-color: var(--surface) !important;
    }
    
    .stError {
        background-color: var(--surface) !important;
    }
    
    /* Dataframes */
    .stDataFrame {
        background-color: var(--surface) !important;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: var(--surface) !important;
        color: var(--text-primary) !important;
    }
    
    .streamlit-expanderContent {
        background-color: var(--surface) !important;
    }
    
    /* Header customizado */
    .header {
        background: linear-gradient(135deg, var(--header-bg) 0%, var(--primary-light) 100%);
        padding: 1.5rem;
        color: var(--header-text);
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px var(--shadow);
    }
    
    .header h1 {
        color: var(--header-text) !important;
        margin-bottom: 0.5rem;
    }
    
    .header p {
        color: var(--header-text) !important;
        margin: 0;
        font-size: 1.25rem;
        opacity: 0.9;
    }
    
    /* Cards */
    .card {
        background-color: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 0.5rem;
        padding: 1.5rem;
        box-shadow: 0 2px 8px var(--shadow);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .card:hover {
        box-shadow: 0 4px 16px var(--shadow);
    }
    
    /* Skills tags */
    .skill-tag {
        background-color: var(--skill-tag-bg);
        color: var(--skill-tag-text);
        border-radius: 9999px;
        padding: 0.25rem 0.75rem;
        font-size: 0.75rem;
        display: inline-block;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        border: 1px solid var(--border);
    }
    
    /* Círculo de ranking */
.rank-circle {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
    color: #FFFFFF !important;
    display: flex;
    justify-content: center;
    align-items: center;
    font-weight: 600;
    box-shadow: 0 2px 8px var(--shadow);
    }

    /* Forçar cor branca especificamente nos números dos círculos */
    div[style*="linear-gradient(135deg, #4F46E5"] {
        color: #FFFFFF !important;
    }

    div[style*="linear-gradient(135deg, var(--primary)"] {
        color: #FFFFFF !important;
    }

    /* Sobrescrever text-secondary apenas nos círculos */
    div[style*="border-radius: 50%"][style*="background: linear-gradient"] {
        color: #FFFFFF !important;
    }
    
    /* Barra de progresso personalizada */
    .custom-progress {
        width: 100%;
        background-color: var(--progress-bg);
        border-radius: 4px;
        height: 8px;
        overflow: hidden;
    }
    
    .custom-progress-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%);
        border-radius: 4px;
        transition: width 0.3s ease;
    }
    
    /* Esconder elementos específicos */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Ajustes específicos para selectbox */
    .stSelectbox > div > div {
        background-color: var(--surface) !important;
        color: var(--text-primary) !important;
    }
    
    /* Melhorias para contraste em modo escuro */
    @media (prefers-color-scheme: dark) {
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
            color: var(--text-primary) !important;
        }
        
        .stMarkdown p, .stMarkdown div {
            color: var(--text-secondary) !important;
        }
    }
</style>
"""

# Cabeçalho personalizado
def render_header():
    st.markdown("""
    <div class="header">
        <h1 style="margin-bottom: 0.5rem;">Decision Recruiter</h1>
        <p style="margin: 0; font-size: 1.25rem;">Sistema de Recomendação de Candidatos</p>
    </div>
    """, unsafe_allow_html=True)

# Função para renderizar uma tag de habilidade
def render_skill_tag(skill):
    return f'<span class="skill-tag">{skill}</span>'

# Função para capitalizar primeira letra de cada palavra
def capitalize_words(text):
    """Capitaliza a primeira letra de cada palavra"""
    if not text or text == 'N/A':
        return text
    return ' '.join(word.capitalize() for word in str(text).split())

# Função para limpar texto removendo palavras duplicadas
def clean_duplicated_words(text):
    """Remove palavras duplicadas mantendo a ordem"""
    if not text or text == 'N/A':
        return text
    
    # Dividir em palavras e remover duplicatas mantendo ordem
    words = str(text).split()
    seen = set()
    unique_words = []
    
    for word in words:
        word_lower = word.lower()
        if word_lower not in seen:
            seen.add(word_lower)
            unique_words.append(word)
    
    return ' '.join(unique_words)

# Função para unir conhecimentos técnicos removendo duplicatas
def merge_technical_knowledge(conhecimentos_tecnicos, conhecimentos_extraidos):
    """Une os conhecimentos técnicos removendo duplicatas e mantendo ordem"""
    # Limpar os dados
    conhecimentos_list = []
    
    # Processar conhecimentos principais
    if conhecimentos_tecnicos and conhecimentos_tecnicos.strip() and conhecimentos_tecnicos != "N/A":
        # Dividir por vírgulas ou quebras de linha
        conhecimentos_principais = re.split(r'[,\n;]', conhecimentos_tecnicos)
        conhecimentos_list.extend([k.strip() for k in conhecimentos_principais if k.strip()])
    
    # Processar conhecimentos extraídos
    if conhecimentos_extraidos and conhecimentos_extraidos.strip() and conhecimentos_extraidos != "N/A":
        conhecimentos_extra = re.split(r'[,\n;]', conhecimentos_extraidos)
        conhecimentos_list.extend([k.strip() for k in conhecimentos_extra if k.strip()])
    
    # Remover duplicatas mantendo a ordem (case insensitive)
    seen = set()
    unique_conhecimentos = []
    
    for conhecimento in conhecimentos_list:
        conhecimento_lower = conhecimento.lower()
        if conhecimento_lower not in seen and len(conhecimento) > 2:
            seen.add(conhecimento_lower)
            unique_conhecimentos.append(conhecimento)
    
    if unique_conhecimentos:
        return ', '.join(unique_conhecimentos)
    else:
        return "N/A"

@st.cache_data
def download_and_load_data():
    """Baixa e carrega os dados do arquivo pickle do Google Drive."""
    # Caminho para salvar o arquivo baixado
    output_path = 'decision_embeddings_enhanced.pkl'
    
    # Verifica se o arquivo já existe localmente
    if not os.path.exists(output_path):
        with st.status("Baixando dados do Google Drive..."):
            # ID do arquivo no Google Drive
            file_id = '1172CYnyderbEHOzdfjXJ1dWfglKvzW-e'
            
            # URL para download direto
            url = f'https://drive.google.com/uc?id={file_id}'
            
            # Baixar o arquivo
            gdown.download(url, output_path, quiet=False)
            st.success("Arquivo baixado com sucesso!")
    
    # Carregar o arquivo
    with open(output_path, 'rb') as f:
        data = pickle.load(f)
    
    return data

def compare_academic_levels(job_level, applicant_level):
    """
    Compara níveis acadêmicos, retornando 1.0 se o candidato atende ou supera o requisito.
    """
    # Ordem de níveis acadêmicos (do menor para o maior)
    academic_hierarchy = {
        "ensino fundamental": 1,
        "ensino médio": 2,
        "ensino técnico": 3,
        "ensino superior incompleto": 4,
        "ensino superior completo": 5,
        "mba": 6,
        "especialização": 6,
        "mba/especialização": 6,
        "mestrado": 7,
        "doutorado": 8,
        "pós-doutorado": 9
    }
    
    # Normalizar textos para comparação
    job_level = job_level.lower()
    applicant_level = applicant_level.lower()
    
    # Buscar o nível na hierarquia
    job_rank = 0
    applicant_rank = 0
    
    for level, rank in academic_hierarchy.items():
        if level in job_level:
            job_rank = max(job_rank, rank)
        if level in applicant_level:
            applicant_rank = max(applicant_rank, rank)
    
    # Se não foi encontrado na hierarquia
    if job_rank == 0 or applicant_rank == 0:
        return 0.5  # Valor neutro para quando não conseguimos determinar
    
    # Se o candidato possui nível maior ou igual ao requisitado
    if applicant_rank >= job_rank:
        return 1.0
    else:
        # Calcular uma pontuação proporcional
        return max(0.2, applicant_rank / job_rank)

def calculate_similarity(job_id, applicant_id, job_embeddings, applicant_embeddings, match_details, processed_jobs, processed_applicants):
    job_emb = job_embeddings[job_id]
    applicant_emb = applicant_embeddings[applicant_id]
    
    # Calcular similaridade de cosseno
    cos_sim = util.cos_sim(job_emb, applicant_emb).item()
    
    # Obter detalhes de match se disponíveis
    details = match_details.get(job_id, {}).get(applicant_id, {})
    details['semantic'] = cos_sim
    
    # Verificar se precisamos recalcular o score acadêmico
    if 'academic_level' in details and processed_jobs[job_id].get('nivel_academico') and processed_applicants[applicant_id].get('nivel_academico'):
        details['academic_level'] = compare_academic_levels(
            processed_jobs[job_id].get('nivel_academico', ''),
            processed_applicants[applicant_id].get('nivel_academico', '')
        )
    
    # Calcular score ponderado
    weighted_score = (
        cos_sim * 0.40 +  # Semântica
        details.get('keywords', 0) * 0.30 +  # Palavras-chave técnicas
        details.get('location', 0) * 0.05 +  # Localização
        details.get('professional_level', 0) * 0.10 +  # Nível profissional
        details.get('academic_level', 0) * 0.10 +  # Nível acadêmico
        details.get('english_level', 0) * 0.025 +  # Nível de inglês
        details.get('spanish_level', 0) * 0.025  # Nível de espanhol
    )
    
    # Retornar similaridade e detalhes
    return {
        'score': weighted_score,
        'details': details
    }

def get_theme_colors():
    """Retorna cores adaptadas ao tema atual"""
    # Cores padrão que funcionam bem em ambos os temas
    return {
        'primary': '#4F46E5',
        'primary_light': '#6366F1',
        'secondary': '#10B981',
        'success': '#059669',
        'warning': '#D97706',
        'error': '#DC2626',
        'info': '#0EA5E9'
    }

def render_radar_chart(match_details):
    """Renderiza o gráfico de radar para os scores de match com tema adaptativo"""
    categories = [
        'Semântica', 'Palavras-chave', 'Localização', 
        'Nível Prof.', 'Nível Acad.', 
        'Inglês', 'Espanhol'
    ]
    
    values = [
        match_details.get('semantic', 0),
        match_details.get('keywords', 0),
        match_details.get('location', 0),
        match_details.get('professional_level', 0),
        match_details.get('academic_level', 0),
        match_details.get('english_level', 0),
        match_details.get('spanish_level', 0)
    ]
    
    # Normalizar valores para 0-100
    values = [val * 100 for val in values]
    
    colors = get_theme_colors()
    
    # Criar figura do radar
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Match Score',
        marker=dict(color=colors['primary']),
        line=dict(color=colors['primary']),
        fillcolor=f"rgba(79, 70, 229, 0.3)"
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=12),
                gridcolor='rgba(128, 128, 128, 0.3)'
            ),
            angularaxis=dict(
                tickfont=dict(size=12),
                gridcolor='rgba(128, 128, 128, 0.3)'
            ),
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=60, b=40),
        height=350,
        showlegend=False,
        title=dict(
            text="Análise de Compatibilidade",
            x=0.5,
            xanchor='center',
            font=dict(size=16)
        )
    )
    
    return fig

def create_cv_download_link(cv_text, candidate_name, candidate_id):
    """Cria um link de download para o currículo do candidato"""
    if not cv_text or cv_text.strip() == "":
        return None
    
    # Preparar o texto do CV para download
    cv_content = f"CURRÍCULO - {candidate_name}\nID: {candidate_id}\n\n"
    cv_content += "=" * 50 + "\n\n"
    cv_content += cv_text
    
    # Converter para bytes
    cv_bytes = cv_content.encode('utf-8')
    
    # Criar nome do arquivo
    filename = f"CV_{candidate_name.replace(' ', '_')}_{candidate_id}.txt"
    
    return cv_bytes, filename

def render_candidate_details(candidate, selected_job):
    """Renderiza os detalhes do candidato selecionado"""
    applicant_data = candidate['applicant_data']
    match_details = candidate['match_details']
    
    # Criar tabs para diferentes visualizações
    tab1, tab2, tab3 = st.tabs(["Perfil", "Currículo", "Compatibilidade"])
    
    with tab1:
        # Layout de três colunas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("##### Informações")
            st.markdown(f"**Email:** {applicant_data.get('email', 'N/A')}")
            st.markdown(f"**Telefone:** {applicant_data.get('telefone', 'N/A')}")
            candidate_location = clean_duplicated_words(applicant_data.get('localizacao', 'N/A'))
            st.markdown(f"**Localização:** {capitalize_words(candidate_location)}")
            st.markdown(f"**Data de Cadastro:** {applicant_data.get('infos_basicas', {}).get('data_criacao', 'N/A')}")
        
        with col2:
            st.markdown("##### Qualificações")
            st.markdown(f"**Nível Profissional:** {capitalize_words(applicant_data.get('nivel_profissional', 'N/A'))}")
            st.markdown(f"**Nível Acadêmico:** {capitalize_words(applicant_data.get('nivel_academico', 'N/A'))}")
            st.markdown(f"**Inglês:** {capitalize_words(applicant_data.get('nivel_ingles', 'N/A'))}")
            st.markdown(f"**Espanhol:** {capitalize_words(applicant_data.get('nivel_espanhol', 'N/A'))}")
        
        with col3:
            st.markdown("##### Conhecimentos Técnicos")
            conhecimentos_unificados = merge_technical_knowledge(
                applicant_data.get('conhecimentos_tecnicos', ''),
                applicant_data.get('conhecimentos_tecnicos_extraidos', '')
            )
            st.markdown(f"{conhecimentos_unificados}")
        
        # Radar chart e explicação de match
        st.markdown("#### Análise de Compatibilidade")
        
        # Primeiro: Radar chart em coluna única (sem título duplicado)
        radar_fig = render_radar_chart(match_details)
        st.plotly_chart(radar_fig, use_container_width=True)
        
        # Segundo: Match com a vaga abaixo do radar
        st.markdown("##### Match com a Vaga")
        
        if match_details.get('semantic', 0) > 0.6:
            st.markdown("✅ **Alto score semântico:** O perfil do candidato tem boa correspondência geral com os requisitos da vaga.")
        
        if match_details.get('keywords', 0) > 0.5:
            job_keywords = set(selected_job.get('keywords', []))
            candidate_keywords = set(applicant_data.get('keywords', []))
            matching_keywords = job_keywords.intersection(candidate_keywords)
            
            if matching_keywords:
                st.markdown(f"✅ **Habilidades técnicas compatíveis:** O candidato possui {len(matching_keywords)} das {len(job_keywords)} habilidades requeridas:")
                st.markdown(", ".join([f"`{kw}`" for kw in matching_keywords]))
        
        if match_details.get('location', 0) > 0.7:
            st.markdown("✅ **Localização compatível:** O candidato está na mesma cidade ou estado da vaga.")
        
        if match_details.get('professional_level', 0) > 0.8:
            st.markdown("✅ **Nível profissional adequado:** O candidato possui o nível de experiência requerido para a vaga.")
        
        if match_details.get('academic_level', 0) > 0.8:
            st.markdown("✅ **Formação acadêmica adequada:** O candidato possui a formação acadêmica compatível com a vaga.")
        
        if match_details.get('english_level', 0) > 0.8:
            st.markdown("✅ **Nível de inglês adequado:** O candidato possui o nível de inglês requerido.")
        
        if match_details.get('spanish_level', 0) > 0.8:
            st.markdown("✅ **Nível de espanhol adequado:** O candidato possui o nível de espanhol requerido.")
    
    with tab2:
        cv_text = applicant_data.get('cv', '')
        
        if cv_text and cv_text.strip():
            st.markdown("#### Preview do Currículo")
            preview_text = cv_text[:500] + "..." if len(cv_text) > 500 else cv_text
            
            if isinstance(selected_job.get('keywords', []), list) and selected_job.get('keywords'):
                for keyword in selected_job.get('keywords', []):
                    try:
                        pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
                        preview_text = pattern.sub(f"**{keyword.upper()}**", preview_text)
                    except:
                        continue
            
            if selected_job.get('keywords'):
                st.info("💡 As palavras-chave relevantes para a vaga estão destacadas em **NEGRITO** no preview.")
            
            with st.container(border=True):
                st.markdown(preview_text)
                if len(cv_text) > 500:
                    st.markdown("*...continue lendo no arquivo baixado*")
            
            cv_download_data = create_cv_download_link(
                cv_text, 
                candidate['nome'], 
                candidate['id']
            )
            
            if cv_download_data:
                cv_bytes, filename = cv_download_data
                
                st.download_button(
                    label="⬇️ Baixar Currículo Completo",
                    data=cv_bytes,
                    file_name=filename,
                    mime="text/plain",
                    help="Clique para baixar o currículo completo como arquivo de texto"
                )
        else:
            st.warning("⚠️ Currículo não disponível para este candidato.")
    
    with tab3:
        st.markdown("#### Score de Compatibilidade Detalhado")
        
        data = {
            'Categoria': ['Semântica', 'Palavras-chave', 'Localização', 'Nível Profissional', 
                         'Nível Acadêmico', 'Inglês', 'Espanhol', 'Score Total'],
            'Score (%)': [
                match_details.get('semantic', 0) * 100,
                match_details.get('keywords', 0) * 100,
                match_details.get('location', 0) * 100,
                match_details.get('professional_level', 0) * 100,
                match_details.get('academic_level', 0) * 100,
                match_details.get('english_level', 0) * 100,
                match_details.get('spanish_level', 0) * 100,
                candidate['score'] * 100
            ],
            'Peso': [40, 30, 5, 10, 10, 2.5, 2.5, 100]
        }
        
        df = pd.DataFrame(data)
        colors = get_theme_colors()
        
        fig = px.bar(
            df, 
            y='Categoria', 
            x='Score (%)', 
            orientation='h',
            color='Score (%)',
            color_continuous_scale=[
                [0, 'rgba(156, 163, 175, 0.3)'],
                [0.33, colors['info']],
                [0.66, colors['primary']],
                [1, colors['success']]
            ],
            labels={'Score (%)': 'Porcentagem de Match'},
            range_color=[0, 100],
            height=400
        )
        
        fig.update_layout(
            yaxis={'categoryorder': 'array', 'categoryarray': list(reversed(df['Categoria']))},
            margin=dict(l=40, r=40, t=60, b=40),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            title=dict(
                text="Score de Compatibilidade por Categoria",
                x=0.5,
                xanchor='center',
                font=dict(size=16)
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Separador
        st.markdown("---")
        
        # Explicação do Score (movida da aba Perfil)
        st.markdown("#### Explicação do Score")
        
        with st.container(border=True):
            st.markdown("""
            O score total é calculado como uma média ponderada dos seguintes componentes:
            - **🧠 Semântica (40%)**: Similaridade geral entre o perfil do candidato e a vaga.
            - **💻 Palavras-chave técnicas (30%)**: Match entre as habilidades técnicas requeridas e as do candidato.
            - **📍 Localização (5%)**: Compatibilidade geográfica (peso reduzido para vagas remotas/híbridas).
            - **💼 Nível Profissional (10%)**: Adequação do nível de experiência.
            - **🎓 Nível Acadêmico (10%)**: Adequação da formação acadêmica.
            - **🇺🇸 Inglês (2.5%)**: Compatibilidade do nível de inglês.
            - **🇪🇸 Espanhol (2.5%)**: Compatibilidade do nível de espanhol.
            """)

def render_job_details(job):
    """Renderiza os detalhes da vaga selecionada"""
    with st.expander("Detalhes da Vaga", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### {capitalize_words(job.get('titulo', 'N/A'))}")
            st.markdown(f"**Cliente:** {capitalize_words(job.get('cliente', 'N/A'))}")
            st.markdown(f"**Empresa/Divisão:** {capitalize_words(job.get('empresa', 'N/A'))}")
            st.markdown(f"**Tipo de Contratação:** {capitalize_words(job.get('tipo_contratacao', 'N/A'))}")
            
            if job.get('beneficios'):
                st.markdown(f"**Benefícios:** {job.get('beneficios', 'N/A')}")
        
        with col2:
            st.markdown("#### Requisitos")
            localizacao_limpa = clean_duplicated_words(job.get('localizacao', 'N/A'))
            st.markdown(f"**Localização:** {capitalize_words(localizacao_limpa)}")
            st.markdown(f"**Nível Profissional:** {capitalize_words(job.get('nivel_profissional', 'N/A'))}")
            st.markdown(f"**Nível Acadêmico:** {capitalize_words(job.get('nivel_academico', 'N/A'))}")
            st.markdown(f"**Idiomas:** Inglês: {capitalize_words(job.get('nivel_ingles', 'N/A'))}, Espanhol: {capitalize_words(job.get('nivel_espanhol', 'N/A'))}")
            
            if job.get('modelo_trabalho'):
                st.markdown(f"**Modelo de Trabalho:** {capitalize_words(job.get('modelo_trabalho', 'N/A'))}")
            elif job.get('remoto') or job.get('hibrido') or job.get('presencial'):
                modelo = []
                if job.get('remoto') and str(job.get('remoto')).lower() in ['sim', 'true', '1']:
                    modelo.append('Remoto')
                if job.get('hibrido') and str(job.get('hibrido')).lower() in ['sim', 'true', '1']:
                    modelo.append('Híbrido')
                if job.get('presencial') and str(job.get('presencial')).lower() in ['sim', 'true', '1']:
                    modelo.append('Presencial')
                
                if modelo:
                    st.markdown(f"** Modelo de Trabalho:** {' / '.join(modelo)}")
        
        st.markdown("---")
        
        st.markdown("#### Habilidades e Tecnologias Requeridas")
        
        if job.get('keywords'):
            keywords_html = ' '.join([render_skill_tag(kw) for kw in job.get('keywords', [])])
            st.markdown(f"<div style='margin-bottom: 1rem;'>{keywords_html}</div>", unsafe_allow_html=True)
        
        if job.get('areas_atuacao'):
            st.markdown(f"**Áreas de Atuação:** {capitalize_words(job.get('areas_atuacao', 'N/A'))}")
        
        with st.container(border=True):
            st.markdown("#### Descrição Completa da Vaga")
            
            if job.get('principais_atividades'):
                st.markdown("##### Principais Atividades")
                st.markdown(job.get('principais_atividades', 'N/A'))
            
            if job.get('competencias'):
                st.markdown("##### Competências Técnicas e Comportamentais")
                st.markdown(job.get('competencias', 'N/A'))

def render_comparison_view(similarities, selected_job, top_n=5):
    """Renderiza uma visualização de comparação entre os candidatos"""
    
    top_candidates = similarities[:top_n]
    
    tab1, tab2 = st.tabs(["Gráfico Comparativo", "Tabela Detalhada"])
    
    with tab1:
        st.markdown("### Comparativo Top 5 Candidatos")
        
        # Radar Chart - Coluna única completa (sem título duplicado)
        categories = [
            'Semântica', 'Palavras-chave', 'Localização', 
            'Nível Prof.', 'Nível Acad.', 
            'Inglês', 'Espanhol'
        ]
        
        fig_radar = go.Figure()
        
        colors_list = ['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
        
        for i, candidate in enumerate(top_candidates):
            match_details = candidate['match_details']
            
            values = [
                match_details.get('semantic', 0) * 100,
                match_details.get('keywords', 0) * 100,
                match_details.get('location', 0) * 100,
                match_details.get('professional_level', 0) * 100,
                match_details.get('academic_level', 0) * 100,
                match_details.get('english_level', 0) * 100,
                match_details.get('spanish_level', 0) * 100
            ]
            
            color = colors_list[i % len(colors_list)]
            
            fig_radar.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=f"{i+1}º - {candidate['nome'][:20]}{'...' if len(candidate['nome']) > 20 else ''}",
                line=dict(color=color),
                fillcolor=f"rgba{tuple(list(bytes.fromhex(color[1:])) + [0.1])}"
            ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(size=14),
                    gridcolor='rgba(128, 128, 128, 0.3)'
                ),
                angularaxis=dict(
                    tickfont=dict(size=14),
                    gridcolor='rgba(128, 128, 128, 0.3)'
                ),
                bgcolor='rgba(0,0,0,0)'
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=60, r=60, t=80, b=60),
            height=600,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.25,
                xanchor="center",
                x=0.5,
                font=dict(size=14)
            ),
            title=dict(
                text="Comparação Multi-dimensional dos Candidatos",
                x=0.5,
                xanchor='center',
                font=dict(size=18)
            )
        )
        
        st.plotly_chart(fig_radar, use_container_width=True)
        
        # Separador
        st.markdown("---")
        
        # Gráfico de Barras - Coluna única completa (sem título duplicado)
        bar_data = []
        candidate_names = []
        
        for i, candidate in enumerate(top_candidates):
            match_details = candidate['match_details']
            candidate_names.append(f"{i+1}º - {candidate['nome'][:20]}{'...' if len(candidate['nome']) > 20 else ''}")
            
            bar_data.append({
                'Candidato': f"{i+1}º",
                'Score Total': candidate['score'] * 100,
                'Semântica': match_details.get('semantic', 0) * 100,
                'Palavras-chave': match_details.get('keywords', 0) * 100,
                'Nível Prof.': match_details.get('professional_level', 0) * 100,
                'Nível Acad.': match_details.get('academic_level', 0) * 100
            })
        
        df_bars = pd.DataFrame(bar_data)
        
        fig_bar = go.Figure()
        
        metrics_colors = {
            'Score Total': '#1F2937',
            'Semântica': '#4F46E5',
            'Palavras-chave': '#10B981',
            'Nível Prof.': '#F59E0B',
            'Nível Acad.': '#EF4444'
        }
        
        for metric in ['Score Total', 'Semântica', 'Palavras-chave', 'Nível Prof.', 'Nível Acad.']:
            fig_bar.add_trace(go.Bar(
                name=metric,
                x=candidate_names,
                y=df_bars[metric],
                marker_color=metrics_colors[metric],
                text=[f"{val:.1f}%" for val in df_bars[metric]],
                textposition='auto',
            ))
        
        fig_bar.update_layout(
            barmode='group',
            height=600,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=60, r=60, t=80, b=100),
            yaxis=dict(
                title="Score (%)",
                range=[0, 100],
                title_font=dict(size=16)
            ),
            xaxis=dict(
                title="Candidatos",
                tickangle=45,
                title_font=dict(size=16)
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.35,
                xanchor="center",
                x=0.5,
                font=dict(size=14)
            ),
            showlegend=True,
            title=dict(
                text="Comparação de Scores por Categoria",
                x=0.5,
                xanchor='center',
                font=dict(size=18)
            )
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Separador
        st.markdown("---")
    
    with tab2:
        st.markdown("### Relatório Detalhado dos Candidatos")
        
        total_candidates = len(similarities)
        best_candidate = top_candidates[0] if top_candidates else None
        avg_score = sum(c['score'] for c in top_candidates) / len(top_candidates) if top_candidates else 0
        hired_count = sum(1 for c in top_candidates if c['is_hired'])
        
        best_technical = max(top_candidates, key=lambda x: x['match_details'].get('keywords', 0)) if top_candidates else None
        
        st.markdown("#### Resumo Executivo")
        
        with st.container(border=True):
            st.markdown(f"""
            **Análise dos {len(top_candidates)} principais candidatos:**
            
            • **🏆 Melhor candidato:** {best_candidate['nome'] if best_candidate else 'N/A'} com {best_candidate['score'] * 100:.1f}% de compatibilidade
            
            • **📈 Score médio:** {avg_score * 100:.1f}%
            
            • **✅ Candidatos já contratados:** {hired_count} de {len(top_candidates)}
            
            • **💻 Melhor match técnico:** {best_technical['nome'] if best_technical else 'N/A'} ({best_technical['match_details'].get('keywords', 0) * 100:.0f}%)
            
            **💡 Recomendação:** {"Excelente pool de candidatos com forte alinhamento técnico." if avg_score > 0.7 else "Pool de candidatos com potencial, recomenda-se análise detalhada dos perfis."}
            """)
        
        st.markdown("---")
        
        detailed_data = []
        
        for i, candidate in enumerate(top_candidates):
            applicant_data = candidate['applicant_data']
            match_details = candidate['match_details']
            
            conhecimentos_unificados = merge_technical_knowledge(
                applicant_data.get('conhecimentos_tecnicos', ''),
                applicant_data.get('conhecimentos_tecnicos_extraidos', '')
            )
            
            job_keywords = set(selected_job.get('keywords', []))
            candidate_keywords = set(applicant_data.get('keywords', []))
            matching_keywords = job_keywords.intersection(candidate_keywords)
            
            row_data = {
                'Posição': f"{i+1}º",
                'Nome': candidate['nome'],
                'Email': applicant_data.get('email', 'N/A'),
                'Telefone': applicant_data.get('telefone', 'N/A'),
                'Localização': capitalize_words(clean_duplicated_words(applicant_data.get('localizacao', 'N/A'))),
                'Nível Profissional': capitalize_words(applicant_data.get('nivel_profissional', 'N/A')),
                'Nível Acadêmico': capitalize_words(applicant_data.get('nivel_academico', 'N/A')),
                'Inglês': capitalize_words(applicant_data.get('nivel_ingles', 'N/A')),
                'Espanhol': capitalize_words(applicant_data.get('nivel_espanhol', 'N/A')),
                'Score Total (%)': f"{candidate['score'] * 100:.1f}%",
                'Score Semântico (%)': f"{match_details.get('semantic', 0) * 100:.1f}%",
                'Score Palavras-chave (%)': f"{match_details.get('keywords', 0) * 100:.1f}%",
                'Score Localização (%)': f"{match_details.get('location', 0) * 100:.1f}%",
                'Score Nível Prof. (%)': f"{match_details.get('professional_level', 0) * 100:.1f}%",
                'Score Nível Acad. (%)': f"{match_details.get('academic_level', 0) * 100:.1f}%",
                'Score Inglês (%)': f"{match_details.get('english_level', 0) * 100:.1f}%",
                'Score Espanhol (%)': f"{match_details.get('spanish_level', 0) * 100:.1f}%",
                'Conhecimentos Técnicos': conhecimentos_unificados,
                'Keywords Compatíveis': ', '.join(matching_keywords) if matching_keywords else 'Nenhuma',
                'Qtd Keywords Compatíveis': len(matching_keywords),
                'Total Keywords Vaga': len(job_keywords),
                'Contratado': 'Sim' if candidate['is_hired'] else 'Não',
                'ID Candidato': candidate['id']
            }
            
            detailed_data.append(row_data)
        
        df_detailed = pd.DataFrame(detailed_data)
        
        st.dataframe(
            df_detailed, 
            height=300, 
            use_container_width=True,
            column_config={
                "Posição": st.column_config.TextColumn(
                    "Posição",
                    width="small",
                    pinned="left"
                )
            },
            hide_index=True
        )
        
        vaga_info = f"Vaga: {capitalize_words(selected_job.get('titulo', 'N/A'))} - {capitalize_words(selected_job.get('cliente', 'N/A'))}"
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv_buffer = io.StringIO()
            
            csv_buffer.write("RELATÓRIO DE CANDIDATOS RECOMENDADOS\n")
            csv_buffer.write(f"Vaga;{capitalize_words(selected_job.get('titulo', 'N/A'))}\n")
            csv_buffer.write(f"Cliente;{capitalize_words(selected_job.get('cliente', 'N/A'))}\n")
            csv_buffer.write(f"Empresa;{capitalize_words(selected_job.get('empresa', 'N/A'))}\n")
            csv_buffer.write(f"Localização;{capitalize_words(clean_duplicated_words(selected_job.get('localizacao', 'N/A')))}\n")
            csv_buffer.write(f"Data do Relatório;{pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}\n")
            csv_buffer.write(f"Melhor Candidato;{best_candidate['nome'] if best_candidate else 'N/A'}\n")
            csv_buffer.write(f"Score Médio;{avg_score * 100:.1f}%\n")
            csv_buffer.write(f"Candidatos Contratados;{hired_count} de {len(top_candidates)}\n")
            csv_buffer.write("\n")
            csv_buffer.write("CANDIDATOS RECOMENDADOS\n")
            
            df_detailed.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8')
            
            csv_content = csv_buffer.getvalue()
            csv_buffer.close()
            
            st.download_button(
                label="📥 Baixar Relatório Completo (CSV)",
                data=csv_content.encode('utf-8'),
                file_name=f"relatorio_candidatos_{timestamp}.csv",
                mime="text/csv",
                help="Baixar relatório completo com resumo executivo e dados dos candidatos"
            )
        
        with col2:
            try:
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    resumo_data = [
                        ['RELATÓRIO DE CANDIDATOS RECOMENDADOS', ''],
                        ['Vaga', capitalize_words(selected_job.get('titulo', 'N/A'))],
                        ['Cliente', capitalize_words(selected_job.get('cliente', 'N/A'))],
                        ['Empresa', capitalize_words(selected_job.get('empresa', 'N/A'))],
                        ['Localização', capitalize_words(clean_duplicated_words(selected_job.get('localizacao', 'N/A')))],
                        ['Data do Relatório', pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")],
                        ['', ''],
                        ['RESUMO EXECUTIVO', ''],
                        ['Melhor Candidato', f"{best_candidate['nome'] if best_candidate else 'N/A'} ({best_candidate['score'] * 100:.1f}%)" if best_candidate else 'N/A'],
                        ['Score Médio', f"{avg_score * 100:.1f}%"],
                        ['Candidatos já Contratados', f"{hired_count} de {len(top_candidates)}"],
                        ['Melhor Match Técnico', f"{best_technical['nome'] if best_technical else 'N/A'} ({best_technical['match_details'].get('keywords', 0) * 100:.0f}%)" if best_technical else 'N/A'],
                        ['', ''],
                        ['CANDIDATOS RECOMENDADOS', '']
                    ]
                    
                    resumo_df = pd.DataFrame(resumo_data, columns=['Campo', 'Valor'])
                    
                    resumo_df.to_excel(writer, sheet_name='Relatório Completo', index=False, startrow=0)
                    
                    df_detailed.to_excel(writer, sheet_name='Relatório Completo', index=False, startrow=len(resumo_data) + 2)
                
                excel_content = excel_buffer.getvalue()
                excel_buffer.close()
                
                st.download_button(
                    label="📊 Baixar Relatório (Excel)",
                    data=excel_content,
                    file_name=f"relatorio_candidatos_{timestamp}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Baixar relatório completo em Excel - tudo em uma única aba"
                )
            except:
                st.button(
                    "📊 Excel (Indisponível)",
                    disabled=True,
                    help="Excel não disponível - instale openpyxl se necessário"
                )
        
        st.info("""
        💡 **Sobre o Relatório:**
        - Contém resumo executivo com análise dos candidatos
        - Inclui todos os scores detalhados e informações de contato
        - Excel gerado em aba única para facilitar visualização
        - Ideal para compartilhar com equipes de RH e gestores
        """)

def main():
    # Aplicar CSS dinâmico
    st.markdown(get_dynamic_css(), unsafe_allow_html=True)
    
    render_header()
    
    try:
        with st.status("Carregando dados..."):
            st.info("Primeiro acesso? Pode levar até 3 minutos para baixar os dados.")
            
            data = download_and_load_data()
            
            processed_jobs = data['processed_jobs']
            processed_applicants = data['processed_applicants']
            hired_candidates = data['hired_candidates']
            job_embeddings = data['job_embeddings']
            applicant_embeddings = data['applicant_embeddings']
            match_details = data.get('match_details', {})
            
            st.success("✅ Dados carregados com sucesso!")
        
        job_options = {}
        for job_id, job in processed_jobs.items():
            title = capitalize_words(job.get('titulo', 'Sem título'))
            company = capitalize_words(job.get('cliente', 'Empresa não especificada'))
            job_options[job_id] = f"{title} - {company} (ID: {job_id})"
        
        st.markdown("## Encontre os candidatos ideais em segundos")
        
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                selected_job_id = st.selectbox(
                    "🔍 Escolha a vaga (digite para buscar):",
                    options=list(job_options.keys()),
                    format_func=lambda x: job_options[x],
                    help="Digite parte do nome da vaga ou empresa para filtrar"
                )
            
            with col2:
                if st.button("🔄 Atualizar Lista"):
                    st.rerun()
        
        if selected_job_id:
            selected_job = processed_jobs[selected_job_id]
            
            render_job_details(selected_job)
            
            cache_key = f"similarities_{selected_job_id}"
            
            if cache_key not in st.session_state:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                similarities = []
                total_applicants = len(applicant_embeddings.keys())
                
                for i, applicant_id in enumerate(applicant_embeddings.keys()):
                    progress = int((i + 1) / total_applicants * 100)
                    progress_bar.progress(progress)
                    status_text.text(f"🔄 Calculando similaridade para candidatos: {i+1}/{total_applicants}")
                    
                    similarity_data = calculate_similarity(
                        selected_job_id, 
                        applicant_id, 
                        job_embeddings, 
                        applicant_embeddings, 
                        match_details, 
                        processed_jobs, 
                        processed_applicants
                    )
                    
                    applicant = processed_applicants[applicant_id]
                    
                    is_hired = applicant['codigo'] in hired_candidates.get(selected_job_id, [])
                    
                    similarities.append({
                        'id': applicant_id,
                        'nome': applicant['nome'],
                        'score': similarity_data['score'],
                        'is_hired': is_hired,
                        'applicant_data': applicant,
                        'match_details': similarity_data['details']
                    })
                
                similarities = sorted(similarities, key=lambda x: x['score'], reverse=True)
                
                st.session_state[cache_key] = similarities
                
                progress_bar.empty()
                status_text.empty()
            else:
                similarities = st.session_state[cache_key]
            
            top_7_ids = [item['id'] for item in similarities[:7]]
            hired_ids = [candidate_id for candidate_id in top_7_ids 
                        if processed_applicants[candidate_id]['codigo'] in hired_candidates.get(selected_job_id, [])]
            
            if hired_ids:
                hit_rate = len(hired_ids) / len(hired_candidates.get(selected_job_id, []) or [1]) * 100
                st.success(f"🎯 O sistema identificou {len(hired_ids)} dos candidatos já contratados para esta vaga entre os 7 mais recomendados! (Taxa de acerto: {hit_rate:.1f}%)")
            
            st.markdown("## Candidatos Recomendados")
            st.markdown("💡 **Clique em qualquer card para ver os detalhes completos do candidato**")
            
            top_candidates = similarities[:7]
            
            session_key = f"selected_candidate_{selected_job_id}"
            if session_key not in st.session_state:
                st.session_state[session_key] = 0
            
            for i, candidate in enumerate(top_candidates):
                is_selected = i == st.session_state[session_key]
                
                with st.container():
                    card_col, select_col = st.columns([10, 1])
                    
                    with card_col:
                        border_color = "var(--border-selected)" if is_selected else "var(--border)"
                        bg_color = "var(--card-bg-selected)" if is_selected else "var(--card-bg)"
                        shadow = "var(--shadow-selected)" if is_selected else "var(--shadow)"
                        
                        html_card = f"""
                        <div style="
                            background-color: {bg_color};
                            border: 2px solid {border_color};
                            border-radius: 8px;
                            padding: 16px;
                            margin-bottom: 8px;
                            transition: all 0.2s ease;
                            box-shadow: 0 4px 12px {shadow};
                        ">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div style="display: flex; align-items: center; gap: 1rem;">
                                    <div style="
                                        width: 40px;
                                        height: 40px;
                                        border-radius: 50%;
                                        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
                                        color: #FFFFFF;
                                        display: flex;
                                        justify-content: center;
                                        align-items: center;
                                        font-weight: 600;
                                        box-shadow: 0 2px 8px var(--shadow);
                                    ">
                                        {i+1}
                                    </div>
                                    <div>
                                        <div style="font-weight: 500; font-size: 1.1rem; color: var(--text-primary);">
                                            {candidate['nome']} {' 🌟' if candidate['is_hired'] else ''}
                                        </div>
                                        <div style="color: var(--text-muted); font-size: 0.875rem;">
                                            ID: {candidate['id']}
                                        </div>
                                    </div>
                                </div>
                                <div style="text-align: right;">
                                    <div class="custom-progress" style="width: 150px; margin: 8px 0;">
                                        <div class="custom-progress-fill" style="width: {candidate['score'] * 100}%;"></div>
                                    </div>
                                    <div style="font-size: 0.875rem; font-weight: 500; color: var(--text-primary);">
                                        {candidate['score'] * 100:.1f}%
                                    </div>
                                </div>
                            </div>
                        </div>
                        """
                        
                        st.markdown(html_card, unsafe_allow_html=True)
                    
                    with select_col:
                        select_emoji = "✅" if is_selected else "☐"
                        button_help = f"Candidato selecionado: {candidate['nome']}" if is_selected else f"Clique para selecionar {candidate['nome']}"
                        
                        button_key = f"select_{selected_job_id}_{i}"
                        
                        if st.button(select_emoji, key=button_key, help=button_help):
                            st.session_state[session_key] = i
                            st.rerun()
            
            st.markdown("---")
            
            selected_candidate = top_candidates[st.session_state[session_key]]
            
            st.markdown("### Detalhes do Candidato Selecionado")
            
            st.markdown(f"""
            <div class="card" style="border: 2px solid var(--border-selected); background: linear-gradient(135deg, var(--card-bg-selected) 0%, var(--card-bg) 100%);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div class="rank-circle" style="width: 50px; height: 50px; font-size: 1.2rem;">
                            {st.session_state[session_key] + 1}
                        </div>
                        <div>
                            <div style="font-weight: 600; font-size: 1.5rem; color: var(--text-primary);">
                                {selected_candidate['nome']} {' 🌟' if selected_candidate['is_hired'] else ''}
                            </div>
                            <div style="color: var(--text-muted); font-size: 0.875rem;">
                                ID: {selected_candidate['id']} • Candidato selecionado
                            </div>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-weight: 600; font-size: 2rem; color: var(--secondary);">
                            {selected_candidate['score'] * 100:.1f}%
                        </div>
                        <div style="color: var(--text-muted); font-size: 0.875rem; font-weight: 500;">
                            Match Score
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            render_candidate_details(selected_candidate, selected_job)
            
            st.markdown("---")
            render_comparison_view(similarities, selected_job)
                        
    except Exception as e:
        st.error(f"❌ Erro ao processar os dados: {e}")
        st.info("""
        ⚠️ Por favor, certifique-se de que você tem acesso ao arquivo no Google Drive e que todas as dependências estão instaladas.
        
        **📦 Dependências necessárias:**
        ```bash
        pip install streamlit pandas numpy plotly sentence-transformers gdown streamlit-nested-layout openpyxl
        ```
        
        **🔧 Como executar:**
        1. Salve este código em um arquivo `.py` (ex: `app.py`)
        2. Instale as dependências acima
        3. Execute: `streamlit run app.py`
        4. O tema será detectado automaticamente baseado nas configurações do seu browser/sistema
        """)

if __name__ == "__main__":
    main()