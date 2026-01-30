import customtkinter as ctk
from tkinter import messagebox
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

class AbaCalculadora(ctk.CTkScrollableFrame):
    def __init__(self, master, refresh_callback):
        super().__init__(master, fg_color="transparent")
        self.refresh_callback = refresh_callback
        
        ctk.CTkLabel(self, text="🚀 CALCULADORA E ORÇAMENTOS", font=("Arial", 20, "bold")).pack(pady=10)
        
        # --- SELEÇÃO ---
        self.frame_sel = ctk.CTkFrame(self)
        self.frame_sel.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(self.frame_sel, text="Usar Modelo Salvo:").grid(row=0, column=0, padx=10, pady=5)
        self.combo_projetos = ctk.CTkOptionMenu(self.frame_sel, values=self.get_lista_projetos(), command=self.carregar, width=200)
        self.combo_projetos.grid(row=0, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(self.frame_sel, text="Filamento:").grid(row=1, column=0, padx=10, pady=5)
        self.combo_mat = ctk.CTkOptionMenu(self.frame_sel, values=self.get_mats(), width=200, fg_color="#27ae60")
        self.combo_mat.grid(row=1, column=1, padx=10, pady=5)

        # --- INPUTS DE CUSTO ---
        self.ent_nome = self.add_i("Nome do Projeto:", "Novo Projeto")
        self.ent_qtd = self.add_i("Qtd de Peças na Impressão:", "1")
        self.ent_peso_total = self.add_i("Peso TOTAL da Bandeja (g):", "0")
        self.ent_horas = self.add_i("Tempo Total (h):", "0")
        
        self.ent_hm = self.add_i("Hora-Máquina (R$):", "2.00")
        self.ent_setup = self.add_i("Setup/Mão de Obra (R$):", "10.00")
        self.ent_markup = self.add_i("Markup (Multiplicador):", "2.0")

        # --- RESULTADOS ---
        self.lbl_detalhes = ctk.CTkLabel(self, text="Material: R$ 0.00 | Máquina: R$ 0.00", font=("Arial", 12))
        self.lbl_detalhes.pack(pady=(15, 0))
        
        self.lbl_res = ctk.CTkLabel(self, text="Venda Total: R$ 0,00", font=("Arial", 26, "bold"), text_color="#2ecc71")
        self.lbl_res.pack(pady=5)
        
        self.lbl_unitario = ctk.CTkLabel(self, text="Unitário: R$ 0,00", font=("Arial", 16), text_color="#3498db")
        self.lbl_unitario.pack(pady=(0, 10))

        # --- BOTÕES ---
        ctk.CTkButton(self, text="CALCULAR COTAÇÃO", fg_color="#555", height=40, command=lambda: self.calc(registrar=False)).pack(pady=5, fill="x", padx=50)
        ctk.CTkButton(self, text="EFETIVAR VENDA (BAIXA ESTOQUE + FINANCEIRO)", fg_color="#e67e22", height=50, font=("Arial", 14, "bold"), command=lambda: self.calc(registrar=True)).pack(pady=5, fill="x", padx=50)

    def add_i(self, txt, padrao):
        f = ctk.CTkFrame(self, fg_color="transparent"); f.pack(fill="x", padx=50)
        ctk.CTkLabel(f, text=txt, width=200, anchor="w").pack(side="left")
        e = ctk.CTkEntry(f, width=150, justify="center"); e.insert(0, padrao); e.pack(side="right", pady=2)
        return e

    def get_lista_projetos(self):
        res = db.query("SELECT nome FROM produtos")
        return ["Novo Projeto"] + [p['nome'] for p in res]

    def get_mats(self):
        mats = db.query("SELECT material, cor, id FROM filamento WHERE peso_atual_g > 0")
        return [f"{m['material']} {m['cor']} | ID:{m['id']}" for m in mats] if mats else ["Sem Filamento"]

    def carregar(self, n):
        if n == "Novo Projeto": return
        try:
            d = db.query("SELECT * FROM produtos WHERE nome=?", (n,))[0]
            self.ent_nome.delete(0, 'end'); self.ent_nome.insert(0, str(d['nome']))
            self.ent_peso_total.delete(0, 'end'); self.ent_peso_total.insert(0, str(d['peso_u']))
            self.ent_horas.delete(0, 'end'); self.ent_horas.insert(0, str(d['tempo_h']))
            self.ent_hm.delete(0, 'end'); self.ent_hm.insert(0, str(d['hora_maq']))
            self.ent_markup.delete(0, 'end'); self.ent_markup.insert(0, str(d['margem']))
            self.ent_setup.delete(0, 'end'); self.ent_setup.insert(0, str(d['setup_valor']))
        except: pass

    def calc(self, registrar):
        try:
            # 1. Obter Dados do Filamento
            txt_mat = self.combo_mat.get()
            if "ID:" not in txt_mat: return messagebox.showerror("Erro", "Selecione o filamento!")
            id_f = txt_mat.split("ID:")[1]
            f = db.query("SELECT preco_por_g, peso_atual_g FROM filamento WHERE id=?", (id_f,))[0]

            # 2. Obter Inputs
            qtd = int(self.ent_qtd.get() or 1)
            peso_t = float(self.ent_peso_total.get().replace(",", "."))
            tempo_t = float(self.ent_horas.get().replace(",", "."))
            v_hm = float(self.ent_hm.get().replace(",", "."))
            v_setup = float(self.ent_setup.get().replace(",", "."))
            markup = float(self.ent_markup.get().replace(",", "."))

            # 3. Lógica de Preço (Conforme o print original)
            custo_mat = peso_t * f['preco_por_g']
            custo_maq = tempo_t * v_hm
            custo_total = custo_mat + custo_maq + v_setup
            total_venda = custo_total * markup
            valor_un = total_venda / qtd

            # Atualizar Labels
            self.lbl_detalhes.configure(text=f"Material: R$ {custo_mat:.2f} | Máquina: R$ {custo_maq:.2f} | Setup: R$ {v_setup:.2f}")
            self.lbl_res.configure(text=f"Venda Total: R$ {total_venda:.2f}")
            self.lbl_unitario.configure(text=f"Preço Unitário: R$ {valor_un:.2f}")

            if registrar:
                # Verificar estoque antes
                if peso_t > f['peso_atual_g']:
                    return messagebox.showerror("Erro", f"Estoque insuficiente! Disponível: {f['peso_atual_g']}g")

                # A. Salvar/Atualizar no Catálogo de Produtos
                nome = self.ent_nome.get()
                existe = db.query("SELECT id FROM produtos WHERE nome=?", (nome,))
                if existe:
                    p_id = existe[0]['id']
                    db.execute("""UPDATE produtos SET peso_u=?, tempo_h=?, hora_maq=?, margem=?, setup_valor=?, preco_sugerido=? 
                                  WHERE id=?""", (peso_t/qtd, tempo_t/qtd, v_hm, markup, v_setup, valor_un, p_id))
                else:
                    db.execute("""INSERT INTO produtos (nome, peso_u, tempo_h, hora_maq, margem, setup_valor, preco_sugerido) 
                                  VALUES (?,?,?,?,?,?,?)""", (nome, peso_t/qtd, tempo_t/qtd, v_hm, markup, v_setup, valor_un))
                    p_id = db.query("SELECT last_insert_rowid() as id")[0]['id']

                # B. Registrar a VENDA
                # Isso dispara o Trigger que: 1. Tira do rolo | 2. Soma no Financeiro
                db.execute("INSERT INTO vendas (produto_id, filamento_id, qtd_vendida, valor_total) VALUES (?,?,?,?)", 
                           (p_id, id_f, qtd, total_venda))

                messagebox.showinfo("Sucesso", "Venda Processada!\n- Estoque atualizado\n- Caixa financeiro atualizado")
                self.refresh_callback()

        except Exception as e:
            messagebox.showerror("Erro de Cálculo", f"Verifique os campos numéricos.\n{e}")