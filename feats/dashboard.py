import customtkinter as ctk
import pandas as pd
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import database as db
import sqlite3
from datetime import datetime
import matplotlib.dates as mdates
from tkcalendar import Calendar

class AbaDashboard(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        # --- TÍTULO PRINCIPAL ---
        ctk.CTkLabel(self, text="📊 DASHBOARD ESTRATÉGICO", font=("Arial", 24, "bold")).pack(pady=20)
        
        # --- FILTROS DE DATA ---
        self.frame_filtros = ctk.CTkFrame(self)
        self.frame_filtros.pack(fill="x", padx=20, pady=10)
        
        self.data_inicio_str = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        self.data_fim_str = datetime.now().strftime('%Y-%m-%d')

        ctk.CTkLabel(self.frame_filtros, text="Início:").pack(side="left", padx=5)
        self.btn_data_inicio = ctk.CTkButton(self.frame_filtros, text=self.data_inicio_str, width=120, fg_color="#34495e", command=lambda: self.abrir_calendario("inicio"))
        self.btn_data_inicio.pack(side="left", padx=5)
        
        ctk.CTkLabel(self.frame_filtros, text="Fim:").pack(side="left", padx=5)
        self.btn_data_fim = ctk.CTkButton(self.frame_filtros, text=self.data_fim_str, width=120, fg_color="#34495e", command=lambda: self.abrir_calendario("fim"))
        self.btn_data_fim.pack(side="left", padx=5)
        
        ctk.CTkButton(self.frame_filtros, text="🔍 ATUALIZAR", width=100, command=self.refresh, fg_color="#3498db").pack(side="left", padx=10)

        # Botão de Exportar
        self.btn_exportar = ctk.CTkButton(self, text="📥 EXCEL: RELATÓRIO COMPLETO", fg_color="#27ae60", hover_color="#1e8449", font=("Arial", 13, "bold"), command=self.exportar_relatorio_geral)
        self.btn_exportar.pack(pady=(10, 20))
        
        # --- CARDS DE KPI ---
        self.frame_cards_master = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_cards_master.pack(fill="x", padx=20, pady=10)
        
        self.card_lucro = self.criar_card(self.frame_cards_master, "Saldo no Período", "R$ 0,00", "#2ecc71")
        self.card_saidas = self.criar_card(self.frame_cards_master, "Total Saídas", "R$ 0,00", "#e74c3c")
        self.card_filamento_real = self.criar_card(self.frame_cards_master, "Estoque Total (g)", "0 g", "#f1c40f")
        self.card_vendas_qtd = self.criar_card(self.frame_cards_master, "Vendas (Período)", "0", "#3498db")

        # Container dos Gráficos
        self.frame_graficos = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_graficos.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.refresh()

    def abrir_calendario(self, tipo):
        janela_cal = ctk.CTkToplevel(self)
        janela_cal.title("Selecionar Data")
        janela_cal.geometry("300x380")
        janela_cal.grab_set() 
        janela_cal.attributes("-topmost", True)
        cal = Calendar(janela_cal, selectmode='day', date_pattern='y-mm-dd')
        cal.pack(pady=20, padx=10, fill="both", expand=True)

        def confirmar():
            data_sel = cal.get_date()
            if tipo == "inicio":
                self.data_inicio_str = data_sel
                self.btn_data_inicio.configure(text=data_sel)
            else:
                self.data_fim_str = data_sel
                self.btn_data_fim.configure(text=data_sel)
            janela_cal.destroy()
            self.refresh()
        ctk.CTkButton(janela_cal, text="Confirmar Data", command=confirmar).pack(pady=10)

    def criar_card(self, master, titulo, valor, cor):
        card = ctk.CTkFrame(master, border_width=2, border_color=cor)
        card.pack(side="left", padx=10, expand=True, fill="both")
        ctk.CTkLabel(card, text=titulo, font=("Arial", 12, "bold")).pack(pady=(15,0))
        lbl_valor = ctk.CTkLabel(card, text=valor, font=("Arial", 22, "bold"), text_color=cor)
        lbl_valor.pack(pady=(5,15))
        return lbl_valor

    def abreviar(self, texto, limite=10):
        texto = str(texto)
        return (texto[:limite] + '..') if len(texto) > limite else texto

    def refresh(self):
        try:
            d_ini, d_fim = self.data_inicio_str, self.data_fim_str
            d_fim_completo = f"{d_fim} 23:59:59"

            conn = sqlite3.connect(db.DB_PATH)
            df_financeiro = pd.read_sql_query(f"SELECT * FROM financeiro WHERE data >= '{d_ini}' AND data <= '{d_fim_completo}'", conn)
            df_filamento = pd.read_sql_query("SELECT material, cor, peso_atual_g FROM filamento ORDER BY material ASC", conn)
            df_vendas = pd.read_sql_query(f"SELECT id FROM vendas WHERE data >= '{d_ini}' AND data <= '{d_fim_completo}'", conn)
            conn.close()

            # --- CARDS ---
            ent = df_financeiro[df_financeiro['tipo'] == 'ENTRADA']['valor'].sum()
            sai = df_financeiro[df_financeiro['tipo'] == 'SAIDA']['valor'].sum()
            self.card_lucro.configure(text=f"R$ {ent - sai:.2f}")
            self.card_saidas.configure(text=f"R$ {sai:.2f}")
            self.card_filamento_real.configure(text=f"{df_filamento['peso_atual_g'].sum():.0f} g")
            self.card_vendas_qtd.configure(text=f"{len(df_vendas)}")

            for w in self.frame_graficos.winfo_children(): w.destroy()
            plt.style.use('dark_background')

            # --- GRÁFICO 1: ESTOQUE (Mantido) ---
            if not df_filamento.empty:
                fig1, ax1 = plt.subplots(figsize=(12, 4))
                labels = [f"{self.abreviar(r['material'], 8)}\n{self.abreviar(r['cor'], 6)}" for _, r in df_filamento.iterrows()]
                cores = ['#e74c3c' if x < 200 else '#3498db' for x in df_filamento['peso_atual_g']]
                bars = ax1.bar(labels, df_filamento['peso_atual_g'], color=cores)
                ax1.bar_label(bars, padding=3, fontsize=8)
                ax1.set_title("Volume em Estoque por Filamento (g)", fontsize=12, pad=20)
                plt.xticks(rotation=45, ha='right', fontsize=9)
                plt.subplots_adjust(bottom=0.3)
                FigureCanvasTkAgg(fig1, self.frame_graficos).get_tk_widget().pack(fill="x", pady=10)

            # --- PROCESSAMENTO FINANCEIRO SEM ZERAR DATAS VAZIAS ---
            if not df_financeiro.empty:
                df_financeiro['data_dt'] = pd.to_datetime(df_financeiro['data']).dt.date
                # Agrupa apenas datas existentes
                resumo = df_financeiro.groupby(['data_dt', 'tipo'])['valor'].sum().unstack().fillna(0)
                resumo = resumo.sort_index()

                for col in ['ENTRADA', 'SAIDA']:
                    if col not in resumo: resumo[col] = 0.0

                # --- GRÁFICO 2: FLUXO DIÁRIO ---
                fig2, ax2 = plt.subplots(figsize=(10, 4))
                # marker='' remove as bolinhas se preferir uma linha limpa, ou use 'o' para destacar os dias com dados
                resumo.plot(kind='line', marker='o', ax=ax2, color=['#2ecc71', '#e74c3c'], linewidth=2)
                
                ax2.set_title(f"Movimentações Reais no Período", fontsize=11)
                
                # Configuração do Eixo X para respeitar o filtro sem criar dados falsos
                ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
                ax2.set_xlim([pd.to_datetime(d_ini), pd.to_datetime(d_fim)]) # Força o limite visual do gráfico
                
                plt.tight_layout()
                FigureCanvasTkAgg(fig2, self.frame_graficos).get_tk_widget().pack(fill="x", pady=10)

                # --- GRÁFICO 3: GASTOS ACUMULADOS ---
                resumo['Gastos_Acumulados'] = resumo['SAIDA'].cumsum()
                fig3, ax3 = plt.subplots(figsize=(10, 4))
                
                # Plotamos apenas onde houve gasto (SAIDA > 0) para não ter escada reta infinita
                df_gastos = resumo[resumo['SAIDA'] > 0]
                
                if not df_gastos.empty:
                    ax3.fill_between(resumo.index, resumo['Gastos_Acumulados'], color='#e74c3c', alpha=0.3)
                    ax3.plot(resumo.index, resumo['Gastos_Acumulados'], color='#c0392b', marker='o', linewidth=2.5)
                
                ax3.set_title("Evolução dos Gastos (R$)", fontsize=11, color="#e74c3c")
                ax3.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
                ax3.set_xlim([pd.to_datetime(d_ini), pd.to_datetime(d_fim)])
                
                plt.tight_layout()
                FigureCanvasTkAgg(fig3, self.frame_graficos).get_tk_widget().pack(fill="x", pady=10)
            else:
                ctk.CTkLabel(self.frame_graficos, text=f"🚫 Sem movimentações entre {d_ini} e {d_fim}.").pack(pady=30)

        except Exception as e:
            print(f"Erro Dashboard: {e}")

    def exportar_relatorio_geral(self):
        try:
            caminho = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")], title="Salvar Relatório")
            if not caminho: return
            conn = sqlite3.connect(db.DB_PATH)
            pd.read_sql_query("SELECT * FROM financeiro", conn).to_excel(caminho, index=False)
            conn.close()
            messagebox.showinfo("Sucesso", "Exportado!")
        except Exception as e:
            messagebox.showerror("Erro", str(e))