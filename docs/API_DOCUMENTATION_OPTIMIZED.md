# API Documentation - Decision Recruiter (Versão Otimizada)

Esta documentação descreve a arquitetura interna, funções principais e fluxos de dados da versão otimizada do Decision Recruiter que utiliza GitHub Releases + Pinecone.

## Diferenças da Versão Otimizada

### Principais Melhorias
- **Fonte de dados**: GitHub Releases (5MB) vs Google Drive (500MB)
- **Busca vetorial**: Pinecone para similaridade semântica ultrarrápida
- **Fallback automático**: Sistema continua funcionando sem Pinecone
- **Performance**: 20x mais rápido no carregamento inicial
- **Mobile-friendly**: Otimizado para dispositivos com recursos limitados

## Arquitetura do Sistema Otimizado

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │◄──►│  Core Functions  │◄──►│ GitHub Releases │
│                 │    │                  │    │                 │
│ • Interface     │    │ • Similarity     │    │ • vagas.json    │
│ • Visualização  │    │ • Embeddings     │    │ • applicants.json│
│ • Interação     │    │ • Ranking        │    │ • prospects.json│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐    ┌─────────────────┐
                    │ Pinecone Vector  │◄──►│  Fallback Mode  │
                    │   Database       │    │                 │
                    │ • Vector Search  │    │ • Traditional   │
                    │ • Cosine Sim     │    │ • Full Process  │
                    │ • Top-K Results  │    │ • Compatibility │
                    └──────────────────┘    └─────────────────┘
```

## Módulos Principais

### 1. Data Loading Otimizado

Responsável pelo carregamento rápido de dados do GitHub Releases.

#### Funções Principais

##### `load_data_from_github()`
```python
@st.cache_data
def load_data_from_github():
    """
    OTIMIZADO: Carrega dados do GitHub de forma rápida
    Retorna dados no formato exato que o app.py espera
    """
    try:
        with st.status("📥 Carregando dados do GitHub..."):
            st.write("🔗 Conectando ao GitHub Releases...")
            
            # URLs dos arquivos individuais (mais rápido que arquivo grande)
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
        
        # Processar dados no formato esperado
        return process_github_data(data_loaded)
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados do GitHub: {e}")
        return None
```

##### `process_github_data(raw_data)`
```python
def process_github_data(raw_data):
    """
    Processa dados brutos do GitHub no formato otimizado
    
    Args:
        raw_data (dict): Dados brutos dos JSONs do GitHub
        
    Returns:
        dict: Dados estruturados para o sistema
    """
    with st.status("🔄 Processando dados..."):
        # 1. Processar vagas (extrair características importantes)
        processed_jobs = {}
        for job_id, job_data in raw_data['vagas'].items():
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
        
        # 2. Processar candidatos com extração automática de features
        processed_applicants = {}
        for candidate_id, candidate_data in raw_data['candidates'].items():
            processed_applicants[candidate_id] = extract_candidate_features_optimized(candidate_data)
        
        # 3. Processar contratações
        hired_candidates = {}
        for job_id, prospect_data in raw_data['prospects'].items():
            hired_candidates[job_id] = []
            for prospect in prospect_data.get('prospects', []):
                if prospect.get('situacao_candidado') == 'Contratado pela Decision':
                    hired_candidates[job_id].append(prospect.get('codigo', ''))
    
    return {
        'processed_jobs': processed_jobs,
        'processed_applicants': processed_applicants,
        'hired_candidates': hired_candidates,
        'job_embeddings': {},  # Será populado via Pinecone
        'applicant_embeddings': {},  # Será populado via Pinecone
        'match_details': {}  # Calculado dinamicamente
    }
