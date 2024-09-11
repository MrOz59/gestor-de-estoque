import ctypes
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from tkinter import messagebox
from tkinter import filedialog
import webbrowser
import winreg
from logs import configurar_logs
from db import (
gerar_relatorio_proximos_da_validade,gerar_relatorio_rotatividade_produtos,
gerar_relatorio_movimentacoes,adicionar_produto_base,buscar_produto_db,
editar_produto_base,buscar_produtos_por_criterio,adicionar_entrada,adicionar_saida,buscar_produtos_e_lotes,
gerar_relatorio_estoque,gerar_relatorio_pl,excluir_produto
)

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None

        # Bind mouse events to the widget
        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        if self.tooltip_window or not self.text:
            return
        
        # Pega a posição do mouse diretamente do evento
        x = event.x_root + 25  # Ajusta a posição da tooltip
        y = event.y_root + 25

        # Cria a janela da tooltip
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # Sem decorações de janela
        tw.wm_geometry(f"+{x}+{y}")  # Posição da tooltip

        # Cria o rótulo para o texto da tooltip
        label = tk.Label(tw, text=self.text, background="white", relief="solid", borderwidth=1, padx=5, pady=5)
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class Aplicacao(tk.Tk):
    def __init__(self,versao):
        logger = configurar_logs()
        logger.info("Interface grafica iniciada.")
        super().__init__()
        self.iconbitmap('icon.ico')
        self.title("Kalymos " + versao)
        self.geometry("600x400")
        self.state('zoomed')

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, expand=True)
        
        # Frame principal para a lista de produtos e a barra de busca
        self.produto_frame = tk.Frame(self)
        self.produto_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        # barra de busca

        self.busca_frame = tk.Frame(self.produto_frame)
        self.busca_frame.pack(pady=10, fill=tk.X)

        # Configure o layout para usar grid
        self.busca_frame.grid_rowconfigure(1, weight=1)  # Para permitir que a entry expanda
        self.busca_frame.grid_columnconfigure(1, weight=1)  # Para permitir que a entry expanda

        # Adicione o rótulo de busca
        self.busca_label = tk.Label(self.busca_frame, text='Buscar:')
        self.busca_label.grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)

        # Adicione a entrada de busca
        self.busca_entry = tk.Entry(self.busca_frame)
        self.busca_entry.grid(row=0, column=1, padx=10, pady=5, sticky=tk.EW)
        self.busca_entry.bind("<Return>", lambda event: self.buscar_produtos())

        # Adicione o botão de buscar
        self.buscar_btn = tk.Button(self.busca_frame, text='Buscar', cursor="hand2", command=self.buscar_produtos)
        self.buscar_btn.grid(row=0, column=2, padx=10, pady=5)

        # Adicione a etiqueta de ajuda
        self.lista_help = tk.Label(self.busca_frame, text="Para copiar um valor da lista, clique duas vezes em cima dele.")
        self.lista_help.grid(row=1, column=0, columnspan=3, padx=10, pady=(5,0), sticky='nsew')



        # Treeview para a lista de produtos
        self.tree = ttk.Treeview(
            self.produto_frame, 
            columns=('Nome', 'SKU', 'Fornecedor', 'Preço', 'PreçoVenda', 'Lote', 'Validade', 'Quantidade'), 
            show='headings'
        )
        # Configurando as colunas com cabeçalhos
        self.tree.heading('Nome', text='Nome', anchor=tk.CENTER)
        self.tree.heading('SKU', text='SKU', anchor=tk.CENTER)
        self.tree.heading('Fornecedor', text='Fornecedor', anchor=tk.CENTER)
        self.tree.heading('Preço', text='Preço', anchor=tk.CENTER)
        self.tree.heading('PreçoVenda', text='Preço de Venda', anchor=tk.CENTER)
        self.tree.heading('Lote', text='Lote', anchor=tk.CENTER)
        self.tree.heading('Validade', text='Validade', anchor=tk.CENTER)
        self.tree.heading('Quantidade', text='Quantidade', anchor=tk.CENTER)

        # Configurando o tamanho das colunas e centralizando o conteúdo
        self.tree.column('Nome', width=100, anchor=tk.CENTER)
        self.tree.column('SKU', width=80, anchor=tk.CENTER)
        self.tree.column('Fornecedor', width=100, anchor=tk.CENTER)
        self.tree.column('Preço', width=70, anchor=tk.CENTER)
        self.tree.column('PreçoVenda', width=100, anchor=tk.CENTER)
        self.tree.column('Lote', width=70, anchor=tk.CENTER)
        self.tree.column('Validade', width=90, anchor=tk.CENTER)
        self.tree.column('Quantidade', width=50, anchor=tk.CENTER)

        self.tree.pack(pady=10, fill=tk.BOTH, expand=True)

        # Bind duplo clique
        self.tree.bind("<Double-1>", self.click_duplo)


        # Aba Produtos
        self.aba_produtos = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_produtos, text='Base de Produtos')

        self.nome_label = tk.Label(self.aba_produtos, text='Nome:')
        self.nome_label.grid(row=0, column=0, padx=10, pady=10)
        self.nome_entry = tk.Entry(self.aba_produtos)
        self.nome_entry.grid(row=0, column=1, padx=10, pady=10)

        self.sku_label = tk.Label(self.aba_produtos, text='SKU:')
        self.sku_label.grid(row=1, column=0, padx=10, pady=10)
        self.help_label_sku = tk.Label(self.aba_produtos, text="?", font=("Arial", 16), fg="blue", cursor="question_arrow")
        ToolTip(self.help_label_sku,"Codigo usado para identificar o produto. Ex: SK-5918 ou 591801")
        self.help_label_sku.grid(row=1, column=2, padx=10, pady=10)
        self.sku_entry = tk.Entry(self.aba_produtos)
        self.sku_entry.grid(row=1, column=1, padx=10, pady=10)

        self.preco_label = tk.Label(self.aba_produtos, text='Preço:')
        self.preco_label.grid(row=2, column=0, padx=10, pady=10)
        self.help_label_preco = tk.Label(self.aba_produtos, text="?", font=("Arial", 16), fg="blue", cursor="question_arrow")
        ToolTip(self.help_label_preco,"Preço de compra do produto, somente numeros Ex: 15 ou 150,99")
        self.help_label_preco.grid(row=2, column=2, padx=10, pady=10)
        self.preco_entry = tk.Entry(self.aba_produtos)
        self.preco_entry.grid(row=2, column=1, padx=10, pady=10)

        self.fator_label = tk.Label(self.aba_produtos, text='Fator:')
        self.fator_label.grid(row=3, column=0, padx=10, pady=10)
        self.help_label_fator = tk.Label(self.aba_produtos, text="?", font=("Arial", 16), fg="blue", cursor="question_arrow")
        self.help_label_fator.grid(row=3, column=2, padx=10, pady=10)
        ToolTip(self.help_label_fator,"Numero usada para calcular o preço de venda. Ex: 1,50 seria 50%, 2,5 seria 150%")
        self.fator_entry = tk.Entry(self.aba_produtos)
        self.fator_entry.grid(row=3, column=1, padx=10, pady=10)

        self.preco_venda_label = tk.Label(self.aba_produtos, text='Preço de Venda:')
        self.preco_venda_label.grid(row=4, column=0, padx=10, pady=10)
        self.preco_venda_entry = tk.Entry(self.aba_produtos, state="disabled")
        self.preco_venda_entry.grid(row=4, column=1, padx=10, pady=10)

        self.preco_entry.bind("<KeyRelease>", self.atualizar_preco_venda)

        self.fornecedor_label = tk.Label(self.aba_produtos, text='Fornecedor:')
        self.fornecedor_label.grid(row=5, column=0, padx=10, pady=10)
        self.fornecedor_entry = tk.Entry(self.aba_produtos)
        self.fornecedor_entry.grid(row=5, column=1, padx=10, pady=10)

        self.adicionar_produto_btn = tk.Button(self.aba_produtos, text='Adicionar Produto',cursor="hand2", command=self.adicionar_produto_base_aba)
        self.adicionar_produto_btn.grid(row=6, column=0, columnspan=2, pady=10)

        # Aba Editar Produtos
        self.aba_produtos_editar = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_produtos_editar, text='Editar Base de Produtos')

        self.sku_editar_label = tk.Label(self.aba_produtos_editar, text='SKU:')
        self.sku_editar_label.grid(row=0, column=0, padx=10, pady=10)
        self.help_label_editar = tk.Label(self.aba_produtos_editar, text="?", font=("Arial", 16), fg="blue", cursor="question_arrow")
        self.help_label_editar.grid(row=0, column=2, padx=10, pady=10)
        ToolTip(self.help_label_editar,"Digite um SKU e tecle ENTER. \n Você tambem pode alterar o SKU do produto depois de carregar os dados dele.")
        self.sku_editar_entry = tk.Entry(self.aba_produtos_editar)
        self.sku_editar_entry.grid(row=0, column=1, padx=10, pady=10)
        self.sku_editar_entry.bind("<Return>", lambda event: self.carregar_dados_produto())

        self.nome_editar_label = tk.Label(self.aba_produtos_editar, text='Nome:')
        self.nome_editar_label.grid(row=1, column=0, padx=10, pady=10)
        self.nome_editar_entry = tk.Entry(self.aba_produtos_editar, state='disabled')
        self.nome_editar_entry.grid(row=1, column=1, padx=10, pady=10)

        self.preco_editar_label = tk.Label(self.aba_produtos_editar, text='Preço:')
        self.preco_editar_label.grid(row=2, column=0, padx=10, pady=10)
        self.help_label_preco_editar = tk.Label(self.aba_produtos_editar, text="?", font=("Arial", 16), fg="blue", cursor="question_arrow")
        ToolTip(self.help_label_preco_editar,"Preço de compra do produto, somente numeros Ex: 15 ou 150,99")
        self.help_label_preco_editar.grid(row=2, column=2, padx=10, pady=10)
        self.preco_editar_entry = tk.Entry(self.aba_produtos_editar, state='disabled')
        self.preco_editar_entry.grid(row=2, column=1, padx=10, pady=10)

        self.fator_editar_label = tk.Label(self.aba_produtos_editar, text='Fator:')
        self.fator_editar_label.grid(row=3, column=0, padx=10, pady=10)
        self.fator_help_label_editar = tk.Label(self.aba_produtos_editar, text="?", font=("Arial", 16), fg="blue", cursor="question_arrow")
        self.fator_help_label_editar.grid(row=3, column=2, padx=10, pady=10)
        ToolTip(self.fator_help_label_editar,"Numero usada para calcular o preço de venda. Ex: 1,50 seria 50%, 2,5 seria 150%")
        self.fator_editar_entry = tk.Entry(self.aba_produtos_editar, state="disabled")
        self.fator_editar_entry.grid(row=3, column=1, padx=10, pady=10)

        self.preco_editar_venda_label = tk.Label(self.aba_produtos_editar, text='Preço de Venda:')
        self.preco_editar_venda_label.grid(row=4, column=0, padx=10, pady=10)
        self.preco_editar_venda_entry = tk.Entry(self.aba_produtos_editar, state="disabled")
        self.preco_editar_venda_entry.grid(row=4, column=1, padx=10, pady=10)

        self.preco_editar_entry.bind("<KeyRelease>", self.atualizar_preco_venda)
        self.fator_editar_entry.bind("<KeyRelease>", self.atualizar_preco_venda)

        self.fornecedor_editar_label = tk.Label(self.aba_produtos_editar, text='Fornecedor:')
        self.fornecedor_editar_label.grid(row=5, column=0, padx=10, pady=10)
        self.fornecedor_editar_entry = tk.Entry(self.aba_produtos_editar, state='disabled')
        self.fornecedor_editar_entry.grid(row=5, column=1, padx=10, pady=10)

        self.salvar_produto_btn = tk.Button(self.aba_produtos_editar, text='Salvar Produto',cursor="hand2", command=self.editar_produto, state='disabled')
        self.salvar_produto_btn.grid(row=6, column=0, columnspan=2, pady=10)

        self.deletar_produto_btn = tk.Button(self.aba_produtos_editar, text='Deletar Produto',cursor="hand2", command=self.excluir_produto, state='disabled')
        self.deletar_produto_btn.grid(row=6, column=2, columnspan=2, pady=10)

        # Aba Entrada
        self.aba_entrada = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_entrada, text='Entrada de Estoque')

        self.sku_entrada_label = tk.Label(self.aba_entrada, text='SKU:')
        self.sku_entrada_label.grid(row=0, column=0, padx=10, pady=10)
        self.sku_entrada_entry = tk.Entry(self.aba_entrada)
        self.sku_entrada_entry.grid(row=0, column=1, padx=10, pady=10)

        self.lote_entrada_label = tk.Label(self.aba_entrada, text='Lote:')
        self.lote_entrada_label.grid(row=1, column=0, padx=10, pady=10)
        self.lote_entrada_entry = tk.Entry(self.aba_entrada)
        self.lote_entrada_entry.grid(row=1, column=1, padx=10, pady=10)

        self.lote_entrada_aplicavel_var = tk.BooleanVar(value=True)
        self.lote_entrada_aplicavel_checkbox = tk.Checkbutton(self.aba_entrada, text='Lote Aplicável', variable=self.lote_entrada_aplicavel_var, command=lambda: self.atualizar_campos(1))
        self.lote_entrada_aplicavel_checkbox.grid(row=1, column=2, padx=10, pady=10, sticky='w')
        self.help_label_entrada = tk.Label(self.aba_entrada, text="?", font=("Arial", 16), fg="blue", cursor="question_arrow")
        self.help_label_entrada.grid(row=1, column=3, padx=10, pady=10, sticky='w')
        ToolTip(self.help_label_entrada,"Caso seu produto não tenha lote desative esta opção")

        self.validade_entrada_label = tk.Label(self.aba_entrada, text='Validade (dd/mm/aaaa):')
        self.validade_entrada_label.grid(row=2, column=0, padx=10, pady=10)
        self.validade_entrada_entry = tk.Entry(self.aba_entrada)
        self.validade_entrada_entry.bind("<FocusOut>", self.formatar_data)
        self.validade_entrada_entry.grid(row=2, column=1, padx=10, pady=10)

        self.validade_entrada_aplicavel_var = tk.BooleanVar(value=True)
        self.validade_entrada_aplicavel_checkbox = tk.Checkbutton(self.aba_entrada, text='Lote Aplicável', variable=self.validade_entrada_aplicavel_var, command=lambda: self.atualizar_campos(1))
        self.validade_entrada_aplicavel_checkbox.grid(row=2, column=2, padx=10, pady=10, sticky='w')
        self.help_label_entrada2 = tk.Label(self.aba_entrada, text="?", font=("Arial", 16), fg="blue", cursor="question_arrow")
        self.help_label_entrada2.grid(row=2, column=3, padx=10, pady=10, sticky='w')
        ToolTip(self.help_label_entrada2,"Caso seu produto não tenha validade desative esta opção")

        self.quantidade_entrada_label = tk.Label(self.aba_entrada, text='Quantidade:')
        self.quantidade_entrada_label.grid(row=3, column=0, padx=10, pady=10)
        self.quantidade_entrada_entry = tk.Entry(self.aba_entrada)
        self.quantidade_entrada_entry.grid(row=3, column=1, padx=10, pady=10)

        self.motivo_entrada_label = tk.Label(self.aba_entrada, text='Motivo:')
        self.motivo_entrada_label.grid(row=4, column=0, padx=10, pady=10)
        self.motivo_entrada_combobox = ttk.Combobox(self.aba_entrada, values=['Compra', 'Devolução', 'Balanço'], state='readonly')
        self.motivo_entrada_combobox.grid(row=4, column=1, padx=10, pady=10)

        self.adicionar_entrada_btn = tk.Button(self.aba_entrada, text='Adicionar Entrada', cursor="hand2", command=self.adicionar_entrada)
        self.adicionar_entrada_btn.grid(row=5, column=0, columnspan=3, pady=10)



        # Aba Saída
        self.aba_saida = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_saida, text='Saída de Estoque')

        self.sku_saida_label = tk.Label(self.aba_saida, text='SKU:')
        self.sku_saida_label.grid(row=0, column=0, padx=10, pady=10)
        self.sku_saida_entry = tk.Entry(self.aba_saida)
        self.sku_saida_entry.grid(row=0, column=1, padx=10, pady=10)

        self.lote_saida_label = tk.Label(self.aba_saida, text='Lote:')
        self.lote_saida_label.grid(row=1, column=0, padx=10, pady=10)
        self.lote_saida_entry = tk.Entry(self.aba_saida)
        self.lote_saida_entry.grid(row=1, column=1, padx=10, pady=10)
        self.help_label_saida = tk.Label(self.aba_saida, text="?", font=("Arial", 16), fg="blue", cursor="question_arrow")
        self.help_label_saida.grid(row=1, column=3, padx=10, pady=10, sticky='w')
        ToolTip(self.help_label_saida,"Caso seu produto não tenha lote desative esta opção")

        # Adicionando checkbox para lote
        self.lote_saida_aplicavel_var = tk.BooleanVar(value=True)
        self.lote_saida_aplicavel_checkbox = tk.Checkbutton(self.aba_saida, text='Lote Aplicável', variable=self.lote_saida_aplicavel_var, command=lambda: self.atualizar_campos(2))
        self.lote_saida_aplicavel_checkbox.grid(row=1, column=2, padx=10, pady=10, sticky='w')

        self.quantidade_saida_label = tk.Label(self.aba_saida, text='Quantidade:')
        self.quantidade_saida_label.grid(row=2, column=0, padx=10, pady=10)
        self.quantidade_saida_entry = tk.Entry(self.aba_saida)
        self.quantidade_saida_entry.grid(row=2, column=1, padx=10, pady=10)

        self.motivo_saida_label = tk.Label(self.aba_saida, text='Motivo:')
        self.motivo_saida_label.grid(row=3, column=0, padx=10, pady=10)
        self.motivo_saida_combobox = ttk.Combobox(self.aba_saida, values=['Venda', 'Vencido', 'Perda/Avaria', 'Consumo'], state='readonly')
        self.motivo_saida_combobox.grid(row=3, column=1, padx=10, pady=10)

        self.adicionar_saida_btn = tk.Button(self.aba_saida, text='Adicionar Saída', cursor="hand2", command=self.adicionar_saida)
        self.adicionar_saida_btn.grid(row=4, column=0, columnspan=3, pady=10)  # Ajustado para ocupar 3 colunas


        # Aba Relatórios
        self.aba_relatorios = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_relatorios, text='Relatórios')

        self.relatorio_vencimento_btn = tk.Button(self.aba_relatorios, text='Relatório de Vencimento Próximo',cursor="hand2", command=gerar_relatorio_proximos_da_validade)
        self.relatorio_vencimento_btn.pack(pady=10)

        self.relatorio_alta_saida_btn = tk.Button(self.aba_relatorios, text='Relatório de Rotatividade',cursor="hand2", command=gerar_relatorio_rotatividade_produtos)
        self.relatorio_alta_saida_btn.pack(pady=10)

        self.relatorio_movimentacoes_btn = tk.Button(self.aba_relatorios, text='Relatório de Movimentações',cursor="hand2", command=gerar_relatorio_movimentacoes)
        self.relatorio_movimentacoes_btn.pack(pady=10)
        
        self.relatorio_estoque_btn = tk.Button(self.aba_relatorios, text='Relatório de Estoque',cursor="hand2", command=gerar_relatorio_estoque)
        self.relatorio_estoque_btn.pack(pady=10)

        self.relatorio_vendas_btn = tk.Button(self.aba_relatorios, text='Relatório P&L',cursor="hand2", command=gerar_relatorio_pl)
        self.relatorio_vendas_btn.pack(pady=10)

        # Aba Configurações
        self.aba_config = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_config, text='Configurações')

        # Diretório dos Relatórios
        self.relatorios_label = tk.Label(self.aba_config, text='Diretório dos Relatórios:')
        self.relatorios_label.grid(row=0, column=0, padx=(10, 5), pady=(10, 8))

        self.relatorios_entry = tk.Entry(self.aba_config)
        self.relatorios_entry.grid(row=1, column=0, padx=(10, 5), pady=(0, 8), sticky="nsew")

        self.relatorios_btn = tk.Button(self.aba_config, text='Selecionar Diretório',cursor="hand2", command=self.selecionar_diretorio)
        self.relatorios_btn.grid(row=1, column=1, padx=(10, 5), pady=(0, 8), sticky="nsew")

        # Botões de Ação
        self.salvar_config_btn = tk.Button(self.aba_config, text='Salvar Configurações',cursor="hand2", command=self.salvar_configuracoes)
        self.salvar_config_btn.grid(row=4, column=0, columnspan=2, pady=10)

        self.restaurar_padrao_btn = tk.Button(self.aba_config, text='Restaurar Padrões',cursor="hand2", command=self.restaurar_padroes)
        self.restaurar_padrao_btn.grid(row=5, column=0, columnspan=2, pady=10)

        # Informações sobre a Versão
        self.sobre_label = tk.Label(self.aba_config, text='Sobre o Aplicativo:')
        self.sobre_label.grid(row=6, column=0, padx=(10, 5), pady=(10, 8))

        self.sobre_info = tk.Label(self.aba_config, text=f'Versão: {versao}\n© 2024 MrOz')
        self.sobre_info.grid(row=7, column=0, columnspan=2, padx=(10, 5), pady=(0, 8))

        # Link para a wiki do GitHub
        self.wiki_link = tk.Label(self.aba_config, text="Wiki do Projeto", fg="blue", cursor="hand2")
        self.wiki_link.grid(row=8, column=0, columnspan=2, pady=(10, 8))
        self.wiki_link.bind("<Button-1>", self.abrir_wiki)

        # Configurando as colunas para expandirem
        self.aba_config.grid_columnconfigure(0, weight=1)  # Expande a coluna do Entry
        self.aba_config.grid_columnconfigure(1, weight=0)  # Expande a coluna do Entry

        self.carregar_configuracoes()
        self.atualizar_lista_produtos()

    def atualizar_campos(self, aba):
        if aba == 1:
            # Atualiza o estado dos campos com base nas checkboxes da aba de entrada
            estado_validade = 'normal' if self.validade_entrada_aplicavel_var.get() else 'disabled'
            self.validade_entrada_entry.config(state=estado_validade)

            estado_lote = 'normal' if self.lote_entrada_aplicavel_var.get() else 'disabled'
            self.lote_entrada_entry.config(state=estado_lote)
        elif aba == 2:
            # Atualiza o estado dos campos com base na checkbox da aba de saída
            estado_lote = 'normal' if self.lote_saida_aplicavel_var.get() else 'disabled'
            self.lote_saida_entry.config(state=estado_lote)

    def click_duplo(self, event):
        # Obtendo o item e a coluna clicada
        item = self.tree.identify('item', event.x, event.y)
        column = self.tree.identify_column(event.x)
        
        # Verificar se o item é válido
        if item:
            column_index = int(column.split('#')[1]) - 1
            value = self.tree.item(item, 'values')[column_index]
            self.copiar_texto(value)
    
    def copiar_texto(self, text):
        # Copiar texto para a área de transferência
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()  # Atualizar o clipboard

    def abrir_wiki(self, event):
        url = "https://github.com/MrOz59/kalymos/wiki"  # Substitua pela URL da wiki do seu projeto
        webbrowser.open(url)
        
    def pegar_diretorio_documentos(self):
        # Definir o identificador da pasta de Documentos
        CSIDL_PERSONAL = 5  # CSIDL para a pasta de Documentos
        SHGFP_TYPE_CURRENT = 0  # Para pegar o caminho atual da pasta

        # Definir MAX_PATH manualmente como 260
        MAX_PATH = 260

        # Buffer para armazenar o caminho da pasta
        buf = ctypes.create_unicode_buffer(MAX_PATH)

        # Chamar a função do Windows para pegar o caminho da pasta de Documentos
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)

        return buf.value

    def selecionar_diretorio(self):
        diretorio = filedialog.askdirectory()
        if diretorio:
            self.relatorios_entry.delete(0, tk.END)
            self.relatorios_entry.insert(0, diretorio)

    def salvar_configuracoes(self):
        diretorio_relatorios = self.relatorios_entry.get()
        
        try:
            # Abrir (ou criar) a chave do registro
            reg_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\KalymosApp")
            
            # Definir valores no registro
            winreg.SetValueEx(reg_key, 'DiretorioRelatorios', 0, winreg.REG_SZ, diretorio_relatorios)
            
            # Fechar a chave
            winreg.CloseKey(reg_key)
            
            tk.messagebox.showinfo("Configurações", "Configurações salvas com sucesso.")
        except Exception as e:
            tk.messagebox.showerror("Erro", f"Erro ao salvar configurações: {e}")

    def restaurar_padroes(self):
        try:
            # Abrir a chave do registro
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\KalymosApp", 0, winreg.KEY_ALL_ACCESS)
            
            # Restaurar valores padrão
            self.relatorios_entry.delete(0, tk.END)
            self.relatorios_entry.insert(0, self.pegar_diretorio_documentos())
            
            # Fechar a chave
            winreg.CloseKey(reg_key)
            
            tk.messagebox.showinfo("Configurações", "Configurações restauradas para os padrões.")
        except FileNotFoundError:
            tk.messagebox.showwarning("Configurações", "Nenhuma configuração encontrada para restaurar.")
        except Exception as e:
            tk.messagebox.showerror("Erro", f"Erro ao restaurar configurações: {e}")
        self.salvar_configuracoes()

    def carregar_configuracoes(self):
        try:
            # Abrir a chave do registro
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\KalymosApp", 0, winreg.KEY_READ)
            
            # Ler valores
            diretorio_relatorios = winreg.QueryValueEx(reg_key, 'DiretorioRelatorios')[0]
            
            # Fechar a chave
            winreg.CloseKey(reg_key)
            
            # Atualizar os campos com os valores do registro
            self.relatorios_entry.delete(0, tk.END)
            self.relatorios_entry.insert(0, diretorio_relatorios)
        except FileNotFoundError:
            # Configurações não encontradas, usar valores padrão
            self.relatorios_entry.insert(0, self.pegar_diretorio_documentos())
            self.formato_combobox.set('PDF')
        except Exception as e:
            tk.messagebox.showerror("Erro", f"Erro ao carregar configurações: {e}")
    
    def atualizar_preco_venda(self, event=None):
        def calcular_e_atualizar_preco_venda(entry_preco, entry_fator, entry_preco_venda):
            try:
               
                preco = float(entry_preco.get().replace(',', '.'))
                fator = float(entry_fator.get().replace(',', '.'))
                preco_venda = preco * fator

               
                entry_preco_venda.config(state="normal")
                entry_preco_venda.delete(0, tk.END)
                entry_preco_venda.insert(0, f"{preco_venda:.2f}")
                entry_preco_venda.config(state="readonly")
            except ValueError:
                
                entry_preco_venda.config(state="normal")
                entry_preco_venda.delete(0, tk.END)
                entry_preco_venda.config(state="readonly")

    def excluir_produto(self):
        resposta = messagebox.askyesno(
                "Confirmação Exclusão",
                f"A exclusão de um produto é definitiva e não pode ser desfeita. Tem certeza de que deseja excluir o produto?"
            )
        if resposta:
            sku = self.sku_editar_entry.get().strip()
            resultado = excluir_produto(sku)
            if resultado["status"] == "sucesso":
                messagebox.showinfo("Sucesso", resultado["mensagem"])
                self.atualizar_lista_produtos()
                self.limpar_campos_produtos(2)
            else:
                messagebox.showerror("Erro", resultado["mensagem"])

    def adicionar_produto_base_aba(self):
        nome = self.nome_entry.get().strip()
        sku = self.sku_entry.get().strip()
        preco = self.preco_entry.get().replace(',', '.').strip()
        fornecedor = self.fornecedor_entry.get().strip()
        fator = self.fator_entry.get().replace(',', '.').strip()
       
        resultado = adicionar_produto_base(nome, sku, preco, fornecedor,fator)
        
        
        if resultado["status"] == "sucesso":
            messagebox.showinfo("Sucesso", resultado["mensagem"])
            self.atualizar_lista_produtos()
            self.limpar_campos_produtos(2)
        else:
            messagebox.showerror("Erro", resultado["mensagem"])
        self.limpar_campos_produtos(1)

    def editar_produto(self):
        sku = self.sku_editar_entry.get()
        nome = self.nome_editar_entry.get()
        preco = self.preco_editar_entry.get().replace(',', '.').strip()
        fornecedor = self.fornecedor_editar_entry.get()
        fator = self.fator_editar_entry.get().replace(',', '.').strip()

        if not sku:
            messagebox.showerror("Erro", "SKU é necessário para a edição.")
            return

        if not nome:
            messagebox.showerror("Erro", "Nome é necessário para a edição.")
            return

        if not preco:
            messagebox.showerror("Erro", "Preço é necessário para a edição.")
            return

        if not fornecedor:
            messagebox.showerror("Erro", "Fornecedor é necessário para a edição.")
            return

        if not fator:
            messagebox.showerror("Erro", "Fator é necessário para a edição.")
            return

       
        resultado = editar_produto_base(self.sku_antigo, sku, nome, preco, fornecedor, fator)
        
        
        if resultado["status"] == "sucesso":
            messagebox.showinfo("Sucesso", resultado["mensagem"])
            self.atualizar_lista_produtos()
            self.limpar_campos_produtos(2)
        else:
            messagebox.showerror("Erro", resultado["mensagem"])
        
    def buscar_produtos(self):
        criterio = self.busca_entry.get()
        if not criterio:
            self.atualizar_lista_produtos()
            return
        
        try:
            resultados = buscar_produtos_por_criterio(criterio)
            self.atualizar_lista_produtos(resultados)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao buscar produtos: {e}")

    def atualizar_lista_produtos(self, resultados=None):

        for row in self.tree.get_children():
            self.tree.delete(row)

        if resultados is None:
            resultados = buscar_produtos_e_lotes()
        
        for row in resultados:
            self.tree.insert('', 'end', values=row)

    def carregar_dados_produto(self):
        sku = self.sku_editar_entry.get()
        produto = buscar_produto_db(sku)

        if produto:
            # Armazena o SKU antigo em uma variável de instância
            self.sku_antigo = sku
            
            self.nome_editar_entry.config(state='normal')
            self.preco_editar_entry.config(state='normal')
            self.fator_editar_entry.config(state='normal')
            self.preco_editar_venda_entry.config(state='readonly')
            self.fornecedor_editar_entry.config(state='normal')
            
            # Preenche os campos com os dados do produto
            self.nome_editar_entry.delete(0, tk.END)
            self.nome_editar_entry.insert(0, produto['nome'])
            self.preco_editar_entry.delete(0, tk.END)
            self.preco_editar_entry.insert(0, produto['preco'])
            self.fator_editar_entry.delete(0, tk.END)
            self.fator_editar_entry.insert(0, produto['fator'])
            self.fornecedor_editar_entry.delete(0, tk.END)
            self.fornecedor_editar_entry.insert(0, produto['fornecedor'])
            
            self.salvar_produto_btn.config(state='normal')
            self.deletar_produto_btn.config(state='normal')
            self.atualizar_preco_venda()
        else:
            # Caso o produto não seja encontrado, desabilita os campos de edição
            self.nome_editar_entry.config(state='disabled')
            self.preco_editar_entry.config(state='disabled')
            self.fator_editar_entry.config(state='disabled')
            self.preco_editar_venda_entry.config(state='disabled')
            self.fornecedor_editar_entry.config(state='disabled')
            self.salvar_produto_btn.config(state='disabled')
            self.deletar_produto_btn.config(state='disabled')

    def adicionar_entrada(self):
        # Verifica se a checkbox de validade está marcada e define o valor como '-' se não estiver
        validade = self.validade_entrada_entry.get() if self.validade_entrada_aplicavel_var.get() else "-"
        
        # Verifica se a checkbox de lote está marcada e define o valor como '-' se não estiver
        lote = self.lote_entrada_entry.get() if self.lote_entrada_aplicavel_var.get() else "-"

        # Obtém os valores dos outros campos
        sku = self.sku_entrada_entry.get()
        quantidade = self.quantidade_entrada_entry.get()
        motivo = self.motivo_entrada_combobox.get()

        # Valida a data se a checkbox de validade estiver marcada
        if self.validade_entrada_aplicavel_var.get() and not self.validar_data(validade):
            messagebox.showerror("Erro", "A validade deve estar no formato dd/mm/aaaa e ser uma data válida.")
            return

        # Adiciona a entrada, com o parâmetro `substituir` como 0 (não substituir)
        resultado = adicionar_entrada(sku, lote, validade, quantidade, motivo, 0)
        
        if resultado["status"] == "erro" and "substituir?" in resultado["mensagem"]:
            validade_existente = resultado["validade_existente"]
            resposta = messagebox.askyesno(
                "Confirmação de Substituição",
                f"A data de validade é diferente da cadastrada. Deseja substituir?\nData cadastrada: {validade_existente}\nNova data: {validade}"
            )
            if resposta:
                # Adiciona a entrada novamente, com o parâmetro `substituir` como 1 (substituir)
                resultado = adicionar_entrada(sku, lote, validade, quantidade, motivo, 1)
            else:
                resultado["status"] = "cancelado"
        
        if resultado["status"] == "sucesso":
            self.atualizar_lista_produtos()
        elif resultado["status"] == "error":
            messagebox.showerror("Erro", resultado["mensagem"])
        self.limpar_campos_produtos(4)

    def adicionar_saida(self):
        sku = self.sku_saida_entry.get()
        
        # Verifica o estado da checkbox
        lote = self.lote_saida_entry.get()
        if not self.lote_saida_aplicavel_var.get():
            lote = "-"  # Define como "-" se a checkbox não estiver marcada

        quantidade = self.quantidade_saida_entry.get()
        motivo = self.motivo_saida_combobox.get()

        resultado = adicionar_saida(sku, lote, quantidade, motivo)
        self.atualizar_lista_produtos()

        if resultado["status"] == "sucesso":
            messagebox.showinfo("Sucesso", resultado["mensagem"])
            self.limpar_campos_produtos(2)  # Limpa os campos da aba de saída
        else:
            messagebox.showerror("Erro", resultado["mensagem"])
        self.limpar_campos_produtos(3)

    def formatar_data(self, event):
        entry = event.widget
        data = entry.get().strip()
        if len(data) == 8:
            try:
                data_formatada = datetime.strptime(data, '%d%m%Y').strftime('%d/%m/%Y')
                entry.delete(0, tk.END)
                entry.insert(0, data_formatada)
            except ValueError:
                # Opcional: exibe uma mensagem de erro se o formato da data estiver incorreto
                messagebox.showerror("Erro", "Formato de data inválido. Utilize o formato ddmmyyyy.")      
    
    def validar_data(self, data_str):
        try:
            datetime.strptime(data_str, '%d/%m/%Y')
            return True
        except ValueError:
            return False
        
    def limpar_campos_produtos(self,form):
        if form == 1:
            self.nome_entry.delete(0, tk.END)
            self.sku_entry.delete(0, tk.END)
            self.preco_entry.delete(0, tk.END)
            self.fator_entry.delete(0, tk.END)
            self.preco_venda_entry.delete(0, tk.END)
            self.fornecedor_entry.delete(0, tk.END)
        if form == 2:
            self.nome_editar_entry.delete(0, tk.END)
            self.sku_editar_entry.delete(0, tk.END)
            self.preco_editar_entry.delete(0, tk.END)
            self.fator_editar_entry.delete(0, tk.END)
            self.preco_editar_venda_entry.delete(0, tk.END)
            self.fornecedor_editar_entry.delete(0, tk.END)
            self.nome_editar_entry.config(state='disabled')
            self.preco_editar_entry.config(state='disabled')
            self.fator_editar_entry.config(state='disabled')
            self.preco_editar_venda_entry.config(state='disabled')
            self.fornecedor_editar_entry.config(state='disabled')
        if form == 3:
            self.lote_saida_entry.delete(0,tk.END)
            self.sku_saida_entry.delete(0,tk.END)
            self.quantidade_saida_entry.delete(0,tk.END)
            self.motivo_saida_combobox.set("")
            self.lote_saida_aplicavel_var.set(True)
            self.atualizar_campos(2)
          
        if form == 4:
            self.lote_entrada_entry.delete(0,tk.END)
            self.sku_entrada_entry.delete(0,tk.END)
            self.quantidade_entrada_entry.delete(0,tk.END)
            self.motivo_entrada_combobox.set("")
            self.validade_entrada_aplicavel_var.set(True)
            self.lote_entrada_aplicavel_var.set(True)
            self.atualizar_campos(1)
            

    
