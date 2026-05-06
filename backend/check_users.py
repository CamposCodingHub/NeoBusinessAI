"""
Verificar usuários no banco SQLite
"""
import sqlite3
import os

# Conectar ao banco
db_path = os.path.join(os.path.dirname(__file__), 'lexscan.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Listar usuários
print("=== USUÁRIOS NO BANCO ===")
cursor.execute("SELECT id, email, name, role, is_active, created_at FROM users")
users = cursor.fetchall()

for user in users:
    print(f"ID: {user[0]}")
    print(f"Email: {user[1]}")
    print(f"Nome: {user[2]}")
    print(f"Role: {user[3]}")
    print(f"Ativo: {user[4]}")
    print(f"Criado: {user[5]}")
    print("-" * 40)

print(f"\nTotal: {len(users)} usuários")

# Verificar se admin existe
admin = cursor.execute(
    "SELECT email, password_hash FROM users WHERE email = ?",
    ('admin@neobusiness.ai',)
).fetchone()

if admin:
    print(f"\n✅ Admin encontrado: {admin[0]}")
    print(f"Hash: {admin[1][:30]}...")
else:
    print("\n❌ Admin NÃO encontrado!")

conn.close()