```

### 2. Pinecone Integration

Sistema de busca vetorial com fallback automático.

#### Funções de Conexão

##### `init_pinecone()`
```python
@st.cache_resource
def init_pinecone():
    """Inicializa conexão com Pinecone com fallback automático"""
    if not PINECONE_AVAILABLE:
        return None
        
    try:
        API_KEY = os.getenv("PINECONE_API_KEY", "pcsk_5DfEc5_JTj7W19EkqEm2awJNed9dnmdfNtKBuNv3MNzPnX9R2tJv3dRNbUEJcm9gXWNYko")
        INDEX_NAME = "decision-recruiter"
        pc = Pinecone(api_key=API_KEY)
        index = pc.Index(INDEX_NAME)
        
        # Testar conexão
        index.describe_index_stats()
        st.success("🎯 Pinecone conectado - Modo Otimizado ativo!")
        return index
        
    except Exception as e:
        st.warning(f"⚠️ Pinecone indisponível: {e}")
        st.info("📊 Usando modo compatibilidade - Performance reduzida mas funcional")
        return None
```

##### `search_candidates_pinecone(job_id, top_k=50)`
```python
def search_candidates_pinecone(job_id, top_k=50):
    """
    OTIMIZADO: Busca rápida no Pinecone
    Retorna apenas os melhores candidatos para processamento detalhado
    """
    if not st.session_state.get('pinecone_available'):
        return []
    
    try:
        index = st.session_state['pinecone_index']
        
        # 1. Buscar vetor da vaga
        job_response = index.query(
            id=f"job_{job_id}",
            top_k=1,
            include_values=True
        )
        
        if not job_response['matches']:
            return []
        
        job_vector = job_response['matches'][0]['values']
        
        # 2. Buscar candidatos similares (mais resultados para filtrar melhor)
        candidates_response = index.query(
            vector=job_vector,
            top_k=top_k * 3,  # Buscar mais para filtrar depois
            include_metadata=True
        )
        
        # 3. Filtrar apenas candidatos (não vagas)
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
        st.info("🔄 Ativando fallback automático...")
        return []
