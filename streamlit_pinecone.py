import streamlit as st
import pinecone
from pinecone import Pinecone
import numpy as np

# Inicializa Pinecone
API_KEY = "pcsk_5DfEc5_JTj7W19EkqEm2awJNed9dnmdfNtKBuNv3MNzPnX9R2tJv3dRNbUEJcm9gXWNYko"
INDEX_NAME = "decision-recruiter"

pc = Pinecone(api_key=API_KEY)
index = pc.Index(INDEX_NAME)

st.title("🔍 Busca de Embeddings no Pinecone")

st.markdown("Insira um vetor de exemplo (ou use um aleatório):")

use_random = st.checkbox("Usar vetor aleatório", value=True)

if use_random:
    query_vector = np.random.rand(512).tolist()  # Supondo vetores de 768 dimensões
else:
    vector_str = st.text_area("Cole aqui seu vetor (valores separados por vírgula)", height=150)
    try:
        query_vector = [float(x.strip()) for x in vector_str.split(",") if x.strip()]
    except:
        st.error("❌ Vetor inválido")
        query_vector = None

if st.button("🔎 Buscar similares") and query_vector:
    st.write("🔄 Consultando o índice...")

    try:
        response = index.query(
            vector=query_vector,
            top_k=5,
            include_metadata=True
        )
        
        st.success(f"✅ Resultados encontrados: {len(response['matches'])}")
        
        for match in response['matches']:
            st.subheader(f"ID: {match['id']}")
            st.write(f"📏 Score: {match['score']:.4f}")
            st.json(match['metadata'])

    except Exception as e:
        st.error(f"❌ Erro na consulta: {e}")
