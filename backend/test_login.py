"""
Testar login do admin
"""
import sqlite3
import os
import sys

# Adicionar o diretório backend ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from security.auth import verify_password

# Conectar ao banco
db_path = os.path.join(os.path.dirname(__file__), 'lexscan.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Buscar hash do admin
admin = cursor.execute(
    "SELECT email, password_hash FROM users WHERE email = ?",
    ('admin@neobusiness.ai',)
).fetchone()

if not admin:
    print("❌ Admin não encontrado!")
    conn.close()
    exit(1)

email, password_hash = admin
print(f"Email: {email}")
print(f"Hash: {password_hash}")
print()

# Testar senha
senha_teste = "admin123"
print(f"Testando senha: '{senha_teste}'")
print(f"Tamanho da senha: {len(senha_teste)} caracteres")

resultado = verify_password(senha_teste, password_hash)
print(f"Resultado: {'✅ CORRETA' if resultado else '❌ INCORRETA'}")

conn.close()
