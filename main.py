import customtkinter as ctk
import database as db
from feats.calculadora_3d import AbaCalculadora
from feats.estoque import AbaEstoque
from feats.vendas import AbaVendas
from feats.dashboard import AbaDashboard
from feats.reparos import AbaReparos
from feats.financeiro import AbaFinanceiro
from feats.visualizador_3d import AbaVisualizadorSTL
import os

# Desativa logs desnecessários de bibliotecas gráficas
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.window=false"

class ERP3D(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # --- CONFIGURAÇÃO DA JANELA ---
        self.title("Sistema Gestão 3D - Pro")
        self.geometry("1100x850")
        self.minsize(900, 700) # Impede que a tela fique pequena demais
        ctk.set_appearance_mode("dark")
        
        # Inicializa Banco de Dados
        db.init_db()

        # --- ESTRUTURA DE ABAS ---
        # fill="both" e expand=True garantem que o fundo ocupe tudo, 
        # mas o conteúdo dentro delas será controlado.
        self.tabs = ctk.CTkTabview(self, segmented_button_fg_color="#2c3e50")
        self.tabs.pack(padx=20, pady=(10, 20), fill="both", expand=True)

        # Adicionando as abas
        self.t_dash = self.tabs.add("Dashboard")
        self.t_est  = self.tabs.add("Estoque")
        self.t_calc = self.tabs.add("Produção")
        self.t_vend = self.tabs.add("Vendas")
        self.t_rep  = self.tabs.add("Reparos")
        self.t_fin  = self.tabs.add("Financeiro")
        self.t_3d = self.tabs.add("Visualizador 3D")

        # --- INICIALIZAÇÃO DAS TELAS ---
        # Passamos as abas como master. Cada classe (AbaEstoque, etc) 
        # deve ter um frame interno centralizado para evitar o "estica-estica".
        
        self.tela_dash = AbaDashboard(self.t_dash)
        self.tela_dash.pack(fill="both", expand=True)

        self.tela_est = AbaEstoque(self.t_est, self.atualizar)
        self.tela_est.pack(fill="both", expand=True)

        self.tela_calc = AbaCalculadora(self.t_calc, self.atualizar)
        self.tela_calc.pack(fill="both", expand=True)

        self.tela_vend = AbaVendas(self.t_vend, self.atualizar)
        self.tela_vend.pack(fill="both", expand=True)

        self.tela_rep = AbaReparos(self.t_rep, self.atualizar)
        self.tela_rep.pack(fill="both", expand=True)

        self.tela_fin = AbaFinanceiro(self.t_fin, self.atualizar)
        self.tela_fin.pack(fill="both", expand=True)

        self.tela_3d = AbaVisualizadorSTL(self.t_3d)
        self.tela_3d.pack(fill="both", expand=True)

        # Atualização inicial
        self.atualizar()

    def atualizar(self):
        """
        Função central de sincronização. 
        Sempre que algo é salvo em uma aba, todas as outras se atualizam.
        """
        try:
            self.tela_dash.refresh()
            self.tela_est.refresh()
            self.tela_vend.atualizar_vendas()
            self.tela_rep.atualizar_tabela()
            self.tela_fin.atualizar_tabela()
            
            # Atualiza os menus de seleção na calculadora (evita que apareçam itens deletados)
            self.tela_calc.combo_mat.configure(values=self.tela_calc.get_mats())
            self.tela_calc.combo_projetos.configure(values=self.tela_calc.get_lista_projetos())
        except Exception as e:
            print(f"Aviso de sincronização: {e}")

if __name__ == "__main__":
    app = ERP3D()
    app.mainloop()