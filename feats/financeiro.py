import customtkinter as ctk
from tkinter import ttk, messagebox
import database as db

class AbaFinanceiro(ctk.CTkScrollableFrame): # Alterado para Scrollable
    def __init__(self, master, refresh_callback):
        super().__init__(master, fg_color="transparent")
        self.refresh_cb = refresh_callback

        ctk.CTkLabel(self, text="💰 FLUXO DE CAIXA E EXTRATO", font=("Arial", 22, "bold")).pack(pady=10)

        # --- RESUMO RÁPIDO (INDICADORES) ---
        self.frame_resumo = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_resumo.pack(fill="x", padx=20, pady=10)

        self.lbl_saldo = self.criar_indicador(self.frame_resumo, "SALDO ATUAL", "#2ecc71")
        self.lbl_entradas = self.criar_indicador(self.frame_resumo, "TOTAL ENTRADAS", "#3498db")
        self.lbl_saidas = self.criar_indicador(self.frame_resumo, "TOTAL SAÍDAS", "#e74c3c")

        # --- BARRA DE BUSCA E FILTROS ---
        self.frame_busca = ctk.CTkFrame(self)
        self.frame_busca.pack(fill="x", padx=20, pady=5)
        
        self.ent_busca = ctk.CTkEntry(self.frame_busca, placeholder_text="🔍 Pesquisar descrição ou data...", width=300)
        self.ent_busca.pack(side="left", padx=10, pady=10)
        self.ent_busca.bind("<KeyRelease>", lambda e: self.atualizar_tabela())

        ctk.CTkLabel(self.frame_busca, text="Tipo:").pack(side="left", padx=(10, 0))
        self.filtro_tipo = ctk.CTkOptionMenu(self.frame_busca, values=["Todos", "ENTRADA", "SAIDA"], 
                                             command=lambda _: self.atualizar_tabela())
        self.filtro_tipo.pack(side="left", padx=5)

        ctk.CTkButton(self.frame_busca, text="🗑️ EXCLUIR", fg_color="#c0392b", width=100, command=self.excluir_registro).pack(side="right", padx=10)

        # --- TABELA COM BARRA DE ROLAGEM ---
        self.container_tabela = ctk.CTkFrame(self)
        self.container_tabela.pack(fill="both", expand=True, padx=20, pady=10)

         # --- CONFIGURAÇÃO DA TABELA (FUNDO BRANCO) ---
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",background="white",foreground="black",fieldbackground="white",rowheight=28,borderwidth=0)

        style.configure("Treeview.Heading",background="#f0f0f0",foreground="black",relief="flat")

        # Cor de quando você clica em uma linha
        style.map("Treeview",background=[('selected', '#3498db')],foreground=[('selected', 'white')])

        self.tree = ttk.Treeview(self.container_tabela, columns=("ID", "Tipo", "Valor", "Descrição", "Data"), show="headings", height=15)
        
        # Adicionando a Scrollbar
        self.scrollbar = ctk.CTkScrollbar(self.container_tabela, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        for c in ("ID", "Tipo", "Valor", "Descrição", "Data"):
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="center", width=100)
        
        self.tree.column("Descrição", width=350, anchor="w") 
        
        # Posicionamento da scrollbar e tabela
        self.scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        self.atualizar_tabela()

    def criar_indicador(self, master, titulo, cor):
        f = ctk.CTkFrame(master, border_width=1, border_color=cor)
        f.pack(side="left", expand=True, fill="both", padx=5)
        ctk.CTkLabel(f, text=titulo, font=("Arial", 10, "bold")).pack(pady=(5,0))
        lbl = ctk.CTkLabel(f, text="R$ 0,00", font=("Arial", 18, "bold"), text_color=cor)
        lbl.pack(pady=(0,5))
        return lbl

    def atualizar_tabela(self):
        for i in self.tree.get_children(): 
            self.tree.delete(i)
        
        tipo_filtro = self.filtro_tipo.get()
        termo_busca = f"%{self.ent_busca.get()}%"

        query = "SELECT * FROM financeiro WHERE (descricao LIKE ? OR data LIKE ?)"
        params = [termo_busca, termo_busca]

        if tipo_filtro != "Todos":
            query += " AND tipo = ?"
            params.append(tipo_filtro)
        
        query += " ORDER BY id DESC"
        dados = db.query(query, tuple(params))

        total_e = 0
        total_s = 0

        for r in dados:
            valor = r['valor']
            if r['tipo'] == 'ENTRADA': total_e += valor
            else: total_s += valor
            
            tag_valor = f"R$ {valor:.2f}"
            self.tree.insert("", "end", values=(r['id'], r['tipo'], tag_valor, r['descricao'], r['data']))

        self.lbl_entradas.configure(text=f"R$ {total_e:.2f}")
        self.lbl_saidas.configure(text=f"R$ {total_s:.2f}")
        self.lbl_saldo.configure(text=f"R$ {(total_e - total_s):.2f}")

    def excluir_registro(self):
        selecao = self.tree.selection()
        if not selecao:
            return messagebox.showwarning("Aviso", "Selecione um registro para excluir.")
        
        if messagebox.askyesno("Confirmar", "Deseja excluir este registro financeiro?"):
            try:
                id_fin = self.tree.item(selecao[0])['values'][0]
                db.execute("DELETE FROM financeiro WHERE id=?", (id_fin,))
                self.atualizar_tabela()
                self.refresh_cb() 
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao excluir: {e}")

    def limpar_busca(self):
        self.ent_busca.delete(0, 'end')
        self.filtro_tipo.set("Todos")
        self.atualizar_tabela()