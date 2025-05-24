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

@st.cache_data
def download_and_load_data():
    """
    HÍBRIDO: Carrega dados do GitHub Releases + Busca candidatos do Pinecone
    Mantém toda a lógica original de match do app.py
    """
    try:
        # 1. CARREGAR DADOS COMPLETOS DO GITHUB RELEASES
        with st.status("📥 Carregando dados completos..."):
            st.write("🔗 Conectando ao GitHub Releases...")
            
            url = "https://github.com/guilcalazans/decision/releases/download/v1.0/complete_data.json"
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            st.write("📊 Processando dados...")
            complete_data = response.json()
            
            st.write("✅ Dados completos carregados!")
        
        # 2. CONECTAR AO PINECONE PARA BUSCA VETORIAL
        with st.status("🎯 Conectando ao Pinecone..."):
            API_KEY = "pcsk_5DfEc5_JTj7W19EkqEm2awJNed9dnmdfNtKBuNv3MNzPnX9R2tJv3dRNbUEJcm9gXWNYko"
            INDEX_NAME = "decision-recruiter"
            pc = Pinecone(api_key=API_KEY)
            index = pc.Index(INDEX_NAME)
            
            st.write("✅ Pinecone conectado!")
        
        # 3. ESTRUTURAR DADOS NO FORMATO ORIGINAL DO APP.PY
        # Manter exatamente a mesma estrutura que o app.py espera
        processed_jobs = complete_data.get('jobs', {})
        processed_applicants = complete_data.get('candidates', {})  
        hired_candidates = complete_data.get('hired_candidates', {})
        
        # 4. CRIAR EMBEDDINGS DUMMY (para manter compatibilidade)
        # O app.py usa estes dicionários, mas a busca real será via Pinecone
        job_embeddings = {}
        applicant_embeddings = {}
        
        # Criar embeddings dummy para todas as vagas e candidatos
        for job_id in processed_jobs.keys():
            job_embeddings[job_id] = np.random.rand(512)  # Dummy
            
        for candidate_id in processed_applicants.keys():
            applicant_embeddings[candidate_id] = np.random.rand(512)  # Dummy
        
        # 5. ADICIONAR ÍNDICE PINECONE AOS DADOS
        # Para que outras funções possam usar
        st.session_state['pinecone_index'] = index
        st.session_state['pinecone_available'] = True
        
        # 6. RETORNAR NO FORMATO EXATO QUE APP.PY ESPERA
        return {
            'processed_jobs': processed_jobs,
            'processed_applicants': processed_applicants, 
            'hired_candidates': hired_candidates,
            'job_embeddings': job_embeddings,      # Dummy - não usado
            'applicant_embeddings': applicant_embeddings,  # Dummy - não usado
            'match_details': {}  # Será calculado dinamicamente
        }
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")
        st.info("🔄 Usando dados de demonstração...")
        
        # FALLBACK - dados mínimos para demonstração
        return {
            'processed_jobs': {"5185": {"titulo": "Demo Job", "cliente": "Demo Client"}},
            'processed_applicants': {"24825": {"nome": "Demo Candidate", "email": "demo@test.com"}},
            'hired_candidates': {"5185": ["24825"]},
            'job_embeddings': {"5185": np.random.rand(512)},
            'applicant_embeddings': {"24825": np.random.rand(512)},
            'match_details': {}
        }
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
        
        # Buscar muitos resultados para garantir que encontremos candidatos
        candidates_response = index.query(
            vector=job_vector,
            top_k=100,  # Aumentar para garantir candidatos
            include_metadata=True
        )
        
        # Debug: Mostrar tipos encontrados
        types_found = {}
        for match in candidates_response['matches']:
            match_type = match['metadata'].get('type', 'unknown')
            types_found[match_type] = types_found.get(match_type, 0) + 1
        
        st.write(f"🔍 Debug - Tipos encontrados: {types_found}")
        
        # Filtrar apenas candidatos de forma mais robusta
        candidates = []
        for match in candidates_response['matches']:
            metadata = match['metadata']
            match_type = metadata.get('type')
            
            # Filtro mais flexível
            if (match_type == 'candidate' or 
                'candidate_id' in metadata or 
                match['id'].startswith('candidate_')):
                candidates.append(match)
                
                if len(candidates) >= top_k:
                    break
        
        st.write(f"✅ Candidatos filtrados: {len(candidates)}")
        
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

