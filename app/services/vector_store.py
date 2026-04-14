import os
import logging
from typing import List, Optional
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from config import DATABASE_DIR

logger = logging.getLogger("KEVIN-BRAIN")

class VectorStore:
    """
    Kevin's Long-Term Memory (RAG logic).
    Uses FAISS and HuggingFace embeddings to store and search technical docs.
    """
    def __init__(self):
        self.index_path = DATABASE_DIR / "faiss_index"
        # Using a small, fast model for embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = self._load_or_create()

    def _load_or_create(self):
        """Loads index from disk or creates a new one."""
        if os.path.exists(self.index_path):
            try:
                logger.info("Loading Kevin's technical memories from disk...")
                return FAISS.load_local(str(self.index_path), self.embeddings, allow_dangerous_deserialization=True)
            except Exception as e:
                logger.error(f"Failed to load vector store: {e}")
        
        logger.info("Initializing new memory bank for Kevin.")
        # Need at least one doc to initialize FAISS
        initial_doc = [Document(page_content="Kevin is an advanced AI assistant created by AS.", metadata={"source": "init"})]
        vs = FAISS.from_documents(initial_doc, self.embeddings)
        return vs

    def add_texts(self, texts: List[str], metadata: Optional[List[dict]] = None):
        """Adds new information to Kevin's knowledge base."""
        self.vector_store.add_texts(texts, metadatas=metadata)
        self.vector_store.save_local(str(self.index_path))
        logger.info(f"Learned {len(texts)} new things.")

    def search(self, query: str, k: int = 3) -> List[Document]:
        """Searches Kevin's memory for relevant information."""
        return self.vector_store.similarity_search(query, k=k)

# Global Instance if needed
# vector_memory = VectorStore()
