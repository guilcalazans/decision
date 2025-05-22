# Estrutura de Dados - Decision Recruiter

Este documento detalha a estrutura dos dados utilizados no sistema de recomendação de candidatos.

## Visão Geral dos Datasets

O sistema utiliza três principais fontes de dados em formato JSON:

- **vagas.json** - Informações das vagas disponíveis
- **applicants.json** - Perfis completos dos candidatos
- **prospects.json** - Histórico de candidaturas e contratações

##  Estrutura das Vagas (vagas.json)

### Exemplo de Registro

```json
{
  "5185": {
    "informacoes_basicas": {
      "data_requicisao": "04-05-2021",
      "limite_esperado_para_contratacao": "00-00-0000",
      "titulo_vaga": "Operation Lead",
      "vaga_sap": "Não",
      "cliente": "Morris, Moran and Dodson",
      "solicitante_cliente": "Dra. Catarina Marques",
      "empresa_divisao": "Decision São Paulo",
      "requisitante": "Maria Laura Nogueira",
      "analista_responsavel": "Srta. Bella Ferreira",
      "tipo_contratacao": "CLT Full",
      "prazo_contratacao": "",
      "objetivo_vaga": "",
      "prioridade_vaga": "",
      "origem_vaga": "",
      "superior_imediato": "Superior Imediato:",
      "nome": "",
      "telefone": ""
    },
    "perfil_vaga": {
      "pais": "Brasil",
      "estado": "São Paulo",
      "cidade": "São Paulo",
      "bairro": "",
      "regiao": "",
      "local_trabalho": "2000",
      "vaga_especifica_para_pcd": "Não",
      "faixa_etaria": "De: Até:",
      "horario_trabalho": "",
      "nivel profissional": "Sênior",
      "nivel_academico": "Ensino Superior Completo",
      "nivel_ingles": "Avançado",
      "nivel_espanhol": "Fluente",
      "outro_idioma": "",
      "areas_atuacao": "TI - Sistemas e Ferramentas",
      "principais_atividades": "Operations Lead\n\nRoles & Responsibilities...",
      "competencia_tecnicas_e_comportamentais": "Required Skills:\n• Prior experience in Cloud Infrastructure...",
      "demais_observacoes": "100% Remoto Período – entre 5 – 6 meses",
      "viagens_requeridas": "",
      "equipamentos_necessarios": "Nenhum"
    },
    "beneficios": {
      "valor_venda": "-",
      "valor_compra_1": "R$",
      "valor_compra_2": ""
    }
  }
}
```

### Campos das Informações Básicas

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `data_requicisao` | String | Data da requisição da vaga | "04-05-2021" |
| `titulo_vaga` | String | Título/nome da posição | "Operation Lead" |
| `cliente` | String | Empresa cliente | "Morris, Moran and Dodson" |
| `empresa_divisao` | String | Divisão da Decision | "Decision São Paulo" |
| `tipo_contratacao` | String | Tipo de contrato | "CLT Full" |
| `analista_responsavel` | String | Analista responsável | "Srta. Bella Ferreira" |

### Campos do Perfil da Vaga

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `pais` | String | País da vaga | "Brasil" |
| `estado` | String | Estado | "São Paulo" |
| `cidade` | String | Cidade | "São Paulo" |
| `nivel profissional` | String | Nível de experiência | "Sênior" |
| `nivel_academico` | String | Formação acadêmica | "Ensino Superior Completo" |
| `nivel_ingles` | String | Nível de inglês | "Avançado" |
| `nivel_espanhol` | String | Nível de espanhol | "Fluente" |
| `areas_atuacao` | String | Área de atuação | "TI - Sistemas e Ferramentas" |
| `principais_atividades` | String | Descrição das atividades | "Operations Lead\n\nRoles & Responsibilities..." |
| `competencia_tecnicas_e_comportamentais` | String | Skills requeridas | "Required Skills:\n• Prior experience..." |

## Estrutura dos Candidatos (applicants.json)

### Exemplo de Registro

