import streamlit as st
import requests
import json
import pinecone
from pinecone import Pinecone

st.title("🔍 Debug - Decision Recruiter")

# === DEBUG 1: PINECONE ===
st.header("🎯 Teste 1: Pinecone")

try:
    API_KEY = "pcsk_5DfEc5_JTj7W19EkqEm2awJNed9dnmdfNtKBuNv3MNzPnX9R2tJv3dRNbUEJcm9gXWNYko"
    INDEX_NAME = "decision-recruiter"
    pc = Pinecone(api_key=API_KEY)
    index = pc.Index(INDEX_NAME)
    
    st.success("✅ Pinecone conectado!")
    
    # Testar busca de vagas
    if st.button("🔍 Buscar Vagas no Pinecone"):
        random_vector = [0.1] * 512
        response = index.query(
            vector=random_vector,
            top_k=10,
            include_metadata=True
        )
        
        st.write(f"Total encontrado: {len(response['matches'])}")
        
        # Filtrar vagas
        vagas = [m for m in response['matches'] if m['metadata'].get('type') == 'job']
        st.write(f"Vagas encontradas: {len(vagas)}")
        
        if vagas:
            st.write("Primeira vaga:")
            st.json(vagas[0]['metadata'])
        
        # Filtrar candidatos
        candidatos = [m for m in response['matches'] if m['metadata'].get('type') == 'candidate']
        st.write(f"Candidatos encontrados: {len(candidatos)}")
        
        if candidatos:
            st.write("Primeiro candidato:")
            st.json(candidatos[0]['metadata'])

except Exception as e:
    st.error(f"❌ Erro Pinecone: {e}")

st.markdown("---")

# === DEBUG 2: GITHUB RELEASES ===
st.header("📥 Teste 2: GitHub Releases")

url = "https://github.com/guilcalazans/decision/releases/download/v1.0/complete_data.json"

if st.button("📥 Testar Download GitHub"):
    try:
        with st.status("Baixando..."):
            st.write("🔗 Conectando...")
            response = requests.get(url, timeout=30)
            st.write(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                st.write("📊 Processando JSON...")
                data = response.json()
                
                st.success("✅ Download OK!")
                st.write(f"Jobs: {len(data.get('jobs', {}))}")
                st.write(f"Candidates: {len(data.get('candidates', {}))}")
                st.write(f"Hired: {len(data.get('hired_candidates', {}))}")
                
                # Mostrar primeira vaga
                if data.get('jobs'):
                    primeiro_job_id = list(data['jobs'].keys())[0]
                    st.write(f"Primeira vaga ID: {primeiro_job_id}")
                    st.json(data['jobs'][primeiro_job_id])
                
            else:
                st.error(f"❌ Status: {response.status_code}")
                
    except Exception as e:
        st.error(f"❌ Erro GitHub: {e}")

st.markdown("---")

# === DEBUG 3: BUSCA COMBINADA ===
st.header("🔄 Teste 3: Busca Combinada")

job_id_test = st.text_input("Job ID para testar:", "5185")

if st.button("🎯 Testar Busca Completa"):
    try:
        # 1. Buscar no Pinecone
        st.write("1️⃣ Buscando vaga no Pinecone...")
        job_response = index.query(
            id=f"job_{job_id_test}",
            top_k=1,
            include_values=True,
            include_metadata=True
        )
        
        if job_response['matches']:
            st.success("✅ Vaga encontrada no Pinecone!")
            job_vector = job_response['matches'][0]['values']
            job_meta = job_response['matches'][0]['metadata']
            st.json(job_meta)
            
            # 2. Buscar candidatos similares
            st.write("2️⃣ Buscando candidatos similares...")
            candidates_response = index.query(
                vector=job_vector,
                top_k=10,
                include_metadata=True
            )
            
            candidates = [m for m in candidates_response['matches'] 
                         if m['metadata'].get('type') == 'candidate']
            
            st.write(f"Candidatos similares: {len(candidates)}")
            
            if candidates:
                for i, c in enumerate(candidates[:3]):
                    st.write(f"Candidato {i+1}: {c['metadata'].get('nome')} (Score: {c['score']:.4f})")
            
            # 3. Buscar dados completos
            st.write("3️⃣ Buscando dados completos...")
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                complete_data = response.json()
                
                # Vaga completa
                job_complete = complete_data.get('jobs', {}).get(job_id_test)
                if job_complete:
                    st.success("✅ Dados completos da vaga encontrados!")
                    st.write(f"Título: {job_complete.get('titulo')}")
                    st.write(f"Cliente: {job_complete.get('cliente')}")
                else:
                    st.warning("⚠️ Vaga não encontrada nos dados completos")
                
                # Candidato completo
                if candidates:
                    first_candidate_id = candidates[0]['metadata'].get('candidate_id')
                    candidate_complete = complete_data.get('candidates', {}).get(first_candidate_id)
                    if candidate_complete:
                        st.success("✅ Dados completos do candidato encontrados!")
                        st.write(f"Nome: {candidate_complete.get('nome')}")
                        st.write(f"Email: {candidate_complete.get('email')}")
                    else:
                        st.warning(f"⚠️ Candidato {first_candidate_id} não encontrado nos dados completos")
            
        else:
            st.error(f"❌ Vaga {job_id_test} não encontrada no Pinecone")
            
    except Exception as e:
        st.error(f"❌ Erro na busca: {e}")
        st.exception(e)
