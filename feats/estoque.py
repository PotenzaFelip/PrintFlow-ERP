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
        self.tabela_ativa = "filamento" # Controla se estamos editando Filamento ou Produto

        # Título Principal
        ctk.CTkLabel(self, text="🛠️ GESTÃO INTEGRADA DE ESTOQUE", font=("Arial", 24, "bold")).pack(pady=20)

        # --- CONTAINER DE ENTRADAS (CARD VISUAL) ---
        self.frame_inputs = ctk.CTkFrame(self, border_width=1, border_color="#333")
        self.frame_inputs.pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(self.frame_inputs, text="📋 FORMULÁRIO DE CADASTRO / EDIÇÃO", 
                     font=("Arial", 14, "bold"), text_color="#3498db").pack(pady=15)

        # Definição dos campos usando o método de alinhamento Grid
        self.ent_id = self.add_field("ID do Registro:", state="readonly")
        
        # Guardamos as referências das Labels para trocar o texto dinamicamente
        self.row_nome = self.add_field_with_label("Material / Nome:")
        self.row_cor = self.add_field_with_label("Cor / Peso Unit. (g):")
        self.row_qtd = self.add_field_with_label("Peso Inicial / Tempo (h):")
        self.row_preco = self.add_field_with_label("Preço g / Hora-Máq:")
        self.row_markup = self.add_field_with_label("Custo Total / Markup:")

        # Desempacotando para fácil acesso
        self.lbl_nome, self.ent_nome = self.row_nome
        self.lbl_cor, self.ent_cor = self.row_cor
        self.lbl_qtd, self.ent_qtd_total = self.row_qtd
        self.lbl_preco, self.ent_preco_g = self.row_preco
        self.lbl_custo, self.ent_custo_total = self.row_markup

        # --- ÁREA DE BOTÕES ---
        self.frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_btns.pack(pady=20)
        
        self.btn_add = ctk.CTkButton(self.frame_btns, text="+ NOVO REGISTRO", fg_color="#27ae60", 
                                     font=("Arial", 13, "bold"), height=40, command=self.adicionar_novo)
        self.btn_add.pack(side="left", padx=10)
        
        self.btn_save = ctk.CTkButton(self.frame_btns, text="SALVAR ALTERAÇÕES", fg_color="#2980b9", 
                                      font=("Arial", 13, "bold"), height=40, command=self.salvar)
        self.btn_save.pack(side="left", padx=10)
        
        self.btn_del = ctk.CTkButton(self.frame_btns, text="EXCLUIR", fg_color="#c0392b", 
                                     font=("Arial", 13, "bold"), height=40, command=self.excluir)
        self.btn_del.pack(side="left", padx=10)
        
        ctk.CTkButton(self.frame_btns, text="LIMPAR", fg_color="#555", height=40, width=80, command=self.limpar).pack(side="left", padx=10)

        # --- TABELAS ---
        # Estilo para as tabelas (Treeview)
        style = ttk.Style()
        style.configure("Treeview", rowheight=30, font=("Arial", 10))
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))

        self.tree_f = self.criar_tabela(
            ("ID", "Material", "Cor", "Inicial (g)", "Saldo Atual (g)", "R$/g", "Custo Total"), 
            "🧵 ESTOQUE DE FILAMENTOS (Clique para selecionar)"
        )
        
        self.tree_p = self.criar_tabela(
            ("ID", "Nome", "Peso (g)", "Tempo (h)", "H-M", "Markup", "Setup", "Preço Sugerido"), 
            "📦 CATÁLOGO DE PRODUTOS SALVOS"
        )
        
        self.refresh()

    # --- MÉTODOS DE CONSTRUÇÃO DE UI ---
    def add_field(self, txt, state="normal"):
        f = ctk.CTkFrame(self.frame_inputs, fg_color="transparent")
        f.pack(fill="x", padx=40, pady=5)
        f.grid_columnconfigure(1, weight=1)
        
        lbl = ctk.CTkLabel(f, text=txt, font=("Arial", 12, "bold"), width=180, anchor="w")
        lbl.grid(row=0, column=0, sticky="w")
        
        e = ctk.CTkEntry(f, height=35)
        e.grid(row=0, column=1, sticky="ew")
        e.configure(state=state)
        return e

    def add_field_with_label(self, txt):
        f = ctk.CTkFrame(self.frame_inputs, fg_color="transparent")
        f.pack(fill="x", padx=40, pady=5)
        f.grid_columnconfigure(1, weight=1)
        
        lbl = ctk.CTkLabel(f, text=txt, font=("Arial", 12, "bold"), width=180, anchor="w")
        lbl.grid(row=0, column=0, sticky="w")
        
        e = ctk.CTkEntry(f, height=35)
        e.grid(row=0, column=1, sticky="ew")
        return lbl, e

    def criar_tabela(self, cols, tit):
        ctk.CTkLabel(self, text=tit, font=("Arial", 15, "bold"), text_color="#ecf0f1").pack(pady=(30, 10))
        
        t_frame = ctk.CTkFrame(self)
        t_frame.pack(fill="x", padx=30)
        
        t = ttk.Treeview(t_frame, columns=cols, show="headings", height=7)
        for c in cols: 
            t.heading(c, text=c)
            t.column(c, width=100, anchor="center")
        
        t.pack(fill="x", side="left", expand=True)
        
        # Scrollbar para a tabela
        sb = ttk.Scrollbar(t_frame, orient="vertical", command=t.yview)
        t.configure(yscroll=sb.set)
        sb.pack(side="right", fill="y")
        
        t.bind("<<TreeviewSelect>>", lambda e: self.selecionar(t))
        return t

    # --- LÓGICA DE FUNCIONAMENTO ---
    def selecionar(self, t):
        selecao = t.selection()
        if not selecao: return
        item = t.item(selecao[0])['values']
        
        self.limpar_campos_sem_reset_labels()
        self.ent_id.configure(state="normal")
        self.ent_id.insert(0, item[0])
        self.ent_id.configure(state="readonly")
        
        if t == self.tree_f:
            self.tabela_ativa = "filamento"
            self.mudar_modo("filamento")
            self.ent_nome.insert(0, item[1])
            self.ent_cor.insert(0, item[2])
            self.ent_qtd_total.insert(0, item[3])
            self.ent_preco_g.insert(0, item[5])
            self.ent_custo_total.insert(0, item[6])
        else:
            self.tabela_ativa = "produtos"
            self.mudar_modo("produtos")
            self.ent_nome.insert(0, item[1])
            self.ent_cor.insert(0, item[2]) # Peso Unitario
            self.ent_qtd_total.insert(0, item[3]) # Tempo
            self.ent_preco_g.insert(0, item[4]) # Hora Máquina
            self.ent_custo_total.insert(0, item[5]) # Markup

    def mudar_modo(self, modo):
        if modo == "filamento":
            self.lbl_nome.configure(text="Material (Ex: PLA):")
            self.lbl_cor.configure(text="Cor:")
            self.lbl_qtd.configure(text="Peso Inicial (g):")
            self.lbl_preco.configure(text="Preço por Grama (R$):")
            self.lbl_custo.configure(text="Custo da Compra (R$):")
            self.btn_add.configure(text="+ NOVO FILAMENTO")
        else:
            self.lbl_nome.configure(text="Nome do Produto:")
            self.lbl_cor.configure(text="Peso Unitário (g):")
            self.lbl_qtd.configure(text="Tempo Impressão (h):")
            self.lbl_preco.configure(text="Hora-Máquina (R$):")
            self.lbl_custo.configure(text="Markup (Multiplicador):")
            self.btn_add.configure(text="+ NOVO PRODUTO")

    def refresh(self):
        for t in [self.tree_f, self.tree_p]:
            for i in t.get_children(): t.delete(i)
        
        for r in db.query("SELECT id, material, cor, quantidade_g, peso_atual_g, preco_por_g, custo_compra FROM filamento"):
            self.tree_f.insert("", "end", values=tuple(r))
            
        for r in db.query("SELECT id, nome, peso_u, tempo_h, hora_maq, margem, setup_valor, preco_sugerido FROM produtos"):
            self.tree_p.insert("", "end", values=tuple(r))

    def adicionar_novo(self):
        try:
            v1 = self.ent_nome.get()
            v2 = self.ent_cor.get().replace(",", ".")
            v3 = self.ent_qtd_total.get().replace(",", ".")
            v4 = self.ent_preco_g.get().replace(",", ".")
            v5 = self.ent_custo_total.get().replace(",", ".")

            if self.tabela_ativa == "filamento":
                sql = "INSERT INTO filamento (material, cor, quantidade_g, peso_atual_g, preco_por_g, custo_compra) VALUES (?,?,?,?,?,?)"
                db.execute(sql, (v1, v2, float(v3), float(v3), float(v4), float(v5)))
            else:
                # Preço sugerido básico para evitar erros na primeira inserção
                p_sug = (float(v2) * 0.05) + (float(v3) * float(v4)) * float(v5)
                sql = "INSERT INTO produtos (nome, peso_u, tempo_h, hora_maq, margem, preco_sugerido) VALUES (?,?,?,?,?,?)"
                db.execute(sql, (v1, float(v2), float(v3), float(v4), float(v5), p_sug))
            
            messagebox.showinfo("Sucesso", "Cadastrado com sucesso!")
            self.refresh_cb()
            self.limpar()
        except Exception as e:
            messagebox.showerror("Erro", f"Preencha todos os campos corretamente.\n{e}")

    def salvar(self):
        idx = self.ent_id.get()
        if not idx: return messagebox.showwarning("Aviso", "Selecione um item na tabela primeiro!")
        try:
            v1, v2, v3, v4, v5 = self.ent_nome.get(), self.ent_cor.get(), self.ent_qtd_total.get(), self.ent_preco_g.get(), self.ent_custo_total.get()
            
            if self.tabela_ativa == "filamento":
                db.execute("UPDATE filamento SET material=?, cor=?, quantidade_g=?, preco_por_g=?, custo_compra=? WHERE id=?", 
                           (v1, v2, v3, v4, v5, idx))
            else:
                db.execute("UPDATE produtos SET nome=?, peso_u=?, tempo_h=?, hora_maq=?, margem=? WHERE id=?", 
                           (v1, v2, v3, v4, v5, idx))
            
            messagebox.showinfo("Sucesso", "Dados atualizados!")
            self.refresh_cb()
        except Exception as e: 
            messagebox.showerror("Erro", str(e))

    def excluir(self):
        idx = self.ent_id.get()
        if not idx: return
        if messagebox.askyesno("Confirmar", f"Deseja realmente excluir este item de {self.tabela_ativa}?"):
            try:
                db.execute(f"DELETE FROM {self.tabela_ativa} WHERE id=?", (idx,))
                self.limpar()
                self.refresh_cb()
            except:
                messagebox.showerror("Erro", "Este item possui vínculos (Vendas/Produção) e não pode ser excluído.")

    def limpar_campos_sem_reset_labels(self):
        self.ent_id.configure(state="normal")
        for e in [self.ent_id, self.ent_nome, self.ent_cor, self.ent_qtd_total, self.ent_preco_g, self.ent_custo_total]:
            e.delete(0, 'end')
        self.ent_id.configure(state="readonly")

    def limpar(self):
        self.limpar_campos_sem_reset_labels()
        self.mudar_modo("filamento")
        self.tabela_ativa = "filamento"
        self.refresh()