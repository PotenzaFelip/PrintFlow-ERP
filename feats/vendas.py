import customtkinter as ctk
from tkinter import ttk, messagebox
import database as db

class AbaVendas(ctk.CTkFrame):
    def __init__(self, master, refresh_callback):
        super().__init__(master, fg_color="transparent")
        self.refresh_cb = refresh_callback
        
        ctk.CTkLabel(self, text="💰 GESTÃO DE VENDAS E SAÍDAS", font=("Arial", 20, "bold")).pack(pady=10)

        # --- ÁREA DE INPUTS ---
        self.frame_inputs = ctk.CTkFrame(self)
        self.frame_inputs.pack(fill="x", padx=20, pady=10)

        # Seleção de Produto
        ctk.CTkLabel(self.frame_inputs, text="Selecione o Produto:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.combo_produto = ctk.CTkOptionMenu(self.frame_inputs, values=self.get_prods(), width=250)
        self.combo_produto.grid(row=0, column=1, padx=10, pady=5)

        # Seleção de Filamento (Obrigatório para o desconto de estoque)
        ctk.CTkLabel(self.frame_inputs, text="Filamento Utilizado:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.combo_filamento = ctk.CTkOptionMenu(self.frame_inputs, values=self.get_filas(), width=250, fg_color="#27ae60")
        self.combo_filamento.grid(row=1, column=1, padx=10, pady=5)

        # Quantidade e Valor
        ctk.CTkLabel(self.frame_inputs, text="Quantidade:").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.ent_qtd = ctk.CTkEntry(self.frame_inputs, placeholder_text="Ex: 1", width=100)
        self.ent_qtd.grid(row=0, column=3, padx=10, pady=5)

        ctk.CTkLabel(self.frame_inputs, text="Valor Final (R$):").grid(row=1, column=2, padx=10, pady=5, sticky="w")
        self.ent_valor = ctk.CTkEntry(self.frame_inputs, placeholder_text="Ex: 50.00", width=100)
        self.ent_valor.grid(row=1, column=3, padx=10, pady=5)

        # --- BOTÕES CRUD ---
        self.frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_btns.pack(pady=10)

        ctk.CTkButton(self.frame_btns, text="REGISTRAR VENDA", fg_color="#e67e22", command=self.vender).pack(side="left", padx=5)
        ctk.CTkButton(self.frame_btns, text="EXCLUIR REGISTRO", fg_color="#c0392b", command=self.excluir_venda).pack(side="left", padx=5)
        ctk.CTkButton(self.frame_btns, text="LIMPAR", fg_color="#7f8c8d", width=80, command=self.limpar_campos).pack(side="left", padx=5)

        # --- TABELA DE HISTÓRICO ---
        self.tree = ttk.Treeview(self, columns=("ID", "Produto", "Filamento", "Qtd", "Total", "Data"), show="headings", height=12)
        for c in ("ID", "Produto", "Filamento", "Qtd", "Total", "Data"): 
            self.tree.heading(c, text=c); self.tree.column(c, width=120, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.atualizar_vendas()

    def get_prods(self):
        res = db.query("SELECT id, nome FROM produtos")
        return [f"{p['nome']} | ID:{p['id']}" for p in res] if res else ["Nenhum Produto"]

    def get_filas(self):
        res = db.query("SELECT id, material, cor, peso_atual_g FROM filamento WHERE peso_atual_g > 0")
        return [f"{f['material']} {f['cor']} ({f['peso_atual_g']}g) | ID:{f['id']}" for f in res] if res else ["Sem Estoque"]

    def vender(self):
        try:
            id_p = self.combo_produto.get().split("ID:")[1]
            id_f = self.combo_filamento.get().split("ID:")[1]
            qtd = int(self.ent_qtd.get())
            valor = float(self.ent_valor.get().replace(",", "."))

            # O Trigger 'tg_venda_processada' no Banco fará o resto sozinho!
            db.execute("INSERT INTO vendas (produto_id, filamento_id, qtd_vendida, valor_total) VALUES (?,?,?,?)", 
                       (id_p, id_f, qtd, valor))
            
            messagebox.showinfo("Sucesso", "Venda realizada! Estoque e Financeiro atualizados.")
            self.refresh_cb()
            self.limpar_campos()
        except Exception as e:
            messagebox.showerror("Erro", f"Verifique os dados: {e}")

    def excluir_venda(self):
        selecao = self.tree.selection()
        if not selecao:
            return messagebox.showwarning("Aviso", "Selecione uma venda para excluir.")
        
        if messagebox.askyesno("Confirmar", "Deseja excluir este registro de venda?\n(Nota: Isso não devolverá o filamento ao estoque automaticamente nesta versão)"):
            id_venda = self.tree.item(selecao[0])['values'][0]
            db.execute("DELETE FROM vendas WHERE id=?", (id_venda,))
            self.refresh_cb()

    def atualizar_vendas(self):
        self.combo_produto.configure(values=self.get_prods())
        self.combo_filamento.configure(values=self.get_filas())
        
        for i in self.tree.get_children(): 
            self.tree.delete(i)
        
        sql = """
            SELECT v.id, p.nome, f.material || ' ' || f.cor, v.qtd_vendida, v.valor_total, v.data 
            FROM vendas v
            JOIN produtos p ON v.produto_id = p.id
            JOIN filamento f ON v.filamento_id = f.id
            ORDER BY v.id DESC
        """
        
        # A MUDANÇA ESTÁ AQUI:
        for r in db.query(sql):
            # Convertemos o sqlite3.Row em uma tupla simples para o Treeview ler
            self.tree.insert("", "end", values=tuple(r))

    def limpar_campos(self):
        self.ent_qtd.delete(0, 'end')
        self.ent_valor.delete(0, 'end')