import sqlite3
import os
import sys

# DETECÇÃO DO CAMINHO REAL DO EXECUTÁVEL
if getattr(sys, 'frozen', False):
    # Se rodando como .exe, BASE_DIR será a pasta onde o .exe está
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Se rodando como .py (durante o desenvolvimento)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define a pasta db e o arquivo fora da pasta temporária
DB_DIR = os.path.join(BASE_DIR, "db")
DB_PATH = os.path.join(DB_DIR, "gestao_3d.db")

def init_db():
    # Cria a pasta 'db' fisicamente ao lado do seu executável
    if not os.path.exists(DB_DIR): 
        os.makedirs(DB_DIR)
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # 1. FILAMENTOS
        cursor.execute("""CREATE TABLE IF NOT EXISTS filamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            material TEXT NOT NULL, 
            cor TEXT,
            quantidade_g REAL NOT NULL, 
            peso_atual_g REAL NOT NULL,
            preco_por_g REAL NOT NULL,
            custo_compra REAL DEFAULT 0.0,
            data_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        
        # 2. PRODUTOS (Removido Markup e Setup)
        cursor.execute("""CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nome TEXT NOT NULL, 
            peso_u REAL NOT NULL, 
            tempo_h REAL NOT NULL,
            quantidade_produzida INTEGER DEFAULT 1,
            hora_maq REAL, 
            preco_sugerido REAL)""")
        
        # 3. VENDAS
        cursor.execute("""CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            produto_id INTEGER, 
            filamento_id INTEGER, 
            qtd_vendida INTEGER NOT NULL, 
            valor_total REAL NOT NULL, 
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produto_id) REFERENCES produtos(id),
            FOREIGN KEY (filamento_id) REFERENCES filamento(id))""")
        
        # 4. FINANCEIRO
        cursor.execute("""CREATE TABLE IF NOT EXISTS financeiro (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            tipo TEXT CHECK(tipo IN ('ENTRADA', 'SAIDA')), 
            valor REAL NOT NULL, 
            descricao TEXT,
            venda_id INTEGER,
            filamento_id INTEGER,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE SET NULL,
            FOREIGN KEY (filamento_id) REFERENCES filamento(id) ON DELETE SET NULL)""")
        
        # 5. REPAROS
        cursor.execute("""CREATE TABLE IF NOT EXISTS reparos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            descricao TEXT NOT NULL, 
            custo REAL NOT NULL, 
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

        # --- TRIGGERS DE AUTOMAÇÃO ---

        # Trigger 1: APENAS lança entrada financeira na Venda (Baixa de estoque agora é manual no Python)
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS tg_venda_processada
        AFTER INSERT ON vendas
        BEGIN
            INSERT INTO financeiro (tipo, valor, descricao, venda_id)
            VALUES ('ENTRADA', NEW.valor_total, 'Venda: ' || (SELECT nome FROM produtos WHERE id = NEW.produto_id), NEW.id);
        END;
        """)

        # Trigger 2: Lança saída financeira na Compra de Filamento
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS tg_compra_filamento
        AFTER INSERT ON filamento
        BEGIN
            INSERT INTO financeiro (tipo, valor, descricao, filamento_id)
            VALUES ('SAIDA', NEW.custo_compra, 'Compra: ' || NEW.material || ' ' || NEW.cor, NEW.id);
        END;
        """)

        # Trigger 3: Lança saída financeira no Reparo
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS tg_reparo_financeiro
        AFTER INSERT ON reparos
        BEGIN
            INSERT INTO financeiro (tipo, valor, descricao, data)
            VALUES ('SAIDA', NEW.custo, 'Manutenção: ' || NEW.descricao, NEW.data);
        END;
        """)
        
        conn.commit()

def query(sql, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

def execute(sql, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute(sql, params)
        conn.commit()