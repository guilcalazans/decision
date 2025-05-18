import streamlit as st
import json
import random
from datetime import datetime

# --- Configurações da página ---
st.set_page_config(
    page_title="Sistema de Gestão de Vagas",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS personalizado ---
st.markdown("""
<style>
    /* Fix para dark mode - garante texto visível em qualquer tema */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--text-color, #1E3A8A);
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: var(--text-color, #1E3A8A);
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .card {
        background-color: var(--background-color, #f8f9fa);
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        color: var(--text-color, #212529);
        border: 1px solid var(--border-color, #e9ecef);
    }
    .card h3, .card h4, .card p, .card strong {
        color: var(--text-color, #212529) !important;
    }
    .badge {
        background-color: #4CAF50;
        color: white;
        font-size: 0.8rem;
        padding: 5px 10px;
        border-radius: 15px;
        margin-right: 5px;
    }
    .candidate-card {
        background-color: var(--background-color, white);
        border-left: 4px solid #1E88E5;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        color: var(--text-color, #212529);
    }
    .candidate-card h4, .candidate-card p {
        color: var(--text-color, #212529) !important;
    }
    .stats-box {
        background-color: #1E3A8A;
        color: white;
        border-radius: 5px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .sidebar-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: var(--text-color, #1E3A8A);
    }
    .stButton>button {
        background-color: #1E3A8A;
        color: white;
        border-radius: 5px;
        padding: 5px 15px;
        font-weight: 500;
        border: none;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #152C6F;
    }
    .highlight {
        background-color: #FFF9C4;
        padding: 2px;
        color: #212529;
    }
    
    /* Define variáveis CSS baseadas no tema */
    @media (prefers-color-scheme: dark) {
        :root {
            --text-color: #f1f1f1;
            --background-color: #2d2d2d;
            --border-color: #444;
        }
    }
    
    @media (prefers-color-scheme: light) {
        :root {
            --text-color: #212529;
            --background-color: #f8f9fa;
            --border-color: #e9ecef;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Carregar os dados ---
def carregar_dados():
    try:
        with open("bases/vagas.json", "r", encoding="utf-8") as f:
            vagas = json.load(f)
        with open("bases/applicants.json", "r", encoding="utf-8") as f:
            candidatos = json.load(f)
        return vagas, candidatos
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return {}, {}

vagas, candidatos = carregar_dados()

# --- Função para buscar candidatos ideais (mock) ---
def buscar_candidatos_ideais(vaga_id):
    todos = list(candidatos.values())
    random.shuffle(todos)  # embaralha para simular seleção
    # Atribuir uma pontuação fictícia de compatibilidade
    candidatos_pontuados = []
    for candidato in todos[:7]:
        compatibilidade = random.randint(60, 99)
        candidatos_pontuados.append((candidato, compatibilidade))
    # Ordenar por compatibilidade
    candidatos_pontuados.sort(key=lambda x: x[1], reverse=True)
    return candidatos_pontuados

# --- Dados estatísticos ---
def obter_estatisticas():
    total_vagas = len(vagas)
    total_candidatos = len(candidatos)
    vagas_ativas = sum(1 for v in vagas.values() if v.get("status", "Ativa") == "Ativa")
    return total_vagas, total_candidatos, vagas_ativas

# --- Sidebar ---
with st.sidebar:
    st.markdown("<div class='sidebar-header'>📊 Painel de Gestão</div>", unsafe_allow_html=True)
    
    total_vagas, total_candidatos, vagas_ativas = obter_estatisticas()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class='stats-box'>
            <h3>{total_vagas}</h3>
            <p>Vagas</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='stats-box'>
            <h3>{total_candidatos}</h3>
            <p>Candidatos</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    st.markdown("<div class='sidebar-header'>🔍 Navegação</div>", unsafe_allow_html=True)
    aba = st.radio("", ["📋 Gerenciar Vagas", "➕ Nova Vaga"])
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
    <div style='padding: 10px; background-color: #E3F2FD; border-radius: 5px;'>
        <p style='margin-bottom: 0px; font-size: 0.85rem;'>
            <strong>💡 Dica:</strong> Use o filtro para encontrar vagas rapidamente.
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- Layout principal ---
st.markdown("<h1 class='main-header'>Sistema de Gestão de Vagas e Candidatos</h1>", unsafe_allow_html=True)

# --- Gerenciar Vagas ---
if aba == "📋 Gerenciar Vagas":
    # Banner
    st.markdown("""
    <div style='background-color: #E3F2FD; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>
        <h3 style='margin: 0; color: #1565C0;'>Visão geral de vagas disponíveis</h3>
        <p style='margin: 5px 0 0 0;'>Filtre, visualize detalhes e encontre candidatos ideais para cada posição</p>
    </div>
    """, unsafe_allow_html=True)

    # Filtros
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        filtro = st.text_input("🔍 Filtrar por ID, título ou cliente", placeholder="Digite para buscar...")
    
    with col2:
        data_filtro = st.date_input("📅 Filtrar por data", value=None)
    
    with col3:
        ordem = st.selectbox("Ordenar por:", ["Mais recente", "Título (A-Z)", "Cliente (A-Z)"])
    
    # Aplica filtro
    vagas_filtradas = {}
    for vid, vaga in vagas.items():
        titulo = vaga["informacoes_basicas"]["titulo_vaga"]
        cliente = vaga["informacoes_basicas"]["cliente"]
        data_vaga_str = vaga["informacoes_basicas"].get("data_requicisao", "")
        
        # Verifica filtro de texto
        texto_ok = filtro.lower() in vid.lower() or filtro.lower() in titulo.lower() or filtro.lower() in cliente.lower()
        
        # Verifica filtro de data
        data_ok = True
        if data_filtro is not None and data_vaga_str:
            try:
                # Converte string para objeto data
                data_vaga = datetime.strptime(data_vaga_str, "%Y-%m-%d").date()
                data_ok = data_vaga == data_filtro
            except:
                data_ok = False
        
        # Aplica ambos os filtros
        if texto_ok and data_ok:
            vagas_filtradas[vid] = vaga
    
    # Ordenar resultados
    if ordem == "Título (A-Z)":
        vagas_filtradas = dict(sorted(vagas_filtradas.items(), key=lambda x: x[1]["informacoes_basicas"]["titulo_vaga"]))
    elif ordem == "Cliente (A-Z)":
        vagas_filtradas = dict(sorted(vagas_filtradas.items(), key=lambda x: x[1]["informacoes_basicas"]["cliente"]))
    # Mais recente é a ordem padrão, não precisa reordenar

    # Opções de quantidade de vagas por página
    col1, col2 = st.columns([3, 1])
    with col2:
        # Dropdown para selecionar a quantidade de vagas a mostrar
        opcoes_qtd = ["50", "100", "200", "Todos"]
        qtd_mostrar = st.selectbox("Mostrar vagas:", opcoes_qtd, index=0)
    
    # Converter para inteiro, exceto "Todos"
    limite_vagas = None if qtd_mostrar == "Todos" else int(qtd_mostrar)
    
    # Mostrar resultados com o limite selecionado
    total_vagas_filtradas = len(vagas_filtradas)
    
    if limite_vagas and total_vagas_filtradas > limite_vagas:
        # Limitar número de vagas a mostrar
        vagas_exibir = dict(list(vagas_filtradas.items())[:limite_vagas])
        st.markdown(f"<div class='sub-header'>🔍 Resultado da busca: Mostrando {len(vagas_exibir)} de {total_vagas_filtradas} vagas encontradas</div>", unsafe_allow_html=True)
    else:
        # Mostrar todas as vagas filtradas
        vagas_exibir = vagas_filtradas
        st.markdown(f"<div class='sub-header'>🔍 Resultado da busca: {total_vagas_filtradas} vagas encontradas</div>", unsafe_allow_html=True)
    
    if vagas_exibir:
        # Grid de cards para selecionar vaga (reduzido em 20%)
        cols = st.columns(4)  # Mudamos de 3 para 4 colunas
        vaga_cards = {}
        
        for i, (vid, vaga) in enumerate(vagas_exibir.items()):
            col_idx = i % 4
            with cols[col_idx]:
                titulo = vaga["informacoes_basicas"]["titulo_vaga"]
                cliente = vaga["informacoes_basicas"]["cliente"]
                data = vaga["informacoes_basicas"].get("data_requicisao", "N/A")
                
                highlight = ""
                if filtro and filtro.lower() in titulo.lower():
                    titulo = titulo.replace(filtro, f"<span class='highlight'>{filtro}</span>")
                if filtro and filtro.lower() in cliente.lower():
                    cliente = cliente.replace(filtro, f"<span class='highlight'>{filtro}</span>")
                
                # Card com tamanho reduzido
                card_html = f"""
                <div class='card' style="padding: 15px; font-size: 0.9em;">
                    <h3 style="font-size: 1.1em; margin-top: 0;">{titulo}</h3>
                    <p style="margin: 5px 0;"><strong>Cliente:</strong> {cliente}</p>
                    <p style="margin: 5px 0;"><small>ID: {vid} | Data: {data}</small></p>
                    <div style='display: flex; justify-content: flex-end;'>
                        <div class='badge'>Ativa</div>
                    </div>
                </div>
                """
                if st.markdown(card_html, unsafe_allow_html=True):
                    vaga_cards[vid] = True
        
        # Adicionar paginação se o número de vagas for limitado e houver mais vagas
        if limite_vagas and total_vagas_filtradas > limite_vagas:
            # Calcular número de páginas
            num_paginas = (total_vagas_filtradas + limite_vagas - 1) // limite_vagas
            pagina_atual = 1  # Implementação inicial mostra apenas primeira página
            
            st.markdown(f"""
            <div style='text-align: center; margin: 20px 0;'>
                <p>Página {pagina_atual} de {num_paginas}</p>
                <p style='color: #666; font-size: 0.8rem;'>
                    Mostrando {limite_vagas} de {total_vagas_filtradas} vagas. Altere a quantidade de vagas exibidas acima.
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Selecionar vaga
        vaga_selecionada = st.selectbox("📌 Selecione uma vaga para ver detalhes", list(vagas_exibir.keys()), format_func=lambda x: vagas_exibir[x]["informacoes_basicas"]["titulo_vaga"])
        
        # Mostrar detalhes
        if vaga_selecionada:
            vaga_atual = vagas_exibir[vaga_selecionada]
            
            # Tabs para organizar informações
            tabs = st.tabs(["📋 Detalhes", "👥 Candidatos Recomendados"])
            
            # Tab de detalhes
            with tabs[0]:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("<div class='sub-header'>📝 Informações da Vaga</div>", unsafe_allow_html=True)
                    
                    # Formatando informações básicas
                    info_basicas = vaga_atual["informacoes_basicas"]
                    st.markdown(f"""
                    <div class='card'>
                        <h3>{info_basicas['titulo_vaga']}</h3>
                        <p><strong>Cliente:</strong> {info_basicas['cliente']}</p>
                        <p><strong>Data:</strong> {info_basicas.get('data_requicisao', 'N/A')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # JSON formatado (expandível)
                    with st.expander("Ver JSON completo"):
                        st.json(vaga_atual)
                
                with col2:
                    st.markdown("<div class='sub-header'>🔄 Ações</div>", unsafe_allow_html=True)
                    
                    st.markdown("""
                    <div class='card'>
                        <p>Gerencie esta vaga:</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Editar Vaga"):
                        st.info("Funcionalidade de edição será implementada em breve.")
                    
                    if st.button("Arquivar Vaga"):
                        st.info("Funcionalidade de arquivamento será implementada em breve.")
                    
                    if st.button("Exportar Detalhes (PDF)"):
                        st.info("Funcionalidade de exportação será implementada em breve.")
            
            # Tab de candidatos
            with tabs[1]:
                st.markdown("<div class='sub-header'>👥 Candidatos Recomendados</div>", unsafe_allow_html=True)
                
                with st.spinner("Buscando candidatos ideais..."):
                    candidatos_ideais = buscar_candidatos_ideais(vaga_selecionada)
                
                # Exibir candidatos
                for i, (c, compatibilidade) in enumerate(candidatos_ideais, 1):
                    nome = c['informacoes_basicas']['nome_completo']
                    email = c['informacoes_basicas']['email']
                    
                    # Determinar a cor da barra de compatibilidade
                    if compatibilidade >= 85:
                        cor_barra = "#4CAF50"  # Verde
                    elif compatibilidade >= 70:
                        cor_barra = "#2196F3"  # Azul
                    else:
                        cor_barra = "#FFC107"  # Amarelo
                    
                    st.markdown(f"""
                    <div class='candidate-card'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div>
                                <h4 style='margin: 0;'>{nome}</h4>
                                <p style='margin: 5px 0;'>{email}</p>
                            </div>
                            <div>
                                <span style='font-size: 1.2rem; font-weight: bold;'>{compatibilidade}%</span>
                            </div>
                        </div>
                        <div style='margin-top: 10px; background-color: #E0E0E0; border-radius: 5px; height: 10px;'>
                            <div style='width: {compatibilidade}%; background-color: {cor_barra}; height: 10px; border-radius: 5px;'></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Botões de ação
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Contatar Todos"):
                        st.info("Funcionalidade de contato será implementada em breve.")
                with col2:
                    if st.button("Exportar Lista"):
                        st.info("Funcionalidade de exportação será implementada em breve.")
                
    else:
        st.info("Nenhuma vaga encontrada com esse filtro.")

# --- Inserir nova vaga ---
elif aba == "➕ Nova Vaga":
    st.markdown("<div class='sub-header'>📥 Inserir Nova Vaga</div>", unsafe_allow_html=True)
    
    # Formulário estruturado
    with st.form(key="nova_vaga_form"):
        # Separar em seções com colunas
        st.markdown("### Informações Básicas")
        
        col1, col2 = st.columns(2)
        with col1:
            nova_id = st.text_input("ID da vaga", placeholder="Ex: VAGA-2025-001")
            titulo = st.text_input("Título da vaga", placeholder="Ex: Desenvolvedor Python Sênior")
        
        with col2:
            cliente = st.text_input("Nome do cliente", placeholder="Ex: Empresa XYZ")
            data_req = st.date_input("Data da requisição", datetime.now())
        
        st.markdown("### Requisitos da Vaga")
        
        col1, col2 = st.columns(2)
        with col1:
            experiencia = st.slider("Anos de experiência", 0, 15, 3)
            nivel = st.selectbox("Nível da vaga", ["Júnior", "Pleno", "Sênior", "Especialista"])
        
        with col2:
            localizacao = st.text_input("Localização", placeholder="Ex: São Paulo, SP")
            modelo_trabalho = st.selectbox("Modelo de trabalho", ["Remoto", "Presencial", "Híbrido"])
        
        descricao = st.text_area("Descrição da vaga", placeholder="Descreva as responsabilidades e detalhes da vaga...")
        
        submit_button = st.form_submit_button(label="Salvar vaga")
        
    if submit_button:
        if nova_id in vagas:
            st.error("❌ ID já existe. Por favor, utilize outro identificador.")
        elif not nova_id or not titulo or not cliente:
            st.warning("⚠️ Por favor, preencha todos os campos obrigatórios.")
        else:
            nova_vaga = {
                "informacoes_basicas": {
                    "data_requicisao": data_req.strftime("%Y-%m-%d"),
                    "titulo_vaga": titulo,
                    "cliente": cliente,
                    "nivel": nivel,
                    "localizacao": localizacao,
                    "modelo_trabalho": modelo_trabalho,
                    "experiencia_minima": experiencia
                },
                "descricao": descricao,
                "status": "Ativa",
                "data_criacao": datetime.now().strftime("%Y-%m-%d")
            }
            
            # Na implementação real, salvaria no arquivo
            # Por enquanto apenas simula
            vagas[nova_id] = nova_vaga
            
            st.success("✅ Vaga salva com sucesso!")
            
            # Mostrar mensagem de sucesso mais elaborada
            st.markdown(f"""
            <div class='card' style='background-color: #E8F5E9; border-left: 4px solid #4CAF50;'>
                <h3>Vaga '{titulo}' criada com sucesso!</h3>
                <p>A vaga foi registrada com o ID <strong>{nova_id}</strong> para o cliente <strong>{cliente}</strong>.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Candidatos recomendados
            st.markdown("<div class='sub-header'>👥 Candidatos Recomendados</div>", unsafe_allow_html=True)
            
            with st.spinner("Buscando candidatos ideais..."):
                candidatos_ideais = buscar_candidatos_ideais(nova_id)
            
            # Exibir candidatos em formato de cards
            for i, (c, compatibilidade) in enumerate(candidatos_ideais, 1):
                nome = c['informacoes_basicas']['nome_completo']
                email = c['informacoes_basicas']['email']
                
                # Determinar a cor da barra de compatibilidade
                if compatibilidade >= 85:
                    cor_barra = "#4CAF50"  # Verde
                elif compatibilidade >= 70:
                    cor_barra = "#2196F3"  # Azul
                else:
                    cor_barra = "#FFC107"  # Amarelo
                
                st.markdown(f"""
                <div class='candidate-card'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <h4 style='margin: 0;'>{nome}</h4>
                            <p style='margin: 5px 0;'>{email}</p>
                        </div>
                        <div>
                            <span style='font-size: 1.2rem; font-weight: bold;'>{compatibilidade}%</span>
                        </div>
                    </div>
                    <div style='margin-top: 10px; background-color: #E0E0E0; border-radius: 5px; height: 10px;'>
                        <div style='width: {compatibilidade}%; background-color: {cor_barra}; height: 10px; border-radius: 5px;'></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# Rodapé
st.markdown("""
<div style='margin-top: 50px; padding: 15px; border-top: 1px solid #e0e0e0; text-align: center;'>
    <p style='color: #666; font-size: 0.8rem;'>MVP Sistema de Gestão de Vagas e Candidatos © 2025</p>
</div>
""", unsafe_allow_html=True)
