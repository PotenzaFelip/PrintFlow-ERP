import customtkinter as ctk
from tkinter import ttk, messagebox
import database as db

class AbaReparos(ctk.CTkScrollableFrame): # Alterado para Scrollable para consistência
    def __init__(self, master, refresh_callback):
        super().__init__(master, fg_color="transparent")
        self.refresh_cb = refresh_callback
        self.id_selecionado = None 

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
        self.btn_excluir.configure(state="disabled")

        self.btn_limpar = ctk.CTkButton(self.frame_form, text="LIMPAR", fg_color="#7f8c8d", width=80, command=self.limpar_campos)
        self.btn_limpar.grid(row=0, column=6, padx=5, pady=5)

        # --- BARRA DE BUSCA ---
        self.frame_busca = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_busca.pack(fill="x", padx=20, pady=(10, 0))

        self.ent_busca = ctk.CTkEntry(self.frame_busca, placeholder_text="🔍 Pesquisar reparo (Descrição ou Data)...", height=35)
        self.ent_busca.pack(fill="x", expand=True)
        self.ent_busca.bind("<KeyRelease>", lambda e: self.atualizar_tabela())

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

        self.tree = ttk.Treeview(self.container_tabela, columns=("ID", "Descrição", "Custo", "Data"), show="headings", height=15)
        
        # Barra de rolagem dedicada para a Treeview
        self.scrollbar = ctk.CTkScrollbar(self.container_tabela, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        for c in ("ID", "Descrição", "Custo", "Data"):
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="center")
        
        # Posicionamento da scrollbar e tabela
        self.scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.preencher_campos)
        self.atualizar_tabela()

    def salvar_reparo(self):
        try:
            desc = self.ent_desc.get()
            valor_text = self.ent_custo.get().replace(",", ".")
            valor = float(valor_text) if valor_text else 0.0
            
            if not desc: 
                return messagebox.showerror("Erro", "A descrição é obrigatória.")

            if self.id_selecionado is None:
                db.execute("INSERT INTO reparos (descricao, custo) VALUES (?, ?)", (desc, valor))
            else:
                db.execute("UPDATE reparos SET descricao=?, custo=? WHERE id=?", (desc, valor, self.id_selecionado))

            self.limpar_campos()
            self.refresh_cb() 
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao processar: {e}")

    def excluir_reparo(self):
        if self.id_selecionado and messagebox.askyesno("Confirmar", "Deseja excluir este registro de manutenção?"):
            try:
                db.execute("DELETE FROM reparos WHERE id=?", (self.id_selecionado,))
                self.limpar_campos()
                self.refresh_cb()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao excluir: {e}")

    def preencher_campos(self, event):
        selecao = self.tree.selection()
        if not selecao: return
        
        item = self.tree.item(selecao[0])['values']
        self.id_selecionado = item[0]
        
        self.ent_desc.delete(0, 'end')
        self.ent_desc.insert(0, item[1])
        self.ent_custo.delete(0, 'end')
        self.ent_custo.insert(0, str(item[2]).replace("R$ ", ""))
        
        self.btn_salvar.configure(text="ATUALIZAR", fg_color="#3498db")
        self.btn_excluir.configure(state="normal")

    def limpar_campos(self):
        self.id_selecionado = None
        self.ent_desc.delete(0, 'end')
        self.ent_custo.delete(0, 'end')
        self.ent_busca.delete(0, 'end')
        self.btn_salvar.configure(text="ADICIONAR", fg_color="#2ecc71")
        self.btn_excluir.configure(state="disabled")
        self.atualizar_tabela()

    def atualizar_tabela(self):
        for i in self.tree.get_children(): 
            self.tree.delete(i)
        
        termo = f"%{self.ent_busca.get()}%"
        query = "SELECT * FROM reparos WHERE descricao LIKE ? OR data LIKE ? ORDER BY id DESC"
        dados = db.query(query, (termo, termo))
        
        for r in dados:
            self.tree.insert("", "end", values=tuple(r))