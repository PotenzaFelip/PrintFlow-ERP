# 🚀 PrintFlow ERP - Gestão Inteligente para Impressão 3D

O **PrintFlow ERP** é uma solução industrial desenvolvida em Python para centralizar o gerenciamento de manufatura aditiva. O sistema une a precisão da engenharia 3D com a robustez de um controle financeiro e de estoque, permitindo que produtores tenham visão total sobre seus custos e processos.

## ✨ Funcionalidades em Destaque

- **🔍 Visualizador 3D High-End (OpenGL):** Inspeção técnica de arquivos STL via motor PyVista, com suporte a sombreamento suave, visualização de malhas (wireframe) e rotação fluida.
- **📐 Engenharia de Precisão:** Extração automática de métricas cruciais para orçamentos:
    - Volume exato em $cm³$.
    - Peso estimado baseado na densidade do filamento (ex: PLA, PETG).
    - Dimensões reais (Bounding Box) em milímetros ($X, Y, Z$).
- **📦 Gestão de Insumos:** Controle de estoque de filamentos com precificação por grama e rastreabilidade por lote/cor.
- **⚙️ Produção & Orçamentos:** Calculadora integrada que cruza dados de material, tempo de impressão e depreciação de hardware para gerar o preço de venda sugerido.
- **💰 Frente de Caixa (PDV):** Registro de vendas com baixa automática de estoque e atualização de valor patrimonial em tempo real.
- **📊 Dashboard Estatístico:** Dashboards gerados com Pandas e Matplotlib para análise de faturamento, lucratividade e materiais mais utilizados.

## 🛠️ Tecnologias Utilizadas

- **Interface:** `CustomTkinter` (Modern Dark Mode).
- **Engine 3D:** `PyVista` (VTK) e `Trimesh` para processamento geométrico e cálculos de volume.
- **Ciência de Dados:** `Pandas` e `Matplotlib`.
- **Persistência:** `SQLite` (Banco de dados relacional integrado).

## 🚀 Como Executar o Projeto

1. **Clone o repositório:**
```bash
git clone [https://github.com/PotenzaFelip/PrintFlow-ERP.git](https://github.com/PotenzaFelip/PrintFlow-ERP.git)
cd printflow-erp
```

## 🛠️ Instalação e Execução

1. **Instale as dependências técnicas:**
```bash
pip install customtkinter pyvista trimesh PyQt5 pandas matplotlib
```

2. **Inicie o sistema:**
```bash
python main.py
```

## 🏗️ Gerar Executável (Build)

Para compilar o projeto em um único diretório para Windows, garantindo que as ferramentas de 3D e as pastas de dados sejam incluídas corretamente:

```bash
# 1. Instale o PyInstaller e o hook necessário
pip install pyinstaller

# 2. Execute o build com suporte total a bibliotecas 3D
pyinstaller --noconfirm --onedir --windowed --clean --add-data "feats;feats" --add-data "stls_projeto;stls_projeto" --collect-submodules "pyvista" --collect-submodules "pyvistaqt" --hidden-import "PyQt5" --name "PrintFlow_ERP" main.py
```

## 📂 Guia do Visualizador 3D

Na aba de visualização, cada arquivo na sua biblioteca possui três ações rápidas:

* **👁 (Ver):** Aciona o motor OpenGL externo para inspeção detalhada da peça.
* **📥 (Download):** Exporta uma cópia do arquivo STL da biblioteca do ERP para qualquer pasta no seu PC.
* **🗑️ (Lixeira):** Remove o arquivo da biblioteca e limpa os dados técnicos associados.

---
