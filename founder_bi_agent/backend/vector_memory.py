import os
import chromadb
from typing import List, Dict, Any
from pathlib import Path
from google import genai
from typing import List, Dict, Any
from pathlib import Path

from founder_bi_agent.backend.config import AgentSettings

class VectorMemoryStore:
    def __init__(self, settings: AgentSettings):
        self.settings = settings
        # Use a writable directory (In Render, /tmp is always writable)
        self.db_path = os.getenv("CHROMA_DB_PATH", "artifacts/chroma_db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize Google GenAI Client (V1 SDK)
        self.genai_client = genai.Client(api_key=self.settings.google_api_key)
        self.embedding_model = "models/gemini-embedding-001"
        
        # We need a custom embedding function adapter for ChromaDB
        class GoogleEmbeddingFunction:
            def __init__(self, client: genai.Client, model: str):
                self.client = client
                self.model = model
            
            def __call__(self, input: chromadb.Documents) -> chromadb.Embeddings:
                try:
                    res = self.client.models.embed_content(
                        model=self.model,
                        contents=list(input)
                    )
                    # Convert to list of lists of floats
                    out = [list(e.values) for e in res.embeddings]
                    return out
                except Exception as e:
                    print(f"DEBUG EMBEDDING CALL ERROR: {e}")
                    raise
                
            def embed_query(self, input: Any) -> list[float]:
                try:
                    txt = str(input[0]) if isinstance(input, list) else str(input)
                    res = self.client.models.embed_content(
                        model=self.model,
                        contents=[txt]
                    )
                    # Convert to list of floats
                    out = list(res.embeddings[0].values)
                    return out
                except Exception as e:
                    print(f"DEBUG EMBEDDING QUERY ERROR: {e}")
                    raise
                
            def embed_documents(self, texts: list[str]) -> list[list[float]]:
                res = self.client.models.embed_content(
                    model=self.model,
                    contents=texts
                )
                return [e.values for e in res.embeddings]
                
            def name(self) -> str:
                return "GoogleGenAIEmbeddingsV1"
                
        self.emb_fn = GoogleEmbeddingFunction(self.genai_client, self.embedding_model)
        
        # Initialize ChromaDB Local Client
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Get or create the collections
        self.collection = self.client.get_or_create_collection(
            name="conversation_memory",
            embedding_function=self.emb_fn
        )

    def add_interaction(self, session_id: str, question: str, response: str) -> None:
        """Embeds and saves the full conversation turn as a document into the collection."""
        if not question or not response:
            return
            
        doc_content = f"User asked: {question}\nAgent responded: {response}"
        
        # Generate a unique ID for this turn
        import uuid
        turn_id = f"{session_id}_{uuid.uuid4().hex[:8]}"
        
        self.collection.add(
            documents=[doc_content],
            metadatas=[{"session_id": session_id}],
            ids=[turn_id]
        )

    def get_relevant_context(self, session_id: str, query: str, k: int = 3) -> str:
        """Queries ChromaDB to find the top K semantically relevant past interactions for the session."""
        try:
            # Manually embed to avoid Chroma internal wrapping issues
            query_emb = self.emb_fn.embed_query(query)
            
            results = self.collection.query(
                query_embeddings=[query_emb],
                n_results=k,
                where={"session_id": session_id}
            )
            
            if not results or not results.get("documents") or not results["documents"][0]:
                return ""
                
            snippets = results["documents"][0]
            context = "\n---\n".join(snippets)
            return f"\n[LONG-TERM MEMORY CONTEXT FROM PAST INTERACTIONS]:\n{context}\n"
        except Exception as e:
            import logging
            logging.getLogger("vector_memory").error(f"Failed to retrieve vector context: {e}", exc_info=True)
            return ""
