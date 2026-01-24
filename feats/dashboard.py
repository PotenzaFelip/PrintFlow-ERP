import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import database as db
import sqlite3

class AbaDashboard(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        ctk.CTkLabel(self, text="📊 ANÁLISE GERAL DE PRODUÇÃO", font=("Arial", 24, "bold")).pack(pady=20)
        
        # --- CARDS DE KPI ---
        self.frame_cards_master = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_cards_master.pack(fill="x", padx=20, pady=10)
        
        self.card_vendas = self.criar_card(self.frame_cards_master, "Faturamento Total", "R$ 0,00", "#2ecc71")
        self.card_pecas = self.criar_card(self.frame_cards_master, "Peças em Estoque", "0 un", "#3498db")
        self.card_filamento_total = self.criar_card(self.frame_cards_master, "Filamento Total (g)", "0 g", "#f1c40f")
        self.card_tipos_filamento = self.criar_card(self.frame_cards_master, "Tipos de Materiais", "0", "#9b59b6")

        # --- CONTAINER DE GRÁFICOS (Vertical) ---
        # Removido pack_propagate para permitir que o scroll funcione conforme os gráficos são adicionados
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
            df_vendas = pd.read_sql_query("SELECT * FROM vendas", conn)
            df_produtos = pd.read_sql_query("SELECT * FROM produtos", conn)
            df_filamento = pd.read_sql_query("SELECT * FROM filamento", conn)
            conn.close()

            # Atualiza Cards
            faturamento = df_vendas['valor_total'].sum() if not df_vendas.empty else 0
            total_pecas = df_produtos['quantidade'].sum() if not df_produtos.empty else 0
            total_gramas = df_filamento['quantidade_g'].sum() if not df_filamento.empty else 0
            qtd_tipos = df_filamento['material'].nunique() if not df_filamento.empty else 0

            self.card_vendas.configure(text=f"R$ {faturamento:.2f}")
            self.card_pecas.configure(text=f"{int(total_pecas)} un")
            self.card_filamento_total.configure(text=f"{total_gramas:.0f} g")
            self.card_tipos_filamento.configure(text=f"{int(qtd_tipos)} tipos")

            # Limpa o container
            for widget in self.frame_graficos.winfo_children(): 
                widget.destroy()
            
            plt.style.use('dark_background')

            # --- GRÁFICO 1: BARRAS (TOPO) ---
            if not df_filamento.empty:
                # Aumentamos a largura (figsize) já que ele ocupa a tela toda
                fig1, ax1 = plt.subplots(figsize=(10, 5)) 
                df_f_plot = df_filamento.sort_values('quantidade_g', ascending=False).head(10)
                
                ax1.bar(df_f_plot['material'], df_f_plot['quantidade_g'], color='#f1c40f')
                ax1.set_title("Estoque por Material (Gramas)", fontsize=16, pad=20)
                plt.xticks(rotation=30, ha='right', fontsize=11)
                plt.tight_layout()

                canvas1 = FigureCanvasTkAgg(fig1, self.frame_graficos)
                canvas1.get_tk_widget().pack(fill="x", pady=(0, 30))

            # --- GRÁFICO 2: PIZZA (EMBAIXO) ---
            if not df_vendas.empty:
                fig2, ax2 = plt.subplots(figsize=(10, 6))
                vendas_resumo = df_vendas.groupby('produto_nome')['valor_total'].sum().sort_values(ascending=False).head(7)
                
                # Pizza com layout mais limpo
                ax2.pie(vendas_resumo, labels=vendas_resumo.index, autopct='%1.1f%%', startangle=140, textprops={'fontsize': 10})
                ax2.set_title("Ranking de Faturamento por Produto", fontsize=16, pad=20)
                plt.tight_layout()

                canvas2 = FigureCanvasTkAgg(fig2, self.frame_graficos)
                canvas2.get_tk_widget().pack(fill="x", pady=20)

        except Exception as e:
            print(f"Erro no Dashboard: {e}")