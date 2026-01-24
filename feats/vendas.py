import customtkinter as ctk
from tkinter import ttk, messagebox
import database as db

class AbaVendas(ctk.CTkFrame):
    def __init__(self, master, refresh_callback):
        super().__init__(master, fg_color="transparent")
        self.refresh_cb = refresh_callback
        
        ctk.CTkLabel(self, text="💰 REGISTRAR VENDA", font=("Arial", 18, "bold")).pack(pady=10)
        self.combo_venda = ctk.CTkOptionMenu(self, values=self.get_prods(), width=400)
        self.combo_venda.pack(pady=5)
        self.ent_qtd = ctk.CTkEntry(self, placeholder_text="Quantidade Vendida", width=400)
        self.ent_qtd.pack(pady=5)
        
        ctk.CTkButton(self, text="CONFIRMAR VENDA", fg_color="#e67e22", height=45, command=self.vender).pack(pady=15)

        # Colunas: ID Venda, ID Peça, Nome da Peça, Qtd Vendida, Valor da Venda, Data/Hora
        self.tree = ttk.Treeview(self, columns=("ID_V", "ID_P", "Peça", "Qtd", "Valor Total", "Data"), show="headings", height=12)
        for c in ("ID_V", "ID_P", "Peça", "Qtd", "Valor Total", "Data"): 
            self.tree.heading(c, text=c); self.tree.column(c, width=120, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.atualizar_vendas()

    def get_prods(self):
        res = db.query("SELECT id, nome, quantidade FROM produtos WHERE quantidade > 0")
        return [f"{p[1]} (Disp: {p[2]}) | ID:{p[0]}" for p in res] if res else ["Estoque Vazio"]

    def vender(self):
        try:
            id_p = self.combo_venda.get().split("ID:")[1]
            qtd_v = int(self.ent_qtd.get())
            p = db.query("SELECT nome, quantidade, preco_sugerido, valor_total_producao FROM produtos WHERE id=?", (id_p,))[0]
            
            if qtd_v > p[1]: return messagebox.showerror("Erro", "Estoque insuficiente!")
            
            valor_venda = qtd_v * p[2]
            db.execute("UPDATE produtos SET quantidade=quantidade-?, valor_total_producao=valor_total_producao-? WHERE id=?", 
                       (qtd_v, valor_venda, id_p))
            db.execute("INSERT INTO vendas (produto_id, produto_nome, qtd_vendida, valor_total) VALUES (?,?,?,?)", 
                       (id_p, p[0], qtd_v, valor_venda))
            
            self.refresh_cb()
            messagebox.showinfo("Sucesso", "Venda registrada!")
        except: pass

    def atualizar_vendas(self):
        self.combo_venda.configure(values=self.get_prods())
        for i in self.tree.get_children(): self.tree.delete(i)
        # Puxa todos os campos da tabela vendas
        dados = db.query("SELECT id, produto_id, produto_nome, qtd_vendida, valor_total, data FROM vendas ORDER BY id DESC")
        for r in dados:
            self.tree.insert("", "end", values=r)