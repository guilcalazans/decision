import streamlit as st
import pickle
import pandas as pd
import numpy as np
from sentence_transformers import util
import plotly.express as px
import plotly.graph_objects as go
import math
import re
import os
from PIL import Image
import base64
import io
import streamlit_nested_layout
import requests
import json

# Importar Pinecone
try:
    from pinecone import Pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    st.error("❌ Pinecone não instalado. Execute: pip install pinecone-client")

# Configuração da página
st.set_page_config(
    page_title="Decision Recruiter - Recomendação de Candidatos",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS dinâmico (mesmo do app.py original)
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
</style>
"""

# Cabeçalho personalizado
def render_header():
    connection_type = "GitHub + Pinecone" if st.session_state.get('pinecone_available') else "GitHub Only"
    st.markdown(f"""
    <div class="header">
        <h1 style="margin-bottom: 0.5rem;">Decision Recruiter</h1>
        <p style="margin: 0; font-size: 1.25rem;">Sistema de Recomendação de Candidatos - {connection_type}</p>
    </div>
    """, unsafe_allow_html=True)

# Funções auxiliares (mesmas do app.py)
def render_skill_tag(skill):
    return f'<span class="skill-tag">{skill}</span>'

def capitalize_words(text):
    """Capitaliza a primeira letra de cada palavra"""
    if not text or text == 'N/A':
        return text
    return ' '.join(word.capitalize() for word in str(text).split())

def clean_duplicated_words(text):
    """Remove palavras duplicadas mantendo a ordem"""
    if not text or text == 'N/A':
        return text
    
    words = str(text).split()
    seen = set()
    unique_words = []
    
    for word in words:
        word_lower = word.lower()
        if word_lower not in seen:
            seen.add(word_lower)
            unique_words.append(word)
    
    return ' '.join(unique_words)

def merge_technical_knowledge(conhecimentos_tecnicos, conhecimentos_extraidos):
    """Une os conhecimentos técnicos removendo duplicatas e mantendo ordem"""
    conhecimentos_list = []
    
    if conhecimentos_tecnicos and conhecimentos_tecnicos.strip() and conhecimentos_tecnicos != "N/A":
        conhecimentos_principais = re.split(r'[,\n;]', conhecimentos_tecnicos)
        conhecimentos_list.extend([k.strip() for k in conhecimentos_principais if k.strip()])
    
    if conhecimentos_extraidos and conhecimentos_extraidos.strip() and conhecimentos_extraidos != "N/A":
        conhecimentos_extra = re.split(r'[,\n;]', conhecimentos_extraidos)
        conhecimentos_list.extend([k.strip() for k in conhecimentos_extra if k.strip()])
    
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

@st.cache_resource
def init_pinecone():
    """Inicializa conexão com Pinecone"""
    if not PINECONE_AVAILABLE:
        return None
        
    try:
        API_KEY = "pcsk_5DfEc5_JTj7W19EkqEm2awJNed9dnmdfNtKBuNv3MNzPnX9R2tJv3dRNbUEJcm9gXWNYko"
        INDEX_NAME = "decision-recruiter"
        pc = Pinecone(api_key=API_KEY)
        index = pc.Index(INDEX_NAME)
        return index
    except Exception as e:
        st.warning(f"⚠️ Pinecone não disponível: {e}")
        return None

@st.cache_data
def load_data_from_github():
    """
    OTIMIZADO: Carrega dados do GitHub de forma rápida
    Retorna dados no formato exato que o app.py espera
    """
    try:
        with st.status("📥 Carregando dados do GitHub..."):
            st.write("🔗 Conectando ao GitHub Releases...")
            
            # URLs dos arquivos individuais (mais rápido que o arquivo grande)
            urls = {
                'vagas': "https://github.com/guilcalazans/decision/releases/download/v1.0/vagas.json",
                'candidates': "https://github.com/guilcalazans/decision/releases/download/v1.0/applicants.json", 
                'prospects': "https://github.com/guilcalazans/decision/releases/download/v1.0/prospects.json"
            }
            
            data_loaded = {}
            
            for data_type, url in urls.items():
                st.write(f"📊 Carregando {data_type}...")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                data_loaded[data_type] = response.json()
            
            st.write("✅ Dados carregados!")
        
        # Processar dados no formato que o app.py espera
        with st.status("🔄 Processando dados..."):
            # 1. Processar vagas (extrair características importantes)
            processed_jobs = {}
            for job_id, job_data in data_loaded['vagas'].items():
                basic_info = job_data.get('informacoes_basicas', {})
                job_profile = job_data.get('perfil_vaga', {})
                
                processed_jobs[job_id] = {
                    'titulo': basic_info.get('titulo_vaga', ''),
                    'cliente': basic_info.get('cliente', ''),
                    'empresa': basic_info.get('empresa_divisao', ''),
                    'tipo_contratacao': basic_info.get('tipo_contratacao', ''),
                    'cidade': job_profile.get('cidade', ''),
                    'estado': job_profile.get('estado', ''),
                    'pais': job_profile.get('pais', ''),
                    'localizacao': f"{job_profile.get('cidade', '')} {job_profile.get('estado', '')} {job_profile.get('pais', '')}",
                    'nivel_profissional': job_profile.get('nivel profissional', ''),
                    'nivel_academico': job_profile.get('nivel_academico', ''),
                    'nivel_ingles': job_profile.get('nivel_ingles', ''),
                    'nivel_espanhol': job_profile.get('nivel_espanhol', ''),
                    'areas_atuacao': job_profile.get('areas_atuacao', ''),
                    'principais_atividades': job_profile.get('principais_atividades', ''),
                    'competencias': job_profile.get('competencia_tecnicas_e_comportamentais', ''),
                    'keywords': extract_keywords_from_job(job_profile)
                }
            
            # 2. Processar candidatos (extrair características importantes)
            processed_applicants = {}
            for candidate_id, candidate_data in data_loaded['candidates'].items():
                basic_info = candidate_data.get('infos_basicas', {})
                personal_info = candidate_data.get('informacoes_pessoais', {})
                prof_info = candidate_data.get('informacoes_profissionais', {})
                education = candidate_data.get('formacao_e_idiomas', {})
                
                processed_applicants[candidate_id] = {
                    'nome': basic_info.get('nome', ''),
                    'codigo': basic_info.get('codigo_profissional', ''),
                    'email': basic_info.get('email', ''),
                    'telefone': basic_info.get('telefone', ''),
                    'cidade': extract_location_from_cv(candidate_data.get('cv_pt', '')).get('cidade', ''),
                    'estado': extract_location_from_cv(candidate_data.get('cv_pt', '')).get('estado', ''),
                    'pais': 'Brasil',
                    'localizacao': f"{extract_location_from_cv(candidate_data.get('cv_pt', '')).get('cidade', '')} {extract_location_from_cv(candidate_data.get('cv_pt', '')).get('estado', '')} Brasil",
                    'nivel_profissional': prof_info.get('nivel_profissional', ''),
                    'nivel_academico': education.get('nivel_academico', ''),
                    'nivel_ingles': education.get('nivel_ingles', ''),
                    'nivel_espanhol': education.get('nivel_espanhol', ''),
                    'conhecimentos_tecnicos': prof_info.get('conhecimentos_tecnicos', ''),
                    'conhecimentos_tecnicos_extraidos': ', '.join(extract_keywords_from_cv(candidate_data.get('cv_pt', ''))),
                    'keywords': extract_keywords_from_cv(candidate_data.get('cv_pt', '')),
                    'cv': candidate_data.get('cv_pt', ''),
                    'infos_basicas': basic_info
                }
            
            # 3. Processar contratações
            hired_candidates = {}
            for job_id, prospect_data in data_loaded['prospects'].items():
                hired_candidates[job_id] = []
                for prospect in prospect_data.get('prospects', []):
                    if prospect.get('situacao_candidado') == 'Contratado pela Decision':
                        hired_candidates[job_id].append(prospect.get('codigo', ''))
        
        # Conectar ao Pinecone se disponível
        pinecone_index = init_pinecone()
        if pinecone_index:
            st.session_state['pinecone_index'] = pinecone_index
            st.session_state['pinecone_available'] = True
        else:
            st.session_state['pinecone_available'] = False
        
        # Retornar no formato exato que o app.py espera
        return {
            'processed_jobs': processed_jobs,
            'processed_applicants': processed_applicants,
            'hired_candidates': hired_candidates,
            'job_embeddings': {},  # Será populado conforme necessário
            'applicant_embeddings': {},  # Será populado conforme necessário  
            'match_details': {}  # Será calculado dinamicamente
        }
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados do GitHub: {e}")
        return None

def extract_keywords_from_job(job_profile):
    """Extrai palavras-chave técnicas da vaga"""
    keywords = []
    
    # Texto para análise
    text_fields = [
        job_profile.get('principais_atividades', ''),
        job_profile.get('competencia_tecnicas_e_comportamentais', ''),
        job_profile.get('areas_atuacao', '')
    ]
    
    combined_text = ' '.join(text_fields).lower()
    
    # Lista de tecnologias comuns
    tech_keywords = [
        "python", "java", "javascript", "js", "c#", "c++", "php", "ruby", "go", "swift",
        "html", "css", "react", "angular", "vue", "node", "django", "flask", "spring",
        "aws", "azure", "gcp", "cloud", "docker", "kubernetes", "terraform",
        "sql", "mysql", "postgresql", "mongodb", "oracle", "redis",
        "git", "jenkins", "devops", "agile", "scrum",
        "excel", "power bi", "tableau", "sap", "erp", "totvs"
    ]
    
    for keyword in tech_keywords:
        if keyword in combined_text:
            keywords.append(keyword)
    
    return keywords

def extract_keywords_from_cv(cv_text):
    """Extrai palavras-chave técnicas do CV"""
    if not cv_text:
        return []
        
    keywords = []
    cv_lower = cv_text.lower()
    
    # Lista de tecnologias comuns
    tech_keywords = [
        "python", "java", "javascript", "js", "c#", "c++", "php", "ruby", "go", "swift",
        "html", "css", "react", "angular", "vue", "node", "django", "flask", "spring",
        "aws", "azure", "gcp", "cloud", "docker", "kubernetes", "terraform",
        "sql", "mysql", "postgresql", "mongodb", "oracle", "redis",
        "git", "jenkins", "devops", "agile", "scrum",
        "excel", "power bi", "tableau", "sap", "erp", "totvs"
    ]
    
    for keyword in tech_keywords:
        if keyword in cv_lower:
            keywords.append(keyword)
    
    return keywords

def extract_location_from_cv(cv_text):
    """Extrai localização básica do CV"""
    if not cv_text:
        return {'cidade': '', 'estado': ''}
    
    # Estados brasileiros
    states = {
        'sp': 'São Paulo', 'rj': 'Rio de Janeiro', 'mg': 'Minas Gerais',
        'pr': 'Paraná', 'rs': 'Rio Grande do Sul', 'sc': 'Santa Catarina'
    }
    
    cv_lower = cv_text.lower()
    
    for abbr, full_name in states.items():
        if abbr in cv_lower or full_name.lower() in cv_lower:
            return {'cidade': 'São Paulo' if abbr == 'sp' else '', 'estado': full_name}
    
    return {'cidade': '', 'estado': ''}

def search_candidates_pinecone(job_id, top_k=50):
    """
    OTIMIZADO: Busca rápida no Pinecone
    Retorna apenas os melhores candidatos para processamento detalhado
    """
    if not st.session_state.get('pinecone_available'):
        return []
    
    try:
        index = st.session_state['pinecone_index']
        
        # Buscar vetor da vaga
        job_response = index.query(
            id=f"job_{job_id}",
            top_k=1,
            include_values=True
        )
        
        if not job_response['matches']:
            return []
        
        job_vector = job_response['matches'][0]['values']
        
        # Buscar candidatos similares (mais resultados para filtrar melhor)
        candidates_response = index.query(
            vector=job_vector,
            top_k=top_k * 3,  # Buscar mais para filtrar depois
            include_metadata=True
        )
        
        # Filtrar apenas candidatos
        candidates = []
        for match in candidates_response['matches']:
            metadata = match['metadata']
            if (metadata.get('type') == 'candidate' or 
                'candidate_id' in metadata or 
                match['id'].startswith('candidate_')):
                
                candidate_id = metadata.get('candidate_id') or match['id'].replace('candidate_', '')
                candidates.append({
                    'id': candidate_id,
                    'score': match['score'],
                    'pinecone_similarity': match['score']
                })
                
                if len(candidates) >= top_k:
                    break
        
        return candidates
        
    except Exception as e:
        st.warning(f"⚠️ Erro no Pinecone: {e}")
        return []

def calculate_similarity_optimized(job_id, candidate_id, processed_jobs, processed_applicants):
    """
    OTIMIZADO: Cálculo rápido de similaridade
    Mantém a mesma lógica do app.py mas otimizada
    """
    job = processed_jobs[job_id]
    candidate = processed_applicants[candidate_id]
    
    # 1. Similaridade semântica (via Pinecone se disponível)
    semantic_score = 0.5  # Valor padrão
    
    if st.session_state.get('pinecone_available'):
        # Usar busca do Pinecone se disponível
        try:
            candidates = search_candidates_pinecone(job_id, top_k=100)
            for c in candidates:
                if c['id'] == candidate_id:
                    semantic_score = c['pinecone_similarity']
                    break
        except:
            semantic_score = 0.5
    
    # 2. Similaridade de keywords (rápida)
    job_keywords = set(job.get('keywords', []))
    candidate_keywords = set(candidate.get('keywords', []))
    
    if job_keywords and candidate_keywords:
        keywords_score = len(job_keywords.intersection(candidate_keywords)) / len(job_keywords)
    else:
        keywords_score = 0.0
    
    # 3. Similaridade de localização (rápida)
    location_score = 0.0
    if job.get('cidade') and candidate.get('cidade'):
        if job['cidade'].lower() == candidate['cidade'].lower():
            location_score = 1.0
    elif job.get('estado') and candidate.get('estado'):
        if job['estado'].lower() == candidate['estado'].lower():
            location_score = 0.7
    else:
        location_score = 0.3  # Mesmo país
    
    # 4. Outros scores (simplificados para velocidade)
    professional_level_score = compare_levels(
        job.get('nivel_profissional', ''),
        candidate.get('nivel_profissional', '')
    )
    
    academic_level_score = compare_levels(
        job.get('nivel_academico', ''),
        candidate.get('nivel_academico', '')
    )
    
    english_score = compare_levels(
        job.get('nivel_ingles', ''),
        candidate.get('nivel_ingles', '')
    )
    
    spanish_score = compare_levels(
        job.get('nivel_espanhol', ''),
        candidate.get('nivel_espanhol', '')
    )
    
    # Score final ponderado (mesma fórmula do app.py)
    final_score = (
        semantic_score * 0.40 +
        keywords_score * 0.30 +
        location_score * 0.05 +
        professional_level_score * 0.10 +
        academic_level_score * 0.10 +
        english_score * 0.025 +
        spanish_score * 0.025
    )
    
    # Retornar detalhes completos
    details = {
        'semantic': semantic_score,
        'keywords': keywords_score,
        'location': location_score,
        'professional_level': professional_level_score,
        'academic_level': academic_level_score,
        'english_level': english_score,
        'spanish_level': spanish_score
    }
    
    return {
        'score': final_score,
        'details': details
    }

def compare_levels(required_level, candidate_level):
    """Comparação rápida de níveis"""
    if not required_level or not candidate_level:
        return 0.5
    
    # Normalizar
    required = required_level.lower()
    candidate = candidate_level.lower()
    
    # Hierarquias simplificadas
    prof_levels = {'junior': 1, 'pleno': 2, 'senior': 3, 'sênior': 3}
    acad_levels = {'médio': 1, 'técnico': 2, 'superior': 3, 'mestrado': 4, 'doutorado': 5}
    lang_levels = {'básico': 1, 'intermediário': 2, 'avançado': 3, 'fluente': 4}
    
    # Determinar qual hierarquia usar
    for levels_dict in [prof_levels, acad_levels, lang_levels]:
        req_score = 0
        cand_score = 0
        
        for level, score in levels_dict.items():
            if level in required:
                req_score = max(req_score, score)
            if level in candidate:
                cand_score = max(cand_score, score)
        
        if req_score > 0 and cand_score > 0:
            return min(1.0, cand_score / req_score)
    
    # Se não encontrou em nenhuma hierarquia, comparação simples
    return 1.0 if required in candidate or candidate in required else 0.5

def get_top_candidates_fast(job_id, processed_jobs, processed_applicants, top_k=7):
    """
    OTIMIZADO: Busca rápida dos melhores candidatos
    Combina Pinecone (se disponível) + filtros rápidos
    """
    candidates_to_evaluate = []
    
    # 1. Se Pinecone disponível, buscar candidatos pré-filtrados
    if st.session_state.get('pinecone_available'):
        pinecone_candidates = search_candidates_pinecone(job_id, top_k=50)
        candidates_to_evaluate = [c['id'] for c in pinecone_candidates]
    
    # 2. Se Pinecone não disponível ou retornou poucos resultados, usar todos
    if len(candidates_to_evaluate) < 20:
        candidates_to_evaluate = list(processed_applicants.keys())
    
    # 3. Calcular similaridade apenas para candidatos selecionados
    results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, candidate_id in enumerate(candidates_to_evaluate):
        # Atualizar progresso
        progress = int((i + 1) / len(candidates_to_evaluate) * 100)
        progress_bar.progress(progress)
        status_text.text(f"🔄 Analisando candidato {i+1}/{len(candidates_to_evaluate)}")
        
        similarity_data = calculate_similarity_optimized(
            job_id, candidate_id, processed_jobs, processed_applicants
        )
        
        candidate = processed_applicants[candidate_id]
        
        results.append({
            'id': candidate_id,
            'nome': candidate['nome'],
            'score': similarity_data['score'],
            'is_hired': False,  # Será atualizado depois
            'applicant_data': candidate,
            'match_details': similarity_data['details']
        })
    
    # Limpar barras de progresso
    progress_bar.empty()
    status_text.empty()
    
    # Ordenar por score e retornar top candidatos
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_k * 2]  # Retornar mais que o necessário para ter opções

# Funções de renderização (EXATAMENTE IGUAIS ao app.py)
def get_theme_colors():
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
    """Renderiza o gráfico de radar (mesmo do app.py)"""
    categories = [
        'Semântica', 'Palavras-chave', 'Localização', 
        'Nível Prof.', 'Nível Acad.', 
        'Inglês', 'Espanhol'
    ]
    
    values = [
        match_details.get('semantic', 0) * 100,
        match_details.get('keywords', 0) * 100,
        match_details.get('location', 0) * 100,
        match_details.get('professional_level', 0) * 100,
        match_details.get('academic_level', 0) * 100,
        match_details.get('english_level', 0) * 100,
        match_details.get('spanish_level', 0) * 100
    ]
    
    colors = get_theme_colors()
    
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
    
    cv_content = f"CURRÍCULO - {candidate_name}\nID: {candidate_id}\n\n"
    cv_content += "=" * 50 + "\n\n"
    cv_content += cv_text
    
    cv_bytes = cv_content.encode('utf-8')
    filename = f"CV_{candidate_name.replace(' ', '_')}_{candidate_id}.txt"
    
    return cv_bytes, filename

def render_candidate_details(candidate, selected_job):
    """Renderiza os detalhes do candidato selecionado (mesmo do app.py)"""
    applicant_data = candidate['applicant_data']
    match_details = candidate['match_details']
    
    tab1, tab2, tab3 = st.tabs(["Perfil", "Currículo", "Compatibilidade"])
    
    with tab1:
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
        
        st.markdown("#### Análise de Compatibilidade")
        radar_fig = render_radar_chart(match_details)
        st.plotly_chart(radar_fig, use_container_width=True)
        
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
            ]
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
        
        st.markdown("---")
        
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
    """Renderiza os detalhes da vaga selecionada (mesmo do app.py)"""
    with st.expander("Detalhes da Vaga", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### {capitalize_words(job.get('titulo', 'N/A'))}")
            st.markdown(f"**Cliente:** {capitalize_words(job.get('cliente', 'N/A'))}")
            st.markdown(f"**Empresa/Divisão:** {capitalize_words(job.get('empresa', 'N/A'))}")
            st.markdown(f"**Tipo de Contratação:** {capitalize_words(job.get('tipo_contratacao', 'N/A'))}")
        
        with col2:
            st.markdown("#### Requisitos")
            localizacao_limpa = clean_duplicated_words(job.get('localizacao', 'N/A'))
            st.markdown(f"**Localização:** {capitalize_words(localizacao_limpa)}")
            st.markdown(f"**Nível Profissional:** {capitalize_words(job.get('nivel_profissional', 'N/A'))}")
            st.markdown(f"**Nível Acadêmico:** {capitalize_words(job.get('nivel_academico', 'N/A'))}")
            st.markdown(f"**Idiomas:** Inglês: {capitalize_words(job.get('nivel_ingles', 'N/A'))}, Espanhol: {capitalize_words(job.get('nivel_espanhol', 'N/A'))}")
        
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
    """Renderiza visualização de comparação (mesmo do app.py)"""
    
    top_candidates = similarities[:top_n]
    
    tab1, tab2 = st.tabs(["Gráfico Comparativo", "Tabela Detalhada"])
    
    with tab1:
        st.markdown("### Comparativo Top 5 Candidatos")
        
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
        
        st.markdown("---")
        
        # Gráfico de Barras
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
    
    with tab2:
        st.markdown("### Relatório Detalhado dos Candidatos")
        
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
        
        # Tabela detalhada
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
                'Score Total (%)': f"{candidate['score'] * 100:.1f}%",
                'Score Semântico (%)': f"{match_details.get('semantic', 0) * 100:.1f}%",
                'Score Palavras-chave (%)': f"{match_details.get('keywords', 0) * 100:.1f}%",
                'Conhecimentos Técnicos': conhecimentos_unificados,
                'Keywords Compatíveis': ', '.join(matching_keywords) if matching_keywords else 'Nenhuma',
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
        
        # Downloads
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv_buffer = io.StringIO()
            
            csv_buffer.write("RELATÓRIO DE CANDIDATOS RECOMENDADOS\n")
            csv_buffer.write(f"Vaga;{capitalize_words(selected_job.get('titulo', 'N/A'))}\n")
            csv_buffer.write(f"Cliente;{capitalize_words(selected_job.get('cliente', 'N/A'))}\n")
            csv_buffer.write(f"Data do Relatório;{pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}\n")
            csv_buffer.write(f"Melhor Candidato;{best_candidate['nome'] if best_candidate else 'N/A'}\n")
            csv_buffer.write(f"Score Médio;{avg_score * 100:.1f}%\n")
            csv_buffer.write("\n")
            csv_buffer.write("CANDIDATOS RECOMENDADOS\n")
            
            df_detailed.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8')
            
            csv_content = csv_buffer.getvalue()
            csv_buffer.close()
            
            st.download_button(
                label="📥 Baixar Relatório (CSV)",
                data=csv_content.encode('utf-8'),
                file_name=f"relatorio_candidatos_otimizado_{timestamp}.csv",
                mime="text/csv"
            )
        
        with col2:
            connection_info = "GitHub + Pinecone" if st.session_state.get('pinecone_available') else "GitHub Only"
            st.info(f"🎯 **Powered by {connection_info}**\n\n✅ Busca otimizada\n✅ Resultados precisos\n✅ Performance melhorada")

def main():
    """Função principal otimizada"""
    # Aplicar CSS
    st.markdown(get_dynamic_css(), unsafe_allow_html=True)
    
    render_header()
    
    # Carregar dados
    data = load_data_from_github()
    
    if not data:
        st.error("❌ Não foi possível carregar os dados. Verifique sua conexão.")
        return
    
    processed_jobs = data['processed_jobs']
    processed_applicants = data['processed_applicants']
    hired_candidates = data['hired_candidates']
    
    st.success("✅ Dados carregados com sucesso!")
    
    # Informar sobre conexões
    if st.session_state.get('pinecone_available'):
        st.info("🎯 **Modo Otimizado:** Busca vetorial via Pinecone + dados completos do GitHub")
    else:
        st.info("📊 **Modo Padrão:** Dados completos do GitHub (Pinecone indisponível)")
    
    # Selectbox de vagas
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
        
        # Cache otimizado
        cache_key = f"similarities_optimized_{selected_job_id}"
        
        if cache_key not in st.session_state:
            # Busca otimizada
            similarities = get_top_candidates_fast(
                selected_job_id, 
                processed_jobs, 
                processed_applicants,
                top_k=7
            )
            
            # Atualizar status de contratação
            for candidate in similarities:
                candidate['is_hired'] = candidate['applicant_data']['codigo'] in hired_candidates.get(selected_job_id, [])
            
            st.session_state[cache_key] = similarities
        else:
            similarities = st.session_state[cache_key]
        
        # Verificar candidatos contratados
        top_7_ids = [item['id'] for item in similarities[:7]]
        hired_ids = [candidate_id for candidate_id in top_7_ids 
                    if processed_applicants[candidate_id]['codigo'] in hired_candidates.get(selected_job_id, [])]
        
        if hired_ids:
            hit_rate = len(hired_ids) / len(hired_candidates.get(selected_job_id, []) or [1]) * 100
            st.success(f"🎯 O sistema identificou {len(hired_ids)} dos candidatos já contratados para esta vaga entre os 7 mais recomendados! (Taxa de acerto: {hit_rate:.1f}%)")
        
        st.markdown("## Candidatos Recomendados")
        st.markdown("💡 **Clique em qualquer card para ver os detalhes completos do candidato**")
        
        top_candidates = similarities[:7]
        
        # Gerenciar seleção
        session_key = f"selected_candidate_{selected_job_id}"
        if session_key not in st.session_state:
            st.session_state[session_key] = 0
        
        # Renderizar cards
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
        
        # Detalhes do candidato selecionado
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

if __name__ == "__main__":
    main()
        