import customtkinter as ctk
from tkinter import ttk, messagebox
import sys
import os

# Garante a importação do banco de dados
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

class AbaEstoque(ctk.CTkScrollableFrame):
    def __init__(self, master, refresh_callback):
        super().__init__(master, fg_color="transparent")
        self.refresh_cb = refresh_callback
        self.tabela_ativa = "filamento"

        ctk.CTkLabel(self, text="🛠️ GESTÃO INTEGRADA DE ESTOQUE", font=("Arial", 20, "bold")).pack(pady=10)

        # --- ÁREA DE INPUTS ---
        self.frame_inputs = ctk.CTkFrame(self)
        self.frame_inputs.pack(fill="x", padx=20, pady=10)

        # Campos adaptados para o novo BD
        self.ent_id = self.add_field("ID Selecionado:", state="readonly")
        self.ent_nome = self.add_field("Material (Ex: PLA):")
        self.ent_cor = self.add_field("Cor:")
        self.ent_qtd_total = self.add_field("Peso Inicial (g):")
        self.ent_preco_g = self.add_field("Preço por Grama (R$):")
        self.ent_custo_total = self.add_field("Custo da Compra (R$):")

        # --- BOTÕES ---
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=10)
        
        ctk.CTkButton(btns, text="+ NOVO FILAMENTO", fg_color="#3498db", command=self.add_novo_filamento).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="SALVAR EDIÇÃO", fg_color="#2ecc71", command=self.salvar).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="EXCLUIR", fg_color="#e74c3c", command=self.excluir).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="LIMPAR", fg_color="#555", width=60, command=self.limpar).pack(side="left", padx=5)

        # --- TABELAS ---
        # Tabela de Filamentos ajustada para mostrar o Saldo Atual (peso_atual_g)
        self.tree_f = self.criar_tabela(
            ("ID", "Material", "Cor", "Inicial (g)", "Saldo Atual (g)", "R$/g", "Custo Total"), 
            "🧵 ESTOQUE DE FILAMENTOS (Saldo Real)"
        )
        
        self.tree_p = self.criar_tabela(
            ("ID", "Nome", "Peso (g)", "Tempo (h)", "H-M", "Markup", "Setup", "Preço Sugerido"), 
            "📦 CATÁLOGO DE PRODUTOS"
        )
        
        self.refresh()

    def add_field(self, txt, state="normal"):
        f = ctk.CTkFrame(self.frame_inputs, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(f, text=txt, width=150, anchor="w").pack(side="left")
        e = ctk.CTkEntry(f)
        e.pack(side="right", expand=True, fill="x", padx=5)
        e.configure(state=state)
        return e

    def criar_tabela(self, cols, tit):
        ctk.CTkLabel(self, text=tit, font=("Arial", 14, "bold")).pack(pady=(20, 5))
        t = ttk.Treeview(self, columns=cols, show="headings", height=8)
        for c in cols: 
            t.heading(c, text=c)
            t.column(c, width=90, anchor="center")
        t.pack(fill="x", padx=20)
        t.bind("<<TreeviewSelect>>", lambda e: self.selecionar(t))
        return t

    def selecionar(self, t):
        try:
            selecao = t.selection()
            if not selecao: return
            item = t.item(selecao[0])['values']
            
            self.limpar()
            self.ent_id.configure(state="normal")
            self.ent_id.insert(0, item[0])
            self.ent_id.configure(state="readonly")
            
            if t == self.tree_f:
                self.tabela_ativa = "filamento"
                self.ent_nome.insert(0, item[1])
                self.ent_cor.insert(0, item[2])
                self.ent_qtd_total.insert(0, item[3])
                self.ent_preco_g.insert(0, item[5])
                self.ent_custo_total.insert(0, item[6])
            else:
                self.tabela_ativa = "produtos"
                self.ent_nome.insert(0, item[1])
                # Para produtos, adaptamos os inputs conforme necessário
        except: pass

    def refresh(self):
        # Limpa as tabelas antes de recarregar
        for t in [self.tree_f, self.tree_p]:
            for i in t.get_children(): 
                t.delete(i)
        
        # 1. Atualiza Tabela de Filamentos
        # Note o tuple(r) para evitar o erro de exibição
        sql_f = "SELECT id, material, cor, quantidade_g, peso_atual_g, preco_por_g, custo_compra FROM filamento"
        for r in db.query(sql_f):
            self.tree_f.insert("", "end", values=tuple(r))
            
        # 2. Atualiza Tabela de Produtos (Catálogo)
        # Aqui é onde estava mostrando os valores errados
        sql_p = "SELECT id, nome, peso_u, tempo_h, hora_maq, margem, setup_valor, preco_sugerido FROM produtos"
        for r in db.query(sql_p):
            self.tree_p.insert("", "end", values=tuple(r))

    def add_novo_filamento(self):
        try:
            n = self.ent_nome.get()
            c = self.ent_cor.get()
            qi = float(self.ent_qtd_total.get().replace(",", "."))
            pg = float(self.ent_preco_g.get().replace(",", "."))
            ct = float(self.ent_custo_total.get().replace(",", "."))
            
            # No NOVO BD, peso_atual_g começa igual ao inicial
            sql = """INSERT INTO filamento 
                     (material, cor, quantidade_g, peso_atual_g, preco_por_g, custo_compra) 
                     VALUES (?, ?, ?, ?, ?, ?)"""
            db.execute(sql, (n, c, qi, qi, pg, ct))
            
            messagebox.showinfo("Sucesso", "Filamento e Gasto Financeiro registrados!")
            self.limpar()
            self.refresh_cb()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    def salvar(self):
        idx = self.ent_id.get()
        if not idx: return
        try:
            if self.tabela_ativa == "filamento":
                n, cor, qi, pg, ct = self.ent_nome.get(), self.ent_cor.get(), self.ent_qtd_total.get(), self.ent_preco_g.get(), self.ent_custo_total.get()
                db.execute("""UPDATE filamento SET material=?, cor=?, quantidade_g=?, preco_por_g=?, custo_compra=? 
                              WHERE id=?""", (n, cor, qi, pg, ct, idx))
            
            messagebox.showinfo("Sucesso", "Dados atualizados!")
            self.refresh_cb()
        except Exception as e: 
            messagebox.showerror("Erro", str(e))

    def excluir(self):
        idx = self.ent_id.get()
        if idx and messagebox.askyesno("Confirmar", "Excluir item? Isso pode afetar o histórico de vendas."):
            try:
                db.execute(f"DELETE FROM {self.tabela_ativa} WHERE id=?", (idx,))
                self.limpar()
                self.refresh_cb()
            except:
                messagebox.showerror("Erro", "Não é possível excluir: item vinculado a uma venda.")

    def limpar(self):
        self.ent_id.configure(state="normal")
        for e in [self.ent_id, self.ent_nome, self.ent_cor, self.ent_qtd_total, self.ent_preco_g, self.ent_custo_total]:
            e.delete(0, 'end')
        self.ent_id.configure(state="readonly")