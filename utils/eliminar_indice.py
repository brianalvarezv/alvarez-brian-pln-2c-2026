import os
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

RAIZ = Path(__file__).resolve().parent
load_dotenv(RAIZ / ".env")
MODELO_GENERADOR = os.getenv("OLLAMA_MODEL", "granite4:latest")
MODELO_EMBEDDINGS = os.getenv("OLLAMA_EMBEDDING_MODEL", "bge-m3")
NOMBRE_COLECCION = (
    "legislacion_comercio_"
    + MODELO_EMBEDDINGS.replace(":", "_").replace("-", "_")
)

#Función para eliminar el índice Chroma actual, si se quiere reindexar
def eliminar_indice():
    embeddings = OllamaEmbeddings(model=MODELO_EMBEDDINGS)

    indice = Chroma(
        collection_name=NOMBRE_COLECCION,
        embedding_function=embeddings,
        persist_directory=str(RAIZ / "chroma_db_bge_m3"),
    )

    indice.delete_collection()

    print("Índice eliminado correctamente.")

eliminar_indice()