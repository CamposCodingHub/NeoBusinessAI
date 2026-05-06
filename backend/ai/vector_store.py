import os
import faiss
import numpy as np

from sentence_transformers import SentenceTransformer
from pypdf import PdfReader

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class VectorStore:
    def __init__(self):

        self.documents = []

        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

        self.index = faiss.IndexFlatL2(384)

    def load_pdfs(self):

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
                    np.array(embedding).astype("float32")
                )

                print(f"✅ PDF carregado: {file}")

            except Exception as e:

                print(f"⚠️ Erro no PDF {file}: {e}")

    def search(self, query):

        if not self.documents:
            return ""

        query_embedding = self.model.encode([query])

        D, I = self.index.search(
            np.array(query_embedding).astype("float32"),
            1
        )

        idx = I[0][0]

        if idx < len(self.documents):
            return self.documents[idx][:3000]

        return ""