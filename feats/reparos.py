import customtkinter as ctk
from tkinter import ttk, messagebox
import database as db

class AbaReparos(ctk.CTkFrame):
    def __init__(self, master, refresh_callback):
        super().__init__(master, fg_color="transparent")
        self.refresh_cb = refresh_callback
        self.id_selecionado = None # Para controlar o que está sendo editado

        ctk.CTkLabel(self, text="🔧 GESTÃO DE MANUTENÇÃO", font=("Arial", 20, "bold")).pack(pady=10)

        # --- FORMULÁRIO ---
        self.frame_form = ctk.CTkFrame(self)
        self.frame_form.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(self.frame_form, text="Descrição:").grid(row=0, column=0, padx=5, pady=5)
        self.ent_desc = ctk.CTkEntry(self.frame_form, width=250)
        self.ent_desc.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(self.frame_form, text="Custo (R$):").grid(row=0, column=2, padx=5, pady=5)
        self.ent_custo = ctk.CTkEntry(self.frame_form, width=80)
        self.ent_custo.grid(row=0, column=3, padx=5, pady=5)

        # --- BOTÕES ---
        self.btn_salvar = ctk.CTkButton(self.frame_form, text="ADICIONAR", fg_color="#2ecc71", width=100, command=self.salvar_reparo)
        self.btn_salvar.grid(row=0, column=4, padx=5, pady=5)

        self.btn_excluir = ctk.CTkButton(self.frame_form, text="EXCLUIR", fg_color="#e74c3c", width=100, command=self.excluir_reparo)
        self.btn_excluir.grid(row=0, column=5, padx=5, pady=5)
        self.btn_excluir.configure(state="disabled") # Só ativa se selecionar algo

        self.btn_limpar = ctk.CTkButton(self.frame_form, text="LIMPAR", fg_color="#7f8c8d", width=80, command=self.limpar_campos)
        self.btn_limpar.grid(row=0, column=6, padx=5, pady=5)

        # --- TABELA ---
        self.tree = ttk.Treeview(self, columns=("ID", "Descrição", "Custo", "Data"), show="headings", height=15)
        for c in ("ID", "Descrição", "Custo", "Data"):
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        # Evento de clique na tabela
        self.tree.bind("<<TreeviewSelect>>", self.preencher_campos)

        self.atualizar_tabela()

    def salvar_reparo(self):
        try:
            desc = self.ent_desc.get()
            valor = float(self.ent_custo.get().replace(",", "."))
            if not desc: raise ValueError("Descrição obrigatória")

            if self.id_selecionado is None:
                # INSERT
                db.execute("INSERT INTO reparos (descricao, custo) VALUES (?, ?)", (desc, valor))
                messagebox.showinfo("Sucesso", "Reparo registrado!")
            else:
                # UPDATE
                db.execute("UPDATE reparos SET descricao=?, custo=? WHERE id=?", (desc, valor, self.id_selecionado))
                messagebox.showinfo("Sucesso", "Registro atualizado!")

            self.limpar_campos()
            self.refresh_cb() 
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao processar: {e}")

    def excluir_reparo(self):
        if self.id_selecionado and messagebox.askyesno("Confirmar", "Deseja excluir este registro de manutenção?"):
            db.execute("DELETE FROM reparos WHERE id=?", (self.id_selecionado,))
            # Nota: No Financeiro o registro de SAIDA permanecerá para não quebrar o caixa passado.
            self.limpar_campos()
            self.refresh_cb()

    def preencher_campos(self, event):
        selecao = self.tree.selection()
        if not selecao: return
        
        item = self.tree.item(selecao[0])['values']
        self.id_selecionado = item[0]
        
        self.ent_desc.delete(0, 'end')
        self.ent_desc.insert(0, item[1])
        self.ent_custo.delete(0, 'end')
        self.ent_custo.insert(0, item[2])
        
        self.btn_salvar.configure(text="ATUALIZAR", fg_color="#3498db")
        self.btn_excluir.configure(state="normal")

    def limpar_campos(self):
        self.id_selecionado = None
        self.ent_desc.delete(0, 'end')
        self.ent_custo.delete(0, 'end')
        self.btn_salvar.configure(text="ADICIONAR", fg_color="#2ecc71")
        self.btn_excluir.configure(state="disabled")
        self.atualizar_tabela()

    def atualizar_tabela(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        dados = db.query("SELECT * FROM reparos ORDER BY id DESC")
        for r in dados:
            self.tree.insert("", "end", values=tuple(r))