```json
{
  "31000": {
    "infos_basicas": {
      "telefone_recado": "",
      "telefone": "(11) 97048-2708",
      "objetivo_profissional": "",
      "data_criacao": "10-11-2021 07:29:49",
      "inserido_por": "Luna Correia",
      "email": "carolina_aparecida@gmail.com",
      "local": "",
      "sabendo_de_nos_por": "",
      "data_atualizacao": "10-11-2021 07:29:49",
      "codigo_profissional": "31000",
      "nome": "Carolina Aparecida"
    },
    "informacoes_pessoais": {
      "data_aceite": "Cadastro anterior ao registro de aceite",
      "nome": "Carolina Aparecida",
      "cpf": "",
      "fonte_indicacao": ":",
      "email": "carolina_aparecida@gmail.com",
      "email_secundario": "",
      "data_nascimento": "0000-00-00",
      "telefone_celular": "(11) 97048-2708",
      "telefone_recado": "",
      "sexo": "",
      "estado_civil": "",
      "pcd": "",
      "endereco": "",
      "skype": "",
      "url_linkedin": "",
      "facebook": ""
    },
    "informacoes_profissionais": {
      "titulo_profissional": "",
      "area_atuacao": "",
      "conhecimentos_tecnicos": "",
      "certificacoes": "",
      "outras_certificacoes": "",
      "remuneracao": "",
      "nivel_profissional": ""
    },
    "formacao_e_idiomas": {
      "nivel_academico": "",
      "nivel_ingles": "",
      "nivel_espanhol": "",
      "outro_idioma": "-"
    },
    "cargo_atual": {},
    "cv_pt": "assistente administrativo\n\n\nsantosbatista...",
    "cv_en": ""
  }
}
```

### Campos das Informações Básicas

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `codigo_profissional` | String | ID único do candidato | "31000" |
| `nome` | String | Nome completo | "Carolina Aparecida" |
| `email` | String | Email principal | "carolina_aparecida@gmail.com" |
| `telefone` | String | Telefone de contato | "(11) 97048-2708" |
| `data_criacao` | String | Data de cadastro | "10-11-2021 07:29:49" |

### Campos Profissionais

| Campo | Tipo | Descrição | Uso no Sistema |
|-------|------|-----------|----------------|
| `titulo_profissional` | String | Título atual | Matching semântico |
| `area_atuacao` | String | Área de especialização | Classificação |
| `conhecimentos_tecnicos` | String | Habilidades técnicas | Matching de keywords |
| `nivel_profissional` | String | Nível de experiência | Scoring direto |

### Campos de Formação

| Campo | Tipo | Descrição | Uso no Sistema |
|-------|------|-----------|----------------|
| `nivel_academico` | String | Formação acadêmica | Requisito mínimo |
| `nivel_ingles` | String | Proficiência em inglês | Requisito linguístico |
| `nivel_espanhol` | String | Proficiência em espanhol | Requisito linguístico |

### Currículo

| Campo | Tipo | Descrição | Uso no Sistema |
|-------|------|-----------|----------------|
| `cv_pt` | String | Currículo em português | Análise semântica principal |
| `cv_en` | String | Currículo em inglês | Backup para análise |

## Estrutura dos Prospectos (prospects.json)

### Exemplo de Registro

```json
{
  "4531": {
    "titulo": "2021-2607395-PeopleSoft Application Engine-Domain Consultant",
    "modalidade": "",
    "prospects": [
      {
        "nome": "Sra. Yasmin Fernandes",
        "codigo": "25364",
        "situacao_candidado": "Contratado pela Decision",
        "data_candidatura": "17-03-2021",
        "ultima_atualizacao": "12-04-2021",
        "comentario": "",
        "recrutador": "Juliana Cassiano"
      }
    ]
  }
}
```

### Campos dos Prospectos

| Campo | Tipo | Descrição | Uso no Sistema |
|-------|------|-----------|----------------|
| `codigo` | String | ID do candidato | Link com applicants.json |
| `situacao_candidado` | String | Status da candidatura | Ground truth para validação |
| `data_candidatura` | String | Data da aplicação | Timeline |
| `recrutador` | String | Responsável | Tracking |

### Status de Candidatura

| Status | Descrição | Uso no ML |
|--------|-----------|-----------|
| `"Contratado pela Decision"` | Candidato foi contratado | ✅ Positive ground truth |
| `"Encaminhado ao Requisitante"` | Em processo | ⚪ Neutral |
| `"Não selecionado"` | Rejeitado | ❌ Negative feedback |
| `"Em análise"` | Pendente | ⚪ Neutral |

## Processamento e Transformação

### Dados Extraídos Automaticamente

