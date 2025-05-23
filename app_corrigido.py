import streamlit as st
import pickle
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import math
import re
import gdown
import os
import base64
import io

# CONFIGURAÇÃO IMPORTANTE: Corrige o erro do PyTorch
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Importação segura do sentence-transformers
try:
    from sentence_transformers import util
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    st.error("⚠️ sentence-transformers não está instalado. Execute: pip install sentence-transformers")

# Configuração da página
st.set_page_config(
    page_title="Decision Recruiter - Recomendação de Candidatos",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS simplificado (remove dependências problemáticas)
def get_simple_css():
    return """
<style>
    /* Tema adaptativo simplificado */
    .main-header {
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
        padding: 1.5rem;
        color: white;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .candidate-card {
        border: 2px solid #E5E7EB;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 8px;
        background: white;
        transition: all 0.2s ease;
    }
    
    .candidate-card.selected {
        border-color: #4F46E5;
        background: #EEF2FF;
    }
    
    .rank-circle {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
        color: white;
        display: flex;
        justify-content: center;
        align-items: center;
        font-weight: 600;
        margin-right: 1rem;
    }
    
    .progress-bar {
        width: 150px;
        height: 8px;
        background-color: #F3F4F6;
        border-radius: 4px;
        overflow: hidden;
        margin: 8px 0;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #4F46E5 0%, #6366F1 100%);
        border-radius: 4px;
    }
    
    .skill-tag {
        background-color: #F3F4F6;
        color: #374151;
        border-radius: 9999px;
        padding: 0.25rem 0.75rem;
        font-size: 0.75rem;
        display: inline-block;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        border: 1px solid #E5E7EB;
    }
    
    /* Esconder elementos desnecessários */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
</style>
"""

# Cabeçalho personalizado
def render_header():
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; color: white;">🎯 Decision Recruiter</h1>
        <p style="margin: 0.5rem 0 0 0; color: white; opacity: 0.9;">Sistema de Recomendação de Candidatos</p>
    </div>
    """, unsafe_allow_html=True)

# Função para capitalizar palavras
def capitalize_words(text):
    if not text or text == 'N/A':
        return text
    return ' '.join(word.capitalize() for word in str(text).split())

# Função para limpar duplicatas
def clean_duplicated_words(text):
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

# Função para unir conhecimentos técnicos
def merge_technical_knowledge(conhecimentos_tecnicos, conhecimentos_extraidos):
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
    
    return ', '.join(unique_conhecimentos) if unique_conhecimentos else "N/A"

# Função para download de dados (com tratamento de erro)
@st.cache_data
def download_and_load_data():
    """Baixa e carrega os dados do arquivo pickle do Google Drive."""
    output_path = 'decision_embeddings_enhanced.pkl'
    
    if not os.path.exists(output_path):
        try:
            with st.status("Baixando dados do Google Drive..."):
                file_id = '1172CYnyderbEHOzdfjXJ1dWfglKvzW-e'
                url = f'https://drive.google.com/uc?id={file_id}'
                gdown.download(url, output_path, quiet=False)
                st.success("Arquivo baixado com sucesso!")
        except Exception as e:
            st.error(f"Erro ao baixar arquivo: {e}")
            return None
    
    try:
        with open(output_path, 'rb') as f:
            data = pickle.load(f)
        return data
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

# Função simplificada para calcular similaridade
def calculate_similarity_simple(job_id, applicant_id, job_embeddings, applicant_embeddings, match_details, processed_jobs, processed_applicants):
    """Versão simplificada que funciona mesmo sem sentence-transformers completo"""
    
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        # Fallback: usar similaridade baseada em keywords apenas
        job_keywords = set(processed_jobs[job_id].get('keywords', []))
        applicant_keywords = set(processed_applicants[applicant_id].get('keywords', []))
        
        if job_keywords and applicant_keywords:
            intersection = len(job_keywords.intersection(applicant_keywords))
            union = len(job_keywords.union(applicant_keywords))
            semantic_score = intersection / union if union > 0 else 0
        else:
            semantic_score = 0.5
    else:
        # Usar sentence-transformers se disponível
        job_emb = job_embeddings[job_id]
        applicant_emb = applicant_embeddings[applicant_id]
        semantic_score = util.cos_sim(job_emb, applicant_emb).item()
    
    # Obter detalhes de match se disponíveis
    details = match_details.get(job_id, {}).get(applicant_id, {})
    details['semantic'] = semantic_score
    
    # Calcular score ponderado simplificado
    weighted_score = (
        semantic_score * 0.40 +
        details.get('keywords', 0) * 0.30 +
        details.get('location', 0) * 0.05 +
        details.get('professional_level', 0) * 0.10 +
        details.get('academic_level', 0) * 0.10 +
        details.get('english_level', 0) * 0.025 +
        details.get('spanish_level', 0) * 0.025
    )
    
    return {
        'score': weighted_score,
        'details': details
    }

# Função para renderizar gráfico radar simplificado
def render_simple_radar_chart(match_details):
    """Gráfico radar simplificado"""
    categories = ['Semântica', 'Palavras-chave', 'Localização', 'Nível Prof.', 'Nível Acad.', 'Inglês', 'Espanhol']
    
    values = [
        match_details.get('semantic', 0) * 100,
        match_details.get('keywords', 0) * 100,
        match_details.get('location', 0) * 100,
        match_details.get('professional_level', 0) * 100,
        match_details.get('academic_level', 0) * 100,
        match_details.get('english_level', 0) * 100,
        match_details.get('spanish_level', 0) * 100
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Match Score',
        line=dict(color='#4F46E5'),
        fillcolor='rgba(79, 70, 229, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100])
        ),
        height=350,
        showlegend=False,
        title="Análise de Compatibilidade"
    )
    
    return fig

# Função para renderizar detalhes do candidato
def render_candidate_details_simple(candidate, selected_job):
    """Versão simplificada dos detalhes do candidato"""
    applicant_data = candidate['applicant_data']
    match_details = candidate['match_details']
    
    tab1, tab2, tab3 = st.tabs(["📋 Perfil", "📄 Currículo", "📊 Compatibilidade"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Informações Pessoais")
            st.write(f"**Email:** {applicant_data.get('email', 'N/A')}")
            st.write(f"**Telefone:** {applicant_data.get('telefone', 'N/A')}")
            st.write(f"**Localização:** {capitalize_words(applicant_data.get('localizacao', 'N/A'))}")
        
        with col2:
            st.subheader("Qualificações")
            st.write(f"**Nível Profissional:** {capitalize_words(applicant_data.get('nivel_profissional', 'N/A'))}")
            st.write(f"**Nível Acadêmico:** {capitalize_words(applicant_data.get('nivel_academico', 'N/A'))}")
            st.write(f"**Inglês:** {capitalize_words(applicant_data.get('nivel_ingles', 'N/A'))}")
        
        st.subheader("Conhecimentos Técnicos")
        conhecimentos = merge_technical_knowledge(
            applicant_data.get('conhecimentos_tecnicos', ''),
            applicant_data.get('conhecimentos_tecnicos_extraidos', '')
        )
        st.write(conhecimentos)
    
    with tab2:
        cv_text = applicant_data.get('cv', '')
        if cv_text and cv_text.strip():
            st.subheader("Preview do Currículo")
            preview_text = cv_text[:500] + "..." if len(cv_text) > 500 else cv_text
            st.text_area("Currículo", preview_text, height=300)
            
            # Download do CV
            cv_bytes = cv_text.encode('utf-8')
            filename = f"CV_{candidate['nome'].replace(' ', '_')}_{candidate['id']}.txt"
            
            st.download_button(
                label="⬇️ Baixar Currículo Completo",
                data=cv_bytes,
                file_name=filename,
                mime="text/plain"
            )
        else:
            st.warning("Currículo não disponível para este candidato.")
    
    with tab3:
        st.subheader("Score de Compatibilidade")
        
        # Gráfico radar
        radar_fig = render_simple_radar_chart(match_details)
        st.plotly_chart(radar_fig, use_container_width=True)
        
        # Detalhes dos scores
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Score Semântico", f"{match_details.get('semantic', 0)*100:.1f}%")
            st.metric("Score Palavras-chave", f"{match_details.get('keywords', 0)*100:.1f}%")
            st.metric("Score Localização", f"{match_details.get('location', 0)*100:.1f}%")
        
        with col2:
            st.metric("Score Nível Prof.", f"{match_details.get('professional_level', 0)*100:.1f}%")
            st.metric("Score Nível Acad.", f"{match_details.get('academic_level', 0)*100:.1f}%")
            st.metric("Score Total", f"{candidate['score']*100:.1f}%")

# Função principal
def main():
    # Aplicar CSS
    st.markdown(get_simple_css(), unsafe_allow_html=True)
    
    # Renderizar cabeçalho
    render_header()
    
    # Verificar dependências
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        st.warning("⚠️ Algumas funcionalidades podem estar limitadas. Instale sentence-transformers para funcionalidade completa.")
    
    try:
        # Carregar dados
        with st.spinner("Carregando dados... (Primeiro acesso pode demorar alguns minutos)"):
            data = download_and_load_data()
            
            if data is None:
                st.error("❌ Não foi possível carregar os dados. Verifique sua conexão com a internet.")
                return
            
            processed_jobs = data.get('processed_jobs', {})
            processed_applicants = data.get('processed_applicants', {})
            hired_candidates = data.get('hired_candidates', {})
            job_embeddings = data.get('job_embeddings', {})
            applicant_embeddings = data.get('applicant_embeddings', {})
            match_details = data.get('match_details', {})
            
            st.success("✅ Dados carregados com sucesso!")
        
        # Verificar se os dados foram carregados corretamente
        if not processed_jobs:
            st.error("❌ Nenhuma vaga encontrada nos dados.")
            return
        
        # Criar opções para o selectbox
        job_options = {}
        for job_id, job in processed_jobs.items():
            title = capitalize_words(job.get('titulo', 'Sem título'))
            company = capitalize_words(job.get('cliente', 'Empresa não especificada'))
            job_options[job_id] = f"{title} - {company} (ID: {job_id})"
        
        st.markdown("## 🔍 Encontre os candidatos ideais")
        
        # Seletor de vaga
        selected_job_id = st.selectbox(
            "Escolha a vaga:",
            options=list(job_options.keys()),
            format_func=lambda x: job_options[x],
            help="Selecione uma vaga para ver os candidatos recomendados"
        )
        
        if selected_job_id:
            selected_job = processed_jobs[selected_job_id]
            
            # Mostrar detalhes da vaga
            with st.expander("📋 Detalhes da Vaga", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Título:** {capitalize_words(selected_job.get('titulo', 'N/A'))}")
                    st.write(f"**Cliente:** {capitalize_words(selected_job.get('cliente', 'N/A'))}")
                    st.write(f"**Localização:** {capitalize_words(selected_job.get('localizacao', 'N/A'))}")
                
                with col2:
                    st.write(f"**Nível Profissional:** {capitalize_words(selected_job.get('nivel_profissional', 'N/A'))}")
                    st.write(f"**Nível Acadêmico:** {capitalize_words(selected_job.get('nivel_academico', 'N/A'))}")
                    st.write(f"**Tipo de Contratação:** {capitalize_words(selected_job.get('tipo_contratacao', 'N/A'))}")
            
            # Calcular similaridades (versão simplificada para evitar erros)
            cache_key = f"similarities_{selected_job_id}"
            
            if cache_key not in st.session_state:
                with st.spinner("Calculando compatibilidade dos candidatos..."):
                    similarities = []
                    
                    # Limitar a 1000 candidatos para melhor performance
                    applicant_ids = list(applicant_embeddings.keys())[:1000]
                    
                    for applicant_id in applicant_ids:
                        try:
                            similarity_data = calculate_similarity_simple(
                                selected_job_id, 
                                applicant_id, 
                                job_embeddings, 
                                applicant_embeddings, 
                                match_details, 
                                processed_jobs, 
                                processed_applicants
                            )
                            
                            applicant = processed_applicants[applicant_id]
                            is_hired = applicant.get('codigo', '') in hired_candidates.get(selected_job_id, [])
                            
                            similarities.append({
                                'id': applicant_id,
                                'nome': applicant['nome'],
                                'score': similarity_data['score'],
                                'is_hired': is_hired,
                                'applicant_data': applicant,
                                'match_details': similarity_data['details']
                            })
                        except Exception as e:
                            st.warning(f"Erro ao processar candidato {applicant_id}: {e}")
                            continue
                    
                    similarities = sorted(similarities, key=lambda x: x['score'], reverse=True)
                    st.session_state[cache_key] = similarities
            else:
                similarities = st.session_state[cache_key]
            
            if not similarities:
                st.warning("Nenhum candidato encontrado para esta vaga.")
                return
            
            # Mostrar top 7 candidatos
            st.markdown("## 🏆 Top 7 Candidatos Recomendados")
            
            top_candidates = similarities[:7]
            
            # Sistema de seleção de candidato
            session_key = f"selected_candidate_{selected_job_id}"
            if session_key not in st.session_state:
                st.session_state[session_key] = 0
            
            # Renderizar cards dos candidatos
            for i, candidate in enumerate(top_candidates):
                is_selected = i == st.session_state[session_key]
                
                # Card do candidato
                card_class = "candidate-card selected" if is_selected else "candidate-card"
                
                col1, col2 = st.columns([9, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="{card_class}">
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <div style="display: flex; align-items: center;">
                                <div class="rank-circle">{i+1}</div>
                                <div>
                                    <strong>{candidate['nome']}</strong> {'🌟' if candidate['is_hired'] else ''}<br>
                                    <small>ID: {candidate['id']}</small>
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: {candidate['score']*100}%;"></div>
                                </div>
                                <strong>{candidate['score']*100:.1f}%</strong>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    button_text = "✅" if is_selected else "☐"
                    if st.button(button_text, key=f"select_{i}", help="Selecionar candidato"):
                        st.session_state[session_key] = i
                        st.rerun()
            
            # Mostrar detalhes do candidato selecionado
            st.markdown("---")
            st.markdown("### 👤 Detalhes do Candidato Selecionado")
            
            selected_candidate = top_candidates[st.session_state[session_key]]
            
            # Header do candidato selecionado
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%); 
                        border: 2px solid #4F46E5; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center;">
                        <div class="rank-circle" style="width: 50px; height: 50px; font-size: 1.2rem;">
                            {st.session_state[session_key] + 1}
                        </div>
                        <div style="margin-left: 1rem;">
                            <h3 style="margin: 0; color: #1F2937;">{selected_candidate['nome']} {'🌟' if selected_candidate['is_hired'] else ''}</h3>
                            <p style="margin: 0; color: #6B7280;">ID: {selected_candidate['id']} • Candidato selecionado</p>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <h2 style="margin: 0; color: #10B981;">{selected_candidate['score']*100:.1f}%</h2>
                        <p style="margin: 0; color: #6B7280; font-weight: 500;">Match Score</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Renderizar detalhes completos
            render_candidate_details_simple(selected_candidate, selected_job)
            
            # Seção de comparação
            st.markdown("---")
            st.markdown("## 📊 Comparação entre Candidatos")
            
            # Gráfico comparativo simples
            comparison_data = []
            for i, candidate in enumerate(top_candidates):
                comparison_data.append({
                    'Candidato': f"{i+1}º - {candidate['nome'][:20]}",
                    'Score Total': candidate['score'] * 100,
                    'Semântica': candidate['match_details'].get('semantic', 0) * 100,
                    'Keywords': candidate['match_details'].get('keywords', 0) * 100
                })
            
            df_comparison = pd.DataFrame(comparison_data)
            
            # Gráfico de barras
            fig_comparison = px.bar(
                df_comparison, 
                x='Candidato', 
                y=['Score Total', 'Semântica', 'Keywords'],
                title="Comparação de Scores dos Top 5 Candidatos",
                barmode='group',
                height=400
            )
            
            fig_comparison.update_layout(
                xaxis_tickangle=-45,
                yaxis_title="Score (%)",
                legend_title="Métricas"
            )
            
            st.plotly_chart(fig_comparison, use_container_width=True)
            
            # Tabela resumo
            st.markdown("### 📋 Resumo dos Candidatos")
            
            summary_data = []
            for i, candidate in enumerate(top_candidates):
                applicant_data = candidate['applicant_data']
                summary_data.append({
                    'Posição': f"{i+1}º",
                    'Nome': candidate['nome'],
                    'Score (%)': f"{candidate['score']*100:.1f}%",
                    'Email': applicant_data.get('email', 'N/A'),
                    'Telefone': applicant_data.get('telefone', 'N/A'),
                    'Nível Profissional': capitalize_words(applicant_data.get('nivel_profissional', 'N/A')),
                    'Contratado': 'Sim' if candidate['is_hired'] else 'Não'
                })
            
            df_summary = pd.DataFrame(summary_data)
            st.dataframe(df_summary, use_container_width=True, hide_index=True)
            
            # Download do relatório
            st.markdown("### 📥 Relatório para Download")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # CSV
                csv_buffer = io.StringIO()
                csv_buffer.write("RELATÓRIO DE CANDIDATOS RECOMENDADOS\n")
                csv_buffer.write(f"Vaga: {capitalize_words(selected_job.get('titulo', 'N/A'))}\n")
                csv_buffer.write(f"Cliente: {capitalize_words(selected_job.get('cliente', 'N/A'))}\n")
                csv_buffer.write(f"Data: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}\n\n")
                
                df_summary.to_csv(csv_buffer, index=False, sep=';')
                csv_content = csv_buffer.getvalue()
                
                st.download_button(
                    label="📥 Baixar Relatório (CSV)",
                    data=csv_content.encode('utf-8'),
                    file_name=f"relatorio_candidatos_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Informações sobre o sistema
                st.info("""
                💡 **Sobre o Sistema:**
                - Utiliza embeddings para análise semântica
                - Considera múltiplos critérios de compatibilidade
                - Baseado em candidatos contratados anteriormente
                - Score ponderado por relevância técnica
                """)
    
    except Exception as e:
        st.error(f"❌ Erro ao processar os dados: {e}")
        st.info("""
        ⚠️ **Solução de Problemas:**
        
        1. **Verifique se todas as dependências estão instaladas:**
        ```bash
        pip install streamlit==1.28.0 pandas numpy plotly sentence-transformers gdown
        ```
        
        2. **Se o erro persistir, tente:**
        ```bash
        pip uninstall torch torchvision torchaudio
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
        ```
        
        3. **Reinicie o ambiente virtual:**
        ```bash
        deactivate
        decision_env\\Scripts\\activate  # Windows
        streamlit run app.py
        ```
        """)

if __name__ == "__main__":
    main()