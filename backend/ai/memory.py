import sqlite3
import os

# 📁 caminho absoluto seguro
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")

DB_PATH = os.path.join(DATA_DIR, "memory.db")


class Memory:
    def __init__(self):

        # cria pasta data automaticamente
        os.makedirs(DATA_DIR, exist_ok=True)

        # conexão sqlite
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)

        self.cursor = self.conn.cursor()

        # tabela
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT,
            response TEXT
        )
        """)

        self.conn.commit()

    # 💾 salva conversa
    def save(self, user_input, response):

        self.cursor.execute("""
        INSERT INTO conversations (user_input, response)
        VALUES (?, ?)
        """, (user_input, response))

        self.conn.commit()

    # 📚 pega histórico
    def get_last(self, limit=5):

        self.cursor.execute("""
        SELECT user_input, response
        FROM conversations
        ORDER BY id DESC
        LIMIT ?
        """, (limit,))

        rows = self.cursor.fetchall()

        return rows[::-1]

    # 🧹 limpar memória
    def clear(self):

        self.cursor.execute("DELETE FROM conversations")

        self.conn.commit()