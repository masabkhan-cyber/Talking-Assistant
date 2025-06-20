# rag_retriever.py

import os
import hashlib
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
# ✅ Corrected the FAISS import for compatibility with newer langchain versions
from langchain_community.vectorstores import FAISS 
from langchain_huggingface import HuggingFaceEmbeddings

class RAGRetriever:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

        # Generate a unique index folder based on PDF filename hash
        pdf_name = os.path.basename(pdf_path)
        pdf_hash = hashlib.md5(pdf_name.encode()).hexdigest()
        self.index_path = os.path.join("faiss_indexes", pdf_hash)

        if os.path.exists(self.index_path):
            # Allow FAISS to load pickle safely if you trust the source
            self.db = FAISS.load_local(
                self.index_path,
                self.embedding_model,
                allow_dangerous_deserialization=True
            )
        else:
            self._create_vector_store()

    def _create_vector_store(self):
        loader = PyPDFLoader(self.pdf_path)
        documents = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = splitter.split_documents(documents)

        self.db = FAISS.from_documents(docs, self.embedding_model)
        os.makedirs(self.index_path, exist_ok=True)
        self.db.save_local(self.index_path)

    def retrieve_context(self, query, k=3):
        results = self.db.similarity_search(query, k=k)
        return "\n\n".join([doc.page_content for doc in results])
