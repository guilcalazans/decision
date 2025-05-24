import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
import io
import os

# Importar Pinecone usando a sintaxe que funcionou
import pinecone
from pinecone import Pinecone

# Configuração da página
st.set_page_config(
    page_title="Decision Recruiter - Recomendação de Candidatos",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS dinâmico baseado no tema (mesmo do seu código original)
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
    st.markdown("""
    <div class="header">
        <h1 style="margin-bottom: 0.5rem;">Decision Recruiter</h1>
        <p style="margin: 0; font-size: 1.25rem;">Sistema de Recomendação de Candidatos - Powered by Pinecone</p>
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
    """Inicializa conexão com Pinecone usando a sintaxe que funcionou"""
    try:
        # Sintaxe exata que funcionou no seu teste
        API_KEY = "pcsk_5DfEc5_JTj7W19EkqEm2awJNed9dnmdfNtKBuNv3MNzPnX9R2tJv3dRNbUEJcm9gXWNYko"
        INDEX_NAME = "decision-recruiter"
        pc = Pinecone(api_key=API_KEY)
        index = pc.Index(INDEX_NAME)
        return index
    except Exception as e:
        st.error(f"❌ Erro ao conectar no Pinecone: {e}")
        return None

def load_static_data():
    """Carrega dados estáticos para demonstração - sem pickle"""
    
    # Dados de vagas (exemplo expandido)
    jobs_data = {
        "5185": {
            "titulo": "Operation Lead - Cloud Infrastructure",
            "cliente": "Morris, Moran and Dodson",
            "empresa": "Decision São Paulo",
            "tipo_contratacao": "CLT Full",
            "cidade": "São Paulo",
            "estado": "São Paulo",
            "pais": "Brasil",
            "localizacao": "São Paulo São Paulo Brasil",
            "nivel_profissional": "Sênior",
            "nivel_academico": "Ensino Superior Completo",
            "nivel_ingles": "Avançado",
            "nivel_espanhol": "Fluente",
            "areas_atuacao": "TI - Sistemas e Ferramentas",
            "principais_atividades": "Operations Lead - Responsável pela entrega de serviços cloud, gerenciamento de infraestrutura AWS, coordenação com fornecedores e terceiros.",
            "competencias": "AWS, SAP BASIS, SQL, Oracle, Cloud Infrastructure Management, SLA Management",
            "keywords": ["aws", "sql", "oracle", "cloud", "infrastructure", "sap", "basis"]
        },
        "5186": {
            "titulo": "Desenvolvedor Python Sênior",
            "cliente": "Tech Solutions Corp",
            "empresa": "Decision Rio",
            "tipo_contratacao": "CLT Full",
            "cidade": "Rio de Janeiro",
            "estado": "Rio de Janeiro", 
            "pais": "Brasil",
            "localizacao": "Rio de Janeiro Rio de Janeiro Brasil",
            "nivel_profissional": "Sênior",
            "nivel_academico": "Ensino Superior Completo",
            "nivel_ingles": "Intermediário",
            "nivel_espanhol": "Básico",
            "areas_atuacao": "TI - Desenvolvimento",
            "principais_atividades": "Desenvolvimento de aplicações Python, APIs REST, integração com bancos de dados, metodologias ágeis.",
            "competencias": "Python, Django, Flask, PostgreSQL, Docker, Git, APIs REST",
            "keywords": ["python", "django", "flask", "postgresql", "docker", "git", "api", "rest"]
        },
        "5187": {
            "titulo": "Analista de Dados Pleno",
            "cliente": "DataCorp Analytics",
            "empresa": "Decision BH",
            "tipo_contratacao": "PJ",
            "cidade": "Belo Horizonte",
            "estado": "Minas Gerais",
            "pais": "Brasil", 
            "localizacao": "Belo Horizonte Minas Gerais Brasil",
            "nivel_profissional": "Pleno",
            "nivel_academico": "Ensino Superior Completo",
            "nivel_ingles": "Intermediário",
            "nivel_espanhol": "Básico",
            "areas_atuacao": "TI - Business Intelligence",
            "principais_atividades": "Análise de dados, criação de dashboards, SQL avançado, Python para análise, Power BI.",
            "competencias": "SQL, Python, Power BI, Excel, Tableau, Estatística",
            "keywords": ["sql", "python", "powerbi", "excel", "tableau", "estatistica", "dados"]
        }
    }
    
    # Dados de candidatos (exemplo expandido)
    applicants_data = {
        "31000": {
            "nome": "Carolina Aparecida Santos",
            "codigo": "31000",
            "email": "carolina_aparecida@gmail.com",
            "telefone": "(11) 97048-2708",
            "cidade": "São Paulo",
            "estado": "São Paulo",
            "pais": "Brasil",
            "localizacao": "São Paulo São Paulo Brasil",
            "nivel_profissional": "Pleno",
            "nivel_academico": "Ensino Superior Completo",
            "nivel_ingles": "Intermediário",
            "nivel_espanhol": "Básico",
            "conhecimentos_tecnicos": "Excel, SQL, Sistemas ERP, Contabilidade",
            "conhecimentos_tecnicos_extraidos": "excel, sql, erp, totvs, navision, contabilidade",
            "keywords": ["excel", "sql", "erp", "totvs", "navision", "contabilidade"],
            "cv": "Assistente administrativo com 8 anos de experiência em departamentos financeiro e contábil. Expertise em Excel avançado, SQL básico, sistemas ERP (TOTVS, Navision). Formação em Ciências Contábeis. Experiência com indicadores KPIs, relatórios gerenciais e fechamento contábil."
        },
        "31001": {
            "nome": "João Silva Oliveira",
            "codigo": "31001", 
            "email": "joao.silva@email.com",
            "telefone": "(11) 98765-4321",
            "cidade": "São Paulo",
            "estado": "São Paulo",
            "pais": "Brasil",
            "localizacao": "São Paulo São Paulo Brasil",
            "nivel_profissional": "Sênior",
            "nivel_academico": "Ensino Superior Completo",
            "nivel_ingles": "Avançado",
            "nivel_espanhol": "Intermediário",
            "conhecimentos_tecnicos": "AWS, Python, Docker, Kubernetes, SQL",
            "conhecimentos_tecnicos_extraidos": "aws, python, docker, kubernetes, sql, devops, cloud",
            "keywords": ["aws", "python", "docker", "kubernetes", "sql", "devops", "cloud"],
            "cv": "Engenheiro DevOps com 10 anos de experiência em cloud computing. Especialista em AWS, Docker, Kubernetes, Python. Experiência com arquiteturas distribuídas, CI/CD, monitoramento e automação de infraestrutura. Certificações AWS Solutions Architect e DevOps Engineer."
        },
        "31002": {
            "nome": "Maria Fernanda Costa",
            "codigo": "31002",
            "email": "maria.costa@email.com", 
            "telefone": "(21) 99888-7777",
            "cidade": "Rio de Janeiro",
            "estado": "Rio de Janeiro",
            "pais": "Brasil",
            "localizacao": "Rio de Janeiro Rio de Janeiro Brasil",
            "nivel_profissional": "Sênior",
            "nivel_academico": "Mestrado",
            "nivel_ingles": "Fluente",
            "nivel_espanhol": "Avançado",
            "conhecimentos_tecnicos": "Python, Django, PostgreSQL, Redis, Git",
            "conhecimentos_tecnicos_extraidos": "python, django, postgresql, redis, git, web, backend",
            "keywords": ["python", "django", "postgresql", "redis", "git", "web", "backend"],
            "cv": "Desenvolvedora Python Sênior com 12 anos de experiência. Especialista em Django, Flask, desenvolvimento de APIs REST, arquitetura de microsserviços. Mestrado em Ciência da Computação. Experiência em liderança técnica e mentoria de equipes."
        },
        "31003": {
            "nome": "Pedro Henrique Alves",
            "codigo": "31003",
            "email": "pedro.alves@email.com",
            "telefone": "(31) 97777-8888",
            "cidade": "Belo Horizonte", 
            "estado": "Minas Gerais",
            "pais": "Brasil",
            "localizacao": "Belo Horizonte Minas Gerais Brasil",
            "nivel_profissional": "Pleno",
            "nivel_academico": "Ensino Superior Completo",
            "nivel_ingles": "Intermediário",
            "nivel_espanhol": "Básico",
            "conhecimentos_tecnicos": "SQL, Python, Power BI, Excel, Tableau",
            "conhecimentos_tecnicos_extraidos": "sql, python, powerbi, excel, tableau, dados, estatistica",
            "keywords": ["sql", "python", "powerbi", "excel", "tableau", "dados", "estatistica"],
            "cv": "Analista de Dados com 6 anos de experiência em Business Intelligence. Expertise em SQL avançado, Python para análise de dados, Power BI, Tableau. Formação em Estatística. Experiência com data lakes, ETL e criação de dashboards executivos."
        },
        "31004": {
            "nome": "Ana Beatriz Moreira",
            "codigo": "31004",
            "email": "ana.moreira@email.com",
            "telefone": "(11) 96666-5555", 
            "cidade": "São Paulo",
            "estado": "São Paulo",
            "pais": "Brasil",
            "localizacao": "São Paulo São Paulo Brasil",
            "nivel_profissional": "Júnior",
            "nivel_academico": "Ensino Superior Completo",
            "nivel_ingles": "Básico",
            "nivel_espanhol": "Básico",
            "conhecimentos_tecnicos": "Oracle, SQL, SAP BASIS, Linux",
            "conhecimentos_tecnicos_extraidos": "oracle, sql, sap, basis, linux, dba",
            "keywords": ["oracle", "sql", "sap", "basis", "linux", "dba"],
            "cv": "Administradora de Banco de Dados júnior com 3 anos de experiência. Conhecimentos em Oracle, SQL, SAP BASIS, Linux. Formação em Sistemas de Informação. Experiência com backup, recovery, performance tuning e monitoramento de bases de dados."
        }
    }
    
    # Dados de contratações (quem foi contratado para cada vaga)
    hired_data = {
        "5185": ["31001", "31004"],  # João (DevOps) e Ana (DBA) contratados para vaga Cloud
        "5186": ["31002"],           # Maria contratada para vaga Python
        "5187": ["31003"]            # Pedro contratado para vaga Analista de Dados
    }
    
    return {
        'processed_jobs': jobs_data,
        'processed_applicants': applicants_data, 
        'hired_candidates': hired_data
    }

def search_candidates_pinecone(job_id, index, top_k=7):
    """Busca candidatos similares no Pinecone usando a sintaxe que funcionou"""
    try:
        # Primeiro, buscar o vetor da vaga (usando sintaxe do seu teste)
        job_response = index.query(
            id=f"job_{job_id}",
            top_k=1,
            include_values=True,
            include_metadata=True
        )
        
        if not job_response['matches']:
            st.error(f"❌ Vaga {job_id} não encontrada no Pinecone")
            return [], None
        
        job_vector = job_response['matches'][0]['values']
        job_metadata = job_response['matches'][0]['metadata']
        
        # Buscar candidatos similares (usando sintaxe do seu teste)
        candidates_response = index.query(
            vector=job_vector,
            top_k=top_k * 2,  # Buscar mais para filtrar apenas candidatos
            include_metadata=True
        )
        
        # Filtrar apenas candidatos
        candidates = []
        for match in candidates_response['matches']:
            if match['metadata'].get('type') == 'candidate':
                candidates.append(match)
                if len(candidates) >= top_k:
                    break
        
        return candidates, job_metadata
        
    except Exception as e:
        st.error(f"❌ Erro ao buscar no Pinecone: {e}")
        return [], None

def get_all_jobs_from_pinecone(index):
    """Busca todas as vagas disponíveis no Pinecone"""
    try:
        # Usar vetor aleatório para busca ampla (baseado no seu teste)
        random_vector = np.random.rand(512).tolist()
        
        # Buscar muitos resultados
        response = index.query(
            vector=random_vector,
            top_k=10000,
            include_metadata=True
        )
        
        # Filtrar apenas vagas
        jobs_dict = {}
        for match in response['matches']:
            metadata = match['metadata']
            if metadata.get('type') == 'job':
                job_id = metadata.get('job_id')
                if job_id:
                    jobs_dict[job_id] = metadata
        
        return jobs_dict
        
    except Exception as e:
        st.error(f"❌ Erro ao buscar vagas no Pinecone: {e}")
        return {}

def calculate_detailed_scores(job_data, candidate_metadata, similarity_score):
    """Calcula scores detalhados baseado nos metadados"""
    scores = {
        'semantic': similarity_score,
        'keywords': 0.0,
        'location': 0.0,
        'professional_level': 0.0,
        'academic_level': 0.0,
        'english_level': 0.5,
        'spanish_level': 0.5
    }
    
    # Score de localização
    job_cidade = job_data.get('cidade', '').lower()
    job_estado = job_data.get('estado', '').lower()
    cand_cidade = candidate_metadata.get('cidade', '').lower()
    cand_estado = candidate_metadata.get('estado', '').lower()
    
    if job_cidade and cand_cidade and job_cidade == cand_cidade:
        scores['location'] = 1.0
    elif job_estado and cand_estado and job_estado == cand_estado:
        scores['location'] = 0.7
    else:
        scores['location'] = 0.3
    
    # Score de nível profissional (simulado)
    job_nivel = job_data.get('nivel_profissional', '').lower()
    cand_nivel = candidate_metadata.get('nivel_profissional', '').lower()
    
    if job_nivel and cand_nivel:
        if job_nivel in cand_nivel or cand_nivel in job_nivel:
            scores['professional_level'] = 1.0
        else:
            scores['professional_level'] = 0.5
    else:
        scores['professional_level'] = 0.5
    
    # Score acadêmico (simulado)
    scores['academic_level'] = 0.8  # Valor padrão
    
    # Score de keywords (baseado nos metadados do Pinecone)
    job_keywords = set(job_data.get('keywords', []))
    cand_keywords_str = candidate_metadata.get('keywords', '')
    if cand_keywords_str:
        cand_keywords = set(cand_keywords_str.split(','))
        if job_keywords and cand_keywords:
            intersection = job_keywords.intersection(cand_keywords)
            scores['keywords'] = len(intersection) / len(job_keywords) if job_keywords else 0
    
    return scores

def get_theme_colors():
    """Retorna cores adaptadas ao tema atual"""
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
    """Renderiza o gráfico de radar para os scores de match"""
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
    """Renderiza os detalhes do candidato selecionado"""
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
    
    with tab2:
        cv_text = applicant_data.get('cv', '')
        
        if cv_text and cv_text.strip():
            st.markdown("#### Preview do Currículo")
            preview_text = cv_text[:500] + "..." if len(cv_text) > 500 else cv_text
            
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
                    mime="text/plain"
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
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

def render_job_details(job):
    """Renderiza os detalhes da vaga selecionada"""
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
        
        st.markdown("---")
        
        st.markdown("#### Habilidades e Tecnologias Requeridas")
        
        if job.get('keywords'):
            keywords_html = ' '.join([render_skill_tag(kw) for kw in job.get('keywords', [])])
            st.markdown(f"<div style='margin-bottom: 1rem;'>{keywords_html}</div>", unsafe_allow_html=True)
        
        with st.container(border=True):
            if job.get('principais_atividades'):
                st.markdown("##### Principais Atividades")
                st.markdown(job.get('principais_atividades', 'N/A'))
            
            if job.get('competencias'):
                st.markdown("##### Competências Técnicas e Comportamentais")
                st.markdown(job.get('competencias', 'N/A'))

def main():
    # Aplicar CSS dinâmico
    st.markdown(get_dynamic_css(), unsafe_allow_html=True)
    
    render_header()
    
    # Inicializar Pinecone
    index = init_pinecone()
    if not index:
        st.stop()
    
    # Buscar todas as vagas do Pinecone
    st.info("🔍 Carregando vagas do Pinecone...")
    all_jobs = get_all_jobs_from_pinecone(index)
    
    if not all_jobs:
        st.error("❌ Nenhuma vaga encontrada no Pinecone")
        st.stop()
    
    st.success(f"✅ {len(all_jobs)} vagas carregadas do Pinecone!")
    
    # Criar opções de vagas baseadas nos dados do Pinecone
    job_options = {}
    for job_id, job_metadata in all_jobs.items():
        title = capitalize_words(job_metadata.get('titulo', 'Sem título'))
        company = capitalize_words(job_metadata.get('cliente', 'Empresa não especificada'))
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
        # Buscar dados da vaga selecionada no Pinecone
        selected_job = all_jobs.get(selected_job_id, {})
        
        # Renderizar detalhes da vaga (usando dados do Pinecone)
        render_job_details(selected_job)
        
        # Buscar candidatos no Pinecone
        with st.status("🔍 Buscando candidatos mais compatíveis no Pinecone..."):
            pinecone_results, job_metadata = search_candidates_pinecone(selected_job_id, index, top_k=7)
        
        if not pinecone_results:
            st.warning("⚠️ Nenhum candidato encontrado para esta vaga.")
            st.stop()
        
        # Processar resultados do Pinecone
        similarities = []
        
        for result in pinecone_results:
            candidate_metadata = result['metadata']
            candidate_id = candidate_metadata.get('candidate_id')
            candidate_name = candidate_metadata.get('nome', 'Nome não disponível')
            similarity_score = result['score']
            
            # Usar os metadados do Pinecone como dados do candidato
            applicant_data = {
                'nome': candidate_name,
                'codigo': candidate_id,
                'email': candidate_metadata.get('email', 'N/A'),
                'telefone': candidate_metadata.get('telefone', 'N/A'),
                'cidade': candidate_metadata.get('cidade', 'N/A'),
                'estado': candidate_metadata.get('estado', 'N/A'),
                'localizacao': f"{candidate_metadata.get('cidade', '')} {candidate_metadata.get('estado', '')} Brasil",
                'nivel_profissional': candidate_metadata.get('nivel_profissional', 'N/A'),
                'nivel_academico': candidate_metadata.get('nivel_academico', 'N/A'),
                'nivel_ingles': candidate_metadata.get('nivel_ingles', 'N/A'),
                'nivel_espanhol': candidate_metadata.get('nivel_espanhol', 'N/A'),
                'conhecimentos_tecnicos': candidate_metadata.get('keywords', 'N/A'),
                'conhecimentos_tecnicos_extraidos': '',
                'keywords': candidate_metadata.get('keywords', '').split(',') if candidate_metadata.get('keywords') else [],
                'cv': f"Candidato ID: {candidate_id}. Perfil compatível com a vaga baseado em análise de similaridade semântica."
            }
            
            # Calcular scores detalhados
            match_details = calculate_detailed_scores(
                job_metadata or selected_job, 
                candidate_metadata, 
                similarity_score
            )
            
            # Calcular score final ponderado
            final_score = (
                match_details['semantic'] * 0.40 +
                match_details['keywords'] * 0.30 +
                match_details['location'] * 0.05 +
                match_details['professional_level'] * 0.10 +
                match_details['academic_level'] * 0.10 +
                match_details['english_level'] * 0.025 +
                match_details['spanish_level'] * 0.025
            )
            
            # Para demonstração, simular alguns candidatos contratados
            is_hired = (hash(candidate_id) % 10) < 2  # ~20% dos candidatos "contratados"
            
            similarities.append({
                'id': candidate_id,
                'nome': candidate_name,
                'score': final_score,
                'is_hired': is_hired,
                'applicant_data': applicant_data,
                'match_details': match_details
            })
        
        # Verificar candidatos contratados (simulado)
        hired_ids = [item['id'] for item in similarities if item['is_hired']]
        
        if hired_ids:
            st.success(f"🎯 Demonstração: {len(hired_ids)} candidatos simulados como 'já contratados' entre os 7 recomendados!")
        
        st.markdown("## Candidatos Recomendados pelo Pinecone")
        st.markdown("💡 **Resultados baseados em busca vetorial semântica**")
        
        # Gerenciar seleção de candidato
        session_key = f"selected_candidate_{selected_job_id}"
        if session_key not in st.session_state:
            st.session_state[session_key] = 0
        
        # Renderizar cards dos candidatos
        for i, candidate in enumerate(similarities):
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
        selected_candidate = similarities[st.session_state[session_key]]
        
        st.markdown("### Detalhes do Candidato Selecionado")
        
        st.markdown(f"""
        <div class="card" style="border: 2px solid var(--border-selected); background: linear-gradient(135deg, var(--card-bg-selected) 0%, var(--card-bg) 100%);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="
                        width: 50px;
                        height: 50px;
                        border-radius: 50%;
                        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
                        color: #FFFFFF;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        font-weight: 600;
                        font-size: 1.2rem;
                        box-shadow: 0 2px 8px var(--shadow);
                    ">
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
        
        # Relatório comparativo
        st.markdown("---")
        st.markdown("### Relatório Comparativo dos Candidatos")
        
        # Criar tabela resumo
        detailed_data = []
        for i, candidate in enumerate(similarities):
            applicant_data = candidate['applicant_data']
            match_details = candidate['match_details']
            
            conhecimentos_unificados = merge_technical_knowledge(
                applicant_data.get('conhecimentos_tecnicos', ''),
                applicant_data.get('conhecimentos_tecnicos_extraidos', '')
            )
            
            row_data = {
                'Posição': f"{i+1}º",
                'Nome': candidate['nome'],
                'Email': applicant_data.get('email', 'N/A'),
                'Score Total (%)': f"{candidate['score'] * 100:.1f}%",
                'Score Semântico (%)': f"{match_details.get('semantic', 0) * 100:.1f}%",
                'Score Localização (%)': f"{match_details.get('location', 0) * 100:.1f}%",
                'Nível Profissional': capitalize_words(applicant_data.get('nivel_profissional', 'N/A')),
                'Conhecimentos Técnicos': conhecimentos_unificados,
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
        
        # Download do relatório
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv_buffer = io.StringIO()
            
            csv_buffer.write("RELATÓRIO DE CANDIDATOS RECOMENDADOS - PINECONE\n")
            csv_buffer.write(f"Vaga;{capitalize_words(selected_job.get('titulo', 'N/A'))}\n")
            csv_buffer.write(f"Cliente;{capitalize_words(selected_job.get('cliente', 'N/A'))}\n")
            csv_buffer.write(f"Data do Relatório;{pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}\n")
            csv_buffer.write(f"Melhor Candidato;{similarities[0]['nome'] if similarities else 'N/A'}\n")
            csv_buffer.write(f"Score Médio;{sum(c['score'] for c in similarities) / len(similarities) * 100:.1f}% (7 candidatos)\n")
            csv_buffer.write("\n")
            csv_buffer.write("CANDIDATOS RECOMENDADOS\n")
            
            df_detailed.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8')
            
            csv_content = csv_buffer.getvalue()
            csv_buffer.close()
            
            st.download_button(
                label="📥 Baixar Relatório Completo (CSV)",
                data=csv_content.encode('utf-8'),
                file_name=f"relatorio_candidatos_pinecone_{timestamp}.csv",
                mime="text/csv",
                help="Baixar relatório completo dos candidatos recomendados pelo Pinecone"
            )
        
        with col2:
            st.info("🎯 **Powered by Pinecone Vector Database**\n\n✅ Busca instantânea entre milhares de candidatos\n✅ Resultados baseados em similaridade semântica\n✅ Performance otimizada com embeddings")

if __name__ == "__main__":
    main()
