import os
import glob
import re
import yaml
import pandas as pd
from flask import Flask, request, jsonify

# LangChain
from langchain_community.chat_models import ChatPerplexity
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.docstore.document import Document
from langchain.schema import SystemMessage
from langchain_community.callbacks.manager import get_openai_callback
from langchain.text_splitter import CharacterTextSplitter

# Arquivo de configuração
CONFIG_FILE = "config.yaml"
with open(CONFIG_FILE, "r") as file:
    config = yaml.safe_load(file)

# Define variável de ambiente com a chave da Perplexity
os.environ["PERPLEXITYAI_API_KEY"] = config["api_key"]["key"]

# Inicializa app Flask
app = Flask(__name__)

# Memória e Contexto dos clientes
client_memories = {}

# Carrega e une dados de cabecalho e itens
def load_merged_documents(cabecalho_path, itens_path):
    try:
        # Colunas selecionadas
        cabecalho_cols = [
            "CHAVE DE ACESSO", "DATA EMISSÃO", "CPF/CNPJ Emitente", "RAZÃO SOCIAL EMITENTE",
            "UF EMITENTE", "MUNICÍPIO EMITENTE", "CNPJ DESTINATÁRIO", "NOME DESTINATÁRIO",
            "UF DESTINATÁRIO", "VALOR NOTA FISCAL"
        ]
        itens_cols = [
            "CHAVE DE ACESSO", "NÚMERO PRODUTO", "DESCRIÇÃO DO PRODUTO/SERVIÇO",
            "CÓDIGO NCM/SH", "CFOP", "QUANTIDADE", "UNIDADE", "VALOR UNITÁRIO", "VALOR TOTAL"
        ]

        # Leitura com colunas filtradas e limite de linhas
        df_cabecalho = pd.read_csv(cabecalho_path, usecols=cabecalho_cols, nrows=2000)
        df_itens = pd.read_csv(itens_path, usecols=itens_cols, nrows=6000)

        # Merge dos dados com base na chave
        df_merged = pd.merge(df_itens, df_cabecalho, on="CHAVE DE ACESSO", how="left")

        # Gerar documentos com split
        documents = []
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        content = df_merged.to_string(index=False)
        splits = text_splitter.split_text(content)
        for chunk in splits:
            documents.append(Document(page_content=chunk, metadata={"source": "merged_csvs"}))
        return documents

    except Exception as e:
        print(f"Erro ao carregar e unir arquivos CSV: {e}")
        return []

# Caminhos dos arquivos CSV
cabecalho_path = "documents/202401_NFs_Cabecalho.csv"
itens_path = "documents/202401_NFs_Itens.csv"

# Carrega os documentos unificados
documents = load_merged_documents(cabecalho_path, itens_path)

# Cria embeddings com HuggingFace
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Cria o vectorstore com FAISS
vectorstore = FAISS.from_documents(documents, embeddings)

# Inicializa modelo de chat
chat = ChatPerplexity(
    model=config["model"]["name"],
    temperature=0,
    pplx_api_key=config["api_key"]["key"]
)

# Mensagem de sistema para restringir o domínio de respostas
system_message = SystemMessage(content=(
    "Você é um assistente especializado em análise de Notas Fiscais. "
    "Responda perguntas como: fornecedor que recebeu mais, item mais comprado, cidade com maior volume de compras, qual item está presente na NF, "
    "ou qualquer análise baseada nos dados das Notas Fiscais presentes nos arquivos CSV. Sua análise deve ser exclusivamente nos dados que estão nos arquivos .csv"
    "Se a pergunta não for sobre Notas Fiscais, responda: 'Desculpe, só posso responder sobre Notas Fiscais.'"
))

# Cria retriever
retriever = vectorstore.as_retriever()

# Endpoint para interação com o assistente
@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    if not data or "client_id" not in data or "question" not in data:
        return jsonify({"error": "Requisição inválida. Forneça 'client_id' e 'question'."}), 400

    client_id = data["client_id"]
    question = data["question"]

    # Recupera ou cria a memória de conversa do cliente
    if client_id not in client_memories:
        client_memories[client_id] = ConversationBufferWindowMemory(memory_key="chat_history", return_messages=True, k=3)
    memory = client_memories[client_id]

    # Adiciona system message se ainda não houver histórico
    if not memory.chat_memory.messages:
        memory.chat_memory.add_message(system_message)

    # Cria cadeia com Retrieval e memória
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=chat,
        retriever=retriever,
        memory=memory
    )

    try:
        with get_openai_callback() as cb:
            result = qa_chain.invoke({"question": question})
            answer = result.get("answer", "")

            print(f"\n\U0001F50D Métricas de Uso:")
            print(f"\u2022 Tokens totais: {cb.total_tokens}")
            print(f"\u2022 Tokens prompt: {cb.prompt_tokens}")
            print(f"\u2022 Tokens completion: {cb.completion_tokens}")
            print(f"\u2022 Custo estimado: ${format(cb.total_cost, '.5f')}")

            return jsonify({"answer": answer})
    except Exception as e:
        print(f"Erro: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)