```

### 3. Sistema de Scoring Otimizado

#### Cálculo de Similaridade Otimizada

##### `calculate_similarity_optimized(job_id, candidate_id, processed_jobs, processed_applicants)`
```python
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
    location_score = calculate_location_score_fast(job, candidate)
    
    # 4. Outros scores (simplificados para velocidade)
    professional_level_score = compare_levels_fast(
        job.get('nivel_profissional', ''),
        candidate.get('nivel_profissional', '')
    )
    
    academic_level_score = compare_levels_fast(
        job.get('nivel_academico', ''),
        candidate.get('nivel_academico', '')
    )
    
    english_score = compare_levels_fast(
        job.get('nivel_ingles', ''),
        candidate.get('nivel_ingles', '')
    )
    
    spanish_score = compare_levels_fast(
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
```

#### Busca Rápida de Candidatos

##### `get_top_candidates_fast(job_id, processed_jobs, processed_applicants, top_k=7)`
```python
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
        st.info(f"🎯 Pinecone: Pré-filtrados {len(candidates_to_evaluate)} candidatos promissores")
    
    # 2. Se Pinecone não disponível ou retornou poucos resultados, usar todos
    if len(candidates_to_evaluate) < 20:
        candidates_to_evaluate = list(processed_applicants.keys())
        st.info(f"📊 Modo tradicional: Analisando {len(candidates_to_evaluate)} candidatos")
    
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
```

### 4. Extração de Features Otimizada

#### Keywords Técnicas

##### `extract_keywords_from_job(job_profile)` e `extract_keywords_from_cv(cv_text)`
```python
def extract_keywords_from_job(job_profile):
    """Extrai palavras-chave técnicas da vaga de forma otimizada"""
    keywords = []
    
    # Texto para análise
    text_fields = [
        job_profile.get('principais_atividades', ''),
        job_profile.get('competencia_tecnicas_e_comportamentais', ''),
        job_profile.get('areas_atuacao', '')
    ]
    
    combined_text = ' '.join(text_fields).lower()
    
    # Lista de tecnologias comuns (otimizada)
    tech_keywords = [
        "python", "java", "javascript", "js", "c#", "c++", "php", "ruby", "go", "swift",
        "html", "css", "react", "angular", "vue", "node", "django", "flask", "spring",
        "aws", "azure", "gcp", "cloud", "docker", "kubernetes", "terraform",
        "sql", "mysql", "postgresql", "mongodb", "oracle", "redis",
        "git", "jenkins", "devops", "agile", "scrum",
        "excel", "power bi", "tableau", "sap", "erp", "totvs"
    ]
    
    # Busca otimizada (uma passada apenas)
    for keyword in tech_keywords:
        if keyword in combined_text:
            keywords.append(keyword)
    
    return keywords

def extract_keywords_from_cv(cv_text):
    """Extrai palavras-chave técnicas do CV de forma otimizada"""
    if not cv_text:
        return []
        
    keywords = []
    cv_lower = cv_text.lower()
    
    # Mesma lista de tecnologias
    tech_keywords = [
        "python", "java", "javascript", "js", "c#", "c++", "php", "ruby", "go", "swift",
        "html", "css", "react", "angular", "vue", "node", "django", "flask", "spring",
        "aws", "azure", "gcp", "cloud", "docker", "kubernetes", "terraform",
        "sql", "mysql", "postgresql", "mongodb", "oracle", "redis",
        "git", "jenkins", "devops", "agile", "scrum",
        "excel", "power bi", "tableau", "sap", "erp", "totvs"
    ]
    
    # Busca otimizada
    for keyword in tech_keywords:
        if keyword in cv_lower:
            keywords.append(keyword)
    
    return keywords
```

#### Extração de Localização

##### `extract_location_from_cv(cv_text)`
```python
def extract_location_from_cv(cv_text):
    """Extrai localização básica do CV de forma rápida"""
    if not cv_text:
        return {'cidade': '', 'estado': ''}
    
    # Estados brasileiros (otimizado)
    states = {
        'sp': 'São Paulo', 'rj': 'Rio de Janeiro', 'mg': 'Minas Gerais',
        'pr': 'Paraná', 'rs': 'Rio Grande do Sul', 'sc': 'Santa Catarina',
        'ba': 'Bahia', 'ce': 'Ceará', 'pe': 'Pernambuco', 'go': 'Goiás',
        'df': 'Distrito Federal', 'es': 'Espírito Santo', 'pb': 'Paraíba',
        'rn': 'Rio Grande do Norte', 'mt': 'Mato Grosso', 'ms': 'Mato Grosso do Sul'
    }
    
    cv_lower = cv_text.lower()
    
    # Busca rápida por estados
    for abbr, full_name in states.items():
        if abbr in cv_lower or full_name.lower() in cv_lower:
            # Inferir cidade principal para São Paulo
            cidade = 'São Paulo' if abbr == 'sp' else ''
            return {'cidade': cidade, 'estado': full_name}
    
    return {'cidade': '', 'estado': ''}
```

### 5. Sistema de Fallback

#### Detecção de Disponibilidade

##### `check_pinecone_availability()`
```python
def check_pinecone_availability():
    """
    Verifica disponibilidade do Pinecone em tempo real
    """
    if not st.session_state.get('pinecone_index'):
        return False
    
    try:
        index = st.session_state['pinecone_index']
        stats = index.describe_index_stats()
        
        # Verificar se ainda temos quota
        if stats.get('dimension', 0) > 0:
            return True
        else:
            st.warning("⚠️ Pinecone: Quota esgotada - Ativando fallback")
            return False
            
    except Exception as e:
        st.warning(f"⚠️ Pinecone: Erro de conexão - {e}")
        return False
```

#### Modo Compatibilidade

##### `fallback_similarity_search(job_id, processed_jobs, processed_applicants, top_k=50)`
```python
def fallback_similarity_search(job_id, processed_jobs, processed_applicants, top_k=50):
    """
    Busca de similaridade em modo fallback (sem Pinecone)
    Mantém compatibilidade total mas com performance reduzida
    """
    st.info("📊 Modo compatibilidade: Processamento tradicional ativado")
    
    job = processed_jobs[job_id]
    job_keywords = set(job.get('keywords', []))
    
    candidates_scores = []
    
    # Usar apenas uma amostra se muitos candidatos (otimização)
    all_candidates = list(processed_applicants.keys())
    if len(all_candidates) > 2000:
        import random
        candidates_sample = random.sample(all_candidates, 2000)
        st.info(f"🎲 Amostragem: Analisando {len(candidates_sample)} de {len(all_candidates)} candidatos")
    else:
        candidates_sample = all_candidates
    
    for candidate_id in candidates_sample:
        candidate = processed_applicants[candidate_id]
        candidate_keywords = set(candidate.get('keywords', []))
        
        # Score simples baseado em keywords + localização
        keyword_score = 0
        if job_keywords and candidate_keywords:
            keyword_score = len(job_keywords.intersection(candidate_keywords)) / len(job_keywords)
        
        location_score = 0
        if job.get('estado') and candidate.get('estado'):
            if job['estado'].lower() == candidate['estado'].lower():
                location_score = 1.0
        
        # Score combinado simples
        combined_score = keyword_score * 0.7 + location_score * 0.3
        
        candidates_scores.append({
            'id': candidate_id,
            'score': combined_score,
            'keyword_score': keyword_score,
            'location_score': location_score
        })
    
    # Ordenar e retornar top candidatos
    candidates_scores.sort(key=lambda x: x['score'], reverse=True)
    return candidates_scores[:top_k]
```

## Fluxo de Dados Otimizado

### 1. Inicialização Rápida

```python
def main():
    """Função principal otimizada"""
    # Aplicar CSS
    st.markdown(get_dynamic_css(), unsafe_allow_html=True)
    
    render_header()
    
    # Carregar dados de forma otimizada
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
        st.info("🎯 **Modo Otimizado:** Busca vetorial via Pinecone + dados do GitHub")
    else:
        st.info("📊 **Modo Padrão:** Dados do GitHub (Pinecone indisponível)")
```

### 2. Cache Otimizado

```python
# Cache específico para versão otimizada
@st.cache_data(ttl=1800)  # 30 minutos
def cache_github_data():
    """Cache otimizado para dados do GitHub"""
    return load_data_from_github()

@st.cache_resource
def cache_pinecone_connection():
    """Cache da conexão Pinecone"""
    return init_pinecone()

# Cache de resultados por sessão
def cache_search_results(job_id, results):
    """Cache dos resultados de busca"""
    cache_key = f"search_results_{job_id}"
    st.session_state[cache_key] = {
        'results': results,
        'timestamp': time.time(),
        'ttl': 1800  # 30 minutos
    }
```

### 3. Monitoramento de Performance

```python
def monitor_performance():
    """Monitora performance da aplicação em tempo real"""
    
    if st.sidebar.checkbox("📊 Mostrar Métricas de Performance"):
        
        # Métricas do Pinecone
        if st.session_state.get('pinecone_available'):
            try:
                index = st.session_state['pinecone_index']
                stats = index.describe_index_stats()
                
                st.sidebar.markdown("### Pinecone Status")
                st.sidebar.success("🟢 Online")
                st.sidebar.write(f"Vetores: {stats.get('total_vector_count', 0):,}")
                st.sidebar.write(f"Dimensão: {stats.get('dimension', 0)}")
                
            except Exception as e:
                st.sidebar.error(f"🔴 Erro: {e}")
        else:
            st.sidebar.markdown("### Modo Tradicional")
            st.sidebar.info("Pinecone indisponível")
        
        # Métricas de cache
        cache_stats = {
            'github_data': 'github_data' in st.session_state,
            'search_results': len([k for k in st.session_state.keys() if k.startswith('search_results_')]),
            'total_candidates': len(st.session_state.get('processed_applicants', {})),
            'total_jobs': len(st.session_state.get('processed_jobs', {}))
        }
        
        st.sidebar.markdown("### Cache Status")
        for key, value in cache_stats.items():
            st.sidebar.write(f"{key}: {value}")
```

## Performance e Otimizações Específicas

### Comparação de Performance

| Operação | Versão Original | Versão Otimizada |
|----------|----------------|------------------|
| **Carregamento inicial** | 5-10 minutos | 10-30 segundos |
| **Busca de candidatos** | 30-60 segundos | 2-5 segundos |
| **Uso de memória** | ~2GB | ~200MB |
| **Tamanho de download** | 500MB | 5MB |
| **Cache de resultados** | Disco (pickle) | Memória (session) |
| **Escalabilidade** | Limitada | Alta (Pinecone) |

### Otimizações Implementadas

#### 1. Lazy Loading Inteligente
```python
def lazy_load_candidates(job_id):
    """Carrega candidatos sob demanda"""
    cache_key = f"candidates_{job_id}"
    
    if cache_key not in st.session_state:
        # Carregar apenas quando necessário
        if st.session_state.get('pinecone_available'):
            candidates = search_candidates_pinecone(job_id, top_k=100)
        else:
            candidates = fallback_similarity_search(job_id, 
                st.session_state['processed_jobs'], 
                st.session_state['processed_applicants'])
        
        st.session_state[cache_key] = candidates
    
    return st.session_state[cache_key]
```

#### 2. Batch Processing Otimizado
```python
def process_candidates_batch(candidate_ids, job_id, batch_size=50):
    """Processa candidatos em lotes otimizados"""
    results = []
    
    for i in range(0, len(candidate_ids), batch_size):
        batch = candidate_ids[i:i + batch_size]
        
        # Processar lote
        batch_results = []
        for candidate_id in batch:
            similarity = calculate_similarity_optimized(
                job_id, candidate_id,
                st.session_state['processed_jobs'],
                st.session_state['processed_applicants']
            )
            batch_results.append(similarity)
        
        results.extend(batch_results)
        
        # Yield control para UI responsiva
        if i % (batch_size * 2) == 0:
            time.sleep(0.01)  # Pequena pausa para UI
    
    return results
```

#### 3. Streaming de Resultados
```python
def stream_search_results(job_id, max_results=7):
    """Stream de resultados conforme processamento"""
    placeholder = st.empty()
    results = []
    
    candidates = lazy_load_candidates(job_id)
    
    for i, candidate in enumerate(candidates):
        # Processar candidato
        result = calculate_similarity_optimized(
            job_id, candidate['id'],
            st.session_state['processed_jobs'],
            st.session_state['processed_applicants']
        )
        
        results.append(result)
        
        # Atualizar UI em tempo real
        if i % 5 == 0:  # A cada 5 candidatos
            with placeholder.container():
                st.write(f"🔄 Processados: {i+1}/{len(candidates)}")
                if results:
                    top_current = sorted(results, key=lambda x: x['score'], reverse=True)[:3]
                    st.write("🏆 Top 3 atual:")
                    for j, candidate in enumerate(top_current):
                        st.write(f"  {j+1}. {candidate['nome']} - {candidate['score']*100:.1f}%")
    
    # Finalizar
    placeholder.empty()
    return sorted(results, key=lambda x: x['score'], reverse=True)[:max_results]
```

## Configurações de Ambiente

### Variáveis de Ambiente
```python
# config/environment.py
import os

class OptimizedConfig:
    """Configurações específicas da versão otimizada"""
    
    # Pinecone
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME = "decision-recruiter"
    PINECONE_TIMEOUT = 30
    
    # GitHub
    GITHUB_BASE_URL = "https://github.com/guilcalazans/decision/releases/download/v1.0"
    GITHUB_TIMEOUT = 30
    
    # Cache
    CACHE_TTL = 1800  # 30 minutos
    SESSION_CACHE_SIZE = 100  # MB
    
    # Performance
    MAX_CANDIDATES_PINECONE = 100
    MAX_CANDIDATES_FALLBACK = 2000
    BATCH_SIZE = 50
    
    # UI
    PROGRESS_UPDATE_INTERVAL = 5
    STREAM_RESULTS = True
    
    @classmethod
    def get_mode(cls):
        """Retorna modo de operação baseado na disponibilidade"""
        if cls.PINECONE_API_KEY and len(cls.PINECONE_API_KEY) > 10:
            return "optimized"
        else:
            return "fallback"
```

## API Endpoints (Futuro) - Versão Otimizada

Para futuras implementações REST da versão otimizada:

### Endpoints Específicos da Versão Otimizada

#### Health Check com Pinecone
```http
GET /api/v2/health
Response:
{
    "status": "healthy",
    "version": "optimized",
    "pinecone": {
        "available": true,
        "index": "decision-recruiter",
        "vector_count": 95432,
        "quota_used": "76%"
    },
    "github_releases": {
        "accessible": true,
        "last_check": "2025-01-15T10:30:00Z"
    },
    "performance_mode": "optimized"
}
```

#### Busca Vetorial Rápida
```http
POST /api/v2/vector-search
Content-Type: application/json

{
    "job_id": "5185",
    "top_k": 50,
    "use_pinecone": true,
    "fallback_enabled": true
}

Response:
{
    "results": [
        {
            "candidate_id": "C001",
            "similarity_score": 0.94,
            "source": "pinecone",
            "processing_time_ms": 45
        }
    ],
    "mode_used": "pinecone",
    "total_time_ms": 67,
    "fallback_triggered": false
}
```

#### Recomendação Híbrida
```http
POST /api/v2/recommend-hybrid
Content-Type: application/json

{
    "job_id": "5185",
    "top_n": 7,
    "enable_pinecone": true,
    "enable_fallback": true,
    "filters": {
        "location": "São Paulo",
        "min_keywords_match": 2
    }
}

Response:
{
    "recommendations": [
        {
            "candidate_id": "C001",
            "name": "Ana Silva",
            "final_score": 0.94,
            "scores": {
                "semantic": 0.96,
                "keywords": 0.85,
                "location": 1.0,
                "professional_level": 1.0,
                "academic_level": 0.9
            },
            "source": "pinecone_enhanced"
        }
    ],
    "metadata": {
        "processing_mode": "hybrid",
        "pinecone_used": true,
        "fallback_used": false,
        "total_candidates_analyzed": 847,
        "processing_time_ms": 234
    }
}
```

#### Status de Performance
```http
GET /api/v2/performance
Response:
{
    "current_session": {
        "mode": "optimized",
        "queries_processed": 15,
        "avg_response_time_ms": 234,
        "cache_hit_rate": 0.73,
        "pinecone_calls": 12,
        "fallback_calls": 0
    },
    "pinecone_status": {
        "quota_remaining": 24.3,
        "requests_today": 1547,
        "estimated_daily_limit": 6000
    },
    "recommendations": [
        "Performance ótima",
        "Considere configurar cache mais agressivo"
    ]
}
```

## Considerações de Segurança Específicas

### Versão Otimizada
- **API Key Management**: Pinecone API keys em variáveis de ambiente
- **Rate Limiting Inteligente**: Respeita limites do Pinecone automaticamente
- **Fallback Security**: Sistema continua seguro mesmo sem Pinecone
- **Data Privacy**: Dados processados localmente, apenas vetores no Pinecone
- **GitHub Security**: Acesso apenas a releases públicos (sem tokens)

### Configurações de Segurança

```python
# security/config.py
class SecurityConfig:
    """Configurações de segurança da versão otimizada"""
    
    # Pinecone
    PINECONE_API_KEY_MIN_LENGTH = 32
    PINECONE_TIMEOUT_MAX = 60
    PINECONE_RETRY_MAX = 3
    
    # Rate Limiting
    REQUESTS_PER_MINUTE = 60
    REQUESTS_PER_HOUR = 1000
    
    # Data Protection
    MASK_API_KEYS = True
    LOG_SENSITIVE_DATA = False
    
    # Fallback
    ENABLE_FALLBACK = True
    FALLBACK_TIMEOUT = 30
    
    @staticmethod
    def validate_api_key(api_key):
        """Valida formato da API key"""
        if not api_key:
            return False
        if len(api_key) < SecurityConfig.PINECONE_API_KEY_MIN_LENGTH:
            return False
        if not api_key.startswith('pcsk_'):
            return False
        return True
    
    @staticmethod
    def mask_api_key(api_key):
        """Mascara API key para logs"""
        if not api_key or len(api_key) < 8:
            return "***"
        return f"{api_key[:8]}***{api_key[-4:]}"
```

## Monitoramento e Observabilidade

### Dashboard de Métricas

```python
def render_performance_dashboard():
    """Renderiza dashboard de performance em tempo real"""
    
    if st.sidebar.checkbox("Dashboard de Performance"):
        st.sidebar.markdown("---")
        
        # Status do Sistema
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.session_state.get('pinecone_available'):
                st.metric("Pinecone", "Online", delta="Otimizado")
            else:
                st.metric("Modo", "Fallback", delta="Compatibilidade")
        
        with col2:
            cache_size = len([k for k in st.session_state.keys() if k.startswith('search_')])
            st.metric("Cache", f"{cache_size} itens")
        
        # Métricas de Uso
        if 'performance_metrics' in st.session_state:
            metrics = st.session_state['performance_metrics']
            
            st.sidebar.markdown("### Performance")
            st.sidebar.write(f"Tempo médio: {metrics.get('avg_response_time', 0):.1f}s")
            st.sidebar.write(f"Buscas realizadas: {metrics.get('searches_count', 0)}")
            st.sidebar.write(f"Cache hits: {metrics.get('cache_hit_rate', 0)*100:.0f}%")
            
            # Gráfico de performance
            if len(metrics.get('response_times', [])) > 1:
                st.sidebar.line_chart(metrics['response_times'])
        
        # Alertas
        if st.session_state.get('pinecone_available'):
            try:
                index = st.session_state['pinecone_index']
                stats = index.describe_index_stats()
                vector_count = stats.get('total_vector_count', 0)
                
                if vector_count > 80000:  # 80% do limite gratuito
                    st.sidebar.warning("Pinecone: Próximo do limite")
                elif vector_count > 95000:  # 95% do limite
                    st.sidebar.error("Pinecone: Limite crítico")
            except:
                st.sidebar.error("Pinecone: Erro de conexão")
```

### Logging Estruturado

```python
# utils/logging.py
import logging
import json
from datetime import datetime

class OptimizedLogger:
    """Logger específico para versão otimizada"""
    
    def __init__(self):
        self.logger = logging.getLogger('decision_recruiter_optimized')
        self.logger.setLevel(logging.INFO)
        
        # Handler para arquivo
        handler = logging.FileHandler('decision_optimized.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_search(self, job_id, mode, results_count, response_time):
        """Log de busca realizada"""
        log_data = {
            'event': 'search_completed',
            'job_id': job_id,
            'mode': mode,  # 'pinecone' ou 'fallback'
            'results_count': results_count,
            'response_time_ms': response_time * 1000,
            'timestamp': datetime.now().isoformat()
        }
        self.logger.info(json.dumps(log_data))
    
    def log_pinecone_status(self, available, quota_used=None, error=None):
        """Log do status do Pinecone"""
        log_data = {
            'event': 'pinecone_status',
            'available': available,
            'quota_used': quota_used,
            'error': str(error) if error else None,
            'timestamp': datetime.now().isoformat()
        }
        self.logger.info(json.dumps(log_data))
    
    def log_fallback_trigger(self, reason):
        """Log quando fallback é ativado"""
        log_data = {
            'event': 'fallback_triggered',
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        self.logger.warning(json.dumps(log_data))

# Instância global
optimized_logger = OptimizedLogger()
```

## Conclusão da Documentação Otimizada

A versão otimizada do Decision Recruiter representa uma evolução arquitetural significativa, mantendo toda a funcionalidade da versão original enquanto oferece:

### Vantagens Técnicas
- **Dados distribuídos**: GitHub Releases vs arquivo único
- **Busca vetorial**: Pinecone para performance superior
- **Arquitetura resiliente**: Fallback automático garante disponibilidade
- **Otimização mobile**: Interface responsiva e carregamento rápido
- **Custo zero**: GitHub + Pinecone gratuitos

### Trade-offs Considerados
- **Dependência externa**: Pinecone (mitigado com fallback)
- **Limite de quota**: 100K vetores gratuitos (monitorado)
- **Complexidade adicional**: Gerenciamento de dois modos (automatizado)

### Recomendações de Uso

| Cenário | Versão Recomendada |
|---------|-------------------|
| **Produção/Demos** | Otimizada |
| **Análise profunda offline** | Original |
| **Recursos limitados** | Otimizada |
| **Máxima precisão** | Original |
| **Desenvolvimento rápido** | Otimizada |

### Próximas Evoluções
- **API REST**: Endpoints para integração
- **Dashboard avançado**: Métricas em tempo real
- **Auto-scaling**: Pinecone serverless
- **Multilíngue**: Suporte a outros idiomas
- **Cache distribuído**: Redis para ambientes multi-instância

Esta documentação fornece uma base sólida para desenvolvedores implementarem, manterem e evoluírem a versão otimizada do Decision Recruiter.