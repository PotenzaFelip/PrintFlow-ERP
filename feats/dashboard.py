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
        
        # Título Principal
        ctk.CTkLabel(self, text="📊 DASHBOARD ESTRATÉGICO", font=("Arial", 24, "bold")).pack(pady=20)
        
        # --- FILTROS DE DATA COM CALENDÁRIO ---
        self.frame_filtros = ctk.CTkFrame(self)
        self.frame_filtros.pack(fill="x", padx=20, pady=10)
        
        # Datas iniciais (Mês atual)
        self.data_inicio_str = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        self.data_fim_str = datetime.now().strftime('%Y-%m-%d')

        # Seletor de Início
        ctk.CTkLabel(self.frame_filtros, text="Início:").pack(side="left", padx=5)
        self.btn_data_inicio = ctk.CTkButton(
            self.frame_filtros, text=self.data_inicio_str, width=120, 
            fg_color="#34495e", command=lambda: self.abrir_calendario("inicio")
        )
        self.btn_data_inicio.pack(side="left", padx=5)
        
        # Seletor de Fim
        ctk.CTkLabel(self.frame_filtros, text="Fim:").pack(side="left", padx=5)
        self.btn_data_fim = ctk.CTkButton(
            self.frame_filtros, text=self.data_fim_str, width=120, 
            fg_color="#34495e", command=lambda: self.abrir_calendario("fim")
        )
        self.btn_data_fim.pack(side="left", padx=5)
        
        # Botão de Comando
        ctk.CTkButton(
            self.frame_filtros, text="🔍 ATUALIZAR", width=100, 
            command=self.refresh, fg_color="#3498db"
        ).pack(side="left", padx=10)

        # Botão de Exportar
        self.btn_exportar = ctk.CTkButton(
            self, text="📥 EXCEL: RELATÓRIO COMPLETO", 
            fg_color="#27ae60", hover_color="#1e8449",
            font=("Arial", 13, "bold"), command=self.exportar_relatorio_geral
        )
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
        """Abre janela para escolha de data via calendário"""
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
            self.refresh() # Atualiza automaticamente ao escolher

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
            d_ini = self.data_inicio_str
            d_fim = self.data_fim_str
            # Correção para o SQLite pegar o dia inteiro até o último segundo
            d_fim_completo = f"{d_fim} 23:59:59"

            conn = sqlite3.connect(db.DB_PATH)
            df_vendas = pd.read_sql_query(f"SELECT * FROM vendas WHERE data >= '{d_ini}' AND data <= '{d_fim_completo}'", conn)
            df_financeiro = pd.read_sql_query(f"SELECT * FROM financeiro WHERE data >= '{d_ini}' AND data <= '{d_fim_completo}'", conn)
            df_filamento = pd.read_sql_query("SELECT material, cor, peso_atual_g FROM filamento", conn)
            conn.close()

            # --- ATUALIZAR CARDS ---
            ent = df_financeiro[df_financeiro['tipo'] == 'ENTRADA']['valor'].sum()
            sai = df_financeiro[df_financeiro['tipo'] == 'SAIDA']['valor'].sum()
            
            self.card_lucro.configure(text=f"R$ {ent - sai:.2f}")
            self.card_saidas.configure(text=f"R$ {sai:.2f}")
            self.card_filamento_real.configure(text=f"{df_filamento['peso_atual_g'].sum():.0f} g")
            self.card_vendas_qtd.configure(text=f"{len(df_vendas)}")

            # Limpar e recriar gráficos
            for w in self.frame_graficos.winfo_children(): w.destroy()
            plt.style.use('dark_background')

            # --- GRÁFICO 1: ESTOQUE (Abreviado) ---
            if not df_filamento.empty:
                fig1, ax1 = plt.subplots(figsize=(10, 3.5))
                labels = [f"{self.abreviar(r['material'])} ({self.abreviar(r['cor'], 5)})" for _, r in df_filamento.iterrows()]
                ax1.bar(labels, df_filamento['peso_atual_g'], color='#3498db')
                ax1.set_title("Volume em Estoque (g)", fontsize=11, color="#3498db")
                plt.xticks(rotation=15, fontsize=8)
                plt.tight_layout()
                FigureCanvasTkAgg(fig1, self.frame_graficos).get_tk_widget().pack(fill="x", pady=10)

            # --- GRÁFICO 2: FINANCEIRO (Focado no Período) ---
            if not df_financeiro.empty:
                fig2, ax2 = plt.subplots(figsize=(10, 4.5))
                df_financeiro['data_dt'] = pd.to_datetime(df_financeiro['data']).dt.date
                resumo = df_financeiro.groupby(['data_dt', 'tipo'])['valor'].sum().unstack().fillna(0)
                resumo = resumo.sort_index()

                if 'ENTRADA' not in resumo: resumo['ENTRADA'] = 0.0
                if 'SAIDA' not in resumo: resumo['SAIDA'] = 0.0

                resumo.plot(kind='line', marker='o', ax=ax2, color=['#2ecc71', '#e74c3c'], linewidth=2)
                
                # Forçar limites do gráfico no filtro selecionado
                lim_ini = pd.to_datetime(d_ini).date()
                lim_fim = pd.to_datetime(d_fim).date()
                ax2.set_xlim(lim_ini, lim_fim)
                
                ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
                ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
                
                ax2.set_title(f"Fluxo Financeiro: {d_ini} a {d_fim}", fontsize=11)
                ax2.grid(True, alpha=0.1)
                plt.tight_layout()
                FigureCanvasTkAgg(fig2, self.frame_graficos).get_tk_widget().pack(fill="x", pady=10)
            else:
                ctk.CTkLabel(self.frame_graficos, text="🚫 Nenhum dado financeiro no período selecionado.", text_color="#e74c3c").pack(pady=30)

        except Exception as e:
            print(f"Erro ao carregar Dashboard: {e}")

    def exportar_relatorio_geral(self):
        try:
            caminho_arquivo = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                title="Salvar Relatório Geral",
                initialfile=f"Relatorio_Gestao_{datetime.now().strftime('%Y%m%d')}.xlsx"
            )
            if not caminho_arquivo: return

            import sqlite3
            from openpyxl.styles import Font, PatternFill
            
            conn = sqlite3.connect(db.DB_PATH)
            
            sql_vendas = """
                SELECT v.id, p.nome as Produto, f.material || ' ' || f.cor as Filamento, 
                v.qtd_vendida, v.valor_total, v.data FROM vendas v
                JOIN produtos p ON v.produto_id = p.id
                JOIN filamento f ON v.filamento_id = f.id
            """
            
            tabelas = {
                'Vendas': pd.read_sql_query(sql_vendas, conn),
                'Financeiro': pd.read_sql_query("SELECT * FROM financeiro", conn),
                'Estoque': pd.read_sql_query("SELECT material, cor, peso_atual_g FROM filamento", conn),
                'Produtos': pd.read_sql_query("SELECT nome, preco_sugerido FROM produtos", conn)
            }
            conn.close()

            with pd.ExcelWriter(caminho_arquivo, engine='openpyxl') as writer:
                for nome, df in tabelas.items():
                    df.to_excel(writer, sheet_name=nome, index=False)
                    ws = writer.sheets[nome]
                    for cell in ws[1]:
                        cell.font = Font(bold=True, color="FFFFFF")
                        cell.fill = PatternFill(start_color="2980B9", end_color="2980B9", fill_type="solid")
                    # Ajuste de colunas simplificado
                    for col in ws.columns:
                        ws.column_dimensions[col[0].column_letter].width = 15
            
            messagebox.showinfo("Sucesso", "Excel exportado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar: {e}")