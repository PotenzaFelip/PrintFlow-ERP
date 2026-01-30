import customtkinter as ctk
from tkinter import ttk, messagebox
import database as db

class AbaFinanceiro(ctk.CTkFrame):
    def __init__(self, master, refresh_callback):
        super().__init__(master, fg_color="transparent")
        self.refresh_cb = refresh_callback

        ctk.CTkLabel(self, text="💰 FLUXO DE CAIXA E EXTRATO", font=("Arial", 22, "bold")).pack(pady=10)

        # --- RESUMO RÁPIDO ---
        self.frame_resumo = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_resumo.pack(fill="x", padx=20, pady=10)

        self.lbl_saldo = self.criar_indicador(self.frame_resumo, "SALDO ATUAL", "#2ecc71")
        self.lbl_entradas = self.criar_indicador(self.frame_resumo, "TOTAL ENTRADAS", "#3498db")
        self.lbl_saidas = self.criar_indicador(self.frame_resumo, "TOTAL SAÍDAS", "#e74c3c")

        # --- FILTROS E BUSCA ---
        self.frame_busca = ctk.CTkFrame(self)
        self.frame_busca.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(self.frame_busca, text="Filtrar por Tipo:").pack(side="left", padx=10)
        self.filtro_tipo = ctk.CTkOptionMenu(self.frame_busca, values=["Todos", "ENTRADA", "SAIDA"], command=lambda _: self.atualizar_tabela())
        self.filtro_tipo.pack(side="left", padx=5)

        ctk.CTkButton(self.frame_busca, text="🗑️ EXCLUIR REGISTRO", fg_color="#c0392b", command=self.excluir_registro).pack(side="right", padx=10)

        # --- TABELA DE EXTRATO ---
        self.tree = ttk.Treeview(self, columns=("ID", "Tipo", "Valor", "Descrição", "Data"), show="headings", height=15)
        for c in ("ID", "Tipo", "Valor", "Descrição", "Data"):
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="center", width=100)
        self.tree.column("Descrição", width=350, anchor="w") # Descrição maior
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        self.atualizar_tabela()

    def criar_indicador(self, master, titulo, cor):
        f = ctk.CTkFrame(master, border_width=1, border_color=cor)
        f.pack(side="left", expand=True, fill="both", padx=5)
        ctk.CTkLabel(f, text=titulo, font=("Arial", 10, "bold")).pack(pady=(5,0))
        lbl = ctk.CTkLabel(f, text="R$ 0,00", font=("Arial", 18, "bold"), text_color=cor)
        lbl.pack(pady=(0,5))
        return lbl

    def atualizar_tabela(self):
        # 1. Limpar tabela
        for i in self.tree.get_children(): self.tree.delete(i)
        
        # 2. Query com Filtro
        tipo = self.filtro_tipo.get()
        if tipo == "Todos":
            dados = db.query("SELECT * FROM financeiro ORDER BY id DESC")
        else:
            dados = db.query("SELECT * FROM financeiro WHERE tipo=? ORDER BY id DESC", (tipo,))

        # 3. Cálculos de Totais
        total_e = 0
        total_s = 0

        for r in dados:
            valor = r['valor']
            if r['tipo'] == 'ENTRADA': total_e += valor
            else: total_s += valor
            
            # Formatação visual para a tabela
            tag = "R$ " + f"{valor:.2f}"
            self.tree.insert("", "end", values=(r['id'], r['tipo'], tag, r['descricao'], r['data']))

        # 4. Atualizar Indicadores
        self.lbl_entradas.configure(text=f"R$ {total_e:.2f}")
        self.lbl_saidas.configure(text=f"R$ {total_s:.2f}")
        self.lbl_saldo.configure(text=f"R$ {(total_e - total_s):.2f}")

    def excluir_registro(self):
        selecao = self.tree.selection()
        if not selecao:
            return messagebox.showwarning("Aviso", "Selecione um registro para excluir.")
        
        if messagebox.askyesno("Confirmar", "Deseja excluir este registro financeiro? (Isso não afetará o estoque ou vendas)"):
            id_fin = self.tree.item(selecao[0])['values'][0]
            db.execute("DELETE FROM financeiro WHERE id=?", (id_fin,))
            self.atualizar_tabela()
            self.refresh_cb() # Atualiza o dashboard