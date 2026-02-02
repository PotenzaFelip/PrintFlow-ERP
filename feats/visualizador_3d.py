import customtkinter as ctk
import trimesh
import pyvista as pv
import os
import shutil
from tkinter import filedialog, messagebox

class AbaVisualizadorSTL(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        # Pasta de banco de dados
        self.pasta_projetos = "stls_projeto"
        if not os.path.exists(self.pasta_projetos):
            os.makedirs(self.pasta_projetos)

        self.mesh_atual = None

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- PAINEL LATERAL ---
        self.frame_lateral = ctk.CTkFrame(self, width=280)
        self.frame_lateral.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(self.frame_lateral, text="📦 GESTÃO DE ARQUIVOS", font=("Arial", 16, "bold")).pack(pady=10)
        ctk.CTkButton(self.frame_lateral, text="IMPORTAR NOVO STL", fg_color="#2ecc71", command=self.importar_e_salvar).pack(pady=10, padx=20)

        # --- INFO BOX ---
        self.info_frame = ctk.CTkFrame(self.frame_lateral, fg_color="#2c3e50")
        self.info_frame.pack(fill="x", padx=10, pady=5)

        self.lbl_volume = ctk.CTkLabel(self.info_frame, text="Volume: ---", font=("Arial", 12))
        self.lbl_volume.pack(pady=2)
        self.lbl_peso = ctk.CTkLabel(self.info_frame, text="Peso (PLA): ---", font=("Arial", 12))
        self.lbl_peso.pack(pady=2)
        self.lbl_dimensoes = ctk.CTkLabel(self.info_frame, text="Dimensões: ---", font=("Arial", 11))
        self.lbl_dimensoes.pack(pady=2)

        # --- LISTA DE ARQUIVOS ---
        self.lista_arquivos = ctk.CTkScrollableFrame(self.frame_lateral, fg_color="#1e272e")
        self.lista_arquivos.pack(fill="both", expand=True, padx=5, pady=5)

        # --- ÁREA CENTRAL ---
        self.frame_central = ctk.CTkFrame(self, fg_color="black")
        self.frame_central.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        self.label_aviso = ctk.CTkLabel(self.frame_central, 
                                        text="Visualizador OpenGL Pronto\n\nClique no ícone 👁 para abrir a peça.", 
                                        font=("Arial", 13), text_color="gray")
        self.label_aviso.place(relx=0.5, rely=0.5, anchor="center")

        self.atualizar_lista_arquivos()

    def visualizar_stl(self, caminho):
        try:
            self.mesh_atual = trimesh.load(caminho)
            
            # Cálculos
            vol_cm3 = self.mesh_atual.volume / 1000
            peso_estimado = vol_cm3 * 1.25 
            bounds = self.mesh_atual.extents

            self.lbl_volume.configure(text=f"Volume: {vol_cm3:.2f} cm³")
            self.lbl_peso.configure(text=f"Peso (PLA): ~{peso_estimado:.1f} g")
            self.lbl_dimensoes.configure(text=f"X:{bounds[0]:.1f} Y:{bounds[1]:.1f} Z:{bounds[2]:.1f} mm")

            # Renderização OpenGL
            plotter = pv.Plotter(title=f"PrintFlow 3D - {os.path.basename(caminho)}")
            plotter.set_background("#2c3e50")
            pv_mesh = pv.wrap(self.mesh_atual)
            plotter.add_mesh(pv_mesh, color="orange", show_edges=True, smooth_shading=True, specular=0.5)
            plotter.add_axes()
            plotter.view_isometric()
            plotter.show()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao abrir motor 3D: {e}")

    def atualizar_lista_arquivos(self):
        """Atualiza a lista lateral com os 3 botões: Ver, Baixar e Deletar"""
        for w in self.lista_arquivos.winfo_children(): w.destroy()
        if not os.path.exists(self.pasta_projetos): return
        
        for arq in [f for f in os.listdir(self.pasta_projetos) if f.endswith('.stl')]:
            f = ctk.CTkFrame(self.lista_arquivos, fg_color="transparent")
            f.pack(fill="x", pady=2)
            
            ctk.CTkLabel(f, text=arq[:15], font=("Arial", 11)).pack(side="left", padx=5)
            
            # Botão Deletar (Lixeira)
            ctk.CTkButton(f, text="🗑️", width=30, fg_color="#c0392b", hover_color="#a93226",
                          command=lambda a=arq: self.deletar_stl(a)).pack(side="right", padx=1)
            
            # Botão Baixar (Download) - RECUPERADO
            ctk.CTkButton(f, text="📥", width=30, fg_color="#d35400", hover_color="#ba4a00",
                          command=lambda a=arq: self.baixar_stl(a)).pack(side="right", padx=1)
            
            # Botão Ver (Olho)
            ctk.CTkButton(f, text="👁", width=30, fg_color="#3498db", hover_color="#2980b9",
                          command=lambda a=arq: self.visualizar_stl(os.path.join(self.pasta_projetos, a))).pack(side="right", padx=1)

    def baixar_stl(self, nome_arquivo):
        """Exporta o arquivo da biblioteca para qualquer lugar do PC"""
        caminho_origem = os.path.join(self.pasta_projetos, nome_arquivo)
        caminho_destino = filedialog.asksaveasfilename(
            defaultextension=".stl",
            initialfile=nome_arquivo,
            filetypes=[("Arquivos STL", "*.stl")]
        )
        if caminho_destino:
            shutil.copy(caminho_origem, caminho_destino)
            messagebox.showinfo("Sucesso", f"Arquivo '{nome_arquivo}' exportado com sucesso!")

    def importar_e_salvar(self):
        origem = filedialog.askopenfilename(filetypes=[("Arquivos STL", "*.stl")])
        if origem:
            nome = os.path.basename(origem)
            destino = os.path.join(self.pasta_projetos, nome)
            shutil.copy(origem, destino)
            self.atualizar_lista_arquivos()

    def deletar_stl(self, nome):
        if messagebox.askyesno("Confirmar", f"Deseja excluir permanentemente {nome}?"):
            try:
                os.remove(os.path.join(self.pasta_projetos, nome))
                self.atualizar_lista_arquivos()
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível deletar: {e}")