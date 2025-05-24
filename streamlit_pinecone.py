"""
Teste simples para verificar se conseguimos puxar dados do Pinecone
"""

import streamlit as st

# Configuração básica
st.set_page_config(page_title="Teste Pinecone", layout="wide")

st.title("🧪 Teste de Conexão com Pinecone")

# Tentar importar Pinecone
try:
    import pinecone
    from pinecone import Pinecone, ServerlessSpec
    st.success("✅ Pinecone importado com sucesso!")
    st.write(f"📦 Versão do Pinecone: {pinecone.__version__}")
except Exception as e:
    st.error(f"❌ Erro ao importar Pinecone: {e}")
    st.stop()

# Conectar ao Pinecone
@st.cache_resource
def conectar_pinecone():
    try:
        API_KEY = "pcsk_5DfEc5_JTj7W19EkqEm2awJNed9dnmdfNtKBuNv3MNzPnX9R2tJv3dRNbUEJcm9gXWNYko"
        pc = Pinecone(api_key=API_KEY)
        index = pc.Index("decision-recruiter")
        return index
    except Exception as e:
        st.error(f"❌ Erro ao conectar: {e}")
        return None

# Testar conexão
st.markdown("## 🔌 Testando Conexão")

index = conectar_pinecone()

if index:
    st.success("✅ Conectado ao Pinecone!")
    
    # Testar estatísticas do índice
    st.markdown("## 📊 Estatísticas do Índice")
    
    try:
        stats = index.describe_index_stats()
        st.json(stats)
        
        total_vectors = stats.get('total_vector_count', 0)
        st.metric("Total de Vetores", total_vectors)
        
    except Exception as e:
        st.error(f"❌ Erro ao obter estatísticas: {e}")
    
    # Testar busca de uma vaga específica
    st.markdown("## 🔍 Teste de Busca - Vaga Específica")
    
    job_id = st.text_input("Digite o ID de uma vaga para testar:", value="5185")
    
    if st.button("🔍 Buscar Vaga"):
        try:
            # Buscar dados da vaga
            result = index.query(
                id=f"job_{job_id}",
                top_k=1,
                include_metadata=True,
                include_values=False
            )
            
            if result.matches:
                st.success(f"✅ Vaga {job_id} encontrada!")
                
                vaga_data = result.matches[0].metadata
                st.json(vaga_data)
                
                # Mostrar informações formatadas
                st.markdown("### 📋 Detalhes da Vaga")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Título:** {vaga_data.get('titulo', 'N/A')}")
                    st.write(f"**Cliente:** {vaga_data.get('cliente', 'N/A')}")
                    st.write(f"**Cidade:** {vaga_data.get('cidade', 'N/A')}")
                    
                with col2:
                    st.write(f"**Estado:** {vaga_data.get('estado', 'N/A')}")
                    st.write(f"**Tipo:** {vaga_data.get('type', 'N/A')}")
                    st.write(f"**ID:** {vaga_data.get('job_id', 'N/A')}")
                
            else:
                st.warning(f"⚠️ Vaga {job_id} não encontrada")
                
        except Exception as e:
            st.error(f"❌ Erro na busca: {e}")
    
    # Testar busca de candidatos
    st.markdown("## 👥 Teste de Busca - Candidatos")
    
    if st.button("🔍 Buscar Candidatos (Top 5)"):
        try:
            # Buscar candidatos usando filtro
            result = index.query(
                vector=[0.0] * 512,  # Vector dummy para busca por filtro
                top_k=5,
                filter={"type": "candidate"},
                include_metadata=True,
                include_values=False
            )
            
            if result.matches:
                st.success(f"✅ Encontrados {len(result.matches)} candidatos!")
                
                # Mostrar candidatos em tabela
                candidatos = []
                for match in result.matches:
                    meta = match.metadata
                    candidatos.append({
                        "Nome": meta.get('nome', 'N/A'),
                        "ID": meta.get('candidate_id', 'N/A'),
                        "Email": meta.get('email', 'N/A'),
                        "Cidade": meta.get('cidade', 'N/A'),
                        "Estado": meta.get('estado', 'N/A'),
                        "Score": f"{match.score:.4f}"
                    })
                
                import pandas as pd
                df = pd.DataFrame(candidatos)
                st.dataframe(df, use_container_width=True)
                
                # Mostrar detalhes do primeiro candidato
                st.markdown("### 👤 Detalhes do Primeiro Candidato")
                primeiro_candidato = result.matches[0].metadata
                st.json(primeiro_candidato)
                
            else:
                st.warning("⚠️ Nenhum candidato encontrado")
                
        except Exception as e:
            st.error(f"❌ Erro na busca de candidatos: {e}")
    
    # Testar busca por similaridade
    st.markdown("## 🎯 Teste de Busca por Similaridade")
    
    if st.button("🔍 Buscar Candidatos Similares para Vaga 5185"):
        try:
            # Primeiro buscar o vetor da vaga
            job_result = index.query(
                id="job_5185",
                top_k=1,
                include_values=True,
                include_metadata=True
            )
            
            if job_result.matches:
                job_vector = job_result.matches[0].values
                job_meta = job_result.matches[0].metadata
                
                st.success("✅ Vetor da vaga obtido!")
                st.write(f"**Vaga:** {job_meta.get('titulo', 'N/A')}")
                
                # Buscar candidatos similares
                candidates_result = index.query(
                    vector=job_vector,
                    top_k=7,
                    filter={"type": "candidate"},
                    include_metadata=True,
                    include_values=False
                )
                
                if candidates_result.matches:
                    st.success(f"✅ Encontrados {len(candidates_result.matches)} candidatos similares!")
                    
                    # Mostrar candidatos ranqueados
                    st.markdown("### 🏆 Ranking de Candidatos")
                    
                    for i, match in enumerate(candidates_result.matches):
                        meta = match.metadata
                        with st.expander(f"{i+1}º - {meta.get('nome', 'N/A')} (Score: {match.score:.4f})"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**ID:** {meta.get('candidate_id', 'N/A')}")
                                st.write(f"**Email:** {meta.get('email', 'N/A')}")
                                st.write(f"**Cidade:** {meta.get('cidade', 'N/A')}")
                            with col2:
                                st.write(f"**Estado:** {meta.get('estado', 'N/A')}")
                                st.write(f"**Score:** {match.score:.4f}")
                else:
                    st.warning("⚠️ Nenhum candidato similar encontrado")
            else:
                st.error("❌ Vaga 5185 não encontrada")
                
        except Exception as e:
            st.error(f"❌ Erro na busca por similaridade: {e}")

else:
    st.error("❌ Não foi possível conectar ao Pinecone")

# Informações de debug
st.markdown("---")
st.markdown("### 🔧 Informações de Debug")
st.write("**Índice:** decision-recruiter")
st.write("**Dimensões esperadas:** 512")
st.write("**Tipos de dados:** job, candidate")