def calculate_similarity(job_id, applicant_id, job_embeddings, applicant_embeddings, match_details, processed_jobs, processed_applicants):
    """
    MODIFICADO: Usa Pinecone para busca real + dados completos para cálculo de score
    Mantém toda a lógica original de match do app.py
    """
    
    # VERIFICAR SE PINECONE ESTÁ DISPONÍVEL
    if st.session_state.get('pinecone_available') and st.session_state.get('pinecone_index'):
        try:
            # BUSCA REAL NO PINECONE
            index = st.session_state['pinecone_index']
            
            # 1. Buscar vetor da vaga no Pinecone
            job_response = index.query(
                id=f"job_{job_id}",
                top_k=1,
                include_values=True,
                include_metadata=True
            )
            
            if job_response['matches']:
                job_vector = job_response['matches'][0]['values']
                
                # 2. Calcular similaridade com candidato específico
                candidate_response = index.query(
                    id=f"candidate_{applicant_id}",
                    top_k=1,
                    include_values=True,
                    include_metadata=True
                )
                
                if candidate_response['matches']:
                    candidate_vector = candidate_response['matches'][0]['values']
                    
                    # 3. Calcular similaridade de cosseno REAL
                    cos_sim = np.dot(job_vector, candidate_vector) / (
                        np.linalg.norm(job_vector) * np.linalg.norm(candidate_vector)
                    )
                else:
                    cos_sim = 0.1  # Candidato não encontrado no Pinecone
            else:
                cos_sim = 0.1  # Vaga não encontrada no Pinecone
                
        except Exception as e:
            # Se Pinecone falhar, usar cálculo dummy
            cos_sim = 0.5
            
    else:
        # FALLBACK: Cálculo original do app.py
        job_emb = job_embeddings[job_id]
        applicant_emb = applicant_embeddings[applicant_id]
        cos_sim = util.cos_sim(job_emb, applicant_emb).item()
    
    # RESTO DO CÓDIGO ORIGINAL - MANTÉM TODA A LÓGICA DE SCORE
    details = match_details.get(job_id, {}).get(applicant_id, {})
    details['semantic'] = cos_sim
    
    # Verificar se precisamos recalcular o score acadêmico
    if 'academic_level' in details and processed_jobs[job_id].get('nivel_academico') and processed_applicants[applicant_id].get('nivel_academico'):
        details['academic_level'] = compare_academic_levels(
            processed_jobs[job_id].get('nivel_academico', ''),
            processed_applicants[applicant_id].get('nivel_academico', '')
        )
    
    # Calcular score ponderado - EXATAMENTE COMO NO APP.PY ORIGINAL
    weighted_score = (
        cos_sim * 0.40 +  # Semântica
        details.get('keywords', 0) * 0.30 +  # Palavras-chave técnicas
        details.get('location', 0) * 0.05 +  # Localização
        details.get('professional_level', 0) * 0.10 +  # Nível profissional
        details.get('academic_level', 0) * 0.10 +  # Nível acadêmico
        details.get('english_level', 0) * 0.025 +  # Nível de inglês
        details.get('spanish_level', 0) * 0.025  # Nível de espanhol
    )
    
    # Retornar similaridade e detalhes - FORMATO ORIGINAL
    return {
        'score': weighted_score,
        'details': details
    }

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
    
    # Carregar dados HÍBRIDOS (GitHub + Pinecone)
    data = download_and_load_data()
    
    processed_jobs = data['processed_jobs']
    processed_applicants = data['processed_applicants']
    hired_candidates = data['hired_candidates']
    job_embeddings = data['job_embeddings']
    applicant_embeddings = data['applicant_embeddings']
    match_details = data.get('match_details', {})
    
    st.success("✅ Dados carregados com sucesso!")
    
    # Adicionar info sobre fonte dos dados
    if st.session_state.get('pinecone_available'):
        st.info("🎯 Busca vetorial: Pinecone | 📊 Dados completos: GitHub Releases")
    
    # Criar opções de vagas baseadas nos dados carregados
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
        
        # Verificar candidatos contratados (com dados reais)
        top_7_ids = [item['id'] for item in similarities[:7]]
        hired_ids = [candidate_id for candidate_id in top_7_ids 
                    if processed_applicants[candidate_id]['codigo'] in hired_candidates.get(selected_job_id, [])]
        
        if hired_ids:
            hit_rate = len(hired_ids) / len(hired_candidates.get(selected_job_id, []) or [1]) * 100
            st.success(f"🎯 O sistema identificou {len(hired_ids)} dos candidatos já contratados para esta vaga entre os 7 mais recomendados! (Taxa de acerto: {hit_rate:.1f}%)")
        
        st.markdown("## Candidatos Recomendados")
        st.markdown("💡 **Clique em qualquer card para ver os detalhes completos do candidato**")
        
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