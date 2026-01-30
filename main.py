import customtkinter as ctk
import database as db
from feats.calculadora_3d import AbaCalculadora
from feats.estoque import AbaEstoque
from feats.vendas import AbaVendas
from feats.dashboard import AbaDashboard
from feats.reparos import AbaReparos
from feats.financeiro import AbaFinanceiro

class ERP3D(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema Gestão 3D - Pro")
        self.geometry("900x800")
        ctk.set_appearance_mode("dark")
        db.init_db()

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(padx=10, pady=10, fill="both", expand=True)

        # Criando as abas
        self.t_dash = self.tabs.add("Dashboard")
        self.t_est = self.tabs.add("Estoque")
        self.t_calc = self.tabs.add("Produção")
        self.t_vend = self.tabs.add("Vendas")
        self.t_rep = self.tabs.add("Reparos")
        self.t_fin = self.tabs.add("Financeiro")

        # Inicializando as telas
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

    def atualizar(self):
        """Função que todas as abas chamam para manter os dados sincronizados"""
        self.tela_dash.refresh()
        self.tela_est.refresh()
        self.tela_vend.atualizar_vendas()
        self.tela_rep.atualizar_tabela()
        self.tela_fin.atualizar_tabela()
        # Atualiza os menus de seleção na calculadora
        self.tela_calc.combo_mat.configure(values=self.tela_calc.get_mats())
        self.tela_calc.combo_projetos.configure(values=self.tela_calc.get_lista_projetos())

if __name__ == "__main__":
    app = ERP3D()
    app.mainloop()