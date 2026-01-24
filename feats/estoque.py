import customtkinter as ctk
from tkinter import ttk, messagebox
import database as db

class AbaEstoque(ctk.CTkScrollableFrame):
    def __init__(self, master, refresh_callback):
        super().__init__(master, fg_color="transparent")
        self.refresh_cb = refresh_callback
        self.tabela_ativa = "filamento"

        # --- ÁREA DE CADASTRO / EDIÇÃO ---
        ctk.CTkLabel(self, text="🛠️ GERENCIAR ITEM SELECIONADO", font=("Arial", 16, "bold")).pack(pady=10)
        self.frame_inputs = ctk.CTkFrame(self)
        self.frame_inputs.pack(fill="x", padx=20, pady=10)

        self.ent_id = self.add_field(self.frame_inputs, "ID (Fixo):", state="readonly")
        self.ent_nome = self.add_field(self.frame_inputs, "Nome / Material:")
        self.ent_qtd = self.add_field(self.frame_inputs, "Quantidade (g ou un):")
        self.ent_preco = self.add_field(self.frame_inputs, "Preço Unitário / g:")

        self.frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_btns.pack(pady=15)
        ctk.CTkButton(self.frame_btns, text="ADICIONAR FILAMENTO", fg_color="#3498db", command=self.add_filamento).pack(side="left", padx=5)
        ctk.CTkButton(self.frame_btns, text="SALVAR EDIÇÃO", fg_color="#2ecc71", command=self.salvar_edicao).pack(side="left", padx=5)
        ctk.CTkButton(self.frame_btns, text="EXCLUIR ITEM", fg_color="#e74c3c", command=self.excluir_item).pack(side="left", padx=5)
        ctk.CTkButton(self.frame_btns, text="LIMPAR", fg_color="#95a5a6", width=60, command=self.limpar_campos).pack(side="left", padx=5)

        # --- TABELAS ---
        # Colunas completas para Filamento
        self.tree_f = self.criar_tabela(("ID", "Material", "Gramas Restantes", "Preço por Grama"), "🧵 FILAMENTOS EM ESTOQUE")
        
        # Colunas completas para Peças (Incluindo dados técnicos do banco)
        self.tree_p = self.criar_tabela(
            ("ID", "Nome", "Qtd", "Preço Sug.", "Total Prod.", "Peso(g)", "Tempo(h)", "H-Máq", "Margem%"), 
            "📦 ESTOQUE DE PEÇAS PRONTAS (DADOS TÉCNICOS)"
        )
        self.refresh()

    def add_field(self, master, label_text, state="normal"):
        f = ctk.CTkFrame(master, fg_color="transparent")
        f.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(f, text=label_text, width=150, anchor="w").pack(side="left")
        e = ctk.CTkEntry(f, state=state); e.pack(side="right", expand=True, fill="x", padx=5)
        return e

    def criar_tabela(self, cols, titulo):
        ctk.CTkLabel(self, text=titulo, font=("Arial", 14, "bold")).pack(pady=(20, 5))
        t = ttk.Treeview(self, columns=cols, show="headings", height=8)
        for c in cols:
            t.heading(c, text=c); t.column(c, width=90, anchor="center")
        t.pack(fill="x", padx=20)
        t.bind("<<TreeviewSelect>>", lambda e: self.carregar_selecao(t))
        return t

    def carregar_selecao(self, t):
        try:
            item = t.item(t.selection()[0])['values']
            self.limpar_campos()
            self.ent_id.configure(state="normal")
            self.ent_id.insert(0, item[0]); self.ent_id.configure(state="readonly")
            self.ent_nome.insert(0, item[1])
            self.ent_qtd.insert(0, item[2])
            self.ent_preco.insert(0, item[3])
            self.tabela_ativa = "filamento" if t == self.tree_f else "produtos"
        except: pass

    def refresh(self):
        for t in [self.tree_f, self.tree_p]:
            for i in t.get_children(): t.delete(i)
        for r in db.query("SELECT * FROM filamento"):
            self.tree_f.insert("", "end", values=r)
        # SELECT * traz: id, nome, quantidade, preco_sugerido, valor_total_producao, peso_u, tempo_h, hora_maq, margem
        for r in db.query("SELECT * FROM produtos"):
            self.tree_p.insert("", "end", values=r)

    # ... (limpar_campos, add_filamento, salvar_edicao, excluir_item iguais aos anteriores)
    def limpar_campos(self):
        for e in [self.ent_nome, self.ent_qtd, self.ent_preco]: e.delete(0, 'end')
        self.ent_id.configure(state="normal"); self.ent_id.delete(0, 'end'); self.ent_id.configure(state="readonly")
    
    def conv(self, v):
        try: return float(str(v).replace(",", "."))
        except: return 0.0

    def add_filamento(self):
        db.execute("INSERT INTO filamento (material, quantidade_g, preco_por_g) VALUES (?,?,?)",
                   (self.ent_nome.get(), self.conv(self.ent_qtd.get()), self.conv(self.ent_preco.get())))
        self.refresh_cb()

    def salvar_edicao(self):
        idx = self.ent_id.get()
        if not idx: return
        n, q, p = self.ent_nome.get(), self.conv(self.ent_qtd.get()), self.conv(self.ent_preco.get())
        if self.tabela_ativa == "filamento":
            db.execute("UPDATE filamento SET material=?, quantidade_g=?, preco_por_g=? WHERE id=?", (n, q, p, idx))
        else:
            db.execute("UPDATE produtos SET nome=?, quantidade=?, preco_sugerido=? WHERE id=?", (n, int(q), p, idx))
        self.refresh_cb()

    def excluir_item(self):
        idx = self.ent_id.get()
        if idx and messagebox.askyesno("Confirmar", "Excluir permanentemente?"):
            db.execute(f"DELETE FROM {self.tabela_ativa} WHERE id=?", (idx,))
            self.refresh_cb()