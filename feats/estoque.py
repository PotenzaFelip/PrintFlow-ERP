import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

class AbaEstoque(ctk.CTkScrollableFrame):
    def __init__(self, master, refresh_callback):
        super().__init__(master, fg_color="transparent")
        self.refresh_cb = refresh_callback
        self.tabela_ativa = "filamento" 
        self.saldo_original = "0"

        ctk.CTkLabel(self, text="🛠️ GESTÃO DE ESTOQUE E CATÁLOGO", font=("Arial", 24, "bold")).pack(pady=20)

        # --- CONTAINER DE ENTRADAS ---
        self.frame_inputs = ctk.CTkFrame(self, border_width=1, border_color="#333")
        self.frame_inputs.pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(self.frame_inputs, text="📋 FORMULÁRIO", font=("Arial", 14, "bold"), text_color="#3498db").pack(pady=10)

        self.ent_id = self.add_field("ID do Registro:", state="readonly")
        self.lbl_nome, self.ent_nome = self.add_field_with_label("Material / Nome:")
        self.lbl_v2, self.ent_v2 = self.add_field_with_label("Cor / Peso Total (g):")
        self.lbl_v3, self.ent_v3 = self.add_field_with_label("Peso Inicial Rolo (g):")
        self.lbl_v4, self.ent_v4 = self.add_field_with_label("R$/g (Calculado):")
        self.lbl_v5, self.ent_v5 = self.add_field_with_label("Custo Compra (R$):")
        self.lbl_data, self.ent_data = self.add_field_with_label("Data da Compra:")
        
        self.ent_data.insert(0, datetime.now().strftime("%d/%m/%Y"))
        
        self.frame_saldo = ctk.CTkFrame(self.frame_inputs, fg_color="transparent")
        self.frame_saldo.pack(fill="x", padx=40, pady=2)
        ctk.CTkLabel(self.frame_saldo, text="Saldo Atual (g):", font=("Arial", 12, "bold"), width=180, anchor="w").pack(side="left")
        self.ent_saldo = ctk.CTkEntry(self.frame_saldo, height=30)
        self.ent_saldo.pack(side="right", fill="x", expand=True)

        self.ent_v3.bind("<KeyRelease>", lambda e: self.calcular_dinamico())
        self.ent_v5.bind("<KeyRelease>", lambda e: self.calcular_dinamico())

        # --- BOTÕES DE AÇÃO ---
        self.frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_btns.pack(pady=20)
        
        ctk.CTkButton(self.frame_btns, text="SALVAR", fg_color="#2980b9", command=self.salvar).pack(side="left", padx=10)
        self.btn_reposicao = ctk.CTkButton(self.frame_btns, text="📦 NOVA COMPRA IGUAL", fg_color="#27ae60", command=self.preparar_reposicao)
        self.btn_reposicao.pack(side="left", padx=10)
        self.btn_reposicao.configure(state="disabled")
        ctk.CTkButton(self.frame_btns, text="EXCLUIR", fg_color="#c0392b", command=self.excluir).pack(side="left", padx=10)
        ctk.CTkButton(self.frame_btns, text="LIMPAR", fg_color="#555", command=self.limpar).pack(side="left", padx=10)

        # --- BARRA DE BUSCA E FILTROS ---
        self.frame_busca_f = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_busca_f.pack(fill="x", padx=30, pady=(20, 0))
        
        self.search_f = ctk.CTkEntry(self.frame_busca_f, placeholder_text="🔍 Pesquisar filamento (Material, Cor ou Data)...", height=35)
        self.search_f.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_f.bind("<KeyRelease>", lambda e: self.refresh())

        self.switch_estoque = ctk.CTkSwitch(self.frame_busca_f, text="Em estoque", command=self.refresh, progress_color="#2ecc71")
        self.switch_estoque.pack(side="right")
        self.switch_estoque.select()

        self.tree_f = self.criar_tabela(("ID", "Material", "Cor", "Total (g)", "Saldo (g)", "R$/g", "Custo", "Data"), "🧵 ESTOQUE FILAMENTOS")

        self.frame_busca_p = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_busca_p.pack(fill="x", padx=30, pady=(30, 0))
        
        self.search_p = ctk.CTkEntry(self.frame_busca_p, placeholder_text="🔍 Pesquisar no catálogo (Nome, Peso ou Preço)...", height=35)
        self.search_p.pack(fill="x", expand=True)
        self.search_p.bind("<KeyRelease>", lambda e: self.refresh())

        self.tree_p = self.criar_tabela(("ID", "Nome", "Peso (g)", "Tempo (h)", "Pçs", "Hora-Máq", "Preço Sug."), "📦 CATÁLOGO PRODUTOS")
        
        self.refresh()

    def refresh(self):
        for t in [self.tree_f, self.tree_p]:
            for i in t.get_children(): t.delete(i)
        
        termo_f = f"%{self.search_f.get()}%"
        apenas_disponiveis = self.switch_estoque.get()
        
        query_f = """SELECT id, material, cor, quantidade_g, peso_atual_g, preco_por_g, custo_compra, data_compra 
                     FROM filamento 
                     WHERE (material LIKE ? OR cor LIKE ? OR data_compra LIKE ?)"""
        if apenas_disponiveis:
            query_f += " AND peso_atual_g > 0"
        
        for r in db.query(query_f, (termo_f, termo_f, termo_f)):
            self.tree_f.insert("", "end", values=tuple(r))
            
        termo_p = f"%{self.search_p.get()}%"
        query_p = """SELECT id, nome, peso_u, tempo_h, quantidade_produzida, hora_maq, preco_sugerido 
                     FROM produtos 
                     WHERE (nome LIKE ? OR preco_sugerido LIKE ?)"""
        
        for r in db.query(query_p, (termo_p, termo_p)):
            self.tree_p.insert("", "end", values=tuple(r))

    def preparar_reposicao(self):
        if not self.ent_id.get(): return
        peso_novo = self.ent_v3.get()
        self.ent_id.configure(state="normal"); self.ent_id.delete(0, 'end'); self.ent_id.configure(state="readonly")
        self.ent_data.delete(0, 'end'); self.ent_data.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.ent_saldo.delete(0, 'end'); self.ent_saldo.insert(0, peso_novo)
        self.saldo_original = str(peso_novo)

    def selecionar(self, t):
        selecao = t.selection()
        if not selecao: return
        item = t.item(selecao[0])['values']
        self.limpar_campos()
        self.ent_id.configure(state="normal"); self.ent_id.insert(0, item[0]); self.ent_id.configure(state="readonly")

        if t == self.tree_f:
            self.tabela_ativa = "filamento"; self.mudar_modo("filamento")
            self.btn_reposicao.configure(state="normal")
            self.ent_nome.insert(0, item[1]); self.ent_v2.insert(0, item[2])
            self.ent_v3.insert(0, item[3]); self.ent_saldo.insert(0, item[4])
            self.saldo_original = str(item[4])
            self.ent_v4.configure(state="normal"); self.ent_v4.insert(0, item[5]); self.ent_v4.configure(state="readonly")
            self.ent_v5.insert(0, item[6]); self.ent_data.insert(0, item[7])
        else:
            self.tabela_ativa = "produtos"; self.mudar_modo("produtos")
            self.btn_reposicao.configure(state="disabled")
            self.ent_nome.insert(0, item[1]); self.ent_v2.insert(0, item[2])
            self.ent_v3.insert(0, item[3]); self.ent_v4.insert(0, item[5]); self.ent_v5.insert(0, item[4])

    def mudar_modo(self, modo):
        self.ent_v5.configure(state="normal")
        if modo == "filamento":
            self.lbl_v2.configure(text="Cor:"); self.lbl_v3.configure(text="Peso Inicial Rolo (g):")
            self.lbl_v4.configure(text="R$/g (Automático):"); self.lbl_v5.configure(text="Custo Compra (R$):")
            self.lbl_data.configure(text="Data da Compra:")
            self.ent_data.configure(state="normal", fg_color=["#F9F9FA", "#1D1E1E"])
            self.frame_saldo.pack(fill="x", padx=40, pady=2)
        else:
            self.lbl_v2.configure(text="Peso Total Bandeja (g):"); self.lbl_v3.configure(text="Tempo Impressão (h):")
            self.lbl_v4.configure(text="Hora-Máquina (R$):"); self.lbl_v5.configure(text="Qtd de Peças:")
            self.lbl_data.configure(text="---"); self.ent_data.delete(0, 'end')
            # CORREÇÃO AQUI: fg_color não aceita "transparent" em CTkEntry. Usando cores do tema.
            self.ent_data.configure(state="disabled", fg_color=["#EBEBEB", "#2B2B2B"])
            self.frame_saldo.pack_forget()

    def salvar(self):
        idx = self.ent_id.get()
        try:
            n = self.ent_nome.get()
            v3 = float(self.ent_v3.get().replace(",", ".") or 0)
            v4 = float(self.ent_v4.get().replace(",", ".") or 0)

            if self.tabela_ativa == "filamento":
                v2, v5, data_c = self.ent_v2.get(), float(self.ent_v5.get().replace(",", ".") or 0), self.ent_data.get()
                txt_s = self.ent_saldo.get().replace(",", "."); saldo_f = float(txt_s) if txt_s else v3
                if idx and str(saldo_f) != self.saldo_original:
                    if not messagebox.askyesno("Confirmar", "Alterar saldo manualmente?"): return
                if not idx:
                    db.execute("INSERT INTO filamento (material, cor, quantidade_g, peso_atual_g, preco_por_g, custo_compra, data_compra) VALUES (?,?,?,?,?,?,?)", 
                               (n, v2, v3, saldo_f, v4, v5, data_c))
                else:
                    db.execute("UPDATE filamento SET material=?, cor=?, quantidade_g=?, peso_atual_g=?, preco_por_g=?, custo_compra=?, data_compra=? WHERE id=?", 
                               (n, v2, v3, saldo_f, v4, v5, data_c, idx))
            else:
                v2_p, v5_p = float(self.ent_v2.get().replace(",", ".") or 0), int(self.ent_v5.get() or 1)
                if not idx:
                    db.execute("INSERT INTO produtos (nome, peso_u, tempo_h, quantidade_produzida, hora_maq, preco_sugerido) VALUES (?,?,?,?,?,?)", 
                               (n, v2_p, v3, v5_p, v4, (v3*v4)))
                else:
                    db.execute("UPDATE produtos SET nome=?, peso_u=?, tempo_h=?, quantidade_produzida=?, hora_maq=?, preco_sugerido=? WHERE id=?", 
                               (n, v2_p, v3, v5_p, v4, (v3*v4), idx))
            # Sucesso sem pop-up
            self.limpar(); self.refresh(); self.refresh_cb()
        except Exception as e: messagebox.showerror("Erro", str(e))

    def calcular_dinamico(self):
        if self.tabela_ativa == "filamento":
            try:
                p_str, c_str = self.ent_v3.get().replace(",", "."), self.ent_v5.get().replace(",", ".")
                if not self.ent_id.get() and p_str:
                    self.ent_saldo.delete(0, 'end'); self.ent_saldo.insert(0, p_str)
                if p_str and c_str:
                    p, c = float(p_str), float(c_str)
                    if p > 0:
                        res = c / p
                        self.ent_v4.configure(state="normal"); self.ent_v4.delete(0, 'end'); self.ent_v4.insert(0, f"{res:.4f}"); self.ent_v4.configure(state="readonly")
            except: pass

    def excluir(self):
        idx = self.ent_id.get()
        if idx and messagebox.askyesno("Confirma", "Excluir permanentemente?"):
            db.execute(f"DELETE FROM {self.tabela_ativa} WHERE id=?", (idx,))
            self.limpar(); self.refresh(); self.refresh_cb()

    def limpar_campos(self):
        for e in [self.ent_id, self.ent_nome, self.ent_v2, self.ent_v3, self.ent_v4, self.ent_v5, self.ent_data, self.ent_saldo]:
            e.configure(state="normal"); e.delete(0, 'end')

    def limpar(self):
        self.limpar_campos(); self.ent_id.configure(state="readonly")
        self.ent_data.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.mudar_modo("filamento"); self.btn_reposicao.configure(state="disabled"); self.refresh()

    def criar_tabela(self, cols, tit):
        ctk.CTkLabel(self, text=tit, font=("Arial", 15, "bold")).pack(pady=(10, 5))
        
        # Frame container da tabela
        t_frame = ctk.CTkFrame(self)
        t_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        # --- CONFIGURAÇÃO DA TABELA (FUNDO BRANCO) ---
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",background="white",foreground="black",fieldbackground="white",rowheight=28,borderwidth=0)

        style.configure("Treeview.Heading",background="#f0f0f0",foreground="black",relief="flat")

        # Cor de quando você clica em uma linha
        style.map("Treeview",background=[('selected', '#3498db')],foreground=[('selected', 'white')])

        # Criar a Treeview
        t = ttk.Treeview(t_frame, columns=cols, show="headings", height=8)
        
        # --- ADICIONANDO A BARRA DE ROLAGEM ---
        scrollbar = ctk.CTkScrollbar(t_frame, orientation="vertical", command=t.yview)
        t.configure(yscrollcommand=scrollbar.set)
        
        # Posicionamento
        scrollbar.pack(side="right", fill="y")
        t.pack(side="left", fill="x", expand=True)

        # Configurar Colunas
        for c in cols: 
            t.heading(c, text=c)
            t.column(c, width=90, anchor="center")
            
        t.bind("<<TreeviewSelect>>", lambda e: self.selecionar(t))
        return t

    def add_field(self, txt, state="normal"):
        f = ctk.CTkFrame(self.frame_inputs, fg_color="transparent"); f.pack(fill="x", padx=40, pady=2)
        ctk.CTkLabel(f, text=txt, font=("Arial", 12, "bold"), width=180, anchor="w").pack(side="left")
        e = ctk.CTkEntry(f, height=30); e.pack(side="right", fill="x", expand=True); e.configure(state=state)
        return e

    def add_field_with_label(self, txt):
        f = ctk.CTkFrame(self.frame_inputs, fg_color="transparent"); f.pack(fill="x", padx=40, pady=2)
        lbl = ctk.CTkLabel(f, text=txt, font=("Arial", 12, "bold"), width=180, anchor="w"); lbl.pack(side="left")
        e = ctk.CTkEntry(f, height=30); e.pack(side="right", fill="x", expand=True)
        return lbl, e