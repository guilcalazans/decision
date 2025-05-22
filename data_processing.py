"""
Sistema de Recomendação de Candidatos - Decision

Este script implementa um sistema que otimiza o processo de triagem de candidatos
usando técnicas de processamento de linguagem natural e machine learning.

Instruções:
1. Instale as dependências:
   pip install pandas numpy tqdm scikit-learn nltk spacy sentence-transformers
   python -m spacy download pt_core_news_sm
   
2. Execute este script:
   python decision_matcher_precisao.py

O script processará os dados em etapas e salvará resultados intermediários,
permitindo continuar de onde parou caso ocorra uma interrupção.
"""

import os
import pandas as pd
import numpy as np
import json
import re
import pickle
import string
from tqdm import tqdm
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import nltk
from nltk.tokenize import word_tokenize

# Criação de diretório para resultados intermediários
output_dir = "resultados_intermediarios"
os.makedirs(output_dir, exist_ok=True)

# ==== Configuração do NLTK e spaCy ====
print("Configurando NLTK e spaCy...")

# Baixar TODOS recursos NLTK para garantir precisão máxima
print("Baixando TODOS os recursos NLTK (isso pode demorar alguns minutos)...")
nltk.download('all')
print("Todos os recursos NLTK foram baixados com sucesso!")

# Carregar spaCy
try:
    import spacy
    try:
        nlp = spacy.load("pt_core_news_lg")
        print("Modelo spaCy 'pt_core_news_lg' carregado com sucesso!")
        spacy_available = True
    except:
        print("Modelo spaCy 'pt_core_news_lg' não disponível. Tentando modelo menor...")
        try:
            nlp = spacy.load("pt_core_news_sm")
            print("Modelo spaCy 'pt_core_news_sm' carregado com sucesso!")
            spacy_available = True
        except:
            print("Instalando modelo spaCy básico...")
            import os
            os.system("python -m spacy download pt_core_news_sm")
            nlp = spacy.load("pt_core_news_sm")
            spacy_available = True
            print("Modelo spaCy instalado e carregado com sucesso!")
except:
    print("Não foi possível carregar o spaCy. Continuando sem extração avançada.")
    spacy_available = False

# ==== Funções Utilitárias ====
def check_intermediate_file(filename):
    """Verifica se um arquivo intermediário existe"""
    return os.path.exists(os.path.join(output_dir, filename))

def save_intermediate(data, filename):
    """Salva resultados intermediários"""
    full_path = os.path.join(output_dir, filename)
    print(f"Salvando dados intermediários em {full_path}...")
    with open(full_path, 'wb') as f:
        pickle.dump(data, f)
    print(f"Dados salvos com sucesso!")

def load_intermediate(filename):
    """Carrega resultados intermediários"""
    full_path = os.path.join(output_dir, filename)
    print(f"Carregando dados intermediários de {full_path}...")
    with open(full_path, 'rb') as f:
        return pickle.load(f)

