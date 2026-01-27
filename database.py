import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "db")
DB_PATH = os.path.join(DB_DIR, "gestao_3d.db")

def init_db():
    if not os.path.exists(DB_DIR): os.makedirs(DB_DIR)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Filamentos
    cursor.execute("""CREATE TABLE IF NOT EXISTS filamento (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        material TEXT, 
        quantidade_g REAL, 
        preco_por_g REAL)""")
    
    # Produtos - Incluindo setup_valor e margem como Markup
    cursor.execute("""CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        nome TEXT, 
        quantidade INTEGER DEFAULT 0, 
        preco_sugerido REAL, 
        valor_total_producao REAL, 
        peso_u REAL, 
        tempo_h REAL, 
        hora_maq REAL, 
        margem REAL,
        setup_valor REAL DEFAULT 10.0)""")
    
    # Histórico de Produção
    cursor.execute("""CREATE TABLE IF NOT EXISTS historico_producao (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        produto_id INTEGER, 
        filamento_id INTEGER, 
        peso_usado REAL, 
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    
    # Vendas
    cursor.execute("""CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        produto_id INTEGER, 
        produto_nome TEXT, 
        qtd_vendida INTEGER, 
        valor_total REAL, 
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    
    conn.commit()
    conn.close()

def query(sql, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

def execute(sql, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()