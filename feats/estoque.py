import customtkinter as ctk
from tkinter import ttk, messagebox
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

class AbaEstoque(ctk.CTkScrollableFrame):
    def __init__(self, master, refresh_callback):
        super().__init__(master, fg_color="transparent")
        self.refresh_cb = refresh_callback
        self.tabela_ativa = "filamento" 

        ctk.CTkLabel(self, text="🛠️ GESTÃO DE ESTOQUE E CATÁLOGO", font=("Arial", 24, "bold")).pack(pady=20)

        # --- CONTAINER DE ENTRADAS ---
        self.frame_inputs = ctk.CTkFrame(self, border_width=1, border_color="#333")
        self.frame_inputs.pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(self.frame_inputs, text="📋 FORMULÁRIO", font=("Arial", 14, "bold"), text_color="#3498db").pack(pady=10)

        self.ent_id = self.add_field("ID do Registro:", state="readonly")
        self.lbl_nome, self.ent_nome = self.add_field_with_label("Material / Nome:")
        self.lbl_v2, self.ent_v2 = self.add_field_with_label("Cor / Peso Unit. (g):")
        self.lbl_v3, self.ent_v3 = self.add_field_with_label("Peso Inicial Rolo (g):")
        self.lbl_v4, self.ent_v4 = self.add_field_with_label("R$/g (Calculado):")
        self.lbl_v5, self.ent_v5 = self.add_field_with_label("Custo Compra (R$):")

        # Configurar cálculo automático ao digitar
        self.ent_v3.bind("<KeyRelease>", lambda e: self.calcular_dinamico())
        self.ent_v5.bind("<KeyRelease>", lambda e: self.calcular_dinamico())

        # --- BOTÕES ---
        self.frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_btns.pack(pady=20)
        ctk.CTkButton(self.frame_btns, text="SALVAR", fg_color="#2980b9", command=self.salvar).pack(side="left", padx=10)
        ctk.CTkButton(self.frame_btns, text="EXCLUIR", fg_color="#c0392b", command=self.excluir).pack(side="left", padx=10)
        ctk.CTkButton(self.frame_btns, text="LIMPAR", fg_color="#555", command=self.limpar).pack(side="left", padx=10)

        # --- TABELAS ---
        self.tree_f = self.criar_tabela(("ID", "Material", "Cor", "Total (g)", "Saldo (g)", "R$/g", "Custo"), "🧵 ESTOQUE FILAMENTOS")
        self.tree_p = self.criar_tabela(("ID", "Nome", "Peso (g)", "Tempo (h)", "Hora-Máq", "Preço Sugerido"), "📦 CATÁLOGO PRODUTOS")
        
        self.refresh()

    def add_field(self, txt, state="normal"):
        f = ctk.CTkFrame(self.frame_inputs, fg_color="transparent")
        f.pack(fill="x", padx=40, pady=2)
        ctk.CTkLabel(f, text=txt, font=("Arial", 12, "bold"), width=180, anchor="w").pack(side="left")
        e = ctk.CTkEntry(f, height=30)
        e.pack(side="right", fill="x", expand=True)
        e.configure(state=state)
        return e

    def add_field_with_label(self, txt):
        f = ctk.CTkFrame(self.frame_inputs, fg_color="transparent")
        f.pack(fill="x", padx=40, pady=2)
        lbl = ctk.CTkLabel(f, text=txt, font=("Arial", 12, "bold"), width=180, anchor="w")
        lbl.pack(side="left")
        e = ctk.CTkEntry(f, height=30)
        e.pack(side="right", fill="x", expand=True)
        return lbl, e

    def criar_tabela(self, cols, tit):
        ctk.CTkLabel(self, text=tit, font=("Arial", 15, "bold")).pack(pady=(20, 5))
        t_frame = ctk.CTkFrame(self); t_frame.pack(fill="x", padx=30)
        t = ttk.Treeview(t_frame, columns=cols, show="headings", height=5)
        for c in cols: t.heading(c, text=c); t.column(c, width=90, anchor="center")
        t.pack(fill="x", side="left", expand=True)
        t.bind("<<TreeviewSelect>>", lambda e: self.selecionar(t))
        return t

    def calcular_dinamico(self):
        """ Calcula o R$/g em tempo real enquanto o usuário digita """
        if self.tabela_ativa == "filamento":
            try:
                peso = float(self.ent_v3.get().replace(",", "."))
                custo = float(self.ent_v5.get().replace(",", "."))
                if peso > 0:
                    res = custo / peso
                    self.ent_v4.configure(state="normal")
                    self.ent_v4.delete(0, 'end')
                    self.ent_v4.insert(0, f"{res:.4f}")
                    self.ent_v4.configure(state="readonly")
            except:
                pass

    def selecionar(self, t):
        selecao = t.selection()
        if not selecao: return
        item = t.item(selecao[0])['values']
        self.limpar_campos()
        
        self.ent_id.configure(state="normal")
        self.ent_id.insert(0, item[0])
        self.ent_id.configure(state="readonly")

        if t == self.tree_f:
            self.tabela_ativa = "filamento"
            self.mudar_modo("filamento")
            self.ent_nome.insert(0, item[1])
            self.ent_v2.insert(0, item[2])
            self.ent_v3.insert(0, item[3])
            self.ent_v4.configure(state="normal")
            self.ent_v4.insert(0, item[5])
            self.ent_v4.configure(state="readonly")
            self.ent_v5.insert(0, item[6])
        else:
            self.tabela_ativa = "produtos"
            self.mudar_modo("produtos")
            self.ent_nome.insert(0, item[1])
            self.ent_v2.insert(0, item[2])
            self.ent_v3.insert(0, item[3])
            self.ent_v4.insert(0, item[4])

    def mudar_modo(self, modo):
        if modo == "filamento":
            self.lbl_v3.configure(text="Peso Inicial Rolo (g):")
            self.lbl_v4.configure(text="R$/g (Automático):")
            self.lbl_v5.configure(text="Custo Compra (R$):")
            self.ent_v5.configure(state="normal")
        else:
            self.lbl_v3.configure(text="Tempo Impressão (h):")
            self.lbl_v4.configure(text="Hora-Máquina (R$):")
            self.lbl_v5.configure(text="---")
            self.ent_v5.configure(state="disabled")

    def refresh(self):
        for t in [self.tree_f, self.tree_p]:
            for i in t.get_children(): t.delete(i)
        
        filas = db.query("SELECT id, material, cor, quantidade_g, peso_atual_g, preco_por_g, custo_compra FROM filamento")
        for r in filas: self.tree_f.insert("", "end", values=tuple(r))
            
        prods = db.query("SELECT id, nome, peso_u, tempo_h, hora_maq, preco_sugerido FROM produtos")
        for r in prods: self.tree_p.insert("", "end", values=tuple(r))

    def salvar(self):
        # Pega o ID (se houver)
        idx = self.ent_id.get()
        
        try:
            # Coleta dados comuns
            n = self.ent_nome.get()
            v2 = self.ent_v2.get()
            v3_text = self.ent_v3.get().replace(",", ".")
            v4_text = self.ent_v4.get().replace(",", ".")

            if not n or not v3_text:
                return messagebox.showwarning("Aviso", "Preencha pelo menos o Nome e o Peso/Tempo!")

            v3 = float(v3_text)
            v4 = float(v4_text) if v4_text else 0.0

            if self.tabela_ativa == "filamento":
                v5 = float(self.ent_v5.get().replace(",", ".") or 0)
                
                if not idx:  # --- NOVO REGISTRO ---
                    db.execute("""INSERT INTO filamento (material, cor, quantidade_g, peso_atual_g, preco_por_g, custo_compra) 
                                  VALUES (?, ?, ?, ?, ?, ?)""", 
                               (n, v2, v3, v3, v4, v5)) # peso_atual_g começa igual ao inicial
                else:        # --- EDITAR EXISTENTE ---
                    db.execute("""UPDATE filamento SET material=?, cor=?, quantidade_g=?, 
                                  preco_por_g=?, custo_compra=? WHERE id=?""", 
                               (n, v2, v3, v4, v5, idx))
            else:
                # Lógica para Produtos
                if not idx:
                    db.execute("""INSERT INTO produtos (nome, peso_u, tempo_h, hora_maq) 
                                  VALUES (?, ?, ?, ?)""", (n, v2, v3, v4))
                else:
                    db.execute("""UPDATE produtos SET nome=?, peso_u=?, tempo_h=?, hora_maq=? WHERE id=?""", 
                               (n, v2, v3, v4, idx))
            
            messagebox.showinfo("Sucesso", "Registro salvo com sucesso!")
            self.limpar() # Limpa campos e reseta ID
            self.refresh()
            self.refresh_cb() 
            
        except ValueError:
            messagebox.showerror("Erro", "Certifique-se de usar apenas números nos campos de peso, custo e tempo.")
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Erro ao salvar: {e}")


    def excluir(self):
        idx = self.ent_id.get()
        if not idx:
            return messagebox.showwarning("Aviso", "Selecione um item na tabela para excluir!")

        if messagebox.askyesno("Confirmar", f"Deseja excluir permanentemente o registro ID {idx}?"):
            try:
                # Executa a exclusão no banco de dados
                db.execute(f"DELETE FROM {self.tabela_ativa} WHERE id=?", (idx,))
                
                messagebox.showinfo("Sucesso", "Registro excluído com sucesso!")
                
                # --- AS TRÊS ETAPAS DE ATUALIZAÇÃO ---
                self.limpar()        # 1. Limpa os campos de texto
                self.refresh()       # 2. Atualiza as tabelas desta tela
                self.refresh_cb()    # 3. Atualiza as outras abas (Calculadora/Dashboard)
                
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível excluir: {e}")

    def limpar_campos(self):
        for e in [self.ent_id, self.ent_nome, self.ent_v2, self.ent_v3, self.ent_v4, self.ent_v5]:
            e.configure(state="normal")
            e.delete(0, 'end')

    def limpar(self):
        self.limpar_campos()
        self.ent_id.configure(state="readonly")
        self.tabela_ativa = "filamento"
        self.mudar_modo("filamento")
        self.refresh()