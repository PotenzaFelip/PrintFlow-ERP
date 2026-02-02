import customtkinter as ctk
from tkinter import messagebox
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

class AbaCalculadora(ctk.CTkScrollableFrame):
    def __init__(self, master, refresh_callback):
        super().__init__(master, fg_color="transparent")
        self.refresh_callback = refresh_callback
        
        ctk.CTkLabel(self, text="🚀 CALCULADORA DE CUSTO REAL", font=("Arial", 20, "bold")).pack(pady=10)
        
        # --- SELEÇÃO ---
        self.frame_sel = ctk.CTkFrame(self)
        self.frame_sel.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(self.frame_sel, text="Usar Modelo Salvo:").grid(row=0, column=0, padx=10, pady=5)
        self.combo_projetos = ctk.CTkOptionMenu(self.frame_sel, values=self.get_lista_projetos(), command=self.carregar, width=200)
        self.combo_projetos.grid(row=0, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(self.frame_sel, text="Filamento:").grid(row=1, column=0, padx=10, pady=5)
        self.combo_mat = ctk.CTkOptionMenu(self.frame_sel, values=self.get_mats(), width=200, fg_color="#27ae60")
        self.combo_mat.grid(row=1, column=1, padx=10, pady=5)

        # --- INPUTS ---
        self.ent_nome = self.add_i("Nome do Projeto:", "Novo Projeto")
        self.ent_qtd = self.add_i("Qtd de Peças na Impressão:", "1")
        self.ent_peso_total = self.add_i("Peso TOTAL da Bandeja (g):", "0")
        self.ent_horas = self.add_i("Tempo Total (h):", "0")
        self.ent_hm = self.add_i("Hora-Máquina (R$):", "16.50")

        # --- RESULTADOS ---
        self.lbl_detalhes = ctk.CTkLabel(self, text="Material: R$ 0.00 | Máquina: R$ 0.00", font=("Arial", 12))
        self.lbl_detalhes.pack(pady=(15, 0))
        
        self.lbl_res = ctk.CTkLabel(self, text="Custo Total: R$ 0,00", font=("Arial", 26, "bold"), text_color="#2ecc71")
        self.lbl_res.pack(pady=5)
        
        self.lbl_unitario = ctk.CTkLabel(self, text="Custo Unitário: R$ 0,00", font=("Arial", 16), text_color="#3498db")
        self.lbl_unitario.pack(pady=(0, 10))

        # --- BOTÕES ---
        ctk.CTkButton(self, text="CALCULAR CUSTOS", fg_color="#555", height=40, command=lambda: self.calc(registrar=False)).pack(pady=5, fill="x", padx=50)
        ctk.CTkButton(self, text="EFETIVAR E SALVAR (CATÁLOGO + ESTOQUE)", fg_color="#e67e22", height=50, font=("Arial", 14, "bold"), command=lambda: self.calc(registrar=True)).pack(pady=5, fill="x", padx=50)

    def add_i(self, txt, padrao):
        f = ctk.CTkFrame(self, fg_color="transparent"); f.pack(fill="x", padx=50)
        ctk.CTkLabel(f, text=txt, width=200, anchor="w").pack(side="left")
        e = ctk.CTkEntry(f, width=150, justify="center"); e.insert(0, padrao); e.pack(side="right", pady=2)
        return e

    def get_lista_projetos(self):
        try:
            res = db.query("SELECT nome FROM produtos")
            return ["Novo Projeto"] + [(p['nome'] if isinstance(p, dict) else p[0]) for p in res]
        except: return ["Novo Projeto"]

    def get_mats(self):
        try:
            mats = db.query("SELECT material, cor, id FROM filamento WHERE peso_atual_g > 0")
            return [f"{m['material'] if isinstance(m, dict) else m[0]} {m['cor'] if isinstance(m, dict) else m[1]} | ID:{m['id'] if isinstance(m, dict) else m[2]}" for m in mats] if mats else ["Sem Filamento"]
        except: return ["Sem Filamento"]

    def carregar(self, n):
        # 1. Limpa todos os campos primeiro
        self.ent_nome.delete(0, 'end')
        self.ent_peso_total.delete(0, 'end')
        self.ent_horas.delete(0, 'end')
        self.ent_qtd.delete(0, 'end')
        self.ent_hm.delete(0, 'end')

        # 2. Se for Novo Projeto, define os padrões e sai
        if n == "Novo Projeto":
            self.ent_nome.insert(0,"Novo Projeto")
            self.ent_qtd.insert(0, "1")
            self.ent_peso_total.insert(0, "0")
            self.ent_horas.insert(0, "0")
            self.ent_hm.insert(0, "16.50")
            self.lbl_detalhes.configure(text="Material: R$ 0.00 | Máquina: R$ 0.00")
            self.lbl_res.configure(text="Custo Total: R$ 0.00")
            self.lbl_unitario.configure(text="Custo Unitário: R$ 0.00")
            return

        # 3. Se for um projeto existente, busca no banco
        try:
            res = db.query("SELECT * FROM produtos WHERE nome=?", (n,))
            if res:
                d = res[0]
                # Suporte para dicionário (Row) ou Tupla
                nome = d['nome'] if isinstance(d, dict) else d[1]
                peso = d['peso_u'] if isinstance(d, dict) else d[2]
                horas = d['tempo_h'] if isinstance(d, dict) else d[3]
                qtd = d['quantidade_produzida'] if isinstance(d, dict) else d[4]
                hm = d['hora_maq'] if isinstance(d, dict) else d[5]

                self.ent_nome.insert(0, str(nome))
                self.ent_peso_total.insert(0, str(peso))
                self.ent_horas.insert(0, str(horas))
                self.ent_qtd.insert(0, str(qtd))
                self.ent_hm.insert(0, str(hm))
                
                # Recalcula as labels sem registrar no banco
                self.calc(registrar=False)
        except Exception as e:
            print(f"Erro ao carregar projeto: {e}")

    def calc(self, registrar):
        try:
            # 1. Identificação
            txt_mat = self.combo_mat.get()
            if "ID:" not in txt_mat: return
            id_f = int(txt_mat.split("ID:")[1].strip())
            
            # 2. Captura de Inputs
            qtd = int(self.ent_qtd.get() or 1)
            peso_bandeja = float(self.ent_peso_total.get().replace(",", "."))
            tempo_t = float(self.ent_horas.get().replace(",", "."))
            v_hm = float(self.ent_hm.get().replace(",", "."))

            # 3. Busca Dados
            res = db.query("SELECT preco_por_g, peso_atual_g FROM filamento WHERE id=?", (id_f,))
            preco_g = float(res[0]['preco_por_g'] if isinstance(res[0], dict) else res[0][0])
            saldo_atual = float(res[0]['peso_atual_g'] if isinstance(res[0], dict) else res[0][1])

            # Cálculos
            custo_mat = round(peso_bandeja * preco_g, 2)
            custo_maq = round(tempo_t * v_hm, 2)
            total = round(custo_mat + custo_maq, 2)
            unid = round(total / qtd, 2)

            self.lbl_detalhes.configure(text=f"Material: R$ {custo_mat:.2f} | Máquina: R$ {custo_maq:.2f}")
            self.lbl_res.configure(text=f"Custo Total: R$ {total:.2f}")
            self.lbl_unitario.configure(text=f"Custo Unitário: R$ {unid:.2f}")

            if registrar:
                if peso_bandeja > (saldo_atual + 0.01): # Margem para erro de arredondamento
                    return messagebox.showerror("Erro", "Estoque insuficiente!")

                nome_p = self.ent_nome.get()
                novo_saldo = round(saldo_atual - peso_bandeja, 2)

                # A. ATUALIZA ESTOQUE NO PYTHON (Sem dupla cobrança do banco)
                db.execute("UPDATE filamento SET peso_atual_g = ? WHERE id = ?", (novo_saldo, id_f))

                # B. SALVA PRODUTO
                db.execute("""INSERT OR REPLACE INTO produtos 
                              (id, nome, peso_u, tempo_h, quantidade_produzida, hora_maq, preco_sugerido) 
                              VALUES ((SELECT id FROM produtos WHERE nome = ?), ?, ?, ?, ?, ?, ?)""",
                           (nome_p, nome_p, peso_bandeja, tempo_t, qtd, v_hm, total))
                
                # C. REGISTRA VENDA (O Trigger novo agora só mexe no financeiro)
                p_res = db.query("SELECT id FROM produtos WHERE nome=?", (nome_p,))
                p_id = p_res[0]['id'] if isinstance(p_res[0], dict) else p_res[0][0]
                db.execute("INSERT INTO vendas (produto_id, filamento_id, qtd_vendida, valor_total) VALUES (?,?,?,?)", 
                           (p_id, id_f, qtd, total))
                messagebox.showinfo("Sucesso", f"Produto Efetivado com Sucesso")
                self.refresh_callback()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {e}")