O sistema extrai informações adicionais dos currículos:

#### Habilidades Técnicas
```python
# Extraídas do texto do CV usando NLP
technical_skills = [
    "python", "java", "sql", "aws", "docker", 
    "machine learning", "excel", "powerbi"
]
```

#### Localização
```python
# Inferida do texto do currículo
location = {
    "cidade": "São Paulo",
    "estado": "São Paulo", 
    "pais": "Brasil"
}
```

#### Níveis Educacionais
```python
# Hierarquia para comparação
education_levels = {
    "ensino médio": 2,
    "ensino técnico": 3,
    "ensino superior incompleto": 4,
    "ensino superior completo": 5,
    "especialização": 6,
    "mestrado": 7,
    "doutorado": 8
}
```

### Features Calculadas

#### Embeddings Semânticos
- **Modelo**: `distiluse-base-multilingual-cased-v1`
- **Dimensão**: 512 features por documento
- **Uso**: Similaridade coseno entre vaga e candidato

#### Scores de Compatibilidade
```python
compatibility_scores = {
    "semantic": 0.85,        # Similaridade semântica (0-1)
    "keywords": 0.70,        # Match de palavras-chave (0-1)
    "location": 1.0,         # Compatibilidade geográfica (0-1)
    "professional_level": 0.9, # Nível profissional (0-1)
    "academic_level": 0.8,   # Nível acadêmico (0-1)
    "english_level": 0.6,    # Inglês (0-1)
    "spanish_level": 0.3     # Espanhol (0-1)
}
```

## Métricas de Qualidade dos Dados

### Completude dos Dados

| Dataset | Registros | Campos Principais | Completude CV |
|---------|-----------|-------------------|---------------|
| Vagas | 1,000+ | 95% completos | N/A |
| Candidatos | 10,000+ | 80% completos | 90% |
| Prospectos | 5,000+ | 100% completos | N/A |

### Distribuição por Área

| Área | Vagas | Candidatos | Proporção |
|------|-------|------------|-----------|
| TI/Tecnologia | 40% | 35% | Balanceado |
| Engenharia | 25% | 20% | Balanceado |
| Gestão | 20% | 25% | Balanceado |
| Financeiro | 15% | 20% | Balanceado |

### Qualidade dos Currículos

- **Tamanho médio**: 2,500 caracteres
- **Idioma principal**: Português (95%)
- **Estruturação**: Texto livre (parsing via NLP)
- **Informações técnicas**: Presente em 80% dos CVs

## Uso dos Dados no Sistema

### Pipeline de Processamento

1. **Carregamento** → JSON para dicionários Python
2. **Limpeza** → Normalização de textos e campos
3. **Extração** → Features automáticas via NLP
4. **Embedding** → Vetorização semântica
5. **Indexação** → Estruturas otimizadas para busca
6. **Caching** → Resultados intermediários salvos

### Otimizações Implementadas

- **Processamento em lotes** para embeddings
- **Cache de resultados intermediários** em .pkl
- **Lazy loading** para datasets grandes
- **Indexação** por ID para acesso O(1)

## Estatísticas dos Dados

### Distribuição de Níveis Profissionais

```
Júnior:     30% (3,000 candidatos)
Pleno:      45% (4,500 candidatos)  
Sênior:     20% (2,000 candidatos)
Especialista: 5% (500 candidatos)
```

### Distribuição Geográfica

```
São Paulo:    35%
Rio de Janeiro: 20%
Minas Gerais:  15%
Outros estados: 30%
```

### Idiomas

```
Português: 100% (nativo)
Inglês:    60% (algum nível)
Espanhol:  25% (algum nível)
```

## Links dos Datasets

Os dados estão disponíveis em:
- **vagas.json**: [Download Link](https://github.com/guilcalazans/decision/releases/download/v1.0/vagas.json)
- **applicants.json**: [Download Link](https://github.com/guilcalazans/decision/releases/download/v1.0/applicants.json)  
- **prospects.json**: [Download Link](https://github.com/guilcalazans/decision/releases/download/v1.0/prospects.json)

## Considerações de Privacidade

- **Dados anonimizados**: Nomes e informações pessoais são fictícios
- **LGPD compliance**: Estrutura preparada para dados reais
- **Segurança**: Sem informações sensíveis nos exemplos
- **Uso acadêmico**: Dados exclusivamente para fins educacionais 