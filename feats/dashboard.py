import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import database as db
import sqlite3

class AbaDashboard(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        ctk.CTkLabel(self, text="📊 DASHBOARD ESTRATÉGICO", font=("Arial", 24, "bold")).pack(pady=20)
        
        # --- CARDS DE KPI (Atualizados para o novo Financeiro) ---
        self.frame_cards_master = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_cards_master.pack(fill="x", padx=20, pady=10)
        
        self.card_lucro = self.criar_card(self.frame_cards_master, "Saldo em Caixa (Lucro)", "R$ 0,00", "#2ecc71")
        self.card_saidas = self.criar_card(self.frame_cards_master, "Total de Investimento", "R$ 0,00", "#e74c3c")
        self.card_filamento_real = self.criar_card(self.frame_cards_master, "Estoque Real (g)", "0 g", "#f1c40f")
        self.card_vendas_qtd = self.criar_card(self.frame_cards_master, "Vendas Realizadas", "0", "#3498db")

        self.frame_graficos = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_graficos.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.refresh()

    def criar_card(self, master, titulo, valor, cor):
        card = ctk.CTkFrame(master, border_width=2, border_color=cor)
        card.pack(side="left", padx=10, expand=True, fill="both")
        ctk.CTkLabel(card, text=titulo, font=("Arial", 12, "bold")).pack(pady=(15,0))
        lbl_valor = ctk.CTkLabel(card, text=valor, font=("Arial", 22, "bold"), text_color=cor)
        lbl_valor.pack(pady=(5,15))
        return lbl_valor

    def refresh(self):
        try:
            conn = sqlite3.connect(db.DB_PATH)
            # Carregando as novas tabelas
            df_vendas = pd.read_sql_query("SELECT * FROM vendas", conn)
            df_filamento = pd.read_sql_query("SELECT * FROM filamento", conn)
            df_financeiro = pd.read_sql_query("SELECT * FROM financeiro", conn)
            conn.close()

            # --- CÁLCULO DOS CARDS ---
            entradas = df_financeiro[df_financeiro['tipo'] == 'ENTRADA']['valor'].sum()
            saidas = df_financeiro[df_financeiro['tipo'] == 'SAIDA']['valor'].sum()
            saldo_caixa = entradas - saidas
            
            # Peso atual (o que sobrou nos rolos)
            peso_real = df_filamento['peso_atual_g'].sum() if not df_filamento.empty else 0
            qtd_vendas = len(df_vendas)

            self.card_lucro.configure(text=f"R$ {saldo_caixa:.2f}")
            self.card_saidas.configure(text=f"R$ {saidas:.2f}")
            self.card_filamento_real.configure(text=f"{peso_real:.0f} g")
            self.card_vendas_qtd.configure(text=f"{qtd_vendas}")

            # Limpa gráficos antigos
            for widget in self.frame_graficos.winfo_children(): 
                widget.destroy()
            
            plt.style.use('dark_background')

            # --- GRÁFICO 1: SAÚDE DO ESTOQUE (Saldo Atual por Rolo) ---
            if not df_filamento.empty:
                fig1, ax1 = plt.subplots(figsize=(10, 4)) 
                # Criamos um nome amigável: Material + Cor
                df_filamento['desc'] = df_filamento['material'] + " " + df_filamento['cor']
                
                ax1.bar(df_filamento['desc'], df_filamento['peso_atual_g'], color='#3498db')
                ax1.axhline(y=100, color='r', linestyle='--', label='Alerta (100g)') # Linha de alerta
                ax1.set_title("Nível de Estoque Real por Rolo (g)", fontsize=14)
                plt.xticks(rotation=20, ha='right')
                plt.tight_layout()

                canvas1 = FigureCanvasTkAgg(fig1, self.frame_graficos)
                canvas1.get_tk_widget().pack(fill="x", pady=20)

            # --- GRÁFICO 2: ENTRADAS VS SAÍDAS NO TEMPO ---
            if not df_financeiro.empty:
                fig2, ax2 = plt.subplots(figsize=(10, 4))
                df_financeiro['data'] = pd.to_datetime(df_financeiro['data'])
                # Agrupa por dia e tipo
                resumo_fin = df_financeiro.groupby([df_financeiro['data'].dt.date, 'tipo'])['valor'].sum().unstack().fillna(0)
                
                resumo_fin.plot(kind='line', marker='o', ax=ax2, color=['#2ecc71', '#e74c3c'])
                ax2.set_title("Movimentação Financeira (Entradas vs Saídas)", fontsize=14)
                plt.tight_layout()

                canvas2 = FigureCanvasTkAgg(fig2, self.frame_graficos)
                canvas2.get_tk_widget().pack(fill="x", pady=20)

        except Exception as e:
            print(f"Erro no Dashboard: {e}")