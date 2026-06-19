import os

from pypdf import PdfReader

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class VectorStore:
    def __init__(self):

        self.documents = []
        self.model = None
        self.faiss = None
        self.np = None
        self.index = None

    def _ensure_backend(self):
        if self.index is None:
            import faiss
            import numpy as np

            self.faiss = faiss
            self.np = np
            self.index = faiss.IndexFlatL2(384)

    def _ensure_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2"
            )

    def load_pdfs(self):
        self._ensure_backend()
        self._ensure_model()

        pdf_dir = os.path.join(BASE_DIR, "knowledge", "docs")

        if not os.path.exists(pdf_dir):
            print("⚠️ Pasta knowledge/docs não encontrada.")
            return

        for file in os.listdir(pdf_dir):

            if not file.endswith(".pdf"):
                continue

            path = os.path.join(pdf_dir, file)

            try:

                # 🚨 ignora pdf vazio
                if os.path.getsize(path) == 0:
                    print(f"⚠️ PDF vazio ignorado: {file}")
                    continue

                reader = PdfReader(path)

                text = ""

                for page in reader.pages:

                    extracted = page.extract_text()

                    if extracted:
                        text += extracted

                # 🚨 ignora pdf sem texto
                if not text.strip():
                    print(f"⚠️ PDF sem texto ignorado: {file}")
                    continue

                self.documents.append(text)

                embedding = self.model.encode([text])

                self.index.add(
                    self.np.array(embedding).astype("float32")
                )

                print(f"✅ PDF carregado: {file}")

            except Exception as e:

                print(f"⚠️ Erro no PDF {file}: {e}")

    def search(self, query, top_k=1):
        self._ensure_backend()
        self._ensure_model()

        if not self.documents:
            return ""

        query_embedding = self.model.encode([query])

        D, I = self.index.search(
            self.np.array(query_embedding).astype("float32"),
            max(1, top_k)
        )
        matches = []

        for idx in I[0]:
            if idx < len(self.documents):
                matches.append(self.documents[idx][:3000])

        return "\n\n---\n\n".join(matches)