def load_local_json(file_path):
    """Carrega um arquivo JSON local"""
    print(f"Carregando dados de {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def clean_text(text):
    """Limpa o texto removendo caracteres especiais e padronizando"""
    if not isinstance(text, str):
        return ""
    # Converter para minúsculas
    text = text.lower()
    # Remover caracteres especiais e números
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\d+', ' ', text)
    # Remover espaços extras
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ==== Funções para Extração de Informações de Currículos ====
def extract_technical_skills(cv_text):
    """Extrai habilidades técnicas do CV usando palavras-chave comuns em TI."""
    if not isinstance(cv_text, str) or not cv_text:
        return []
    
    # Lista de palavras-chave técnicas comuns
    tech_keywords = [
        "python", "java", "javascript", "js", "c#", "c++", "php", "ruby", "go", "golang", "swift",
        "html", "css", "react", "angular", "vue", "node", "django", "flask", "laravel", "spring",
        "aws", "azure", "gcp", "cloud", "docker", "kubernetes", "k8s", "terraform", "ansible",
        "sql", "mysql", "postgresql", "mongodb", "oracle", "sql server", "nosql", "redis",
        "git", "jenkins", "cicd", "ci/cd", "devops", "agile", "scrum", "kanban",
        "machine learning", "ml", "ai", "data science", "big data", "hadoop", "spark",
        "excel", "power bi", "tableau", "data visualization", "análise de dados",
        "totvs", "sap", "erp", "crm", "navision", "dynamics", "salesforce",
        "linux", "windows", "unix", "bash", "shell", "powershell",
        "api", "rest", "soap", "microservices", "microsserviços", "web services",
        "ux", "ui", "user experience", "user interface", "figma", "sketch", "adobe xd",
        "jira", "confluence", "scrum", "gestão de projetos", "project management"
    ]
    
    # Tokenizar o texto usando o tokenizador do NLTK
    tokens = word_tokenize(cv_text.lower())
    
    # Encontrar correspondências
    found_skills = []
    for i in range(len(tokens)):
        for skill in tech_keywords:
            skill_tokens = skill.split()
            if len(skill_tokens) == 1:
                if tokens[i] == skill:
                    found_skills.append(skill)
            elif i + len(skill_tokens) <= len(tokens):
                potential_match = " ".join(tokens[i:i+len(skill_tokens)])
                if potential_match == skill:
                    found_skills.append(skill)
    
    # Contar ocorrências e retornar as mais frequentes
    skill_counter = Counter(found_skills)
    return [skill for skill, count in skill_counter.most_common(20)]

def extract_education_level(cv_text):
    """Tenta extrair o nível educacional do currículo."""
    if not cv_text:
        return ""
    
    # Palavras-chave para diferentes níveis educacionais
    education_keywords = {
        "doutorado": "Doutorado",
        "doutor": "Doutorado",
        "phd": "Doutorado",
        "mestrado": "Mestrado",
        "mestre": "Mestrado",
        "mba": "MBA/Especialização",
        "especialização": "MBA/Especialização",
        "pós-graduação": "MBA/Especialização",
        "graduação": "Ensino Superior Completo",
        "bacharel": "Ensino Superior Completo",
        "bacharelado": "Ensino Superior Completo",
        "licenciatura": "Ensino Superior Completo",
        "superior completo": "Ensino Superior Completo",
        "superior incompleto": "Ensino Superior Incompleto",
        "cursando": "Ensino Superior Incompleto",
        "técnico": "Ensino Técnico",
        "curso técnico": "Ensino Técnico",
        "ensino médio": "Ensino Médio"
    }
    
    cv_lower = cv_text.lower()
    
    # Verificar correspondências
    for keyword, level in education_keywords.items():
        if keyword in cv_lower:
            # Verificar se está "cursando" ou "incompleto"
            if level == "Ensino Superior Completo" and ("cursando" in cv_lower or "incompleto" in cv_lower):
                return "Ensino Superior Incompleto"
            return level
    
    # Padrão se nada for encontrado
    return ""

def extract_professional_level(cv_text, years_experience=None):
    """Tenta extrair o nível profissional com base no tempo de experiência."""
    if not cv_text:
        return ""
    
    cv_lower = cv_text.lower()
    
    # Verificar por palavras-chave diretas
    if "senior" in cv_lower or "sênior" in cv_lower:
        return "Sênior"
    elif "pleno" in cv_lower:
        return "Pleno"
    elif "junior" in cv_lower or "júnior" in cv_lower:
        return "Júnior"
    elif "estagiário" in cv_lower or "estagio" in cv_lower:
        return "Estágio"
    
    # Se temos o número de anos de experiência, podemos estimar
    if years_experience:
        if years_experience > 5:
            return "Sênior"
        elif years_experience > 2:
            return "Pleno"
        elif years_experience > 0:
            return "Júnior"
    
    # Tentativa de extrair experiência com base nos anos
    try:
        if spacy_available:
            doc = nlp(cv_text)
            # Olhar por padrões como "X anos de experiência"
            for sent in doc.sents:
                sent_text = sent.text.lower()
                if "anos" in sent_text and ("experiência" in sent_text or "experiencia" in sent_text):
                    # Extrair número antes de "anos"
                    matches = re.findall(r'(\d+)\s*anos', sent_text)
                    if matches:
                        years = int(matches[0])
                        if years > 5:
                            return "Sênior"
                        elif years > 2:
                            return "Pleno"
                        elif years > 0:
                            return "Júnior"
    except:
        pass
    
    # Padrão se nada for encontrado
    return ""

def extract_language_level(cv_text, language="inglês"):
    """Tenta extrair o nível de idioma do currículo."""
    if not cv_text:
        return ""
    
    cv_lower = cv_text.lower()
    language = language.lower()
    
    # Verificar se o idioma é mencionado
    if language not in cv_lower:
        return ""
    
    # Palavras-chave para diferentes níveis
    levels = {
        "fluente": "Fluente",
        "avançado": "Avançado",
        "intermediário": "Intermediário",
        "básico": "Básico",
        "beginner": "Básico",
        "basic": "Básico",
        "intermediate": "Intermediário",
        "advanced": "Avançado",
        "fluent": "Fluente",
        "proficient": "Fluente",
        "nativo": "Fluente",
        "native": "Fluente"
    }
    
    # Procurar por padrões como "inglês: avançado" ou "inglês avançado"
    for level_word, level_value in levels.items():
        pattern1 = f"{language}\\s*[:-]\\s*{level_word}"  # inglês: avançado
        pattern2 = f"{language}\\s+{level_word}"          # inglês avançado
        if re.search(pattern1, cv_lower) or re.search(pattern2, cv_lower):
            return level_value
    
    # Se menciona o idioma mas não especifica nível
    return "Mencionado (Nível não especificado)"

def extract_location(cv_text):
    """Tenta extrair a localização do candidato."""
    if not cv_text:
        return {}
    
    # Estados brasileiros para reconhecimento
    brazilian_states = {
        "AC": "Acre",
        "AL": "Alagoas",
        "AP": "Amapá",
        "AM": "Amazonas",
        "BA": "Bahia",
        "CE": "Ceará",
        "DF": "Distrito Federal",
        "ES": "Espírito Santo",
        "GO": "Goiás",
        "MA": "Maranhão",
        "MT": "Mato Grosso",
        "MS": "Mato Grosso do Sul",
        "MG": "Minas Gerais",
        "PA": "Pará",
        "PB": "Paraíba",
        "PR": "Paraná",
        "PE": "Pernambuco",
        "PI": "Piauí",
        "RJ": "Rio de Janeiro",
        "RN": "Rio Grande do Norte",
        "RS": "Rio Grande do Sul",
        "RO": "Rondônia",
        "RR": "Roraima",
        "SC": "Santa Catarina",
        "SP": "São Paulo",
        "SE": "Sergipe",
        "TO": "Tocantins"
    }
    
    result = {"cidade": "", "estado": "", "pais": "Brasil"}
    
    try:
        if spacy_available:
            doc = nlp(cv_text)
            for ent in doc.ents:
                if ent.label_ == "LOC":
                    # Verificar se é um estado
                    for state_abbr, state_name in brazilian_states.items():
                        if state_abbr.lower() == ent.text.lower() or state_name.lower() == ent.text.lower():
                            result["estado"] = state_name
                            break
                    # Se não for um estado, considerar como cidade
                    if not result["estado"] and len(ent.text) > 3:  # para evitar abreviações muito curtas
                        result["cidade"] = ent.text
    except:
        pass
    
    # Usar regex como backup
    if not result["estado"]:
        for state_abbr, state_name in brazilian_states.items():
            # Procurar pelo padrão "Cidade/SP" ou "Cidade - SP"
            pattern = r'(\w+)[\s\/\-]+' + state_abbr + r'(?!\w)'
            matches = re.findall(pattern, cv_text)
            if matches:
                result["cidade"] = matches[0]
                result["estado"] = state_name
                break
    
    return result

def extract_all_from_cv(cv_text):
    """Extrai todas as informações relevantes do currículo."""
    result = {
        "conhecimentos_tecnicos": extract_technical_skills(cv_text),
        "nivel_academico": extract_education_level(cv_text),
        "nivel_profissional": extract_professional_level(cv_text),
        "nivel_ingles": extract_language_level(cv_text, "inglês"),
        "nivel_espanhol": extract_language_level(cv_text, "espanhol"),
        "localizacao": extract_location(cv_text)
    }
    return result

# ==== Funções para Extração de Características de Vagas e Candidatos ====
def extract_job_features(job):
    """Extrai características importantes da vaga"""
    features = {}
    
    # Informações básicas
    basic_info = job.get('informacoes_basicas', {})
    features['titulo'] = clean_text(basic_info.get('titulo_vaga', ''))
    features['empresa'] = clean_text(basic_info.get('empresa_divisao', ''))
    features['tipo_contratacao'] = clean_text(basic_info.get('tipo_contratacao', ''))
    features['cliente'] = clean_text(basic_info.get('cliente', ''))
    
    # Perfil da vaga
    job_profile = job.get('perfil_vaga', {})
    features['pais'] = clean_text(job_profile.get('pais', ''))
    features['estado'] = clean_text(job_profile.get('estado', ''))
    features['cidade'] = clean_text(job_profile.get('cidade', ''))
    features['localizacao'] = f"{features['cidade']} {features['estado']} {features['pais']}"
    features['nivel_profissional'] = clean_text(job_profile.get('nivel profissional', ''))
    features['nivel_academico'] = clean_text(job_profile.get('nivel_academico', ''))
    features['nivel_ingles'] = clean_text(job_profile.get('nivel_ingles', ''))
    features['nivel_espanhol'] = clean_text(job_profile.get('nivel_espanhol', ''))
    features['areas_atuacao'] = clean_text(job_profile.get('areas_atuacao', ''))
    features['principais_atividades'] = clean_text(job_profile.get('principais_atividades', ''))
    features['competencias'] = clean_text(job_profile.get('competencia_tecnicas_e_comportamentais', ''))
    
    # Extrair palavras-chave das competências e atividades
    features['keywords'] = []
    if features['competencias']:
        features['keywords'].extend(extract_technical_skills(features['competencias']))
    if features['principais_atividades']:
        features['keywords'].extend(extract_technical_skills(features['principais_atividades']))
    
    # Remover duplicatas
    features['keywords'] = list(set(features['keywords']))
    
    # Combinando todas as características em um texto único para embedding
    all_text = f"{features['titulo']} {features['empresa']} {features['cliente']} {features['nivel_profissional']} {features['nivel_academico']} {features['nivel_ingles']} {features['nivel_espanhol']} {features['areas_atuacao']} {features['principais_atividades']} {features['competencias']}"
    
    features['full_text'] = all_text
    
    return features

def extract_applicant_features(applicant):
    """Extrai características importantes do candidato"""
    features = {}
    
    # Informações básicas
    basic_info = applicant.get('infos_basicas', {})
    features['nome'] = basic_info.get('nome', '')
    features['codigo'] = basic_info.get('codigo_profissional', '')
    features['email'] = basic_info.get('email', '')
    features['telefone'] = basic_info.get('telefone', '')
    
    # Currículo completo
    cv_pt = applicant.get('cv_pt', '')
    cv_en = applicant.get('cv_en', '')
    features['cv'] = cv_pt if cv_pt else cv_en
    
    # Informações profissionais
    prof_info = applicant.get('informacoes_profissionais', {})
    features['titulo_profissional'] = clean_text(prof_info.get('titulo_profissional', ''))
    features['area_atuacao'] = clean_text(prof_info.get('area_atuacao', ''))
    features['conhecimentos_tecnicos'] = clean_text(prof_info.get('conhecimentos_tecnicos', ''))
    features['nivel_profissional'] = clean_text(prof_info.get('nivel_profissional', ''))
    
    # Formação e idiomas
    education = applicant.get('formacao_e_idiomas', {})
    features['nivel_academico'] = clean_text(education.get('nivel_academico', ''))
    features['nivel_ingles'] = clean_text(education.get('nivel_ingles', ''))
    features['nivel_espanhol'] = clean_text(education.get('nivel_espanhol', ''))
    
    # Extração de informações do currículo quando os campos estão vazios
    cv_info = extract_all_from_cv(features['cv'])
    
    # Atualizar informações com dados extraídos do currículo (apenas se os campos atuais estiverem vazios)
    if not features['conhecimentos_tecnicos'] and cv_info['conhecimentos_tecnicos']:
        features['conhecimentos_tecnicos_extraidos'] = ", ".join(cv_info['conhecimentos_tecnicos'])
        features['conhecimentos_tecnicos'] = features['conhecimentos_tecnicos_extraidos']
    else:
        features['conhecimentos_tecnicos_extraidos'] = ""
    
    if not features['nivel_academico'] and cv_info['nivel_academico']:
        features['nivel_academico_extraido'] = cv_info['nivel_academico']
        features['nivel_academico'] = features['nivel_academico_extraido']
    else:
        features['nivel_academico_extraido'] = ""
    
    if not features['nivel_profissional'] and cv_info['nivel_profissional']:
        features['nivel_profissional_extraido'] = cv_info['nivel_profissional']
        features['nivel_profissional'] = features['nivel_profissional_extraido']
    else:
        features['nivel_profissional_extraido'] = ""
    
    if not features['nivel_ingles'] and cv_info['nivel_ingles']:
        features['nivel_ingles_extraido'] = cv_info['nivel_ingles']
        features['nivel_ingles'] = features['nivel_ingles_extraido']
    else:
        features['nivel_ingles_extraido'] = ""
    
    if not features['nivel_espanhol'] and cv_info['nivel_espanhol']:
        features['nivel_espanhol_extraido'] = cv_info['nivel_espanhol']
        features['nivel_espanhol'] = features['nivel_espanhol_extraido']
    else:
        features['nivel_espanhol_extraido'] = ""
    
    # Localização
    info_pessoais = applicant.get('informacoes_pessoais', {})
    endereco = clean_text(info_pessoais.get('endereco', ''))
    
    if not endereco and cv_info['localizacao']:
        features['cidade'] = cv_info['localizacao'].get('cidade', '')
        features['estado'] = cv_info['localizacao'].get('estado', '')
        features['pais'] = cv_info['localizacao'].get('pais', 'Brasil')
    else:
        features['cidade'] = ''
        features['estado'] = ''
        features['pais'] = 'Brasil'
    
    features['localizacao'] = f"{features['cidade']} {features['estado']} {features['pais']}"
    
    # Armazenar as keywords extraídas para uso posterior
    features['keywords'] = cv_info['conhecimentos_tecnicos']
    
    # Combinando todas as características em um texto único para embedding
    all_text = f"{features['titulo_profissional']} {features['area_atuacao']} {features['conhecimentos_tecnicos']} {features['nivel_profissional']} {features['nivel_academico']} {features['nivel_ingles']} {features['nivel_espanhol']} {features['cv']}"
    
    features['full_text'] = all_text
    
    return features

# ==== Funções para Cálculo de Similaridade ====
def calculate_keyword_similarity(job_keywords, applicant_keywords):
    """Calcula a similaridade com base em palavras-chave compartilhadas."""
    if not job_keywords or not applicant_keywords:
        return 0.0
    
    job_keywords_set = set(job_keywords)
    applicant_keywords_set = set(applicant_keywords)
    
    # Calcular interseção
    common_keywords = job_keywords_set.intersection(applicant_keywords_set)
    
    # Calcular coeficiente de Jaccard
    if len(job_keywords_set) + len(applicant_keywords_set) == 0:
        return 0.0
    
    return len(common_keywords) / len(job_keywords_set) if len(job_keywords_set) > 0 else 0.0

def calculate_location_similarity(job_location, applicant_location):
    """Calcula a similaridade de localização."""
    # Extrair cidade, estado, país
    job_city = job_location.get('cidade', '').lower()
    job_state = job_location.get('estado', '').lower()
    job_country = job_location.get('pais', '').lower()
    
    app_city = applicant_location.get('cidade', '').lower()
    app_state = applicant_location.get('estado', '').lower()
    app_country = applicant_location.get('pais', '').lower()
    
    # Calcular pontuação (mesma cidade: 1.0, mesmo estado: 0.7, mesmo país: 0.3)
    if job_city and app_city and job_city == app_city:
        return 1.0
    elif job_state and app_state and job_state == app_state:
        return 0.7
    elif job_country and app_country and job_country == app_country:
        return 0.3
    else:
        return 0.0

def calculate_level_similarity(job_level, applicant_level):
    """Calcula a similaridade entre níveis profissionais."""
    # Definir níveis em ordem crescente
    levels = ["estagio", "estágio", "junior", "júnior", "pleno", "senior", "sênior"]
    
    # Normalizar níveis
    job_level = job_level.lower().strip()
    applicant_level = applicant_level.lower().strip()
    
    # Se ambos são iguais
    if job_level == applicant_level:
        return 1.0
    
    # Se algum está vazio
    if not job_level or not applicant_level:
        return 0.5
    
    # Encontrar índices nos níveis
    job_index = -1
    app_index = -1
    
    for i, level in enumerate(levels):
        if level in job_level:
            job_index = i
        if level in applicant_level:
            app_index = i
    
    # Se não encontrou algum dos níveis
    if job_index == -1 or app_index == -1:
        return 0.5
    
    # Se o candidato tem nível maior ou igual ao requerido
    if app_index >= job_index:
        return 1.0
    else:
        # Calcular distância entre níveis
        diff = job_index - app_index
        max_diff = len(levels) - 1
        return 1.0 - (diff / max_diff)

def calculate_detailed_match_score(job, applicant):
    """Calcula uma pontuação detalhada de compatibilidade entre vaga e candidato."""
    
    # Componentes do score
    scores = {
        "semantic": 0.0,         # Similaridade semântica via embeddings
        "keywords": 0.0,         # Match de palavras-chave técnicas
        "location": 0.0,         # Compatibilidade geográfica
        "professional_level": 0.0, # Compatibilidade de nível profissional
        "academic_level": 0.0,   # Compatibilidade de formação acadêmica
        "english_level": 0.0,    # Compatibilidade de inglês
        "spanish_level": 0.0     # Compatibilidade de espanhol
    }
    
    # Calcular score de keywords (habilidades técnicas)
    if 'keywords' in job and 'keywords' in applicant:
        scores["keywords"] = calculate_keyword_similarity(job.get('keywords', []), 
                                                         applicant.get('keywords', []))
    
    # Calcular score de localização
    job_location = {
        "cidade": job.get('cidade', ''),
        "estado": job.get('estado', ''),
        "pais": job.get('pais', '')
    }
    
    applicant_location = {
        "cidade": applicant.get('cidade', ''),
        "estado": applicant.get('estado', ''),
        "pais": applicant.get('pais', '')
    }
    
    scores["location"] = calculate_location_similarity(job_location, applicant_location)
    
    # Calcular score de nível profissional
    scores["professional_level"] = calculate_level_similarity(
        job.get('nivel_profissional', ''), 
        applicant.get('nivel_profissional', '')
    )
    
    # Calcular score acadêmico (se informações disponíveis)
    if job.get('nivel_academico', '') and applicant.get('nivel_academico', ''):
        if job['nivel_academico'].lower() in applicant['nivel_academico'].lower():
            scores["academic_level"] = 1.0
        else:
            scores["academic_level"] = 0.5
    else:
        scores["academic_level"] = 0.5
    
    # Calcular score de inglês
    if job.get('nivel_ingles', '') and applicant.get('nivel_ingles', ''):
        if job['nivel_ingles'].lower() in applicant['nivel_ingles'].lower():
            scores["english_level"] = 1.0
        else:
            scores["english_level"] = 0.5
    else:
        scores["english_level"] = 0.5
    
    # Calcular score de espanhol
    if job.get('nivel_espanhol', '') and applicant.get('nivel_espanhol', ''):
        if job['nivel_espanhol'].lower() in applicant['nivel_espanhol'].lower():
            scores["spanish_level"] = 1.0
        else:
            scores["spanish_level"] = 0.5
    else:
        scores["spanish_level"] = 0.5
    
    return scores

# ==== Processamento Principal ====
def main():
    print("Decision Matcher - Sistema de Recomendação de Candidatos")
    print("="*70)
    
    # Caminhos dos arquivos locais - ajuste conforme necessário
    vagas_path = r"C:\Users\glynd\decision-recruiter\bases\vagas.json"
    applicants_path = r"C:\Users\glynd\decision-recruiter\bases\applicants.json"
    prospects_path = r"C:\Users\glynd\decision-recruiter\bases\prospects.json"
    
    # ==== ETAPA 1: Carregamento dos dados ====
    # Verificar se os dados já foram carregados anteriormente
    if check_intermediate_file("raw_data.pkl"):
        print("Carregando dados brutos de arquivo intermediário...")
        raw_data = load_intermediate("raw_data.pkl")
        vagas = raw_data['vagas']
        applicants = raw_data['applicants']
        prospects = raw_data['prospects']
    else:
        # Carregar os dados dos arquivos locais
        vagas = load_local_json(vagas_path)
        applicants = load_local_json(applicants_path)
        prospects = load_local_json(prospects_path)
        
        # Salvar dados brutos para uso futuro
        raw_data = {
            'vagas': vagas,
            'applicants': applicants,
            'prospects': prospects
        }
        save_intermediate(raw_data, "raw_data.pkl")

    print(f"Número de vagas: {len(vagas)}")
    print(f"Número de candidatos: {len(applicants)}")
    print(f"Número de prospectos: {len(prospects)}")
    
    # ==== ETAPA 2: Processamento de vagas ====
    # Processar vagas
    if check_intermediate_file("processed_jobs.pkl"):
        print("Carregando vagas processadas do arquivo intermediário...")
        processed_jobs = load_intermediate("processed_jobs.pkl")
    else:
        print("Processamento de vagas iniciando...")
        processed_jobs = {}
        for i, (job_id, job) in enumerate(tqdm(vagas.items(), desc="Processando vagas")):
            try:
                processed_jobs[job_id] = extract_job_features(job)
                
                # Salvar resultados parciais a cada 1000 vagas
                if (i + 1) % 1000 == 0:
                    print(f"Salvando resultados parciais após processar {i + 1} vagas...")
                    save_intermediate(processed_jobs, f"processed_jobs_partial_{i+1}.pkl")
                    
            except Exception as e:
                print(f"Erro ao processar vaga {job_id}: {str(e)}")
                # Continue com a próxima vaga
                continue
        
        # Salvar resultados finais
        save_intermediate(processed_jobs, "processed_jobs.pkl")

    print(f"Total de vagas processadas: {len(processed_jobs)}")
    
    # ==== ETAPA 3: Processamento de candidatos ====
    # Processar candidatos
    if check_intermediate_file("processed_applicants.pkl"):
        print("Carregando candidatos processados do arquivo intermediário...")
        processed_applicants = load_intermediate("processed_applicants.pkl")
    else:
        print("Processamento de candidatos iniciando...")
        processed_applicants = {}
        # Processar em lotes para facilitar o monitoramento e reduzir o uso de memória
        batch_size = 1000
        applicant_ids = list(applicants.keys())
        batches = [applicant_ids[i:i + batch_size] for i in range(0, len(applicant_ids), batch_size)]
        
        for batch_idx, batch in enumerate(batches):
            print(f"Processando lote {batch_idx+1}/{len(batches)} de candidatos...")
            for i, applicant_id in enumerate(tqdm(batch, desc=f"Lote {batch_idx+1}")):
                try:
                    processed_applicants[applicant_id] = extract_applicant_features(applicants[applicant_id])
                except Exception as e:
                    print(f"Erro ao processar candidato {applicant_id}: {str(e)}")
                    # Continue com o próximo candidato
                    continue
                
                # Mostrar progresso a cada 100 candidatos
                if (i + 1) % 100 == 0:
                    print(f"  Processados {i+1}/{len(batch)} candidatos deste lote")
            
            # Salvar resultados intermediários a cada lote
            save_intermediate(processed_applicants, f"processed_applicants_temp_{batch_idx}.pkl")
        
        # Salvar resultados intermediários finais
        save_intermediate(processed_applicants, "processed_applicants.pkl")

    print(f"Total de candidatos processados: {len(processed_applicants)}")
    
    # ==== ETAPA 4: Identificação de candidatos já contratados ====
    # Identificar candidatos já contratados
    if check_intermediate_file("hired_candidates.pkl"):
        print("Carregando candidatos contratados do arquivo intermediário...")
        hired_candidates = load_intermediate("hired_candidates.pkl")
    else:
        print("Identificando candidatos já contratados...")
        hired_candidates = {}
        for prospect_id, prospect_data in tqdm(prospects.items(), desc="Processando prospectos"):
            job_id = prospect_id
            hired_candidates[job_id] = []
            
            for prospect in prospect_data.get('prospects', []):
                if prospect.get('situacao_candidado') == 'Contratado pela Decision':
                    hired_candidates[job_id].append(prospect.get('codigo', ''))
        
        # Salvar resultados intermediários
        save_intermediate(hired_candidates, "hired_candidates.pkl")

    # Contagem de vagas com candidatos contratados
    vagas_com_contratados = sum(1 for job_id, candidates in hired_candidates.items() if candidates)
    print(f"Vagas com candidatos contratados: {vagas_com_contratados} de {len(hired_candidates)}")
    
    # ==== ETAPA 5: Geração de embeddings ====
    # Importar SentenceTransformer se ainda não foi importado
    try:
        from sentence_transformers import SentenceTransformer
        print("Biblioteca SentenceTransformer importada com sucesso!")
    except ImportError:
        print("ERRO: Biblioteca SentenceTransformer não encontrada.")
        print("Por favor, instale com: pip install sentence-transformers")
        return
    
    # Gerar embeddings para vagas
    if check_intermediate_file("job_embeddings.pkl"):
        print("Carregando embeddings de vagas do arquivo intermediário...")
        job_embeddings = load_intermediate("job_embeddings.pkl")
    else:
        # Carregar o modelo de embeddings
        print("Carregando modelo de embeddings...")
        model = SentenceTransformer('distiluse-base-multilingual-cased-v1')
        
        # Criar embeddings para vagas
        print("Gerando embeddings para vagas...")
        job_embeddings = {}
        
        # Processar em lotes para economia de memória
        batch_size = 100
        job_ids = list(processed_jobs.keys())
        job_batches = [job_ids[i:i + batch_size] for i in range(0, len(job_ids), batch_size)]
        
        for batch_idx, batch in enumerate(tqdm(job_batches, desc="Processando lotes de vagas")):
            # Preparar textos para o lote
            texts = [processed_jobs[job_id]['full_text'] for job_id in batch]
            # Codificar em lote
            embeddings = model.encode(texts)
            
            # Armazenar embeddings
            for i, job_id in enumerate(batch):
                job_embeddings[job_id] = embeddings[i]
                
            # Salvar resultados intermediários a cada 5 lotes
            if (batch_idx + 1) % 5 == 0:
                save_intermediate(job_embeddings, f"job_embeddings_temp_{batch_idx}.pkl")
        
        # Salvar resultados intermediários
        save_intermediate(job_embeddings, "job_embeddings.pkl")

    print(f"Total de embeddings de vagas: {len(job_embeddings)}")
    
    # Gerar embeddings para candidatos
    if check_intermediate_file("applicant_embeddings.pkl"):
        print("Carregando embeddings de candidatos do arquivo intermediário...")
        applicant_embeddings = load_intermediate("applicant_embeddings.pkl")
    else:
        # Verificar se o modelo já foi carregado
        if 'model' not in locals():
            print("Carregando modelo de embeddings...")
            model = SentenceTransformer('distiluse-base-multilingual-cased-v1')
        
        print("Gerando embeddings para candidatos...")
        applicant_embeddings = {}
        batch_size = 100
        applicant_ids = list(processed_applicants.keys())
        batches = [applicant_ids[i:i + batch_size] for i in range(0, len(applicant_ids), batch_size)]
        
        for batch_idx, batch in enumerate(batches):
            print(f"Processando lote {batch_idx+1}/{len(batches)} de candidatos para embeddings...")
            texts = [processed_applicants[applicant_id]['full_text'] for applicant_id in batch]
            embeddings = model.encode(texts)
            
            for i, applicant_id in enumerate(batch):
                applicant_embeddings[applicant_id] = embeddings[i]
            
            # Salvar resultados intermediários a cada 10 lotes
            if (batch_idx + 1) % 10 == 0:
                save_intermediate(applicant_embeddings, f"applicant_embeddings_temp_{batch_idx}.pkl")
        
        # Salvar resultados finais
        save_intermediate(applicant_embeddings, "applicant_embeddings.pkl")

    print(f"Total de embeddings de candidatos: {len(applicant_embeddings)}")
    print("Embeddings gerados com sucesso!")
    
    # ==== ETAPA 6: Cálculo de similaridade entre vagas e candidatos ====
    # Esta é a etapa que estava consumindo muita memória no Colab
    # Vamos torná-la mais eficiente processando uma vaga por vez e salvando regularmente
    
    if check_intermediate_file("match_details_full.pkl"):
        print("Carregando detalhes de match do arquivo intermediário...")
        match_details = load_intermediate("match_details_full.pkl")
    else:
        # Verificar se já existe um arquivo parcial
        if check_intermediate_file("match_details_partial.pkl"):
            print("Carregando detalhes de match parciais...")
            match_details = load_intermediate("match_details_partial.pkl")
            # Identificar vagas que já foram processadas
            processed_job_ids = set(match_details.keys())
            remaining_job_ids = [job_id for job_id in processed_jobs.keys() if job_id not in processed_job_ids]
            print(f"Continuando de onde parou: {len(processed_job_ids)} vagas processadas, {len(remaining_job_ids)} restantes")
        else:
            print("Iniciando cálculo de detalhes de match do zero...")
            match_details = {}
            remaining_job_ids = list(processed_jobs.keys())
        
        # Processar cada vaga individualmente para economizar memória
        for job_idx, job_id in enumerate(tqdm(remaining_job_ids, desc="Calculando matches por vaga")):
            try:
                job_features = processed_jobs[job_id]
                job_vector = job_embeddings[job_id]
                match_details[job_id] = {}
                
                # Para fins de demonstração, vamos calcular similaridade para apenas um subconjunto de candidatos
                # para vagas com muitos candidatos potenciais
                # Em uma implementação completa, você pode adaptar isso conforme necessário
                
                # Calcular similaridade de cosseno do vetor da vaga com todos os candidatos
                all_similarities = {}
                for applicant_id, applicant_vector in applicant_embeddings.items():
                    # Similaridade de cosseno entre vetores de embedding
                    similarity = np.dot(job_vector, applicant_vector) / (
                        np.linalg.norm(job_vector) * np.linalg.norm(applicant_vector)
                    )
                    all_similarities[applicant_id] = similarity
                
                # Pegar os top 1000 candidatos com maior similaridade de vetores
                top_candidates = sorted(all_similarities.items(), key=lambda x: x[1], reverse=True)[:1000]
                
                # Calcular detalhes de match apenas para os top candidatos para economizar memória
                for applicant_id, similarity in tqdm(top_candidates, desc=f"Vaga {job_id}", leave=False):
                    applicant_features = processed_applicants[applicant_id]
                    
                    # Calcular scores detalhados
                    detail_scores = calculate_detailed_match_score(job_features, applicant_features)
                    
                    # Adicionar similaridade semântica ao score
                    detail_scores["semantic"] = similarity
                    
                    # Calcular média ponderada para score final
                    weights = {
                        "semantic": 0.4,
                        "keywords": 0.2,
                        "location": 0.1,
                        "professional_level": 0.1,
                        "academic_level": 0.1,
                        "english_level": 0.05,
                        "spanish_level": 0.05
                    }
                    
                    final_score = sum(score * weights[key] for key, score in detail_scores.items())
                    detail_scores["final_score"] = final_score
                    
                    match_details[job_id][applicant_id] = detail_scores
                
                # Salvar resultados parciais a cada 10 vagas ou na última vaga
                if (job_idx + 1) % 10 == 0 or job_idx == len(remaining_job_ids) - 1:
                    save_intermediate(match_details, "match_details_partial.pkl")
                    print(f"Salvos detalhes parciais após processar {job_idx + 1} vagas")
            
            except Exception as e:
                print(f"Erro ao calcular matches para vaga {job_id}: {str(e)}")
                # Continue com a próxima vaga
                continue
        
        # Salvar resultados finais
        save_intermediate(match_details, "match_details_full.pkl")
    
    # ==== ETAPA 7: Combinar Todos os Dados para Uso Posterior ====
    print("Salvando os dados processados, embeddings e detalhes de match...")
    data_to_save = {
        'processed_jobs': processed_jobs,
        'processed_applicants': processed_applicants,
        'hired_candidates': hired_candidates,
        'job_embeddings': job_embeddings,
        'applicant_embeddings': applicant_embeddings,
        'match_details': match_details
    }

    with open('decision_embeddings_enhanced_precisao.pkl', 'wb') as f:
        pickle.dump(data_to_save, f)

    print("Dados salvos com sucesso em 'decision_embeddings_enhanced_precisao.pkl'")
    print("Processamento concluído com sucesso!")
    
    # ==== ETAPA 8: Demonstração - Mostrar Candidatos Recomendados para uma Vaga ====
    # Como exemplo, vamos selecionar uma vaga aleatória e mostrar os top 7 candidatos
    import random
    
    # Escolher uma vaga aleatória que tenha candidatos contratados (para comparação)
    vagas_com_contratados = [job_id for job_id, candidates in hired_candidates.items() if candidates]
    
    if vagas_com_contratados:
        example_job_id = random.choice(vagas_com_contratados)
        
        print("\n" + "="*70)
        print(f"DEMONSTRAÇÃO - Recomendação para Vaga: {example_job_id}")
        print("="*70)
        
        # Mostrar detalhes da vaga
        job = vagas[example_job_id]
        job_features = processed_jobs[example_job_id]
        
        print(f"Título: {job['informacoes_basicas'].get('titulo_vaga', 'N/A')}")
        print(f"Cliente: {job['informacoes_basicas'].get('cliente', 'N/A')}")
        print(f"Localização: {job_features['cidade']}, {job_features['estado']}")
        print(f"Nível: {job_features['nivel_profissional']}")
        
        # Mostrar candidatos já contratados para esta vaga
        hired_ids = hired_candidates.get(example_job_id, [])
        print(f"\nCandidatos já contratados para esta vaga: {len(hired_ids)}")
        for hired_id in hired_ids:
            if hired_id in applicants:
                print(f"  - {applicants[hired_id]['infos_basicas'].get('nome', 'N/A')}")
        
        # Obter os matches para esta vaga
        job_matches = match_details.get(example_job_id, {})
        if job_matches:
            # Ordenar candidatos por score final
            ranked_candidates = sorted(job_matches.items(), key=lambda x: x[1]["final_score"], reverse=True)
            
            print(f"\nTop 7 Candidatos Recomendados:")
            for i, (candidate_id, scores) in enumerate(ranked_candidates[:7]):
                candidate = applicants[candidate_id]
                print(f"\n{i+1}. {candidate['infos_basicas'].get('nome', 'N/A')}")
                print(f"   Score Final: {scores['final_score']:.2f}")
                print(f"   Similaridade Semântica: {scores['semantic']:.2f}")
                print(f"   Match Keywords: {scores['keywords']:.2f}")
                print(f"   Match Localização: {scores['location']:.2f}")
                print(f"   Match Nível Profissional: {scores['professional_level']:.2f}")
                
                # Verificar se este candidato já foi contratado para esta vaga
                if candidate_id in hired_ids:
                    print(f"   ** CANDIDATO JÁ CONTRATADO PARA ESTA VAGA! **")
        else:
            print("\nNenhum match encontrado para esta vaga.")
    else:
        print("\nNenhuma vaga com candidatos contratados encontrada para demonstração.")

# Ponto de entrada principal
if __name__ == "__main__":
    main()