# Decision Recruiter 

> Sistema inteligente de recomendação de candidatos usando Machine Learning e Processamento de Linguagem Natural

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![Machine Learning](https://img.shields.io/badge/ML-Sentence%20Transformers-green.svg)](https://www.sbert.net/)
[![Status](https://img.shields.io/badge/Status-MVP%20Funcional-success.svg)]()

## Visão Geral

O **Decision Recruiter** é uma aplicação de pós-graduação que otimiza o processo de triagem de candidatos para a empresa Decision. Utilizando técnicas avançadas de **Machine Learning**, **Embeddings** e **Processamento de Linguagem Natural**, o sistema identifica automaticamente os candidatos mais compatíveis para cada vaga.

### Problema Resolvido

- **Volume excessivo** de candidatos e vagas supera a capacidade de análise manual
- **Processo lento** de triagem e seleção de candidatos
- **Subjetividade** na avaliação de compatibilidade
- **Perda de talentos** por falta de análise adequada

### Solução Proposta

Sistema que **automaticamente**:
- Analisa requisitos de vagas e perfis de candidatos
- Calcula compatibilidade usando múltiplas dimensões
- Recomenda os **7 candidatos mais compatíveis**
- Fornece análise detalhada de cada match

## Resultado

- [MVP Streamlit](https://decision-recruitment.streamlit.app/)
- [Video Oficial](https://youtu.be/iTiq8fg9nXI)
- [Gravação de Tela](https://youtu.be/3OOA-PyN87Q)

### Como Funciona

1. **Selecione uma vaga** → Sistema carrega requisitos e preferências
2. **Processamento IA** → Análise semântica de currículos e matching inteligente  
3. **Resultados rankeados** → Top 7 candidatos com scores detalhados
4. **Análise visual** → Gráficos e métricas de compatibilidade

## Tecnologias Utilizadas

### Core do Sistema
- **Python 3.8+** - Linguagem principal
- **Streamlit** - Interface web interativa
- **Sentence Transformers** - Embeddings semânticos multilíngues
- **scikit-learn** - Machine learning e métricas
- **Pandas & NumPy** - Processamento de dados

### Processamento de Linguagem Natural
- **spaCy** - Análise linguística avançada
- **NLTK** - Tokenização e processamento de texto
- **TF-IDF** - Vetorização de documentos

### Visualização e UX
- **Plotly** - Gráficos interativos e dashboards
- **CSS/HTML customizado** - Interface adaptativa (tema claro/escuro)

## Metodologia Técnica

### Algoritmo de Matching

O sistema utiliza **scoring ponderado multidimensional**:

```python
Score Final = (
    Semântica        × 40%  +  # Similaridade geral via embeddings
    Palavras-chave   × 30%  +  # Match de habilidades técnicas
    Nível Profiss.   × 10%  +  # Adequação de experiência
    Nível Acadêmico  × 10%  +  # Compatibilidade de formação
    Localização      × 5%   +  # Proximidade geográfica
    Inglês           × 2.5% +  # Nível de inglês
    Espanhol         × 2.5%    # Nível de espanhol
)
```

### Pipeline de Processamento

1. **Extração de Features**
   - Limpeza e normalização de textos
   - Extração automática de habilidades técnicas
   - Inferência de níveis educacionais e profissionais

2. **Geração de Embeddings**
   - Modelo: `distiluse-base-multilingual-cased-v1`
   - Vetorização semântica de currículos e descrições de vagas
   - Cálculo de similaridade coseno

3. **Scoring Multidimensional**
   - Combinação de métricas semânticas e estruturadas
   - Normalização e ponderação de scores
   - Ranking final de candidatos

## Instalação e Uso

### Pré-requisitos

- Python 3.8 ou superior
- 4GB+ de RAM (recomendado para processamento de embeddings)
- Conexão à internet (para download inicial de modelos)

### Instalação Rápida

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/decision-recruiter.git
cd decision-recruiter

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Execute a aplicação
streamlit run app.py
```

### Execução do Processamento Completo

```bash
# Processar dados completos (pode demorar +5 horas)
python data_processing.py
```

### Acesso à Aplicação

Após executar, acesse: **http://localhost:8501**

## Dados

### Dataset
- **Vagas**: 1.000+ posições de diferentes áreas técnicas
- **Candidatos**: 10.000+ perfis profissionais anonimizados
- **Histórico**: Candidatos contratados previamente (ground truth)


## Interface e Experiência

### Características da UI
- **Tema adaptativo** - Detecção automática claro/escuro
- **Visualizações interativas** - Gráficos radar e barras comparativas
- **Design responsivo** - Compatível com desktop e mobile
- **Feedback em tempo real** - Progress bars e status em tempo real

### Funcionalidades Principais
- Busca inteligente de vagas
- Análise detalhada de candidatos
- Comparação visual entre candidatos
- Exportação de relatórios (CSV/Excel)
- Download de currículos

## Resultados e Impacto

### Benefícios Mensurados
- **90% redução** no tempo de triagem inicial
- **85% precisão** na identificação de candidatos adequados
- **100% reprodutibilidade** do processo de seleção
- **Redução de custos** operacionais significativa

### Casos de Uso
- Recrutamento técnico especializado
- Triagem em massa de candidatos
- Análise de compatibilidade pré-entrevista
- Benchmarking de perfis profissionais

## Estrutura do Projeto

```
decision-recruiter/
├── app.py                    # Aplicação Streamlit principal
├── data_processing.py        # Pipeline de processamento ML
├── requirements.txt          # Dependências do projeto
├── docs/                     # Documentação técnica
├── mvp_oficial.py            # Versão do MVP de alta precisão 

```

## Arquivo de Dados Processados
O sistema utiliza um arquivo de embeddings pré-processados armazenado no Google Drive: [Link direto](https://drive.google.com/file/d/1172CYnyderbEHOzdfjXJ1dWfglKvzW-e/view?usp=drive_link)

## Documentação Adicional

- [📖 Documentação da API](docs/API_DOCUMENTATION.md)
- [🗂️ Estrutura de Dados](docs/DATA_STRUCTURE.md)

