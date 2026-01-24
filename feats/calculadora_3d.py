import customtkinter as ctk
from tkinter import messagebox
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

class AbaCalculadora(ctk.CTkScrollableFrame):
    def __init__(self, master, refresh_callback):
        super().__init__(master, fg_color="transparent")
        self.refresh_callback = refresh_callback
        
        ctk.CTkLabel(self, text="🚀 PRODUÇÃO E ORÇAMENTOS", font=("Arial", 18, "bold")).pack(pady=10)
        
        # Seleção de Projetos e Materiais
        ctk.CTkLabel(self, text="Selecione um Modelo Salvo:").pack()
        self.combo_projetos = ctk.CTkOptionMenu(self, values=self.get_lista_projetos(), command=self.carregar, width=350)
        self.combo_projetos.pack(pady=5)
        
        ctk.CTkLabel(self, text="Selecione o Filamento:").pack()
        self.combo_mat = ctk.CTkOptionMenu(self, values=self.get_mats(), width=350)
        self.combo_mat.pack(pady=5)

        # Campos de Entrada
        self.ent_nome = self.add_i("Nome da Peça:", "Nova Peça")
        self.ent_qtd = self.add_i("Quantidade de Peças na Bandeja:", "1")
        self.ent_peso_total = self.add_i("Peso TOTAL da Impressão (g):", "0")
        self.ent_horas = self.add_i("Tempo Total de Impressão (h):", "0")
        self.ent_hm = self.add_i("Valor da Hora-Máquina (R$):", "16.50")
        self.ent_taxa = self.add_i("Margem de Lucro/Taxas (%):", "10")

        # Exibição do Resultado
        self.lbl_detalhes = ctk.CTkLabel(self, text="Custo Mat: R$ 0.00 | Custo Maq: R$ 0.00", font=("Arial", 11))
        self.lbl_detalhes.pack(pady=(15, 0))
        
        self.lbl_res = ctk.CTkLabel(self, text="Venda Total: R$ 0,00", font=("Arial", 24, "bold"), text_color="#2ecc71")
        self.lbl_res.pack(pady=5)
        
        self.lbl_unitario = ctk.CTkLabel(self, text="Preço Unitário Sugerido: R$ 0,00", font=("Arial", 14), text_color="#3498db")
        self.lbl_unitario.pack(pady=(0, 10))

        # --- BOTÕES ---
        # Botão de Cotar: Apenas faz o cálculo visual
        ctk.CTkButton(self, text="APENAS CALCULAR COTAÇÃO", fg_color="#555", height=45, command=lambda: self.calc(salvar=False)).pack(pady=5)
        
        # Botão de Produzir: Salva no banco e abate estoque
        ctk.CTkButton(self, text="PRODUZIR E LANÇAR NO ESTOQUE", fg_color="#2ecc71", height=50, command=lambda: self.calc(salvar=True)).pack(pady=5)

    def add_i(self, txt, padrao):
        ctk.CTkLabel(self, text=txt).pack(); e = ctk.CTkEntry(self, width=350, justify="center"); e.insert(0, padrao); e.pack(); return e

    def get_lista_projetos(self):
        res = db.query("SELECT DISTINCT nome FROM produtos")
        return ["Novo Projeto"] + [p[0] for p in res]

    def get_mats(self):
        mats = db.query("SELECT material, id FROM filamento")
        return [f"{m[0]} (ID: {m[1]})" for m in mats] if mats else ["Nenhum Filamento"]

    def carregar(self, n):
        if n == "Novo Projeto": return
        try:
            d = db.query("SELECT nome, peso_u, tempo_h, hora_maq, margem FROM produtos WHERE nome=?", (n,))[0]
            self.ent_nome.delete(0, 'end'); self.ent_nome.insert(0, str(d[0]))
            self.ent_qtd.delete(0, 'end'); self.ent_qtd.insert(0, "1")
            self.ent_peso_total.delete(0, 'end'); self.ent_peso_total.insert(0, str(d[1]))
            self.ent_horas.delete(0, 'end'); self.ent_horas.insert(0, str(d[2]))
            self.ent_hm.delete(0, 'end'); self.ent_hm.insert(0, str(d[3]))
            self.ent_taxa.delete(0, 'end'); self.ent_taxa.insert(0, str(d[4]))
            self.calc(salvar=False)
        except: pass

    def conv(self, v): 
        try: return float(str(v).replace(",", ".")) if v else 0.0
        except: return 0.0

    def calc(self, salvar):
        try:
            txt_mat = self.combo_mat.get()
            if "ID:" not in txt_mat: return messagebox.showerror("Erro", "Selecione um filamento!")
            id_f = txt_mat.split("ID: ")[1].replace(")", "")
            f = db.query("SELECT preco_por_g, quantidade_g FROM filamento WHERE id=?", (id_f,))[0]
            
            nome = self.ent_nome.get()
            qtd = int(self.ent_qtd.get() or 1)
            peso_t = self.conv(self.ent_peso_total.get())
            tempo_t = self.conv(self.ent_horas.get())
            v_hm = self.conv(self.ent_hm.get())
            margem = self.conv(self.ent_taxa.get())

            custo_mat = peso_t * f[0]
            custo_maq = tempo_t * v_hm
            total_venda = (custo_mat + custo_maq) / (1 - (margem/100))
            valor_un = total_venda / qtd

            self.lbl_detalhes.configure(text=f"Material: R$ {custo_mat:.2f} | Máquina: R$ {custo_maq:.2f}")
            self.lbl_res.configure(text=f"Venda Total: R$ {total_venda:.2f}")
            self.lbl_unitario.configure(text=f"Preço Unitário: R$ {valor_un:.2f}")

            if salvar:
                if peso_t > f[1]: return messagebox.showerror("Erro", "Filamento insuficiente!")
                
                # Baixa filamento e atualiza estoque de peças
                db.execute("UPDATE filamento SET quantidade_g = quantidade_g - ? WHERE id=?", (peso_t, id_f))
                
                existe = db.query("SELECT id FROM produtos WHERE nome=?", (nome,))
                if existe:
                    p_id = existe[0][0]
                    db.execute("""UPDATE produtos SET quantidade=quantidade+?, preco_sugerido=?, 
                               valor_total_producao=valor_total_producao+?, peso_u=?, tempo_h=?, 
                               hora_maq=?, margem=? WHERE id=?""", (qtd, valor_un, total_venda, peso_t, tempo_t, v_hm, margem, p_id))
                else:
                    db.execute("""INSERT INTO produtos (nome, quantidade, preco_sugerido, valor_total_producao, peso_u, tempo_h, hora_maq, margem) 
                               VALUES (?,?,?,?,?,?,?,?)""", (nome, qtd, valor_un, total_venda, peso_t, tempo_t, v_hm, margem))
                    p_id = db.query("SELECT last_insert_rowid()")[0][0]

                db.execute("INSERT INTO historico_producao (produto_id, filamento_id, peso_usado) VALUES (?,?,?)", (p_id, id_f, peso_t))
                messagebox.showinfo("Sucesso", "Produção registrada!")
                self.refresh_callback()
        except Exception as e: messagebox.showerror("Erro", f"Confira os dados: {e}")