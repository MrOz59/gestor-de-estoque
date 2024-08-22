import tkinter as tk
from tkinter import ttk
from datetime import datetime
from tkinter import messagebox
from logs import configurar_logs
from db import (
gerar_relatorio_proximos_da_validade,gerar_relatorio_rotatividade_produtos,
gerar_relatorio_movimentacoes,adicionar_produto_base,buscar_produto_db,
editar_produto_base,buscar_produtos_por_criterio,adicionar_entrada,adicionar_saida,buscar_produtos_e_lotes,
gerar_relatorio_estoque,gerar_relatorio_pl
)

class Aplicacao(tk.Tk):
    def __init__(self):
        logger = configurar_logs()
        logger.info("Interface grafica iniciada.")
        super().__init__()
        self.title("kalymos")
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

        self.busca_label = tk.Label(self.busca_frame, text='Buscar:')
        self.busca_label.pack(padx=10, pady=5, side=tk.LEFT)

        self.busca_entry = tk.Entry(self.busca_frame)
        self.busca_entry.pack(padx=10, pady=5, side=tk.LEFT, fill=tk.X, expand=True)

        self.buscar_btn = tk.Button(self.busca_frame, text='Buscar', command=self.buscar_produtos)
        self.buscar_btn.pack(padx=10, pady=5, side=tk.LEFT)

        # Treeview para a lista de produtos
        self.tree = ttk.Treeview(self.produto_frame, columns=('Nome', 'SKU', 'Fornecedor', 'Preço', 'PreçoVenda', 'Lote', 'Validade', 'Quantidade'), show='headings')
        self.tree.heading('Nome', text='Nome')
        self.tree.heading('SKU', text='SKU')
        self.tree.heading('Fornecedor', text='Fornecedor')
        self.tree.heading('Preço', text='Preço')
        self.tree.heading('PreçoVenda', text='Preço de Venda')
        self.tree.heading('Lote', text='Lote')
        self.tree.heading('Validade', text='Validade')
        self.tree.heading('Quantidade', text='Quantidade')
        self.tree.column('Nome', width=100)
        self.tree.column('SKU', width=80)
        self.tree.column('Fornecedor', width=100)
        self.tree.column('Preço', width=70)
        self.tree.column('PreçoVenda', width=100)
        self.tree.column('Lote', width=70)
        self.tree.column('Validade', width=90)
        self.tree.column('Quantidade', width=50)

        self.tree.pack(pady=10, fill=tk.BOTH, expand=True)

        # Aba Produtos
        self.aba_produtos = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_produtos, text='Base de Produtos')

        self.nome_label = tk.Label(self.aba_produtos, text='Nome:')
        self.nome_label.grid(row=0, column=0, padx=10, pady=10)
        self.nome_entry = tk.Entry(self.aba_produtos)
        self.nome_entry.grid(row=0, column=1, padx=10, pady=10)

        self.sku_label = tk.Label(self.aba_produtos, text='SKU:')
        self.sku_label.grid(row=1, column=0, padx=10, pady=10)
        self.sku_entry = tk.Entry(self.aba_produtos)
        self.sku_entry.grid(row=1, column=1, padx=10, pady=10)

        self.preco_label = tk.Label(self.aba_produtos, text='Preço:')
        self.preco_label.grid(row=2, column=0, padx=10, pady=10)
        self.preco_entry = tk.Entry(self.aba_produtos)
        self.preco_entry.grid(row=2, column=1, padx=10, pady=10)

        self.fator_label = tk.Label(self.aba_produtos, text='Fator:')
        self.fator_label.grid(row=3, column=0, padx=10, pady=10)
        self.fator_entry = tk.Entry(self.aba_produtos)
        self.fator_entry.grid(row=3, column=1, padx=10, pady=10)

        self.preco_venda_label = tk.Label(self.aba_produtos, text='Preço de Venda:')
        self.preco_venda_label.grid(row=4, column=0, padx=10, pady=10)
        self.preco_venda_entry = tk.Entry(self.aba_produtos, state="disabled")
        self.preco_venda_entry.grid(row=4, column=1, padx=10, pady=10)

        self.preco_entry.bind("<KeyRelease>", self.atualizar_preco_venda)
        self.fator_entry.bind("<KeyRelease>", self.atualizar_preco_venda)

        self.fornecedor_label = tk.Label(self.aba_produtos, text='Fornecedor:')
        self.fornecedor_label.grid(row=5, column=0, padx=10, pady=10)
        self.fornecedor_entry = tk.Entry(self.aba_produtos)
        self.fornecedor_entry.grid(row=5, column=1, padx=10, pady=10)

        self.adicionar_produto_btn = tk.Button(self.aba_produtos, text='Adicionar Produto', command=self.adicionar_produto_base_aba)
        self.adicionar_produto_btn.grid(row=6, column=0, columnspan=2, pady=10)

        # Aba Editar Produtos
        self.aba_produtos_editar = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_produtos_editar, text='Editar Base de Produtos')

        self.sku_editar_label = tk.Label(self.aba_produtos_editar, text='SKU:')
        self.sku_editar_label.grid(row=0, column=0, padx=10, pady=10)
        self.sku_editar_entry = tk.Entry(self.aba_produtos_editar)
        self.sku_editar_entry.grid(row=0, column=1, padx=10, pady=10)
        self.sku_editar_entry.bind("<Return>", lambda event: self.carregar_dados_produto())

        self.nome_editar_label = tk.Label(self.aba_produtos_editar, text='Nome:')
        self.nome_editar_label.grid(row=1, column=0, padx=10, pady=10)
        self.nome_editar_entry = tk.Entry(self.aba_produtos_editar, state='disabled')
        self.nome_editar_entry.grid(row=1, column=1, padx=10, pady=10)

        self.preco_editar_label = tk.Label(self.aba_produtos_editar, text='Preço:')
        self.preco_editar_label.grid(row=2, column=0, padx=10, pady=10)
        self.preco_editar_entry = tk.Entry(self.aba_produtos_editar, state='disabled')
        self.preco_editar_entry.grid(row=2, column=1, padx=10, pady=10)

        self.fator_editar_label = tk.Label(self.aba_produtos_editar, text='Fator:')
        self.fator_editar_label.grid(row=3, column=0, padx=10, pady=10)
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

        self.salvar_produto_btn = tk.Button(self.aba_produtos_editar, text='Salvar Produto', command=self.editar_produto)
        self.salvar_produto_btn.grid(row=6, column=0, columnspan=2, pady=10)

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

        self.validade_entrada_label = tk.Label(self.aba_entrada, text='Validade (dd/mm/aaaa):')
        self.validade_entrada_label.grid(row=2, column=0, padx=10, pady=10)
        self.validade_entrada_entry = tk.Entry(self.aba_entrada)
        self.validade_entrada_entry.grid(row=2, column=1, padx=10, pady=10)
        self.validade_entrada_entry.bind("<FocusOut>", lambda e: self.formatar_data(self.validade_entrada_entry))

        self.quantidade_entrada_label = tk.Label(self.aba_entrada, text='Quantidade:')
        self.quantidade_entrada_label.grid(row=3, column=0, padx=10, pady=10)
        self.quantidade_entrada_entry = tk.Entry(self.aba_entrada)
        self.quantidade_entrada_entry.grid(row=3, column=1, padx=10, pady=10)

        self.motivo_entrada_label = tk.Label(self.aba_entrada, text='Motivo:')
        self.motivo_entrada_label.grid(row=4, column=0, padx=10, pady=10)
        self.motivo_entrada_combobox = ttk.Combobox(self.aba_entrada, values=['Compra', 'Devolução', 'Balanço'], state='readonly')
        self.motivo_entrada_combobox.grid(row=4, column=1, padx=10, pady=10)

        self.adicionar_entrada_btn = tk.Button(self.aba_entrada, text='Adicionar Entrada', command=self.adicionar_entrada)
        self.adicionar_entrada_btn.grid(row=5, column=0, columnspan=2, pady=10)

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

        self.quantidade_saida_label = tk.Label(self.aba_saida, text='Quantidade:')
        self.quantidade_saida_label.grid(row=2, column=0, padx=10, pady=10)
        self.quantidade_saida_entry = tk.Entry(self.aba_saida)
        self.quantidade_saida_entry.grid(row=2, column=1, padx=10, pady=10)

        self.motivo_saida_label = tk.Label(self.aba_saida, text='Motivo:')
        self.motivo_saida_label.grid(row=3, column=0, padx=10, pady=10)
        self.motivo_saida_combobox = ttk.Combobox(self.aba_saida, values=['Venda', 'Vencido','Perda/Avaria'], state='readonly')
        self.motivo_saida_combobox.grid(row=3, column=1, padx=10, pady=10)

        self.adicionar_saida_btn = tk.Button(self.aba_saida, text='Adicionar Saída', command=self.adicionar_saida)
        self.adicionar_saida_btn.grid(row=4, column=0, columnspan=2, pady=10)

        # Aba Relatórios
        self.aba_relatorios = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_relatorios, text='Relatórios')

        self.relatorio_vencimento_btn = tk.Button(self.aba_relatorios, text='Relatório de Vencimento Próximo', command=gerar_relatorio_proximos_da_validade)
        self.relatorio_vencimento_btn.pack(pady=10)

        self.relatorio_alta_saida_btn = tk.Button(self.aba_relatorios, text='Relatório de Rotatividade', command=gerar_relatorio_rotatividade_produtos)
        self.relatorio_alta_saida_btn.pack(pady=10)

        self.relatorio_movimentacoes_btn = tk.Button(self.aba_relatorios, text='Relatório de Movimentações', command=gerar_relatorio_movimentacoes)
        self.relatorio_movimentacoes_btn.pack(pady=10)
        
        self.relatorio_estoque_btn = tk.Button(self.aba_relatorios, text='Relatório de Estoque', command=gerar_relatorio_estoque)
        self.relatorio_estoque_btn.pack(pady=10)

        self.relatorio_vendas_btn = tk.Button(self.aba_relatorios, text='Relatório P&L', command=gerar_relatorio_pl)
        self.relatorio_vendas_btn.pack(pady=10)

        self.atualizar_lista_produtos()

    def atualizar_preco_venda(self, event=None):
        try:
            preco = float(self.preco_entry.get())
            fator = float(self.fator_entry.get())
            preco_venda = preco * fator
            # Atualiza o campo de preço de venda
            self.preco_venda_entry.config(state="normal")
            self.preco_venda_entry.delete(0, tk.END)
            self.preco_venda_entry.insert(0, f"{preco_venda:.2f}")
            self.preco_venda_entry.config(state="readonly")
        except ValueError:
            # Se os valores não forem válidos, limpa o campo de preço de venda
            self.preco_venda_entry.config(state="normal")
            self.preco_venda_entry.delete(0, tk.END)
            self.preco_venda_entry.config(state="readonly")
        try:
            print("entrou")
            preco = float(self.preco_editar_entry.get())
            fator = float(self.fator_editar_entry.get())
            preco_venda = preco * fator
            # Atualiza o campo de preço de venda
            self.preco_editar_venda_entry.config(state="normal")
            self.preco_editar_venda_entry.delete(0, tk.END)
            self.preco_editar_venda_entry.insert(0, f"{preco_venda:.2f}")
            self.preco_editar_venda_entry.config(state="readonly")
        except ValueError:
            # Se os valores não forem válidos, limpa o campo de preço de venda
            self.preco_editar_venda_entry.config(state="normal")
            self.preco_editar_venda_entry.delete(0, tk.END)
            self.preco_editar_venda_entry.config(state="readonly")

    def adicionar_produto_base_aba(self):
        nome = self.nome_entry.get()
        sku = self.sku_entry.get()
        preco = self.preco_entry.get()
        fornecedor = self.fornecedor_entry.get()
        fator = self.fator_entry.get()
       # Adiciona o produto e obtém a mensagem de status
        resultado = adicionar_produto_base(nome, sku, preco, fornecedor,fator)
        
        # Exibe a mensagem
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
        preco = self.preco_editar_entry.get()
        fornecedor = self.fornecedor_editar_entry.get()
        fator = self.fator_editar_entry.get()

        if not sku:
            messagebox.showerror("Erro", "SKU é necessário para a edição.")
            return
        # Adiciona o produto e obtém a mensagem de status
        resultado = editar_produto_base(nome, sku, preco, fornecedor,fator)
        
        # Exibe a mensagem
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
            self.nome_editar_entry.config(state='normal')
            self.preco_editar_entry.config(state='normal')
            self.fator_editar_entry.config(state='normal')
            self.preco_editar_venda_entry.config(state='readonly')
            self.fornecedor_editar_entry.config(state='normal')
            self.nome_editar_entry.delete(0, tk.END)
            self.nome_editar_entry.insert(0, produto['nome'])
            self.preco_editar_entry.delete(0, tk.END)
            self.preco_editar_entry.insert(0, produto['preco'])
            self.fator_editar_entry.delete(0, tk.END)
            self.fator_editar_entry.insert(0, produto['fator'])
            self.fornecedor_editar_entry.delete(0, tk.END)
            self.fornecedor_editar_entry.insert(0, produto['fornecedor'])
            self.atualizar_preco_venda()
        else:
            self.nome_editar_entry.config(state='disabled')
            self.preco_editar_entry.config(state='disabled')
            self.fator_editar_entry.config(state='disabled')
            self.preco_editar_venda_entry.config(state='disabled')
            self.fornecedor_editar_entry.config(state='disabled')

    def adicionar_entrada(self):
        sku = self.sku_entrada_entry.get()
        lote = self.lote_entrada_entry.get()
        validade = self.validade_entrada_entry.get()
        quantidade = self.quantidade_entrada_entry.get()
        motivo = self.motivo_entrada_combobox.get()

        resultado = adicionar_entrada(sku, lote, validade, quantidade, motivo,0)
        
        if resultado["status"] == "erro" and "substituir?" in resultado["mensagem"]:
            validade_existente = resultado["validade_existente"]
            resposta = messagebox.askyesno(
                "Confirmação de Substituição",
                f"A data de validade é diferente da cadastrada. Deseja substituir?\nData cadastrada: {validade_existente}\nNova data: {validade}"
            )
            if resposta:
               # Subistituindo a validade
                resultado = adicionar_entrada(sku, lote, validade, quantidade, motivo, 1)
            else:
                resultado["status"] = "cancelado"
        
        if resultado["status"] == "sucesso":
            self.atualizar_lista_produtos()
        if resultado["status"] == "error":
            messagebox.showerror("Erro", resultado["mensagem"])

    def adicionar_saida(self):
        sku = self.sku_saida_entry.get()
        lote = self.lote_saida_entry.get()
        quantidade = self.quantidade_saida_entry.get()
        motivo = self.motivo_saida_combobox.get()
        resultado = adicionar_saida(sku, lote, quantidade, motivo)
        self.atualizar_lista_produtos()
        if resultado["status"] == "sucesso":
            messagebox.showinfo("Sucesso", resultado["mensagem"])
            self.atualizar_lista_produtos()
            self.limpar_campos_produtos(2)
        else:
            messagebox.showerror("Erro", resultado["mensagem"])

    def formatar_data(self, entry):
        data = entry.get()
        if len(data) == 8:
            try:
                data_formatada = datetime.strptime(data, '%d%m%Y').strftime('%d/%m/%Y')
                entry.delete(0, tk.END)
                entry.insert(0, data_formatada)
            except ValueError:
                pass  

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

    
