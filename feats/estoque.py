import customtkinter as ctk
from tkinter import ttk, messagebox
import sys
import os

# Isso resolve o erro de importar o database quando rodar
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

class AbaEstoque(ctk.CTkScrollableFrame):
    def __init__(self, master, refresh_callback):
        super().__init__(master, fg_color="transparent")
        self.refresh_cb = refresh_callback
        self.tabela_ativa = "filamento"

        ctk.CTkLabel(self, text="🛠️ GESTÃO DE ESTOQUE", font=("Arial", 18, "bold")).pack(pady=10)

        # --- ÁREA DE INPUTS ---
        self.frame_inputs = ctk.CTkFrame(self)
        self.frame_inputs.pack(fill="x", padx=20, pady=10)

        self.ent_id = self.add_field("ID Selecionado:", state="readonly")
        self.ent_nome = self.add_field("Nome / Material:")
        self.ent_qtd = self.add_field("Quantidade (g ou un):")
        self.ent_preco = self.add_field("Preço (R$/g ou Venda):")

        # --- BOTÕES ---
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=10)
        
        ctk.CTkButton(btns, text="+ NOVO FILAMENTO", fg_color="#3498db", command=self.add_novo_filamento).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="SALVAR EDIÇÃO", fg_color="#2ecc71", command=self.salvar).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="EXCLUIR", fg_color="#e74c3c", command=self.excluir).pack(side="left", padx=5)
        # O BOTÃO QUE ESTAVA DANDO ERRO:
        ctk.CTkButton(btns, text="LIMPAR", fg_color="#555", width=60, command=self.limpar).pack(side="left", padx=5)

        # --- TABELAS ---
        self.tree_f = self.criar_tabela(("ID", "Material", "Gramas", "R$/g"), "🧵 FILAMENTOS")
        self.tree_p = self.criar_tabela(("ID", "Nome", "Qtd", "Preço Venda", "Custo Total", "Peso", "Tempo", "H-M", "MKP", "Setup"), "📦 PEÇAS PRONTAS")
        
        self.refresh()

    def add_field(self, txt, state="normal"):
        f = ctk.CTkFrame(self.frame_inputs, fg_color="transparent"); f.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(f, text=txt, width=150, anchor="w").pack(side="left")
        e = ctk.CTkEntry(f); e.pack(side="right", expand=True, fill="x", padx=5); e.configure(state=state)
        return e

    def criar_tabela(self, cols, tit):
        ctk.CTkLabel(self, text=tit, font=("Arial", 14, "bold")).pack(pady=(20, 5))
        t = ttk.Treeview(self, columns=cols, show="headings", height=7)
        for c in cols: 
            t.heading(c, text=c)
            t.column(c, width=100, anchor="center")
        t.pack(fill="x", padx=20)
        t.bind("<<TreeviewSelect>>", lambda e: self.selecionar(t))
        return t

    def selecionar(self, t):
        try:
            selecao = t.selection()
            if not selecao: return
            item = t.item(selecao[0])['values']
            
            self.ent_id.configure(state="normal")
            self.ent_id.delete(0, 'end'); self.ent_id.insert(0, item[0])
            self.ent_id.configure(state="readonly")
            
            self.ent_nome.delete(0, 'end'); self.ent_nome.insert(0, item[1])
            self.ent_qtd.delete(0, 'end'); self.ent_qtd.insert(0, item[2])
            self.ent_preco.delete(0, 'end'); self.ent_preco.insert(0, item[3])
            
            self.tabela_ativa = "filamento" if t == self.tree_f else "produtos"
        except: pass

    def refresh(self):
        for t in [self.tree_f, self.tree_p]:
            for i in t.get_children(): t.delete(i)
        for r in db.query("SELECT * FROM filamento"):
            self.tree_f.insert("", "end", values=r)
        for r in db.query("SELECT * FROM produtos"):
            self.tree_p.insert("", "end", values=r)

    def add_novo_filamento(self):
        try:
            n = self.ent_nome.get()
            q = float(self.ent_qtd.get().replace(",", "."))
            p = float(self.ent_preco.get().replace(",", "."))
            db.execute("INSERT INTO filamento (material, quantidade_g, preco_por_g) VALUES (?,?,?)", (n, q, p))
            messagebox.showinfo("Sucesso", "Filamento Adicionado!")
            self.limpar()
            self.refresh_cb()
        except:
            messagebox.showerror("Erro", "Preencha os campos corretamente.")

    def salvar(self):
        idx = self.ent_id.get()
        if not idx: return
        try:
            n, q, p = self.ent_nome.get(), self.ent_qtd.get(), self.ent_preco.get()
            tabela = "filamento" if self.tabela_ativa == "filamento" else "produtos"
            col_nome = "material" if self.tabela_ativa == "filamento" else "nome"
            col_qtd = "quantidade_g" if self.tabela_ativa == "filamento" else "quantidade"
            col_preco = "preco_por_g" if self.tabela_ativa == "filamento" else "preco_sugerido"
            
            db.execute(f"UPDATE {tabela} SET {col_nome}=?, {col_qtd}=?, {col_preco}=? WHERE id=?", (n, q, p, idx))
            messagebox.showinfo("Sucesso", "Item atualizado!")
            self.refresh_cb()
        except Exception as e: messagebox.showerror("Erro", str(e))

    def excluir(self):
        idx = self.ent_id.get()
        if idx and messagebox.askyesno("Confirmar", "Excluir item?"):
            db.execute(f"DELETE FROM {self.tabela_ativa} WHERE id=?", (idx,))
            self.limpar()
            self.refresh_cb()

    def limpar(self):
        self.ent_id.configure(state="normal")
        for e in [self.ent_id, self.ent_nome, self.ent_qtd, self.ent_preco]:
            e.delete(0, 'end')
        self.ent_id.configure(state="readonly")