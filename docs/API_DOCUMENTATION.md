# API Documentation - Decision Recruiter

Esta documentação descreve a arquitetura interna, funções principais e fluxos de dados do sistema Decision Recruiter.

## Arquitetura do Sistema

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │◄──►│  Core Functions  │◄──►│  Data Sources   │
│                 │    │                  │    │                 │
│ • Interface     │    │ • Similarity     │    │ • vagas.json    │
│ • Visualização  │    │ • Embeddings     │    │ • applicants.json│
│ • Interação     │    │ • Ranking        │    │ • prospects.json│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   ML Pipeline    │
                    │                  │
                    │ • NLP Processing │
                    │ • Feature Extract│
                    │ • Scoring        │
                    └──────────────────┘
```

## Módulos Principais

### 1. Data Processing (`data_processing.py`)

Responsável pelo pipeline completo de processamento de dados.

#### Funções Principais

##### `load_local_json(file_path)`
```python
def load_local_json(file_path):
    """Carrega um arquivo JSON local"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
```

##### `extract_job_features(job)`
```python
def extract_job_features(job):
    """Extrai características importantes da vaga
    
    Args:
        job (dict): Dados brutos da vaga
        
    Returns:
        dict: Features estruturadas da vaga
    """
    features = {
        'titulo': clean_text(job['informacoes_basicas']['titulo_vaga']),
        'cliente': clean_text(job['informacoes_basicas']['cliente']),
        'nivel_profissional': clean_text(job['perfil_vaga']['nivel profissional']),
        'keywords': extract_technical_skills(job['perfil_vaga']['competencia_tecnicas_e_comportamentais']),
        'full_text': combined_text
    }
    return features
```

##### `extract_applicant_features(applicant)`
```python
def extract_applicant_features(applicant):
    """Extrai características importantes do candidato
    
    Args:
        applicant (dict): Dados brutos do candidato
        
    Returns:
        dict: Features estruturadas do candidato
    """
    features = {
        'nome': applicant['infos_basicas']['nome'],
        'cv': applicant.get('cv_pt', ''),
        'keywords': extract_technical_skills(features['cv']),
        'nivel_profissional': extract_professional_level(features['cv']),
        'full_text': combined_text
    }
    return features
```

#### Pipeline de Processamento

```python
def main():
    """Pipeline principal de processamento"""
    # 1. Carregamento dos dados
    vagas = load_local_json("vagas.json")
    applicants = load_local_json("applicants.json")
    prospects = load_local_json("prospects.json")
    
    # 2. Processamento de features
    processed_jobs = {id: extract_job_features(job) for id, job in vagas.items()}
    processed_applicants = {id: extract_applicant_features(app) for id, app in applicants.items()}
    
    # 3. Geração de embeddings
    model = SentenceTransformer('distiluse-base-multilingual-cased-v1')
    job_embeddings = {id: model.encode(job['full_text']) for id, job in processed_jobs.items()}
    applicant_embeddings = {id: model.encode(app['full_text']) for id, app in processed_applicants.items()}
    
    # 4. Cálculo de similaridades
    match_details = calculate_all_similarities(processed_jobs, processed_applicants, job_embeddings, applicant_embeddings)
    
    # 5. Salvamento dos resultados
    save_processed_data(processed_jobs, processed_applicants, job_embeddings, applicant_embeddings, match_details)
```

### 2. Streamlit App (`app.py`)

Interface principal do usuário.

#### Funções de Interface

##### `render_header()`
```python
def render_header():
    """Renderiza o cabeçalho personalizado da aplicação"""
    st.markdown("""
    <div class="header">
        <h1>Decision Recruiter</h1>
        <p>Sistema de Recomendação de Candidatos</p>
    </div>
    """, unsafe_allow_html=True)
```

##### `calculate_similarity(job_id, applicant_id, ...)`
```python
def calculate_similarity(job_id, applicant_id, job_embeddings, applicant_embeddings, match_details, processed_jobs, processed_applicants):
    """Calcula similaridade entre vaga e candidato
    
    Args:
        job_id (str): ID da vaga
        applicant_id (str): ID do candidato
        job_embeddings (dict): Embeddings das vagas
        applicant_embeddings (dict): Embeddings dos candidatos
        match_details (dict): Detalhes pré-calculados
        processed_jobs (dict): Jobs processados
        processed_applicants (dict): Candidatos processados
        
    Returns:
        dict: {
            'score': float,      # Score final (0-1)
            'details': dict      # Breakdown dos scores
        }
    """
    # Similaridade semântica
    cos_sim = util.cos_sim(job_embeddings[job_id], applicant_embeddings[applicant_id]).item()
    
    # Recuperar ou calcular outros scores
    details = match_details.get(job_id, {}).get(applicant_id, {})
    details['semantic'] = cos_sim
    
    # Score ponderado final
    weighted_score = (
        cos_sim * 0.40 +
        details.get('keywords', 0) * 0.30 +
        details.get('location', 0) * 0.05 +
        details.get('professional_level', 0) * 0.10 +
        details.get('academic_level', 0) * 0.10 +
        details.get('english_level', 0) * 0.025 +
        details.get('spanish_level', 0) * 0.025
    )
    
    return {'score': weighted_score, 'details': details}
```

#### Funções de Visualização

##### `render_radar_chart(match_details)`
```python
def render_radar_chart(match_details):
    """Renderiza gráfico radar para scores de match
    
    Args:
        match_details (dict): Detalhes do match
        
    Returns:
        plotly.graph_objects.Figure: Gráfico radar configurado
    """
    categories = ['Semântica', 'Palavras-chave', 'Localização', 'Nível Prof.', 'Nível Acad.', 'Inglês', 'Espanhol']
    values = [match_details.get(key, 0) * 100 for key in ['semantic', 'keywords', 'location', 'professional_level', 'academic_level', 'english_level', 'spanish_level']]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself'))
    # ... configurações do layout
    return fig
```

##### `render_candidate_details(candidate, selected_job)`
```python
def render_candidate_details(candidate, selected_job):
    """Renderiza detalhes completos do candidato
    
    Args:
        candidate (dict): Dados do candidato selecionado
        selected_job (dict): Dados da vaga selecionada
    """
    # Criar tabs para diferentes visualizações
    tab1, tab2, tab3 = st.tabs(["Perfil", "Currículo", "Compatibilidade"])
    
    with tab1:
        # Informações pessoais e profissionais
        col1, col2, col3 = st.columns(3)
        # ... renderização dos dados
        
    with tab2:
        # Preview e download do currículo
        # ... funcionalidades de CV
        
    with tab3:
        # Gráficos e métricas detalhadas
        # ... visualizações de compatibilidade
```

## Algoritmos de Machine Learning

### 1. Extração de Features via NLP

#### Habilidades Técnicas
```python
def extract_technical_skills(cv_text):
    """Extrai habilidades técnicas usando palavras-chave e NLP
    
    Args:
        cv_text (str): Texto do currículo
        
    Returns:
        list: Lista de habilidades encontradas
    """
    tech_keywords = [
        "python", "java", "javascript", "sql", "aws", "docker",
        "machine learning", "react", "angular", "kubernetes"
        # ... lista completa
    ]
    
    # Tokenização com NLTK
    tokens = word_tokenize(cv_text.lower())
    
    # Encontrar correspondências
    found_skills = []
    for i in range(len(tokens)):
        for skill in tech_keywords:
            if skill in " ".join(tokens[i:i+len(skill.split())]):
                found_skills.append(skill)
    
    return list(set(found_skills))
```

#### Extração de Níveis
```python
def extract_professional_level(cv_text):
    """Extrai nível profissional do CV
    
    Args:
        cv_text (str): Texto do currículo
        
    Returns:
        str: Nível profissional identificado
    """
    cv_lower = cv_text.lower()
    
    # Palavras-chave diretas
    if "senior" in cv_lower or "sênior" in cv_lower:
        return "Sênior"
    elif "pleno" in cv_lower:
        return "Pleno"
    elif "junior" in cv_lower or "júnior" in cv_lower:
        return "Júnior"
    
    # Análise de experiência via spaCy
    if spacy_available:
        doc = nlp(cv_text)
        for sent in doc.sents:
            # Buscar padrões como "X anos de experiência"
            if re.search(r'(\d+)\s*anos.*experiên', sent.text.lower()):
                years = int(re.findall(r'(\d+)\s*anos', sent.text.lower())[0])
                if years > 5: return "Sênior"
                elif years > 2: return "Pleno"
                else: return "Júnior"
    
    return ""
```

### 2. Sistema de Scoring

#### Score de Palavras-chave
```python
def calculate_keyword_similarity(job_keywords, applicant_keywords):
    """Calcula similaridade baseada em palavras-chave compartilhadas
    
    Args:
        job_keywords (list): Keywords da vaga
        applicant_keywords (list): Keywords do candidato
        
    Returns:
        float: Score de 0 a 1
    """
    if not job_keywords or not applicant_keywords:
        return 0.0
    
    job_set = set(job_keywords)
    applicant_set = set(applicant_keywords)
    
    # Coeficiente de Jaccard
    intersection = len(job_set.intersection(applicant_set))
    union = len(job_set.union(applicant_set))
    
    return intersection / union if union > 0 else 0.0
```

#### Score de Localização
```python
def calculate_location_similarity(job_location, applicant_location):
    """Calcula compatibilidade geográfica
    
    Args:
        job_location (dict): {'cidade': str, 'estado': str, 'pais': str}
        applicant_location (dict): {'cidade': str, 'estado': str, 'pais': str}
        
    Returns:
        float: Score de 0 a 1
    """
    job_city = job_location.get('cidade', '').lower()
    job_state = job_location.get('estado', '').lower()
    job_country = job_location.get('pais', '').lower()
    
    app_city = applicant_location.get('cidade', '').lower()
    app_state = applicant_location.get('estado', '').lower()
    app_country = applicant_location.get('pais', '').lower()
    
    # Pontuação hierárquica
    if job_city and app_city and job_city == app_city:
        return 1.0  # Mesma cidade
    elif job_state and app_state and job_state == app_state:
        return 0.7  # Mesmo estado
    elif job_country and app_country and job_country == app_country:
        return 0.3  # Mesmo país
    else:
        return 0.0  # Localizações diferentes
```

#### Score Acadêmico
```python
def compare_academic_levels(job_level, applicant_level):
    """Compara níveis acadêmicos
    
    Args:
        job_level (str): Nível requerido pela vaga
        applicant_level (str): Nível do candidato
        
    Returns:
        float: Score de 0 a 1
    """
    academic_hierarchy = {
        "ensino fundamental": 1,
        "ensino médio": 2,
        "ensino técnico": 3,
        "ensino superior incompleto": 4,
        "ensino superior completo": 5,
        "especialização": 6,
        "mestrado": 7,
        "doutorado": 8
    }
    
    job_rank = 0
    applicant_rank = 0
    
    # Encontrar níveis na hierarquia
    for level, rank in academic_hierarchy.items():
        if level in job_level.lower():
            job_rank = max(job_rank, rank)
        if level in applicant_level.lower():
            applicant_rank = max(applicant_rank, rank)
    
    # Score baseado na adequação
    if applicant_rank >= job_rank:
        return 1.0  # Candidato atende ou supera requisito
    elif job_rank > 0:
        return max(0.2, applicant_rank / job_rank)  # Score proporcional
    else:
        return 0.5  # Não foi possível determinar
```

### 3. Embeddings Semânticos

#### Configuração do Modelo
```python
def setup_embeddings_model():
    """Configura o modelo de embeddings
    
    Returns:
        SentenceTransformer: Modelo configurado
    """
    model_name = 'distiluse-base-multilingual-cased-v1'
    model = SentenceTransformer(model_name)
    
    # Configurações otimizadas
    model.max_seq_length = 512  # Limite de tokens
    
    return model
```

#### Geração de Embeddings
```python
def generate_embeddings(texts, model, batch_size=100):
    """Gera embeddings em lotes para eficiência
    
    Args:
        texts (list): Lista de textos
        model (SentenceTransformer): Modelo de embeddings
        batch_size (int): Tamanho do lote
        
    Returns:
        numpy.ndarray: Array de embeddings
    """
    embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = model.encode(batch, show_progress_bar=True)
        embeddings.extend(batch_embeddings)
    
    return np.array(embeddings)
```

## Fluxo de Dados

### 1. Inicialização da Aplicação

```python
@st.cache_data
def download_and_load_data():
    """Download e carregamento dos dados processados"""
    # Download do Google Drive se necessário
    if not os.path.exists('decision_embeddings_enhanced.pkl'):
        gdown.download(GDRIVE_URL, 'decision_embeddings_enhanced.pkl')
    
    # Carregamento dos dados
    with open('decision_embeddings_enhanced.pkl', 'rb') as f:
        data = pickle.load(f)
    
    return data
```

### 2. Seleção de Vaga

```python
def handle_job_selection():
    """Manipula a seleção de vaga pelo usuário"""
    # Preparar opções de vaga
    job_options = {}
    for job_id, job in processed_jobs.items():
        title = job.get('titulo', 'Sem título')
        company = job.get('cliente', 'Empresa não especificada')
        job_options[job_id] = f"{title} - {company} (ID: {job_id})"
    
    # Selectbox com busca
    selected_job_id = st.selectbox(
        "🔍 Escolha a vaga:",
        options=list(job_options.keys()),
        format_func=lambda x: job_options[x]
    )
    
    return selected_job_id
```

### 3. Cálculo de Similaridades

```python
def calculate_all_similarities(selected_job_id):
    """Calcula similaridades para todos os candidatos"""
    similarities = []
    
    with st.progress(0) as progress_bar:
        total = len(applicant_embeddings)
        
        for i, applicant_id in enumerate(applicant_embeddings.keys()):
            # Atualizar barra de progresso
            progress_bar.progress((i + 1) / total)
            
            # Calcular similaridade
            similarity_data = calculate_similarity(
                selected_job_id, applicant_id,
                job_embeddings, applicant_embeddings,
                match_details, processed_jobs, processed_applicants
            )
            
            # Adicionar à lista
            similarities.append({
                'id': applicant_id,
                'nome': processed_applicants[applicant_id]['nome'],
                'score': similarity_data['score'],
                'details': similarity_data['details']
            })
    
    # Ordenar por score
    return sorted(similarities, key=lambda x: x['score'], reverse=True)
```

## Performance e Otimizações

### Cache Strategy

```python
# Cache de dados principais
@st.cache_data
def load_processed_data():
    """Cache dos dados processados"""
    pass

# Cache de similaridades por vaga
if f"similarities_{job_id}" not in st.session_state:
    st.session_state[f"similarities_{job_id}"] = calculate_similarities()
```

### Processamento em Lotes

```python
def process_in_batches(items, batch_size=1000, process_func=None):
    """Processa itens em lotes para otimização de memória"""
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = process_func(batch)
        results.extend(batch_results)
        
        # Limpeza de memória
        if i % (batch_size * 5) == 0:
            gc.collect()
    
    return results
```

### Salvamento Intermediário

```python
def save_intermediate_results(data, filename):
    """Salva resultados intermediários para recuperação"""
    output_dir = "resultados_intermediarios"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, filename), 'wb') as f:
        pickle.dump(data, f)
```

## API Endpoints (Futuro)

Para futuras implementações como API REST:

### Recomendação de Candidatos
```http
POST /api/v1/recommend
Content-Type: application/json

{
    "job_id": "5185",
    "top_n": 7,
    "filters": {
        "location": "São Paulo",
        "min_score": 0.5
    }
}
```

### Análise de Candidato
```http
GET /api/v1/candidate/{candidate_id}/analysis?job_id={job_id}
```

### Batch Processing
```http
POST /api/v1/batch/recommend
Content-Type: application/json

{
    "job_ids": ["5185", "5186", "5187"],
    "top_n": 5
}
```

## Considerações de Segurança

- **Rate Limiting**: Implementar limites de requisições
- **Authentication**: Sistema de autenticação para APIs
- **Data Privacy**: Criptografia de dados sensíveis
- **Input Validation**: Validação rigorosa de entradas
- **Audit Logging**: Log de todas as operações críticas

Esta documentação fornece uma visão completa da arquitetura e implementação do Decision Recruiter, servindo como referência para desenvolvedores e para futuras extensões do sistema.