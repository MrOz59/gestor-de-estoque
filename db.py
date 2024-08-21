import sqlite3
from datetime import datetime, timedelta
from fpdf import FPDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

class ConexaoBD:
    def __init__(self, db_path='estoque.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        return self.conn, self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

def conectar_bd():
    """Estabelece uma conexão com o banco de dados e retorna o objeto de conexão e cursor como um gerenciador de contexto."""
    return ConexaoBD()
def criar_tabelas():
    """Cria as tabelas no banco de dados se não existirem."""
    with conectar_bd() as (conn, cursor):
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            sku TEXT UNIQUE NOT NULL,
            preco REAL NOT NULL,
            fornecedor TEXT NOT NULL
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS lotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL,
            lote TEXT NOT NULL,
            validade DATE NOT NULL,
            quantidade INTEGER NOT NULL,
            UNIQUE(sku, lote)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data DATE NOT NULL,
            tipo TEXT NOT NULL,
            sku TEXT NOT NULL,
            lote TEXT,
            quantidade INTEGER NOT NULL,
            motivo TEXT NOT NULL,
            FOREIGN KEY (sku) REFERENCES produtos(sku),
            FOREIGN KEY (lote) REFERENCES lotes(lote)
        )
        ''')
        conn.commit()

def buscar_produtos_e_lotes():
    """Busca todos os produtos e lotes do banco de dados e retorna uma lista de resultados."""
    query = '''
    SELECT p.nome, p.sku, p.fornecedor, p.preco, l.lote, l.validade, l.quantidade
    FROM produtos p
    LEFT JOIN lotes l ON p.sku = l.sku
    ORDER BY p.nome, l.lote
    '''
    with conectar_bd() as (conn, cursor):
        cursor.execute(query)
        return cursor.fetchall()

def buscar_produtos_por_criterio(valor):
    """Busca produtos no banco de dados com base em um critério e valor fornecidos."""
    query = """
    SELECT p.nome, p.sku, p.preco, p.fornecedor, l.lote, l.validade, l.quantidade
    FROM produtos p
    LEFT JOIN lotes l ON p.sku = l.sku
    WHERE p.nome LIKE ? OR p.sku LIKE ? OR l.lote LIKE ? OR p.fornecedor LIKE ?
    """
    valor = f'%{valor}%'
    with conectar_bd() as (conn, cursor):
        cursor.execute(query, (valor, valor, valor, valor))
        return cursor.fetchall()
    
def editar_produto_base(nome, sku, preco, fornecedor):
    """Atualiza os detalhes de um produto existente no banco de dados."""
    try:
        # Conectar ao banco de dados
        with conectar_bd() as (conn, cursor):
            # Verificar se o SKU existe
            cursor.execute("SELECT SKU FROM produtos WHERE SKU = ?", (sku,))
            if not cursor.fetchone():
                return {"status": "erro", "mensagem": "Produto com SKU não encontrado."}

            # Verificar se já existe um produto com o mesmo nome e SKU diferente
            cursor.execute("SELECT SKU FROM produtos WHERE nome = ? AND SKU != ?", (nome, sku))
            if cursor.fetchone():
                return {"status": "erro", "mensagem": "Produto com o mesmo nome já existe."}

            # Atualizar o produto
            cursor.execute("""
                UPDATE produtos
                SET nome = ?, preco = ?, fornecedor = ?
                WHERE SKU = ?
            """, (nome, preco, fornecedor, sku))
            
            # Confirmar as mudanças
            conn.commit()

            return {"status": "sucesso", "mensagem": "Produto atualizado com sucesso!"}
    except Exception as e:
        return {"status": "erro", "mensagem": f"Ocorreu um erro: {e}"}
def buscar_produto_db(sku):
    """Busca um produto no banco de dados pelo SKU e retorna um dicionário com os detalhes do produto."""
    # Conectar ao banco de dados
    with conectar_bd() as (conn, cursor):
        # Executar a consulta para buscar o produto pelo SKU
        cursor.execute("""
            SELECT nome, preco, fornecedor
            FROM produtos
            WHERE SKU = ?
        """, (sku,))
        
        # Obter o resultado
        resultado = cursor.fetchone()
        
        # Se o resultado existir, retornar como um dicionário
        if resultado:
            nome, preco, fornecedor = resultado
            return {
                'nome': nome,
                'preco': preco,
                'fornecedor': fornecedor
            }
        else:
            # Se o produto não for encontrado, retornar None
            return None

def adicionar_produto_base(nome, sku, preco, fornecedor):
    print ("entrou")
    """Adiciona um novo produto ao banco de dados."""
    if not nome.strip():
        return {"status": "erro", "mensagem": "O campo 'Nome' não pode estar em branco."}
    if not sku.strip():
        return {"status": "erro", "mensagem": "O campo 'SKU' não pode estar em branco."}
    if not preco.strip():
        return {"status": "erro", "mensagem": "O campo 'Preço' não pode estar em branco."}
    if not fornecedor.strip():
        return {"status": "erro", "mensagem": "O campo 'Fornecedor' não pode estar em branco."}
    with conectar_bd() as (conn, cursor):
        try:
            cursor.execute('SELECT COUNT(*) FROM produtos WHERE sku = ?', (sku,))
            sku_existe = cursor.fetchone()[0] > 0

            cursor.execute('SELECT COUNT(*) FROM produtos WHERE nome = ?', (nome,))
            nome_existe = cursor.fetchone()[0] > 0

            if sku_existe:
                return {"status": "erro", "mensagem": "Produto com SKU já existe."}
            elif nome_existe:
                return {"status": "erro", "mensagem": "Produto com o mesmo nome já existe."}

            cursor.execute('INSERT INTO produtos (nome, sku, preco, fornecedor) VALUES (?, ?, ?, ?)',
                           (nome, sku, preco, fornecedor))
            conn.commit()
            return {"status": "sucesso", "mensagem": "Produto adicionado com sucesso!"}

        except Exception as e:
            return {"status": "erro", "mensagem": f"Ocorreu um erro: {e}"}

def adicionar_entrada(sku, lote, validade, quantidade, motivo, substituir):
    """Adiciona uma entrada no banco de dados, somando quantidades se o lote já existir."""
    with conectar_bd() as (conn, cursor):
        # Verificar se o SKU existe
        cursor.execute('SELECT COUNT(*) FROM produtos WHERE sku = ?', (sku,))
        if cursor.fetchone()[0] == 0:
            return {"status": "erro", "mensagem": "SKU não existe."}

        # Verificar se o lote já existe
        cursor.execute('''
        SELECT quantidade, validade FROM lotes WHERE sku = ? AND lote = ?
        ''', (sku, lote))
        resultado = cursor.fetchone()

        if resultado:
            quantidade_existente, validade_existente = resultado
            if validade != validade_existente and substituir != 1:
                # Retorna a validade existente para a interface gráfica
                return {
                    "status": "erro",
                    "mensagem": "A data de validade é diferente da cadastrada. Deseja substituir?",
                    "validade_existente": validade_existente
                }
            # Atualizar quantidade do lote existente
            nova_quantidade = quantidade_existente + int(quantidade)
            cursor.execute('''
            UPDATE lotes
            SET quantidade = ?, validade = ?
            WHERE sku = ? AND lote = ?
            ''', (nova_quantidade, validade, sku, lote))
        else:
            # Inserir novo lote
            cursor.execute('''
            INSERT INTO lotes (sku, lote, validade, quantidade)
            VALUES (?, ?, ?, ?)
            ''', (sku, lote, validade, quantidade))

        # Registrar movimentação de entrada utilizando a mesma conexão e cursor
        registrar_movimentacao(cursor, conn, "Entrada", sku, lote, quantidade, motivo)

        conn.commit()
        return {"status": "sucesso", "mensagem": "Entrada adicionada com sucesso!"}

    
def adicionar_saida(sku, lote, quantidade, motivo):
    """Adiciona uma saída no banco de dados, verificando a quantidade disponível."""
    with conectar_bd() as (conn, cursor):
        # Verificar se o SKU existe
        cursor.execute('SELECT COUNT(*) FROM produtos WHERE sku = ?', (sku,))
        if cursor.fetchone()[0] == 0:
            return {"status": "erro", "mensagem": "SKU não existe."}

        # Verificar quantidade disponível no lote
        cursor.execute('''
        SELECT quantidade FROM lotes WHERE sku = ? AND lote = ?
        ''', (sku, lote))
        resultado = cursor.fetchone()

        if not resultado:
            return {"status": "erro", "mensagem": "Lote não encontrado."}
        
        quantidade_disponivel = resultado[0]
        if int(quantidade) > quantidade_disponivel:
            return {"status": "erro", "mensagem": "Quantidade solicitada excede a quantidade disponível."}

        # Atualizar quantidade no lote
        nova_quantidade = quantidade_disponivel - int(quantidade)
        cursor.execute('''
        UPDATE lotes
        SET quantidade = ?
        WHERE sku = ? AND lote = ?
        ''', (nova_quantidade, sku, lote))

        # Registrar movimentação de saída utilizando a mesma conexão e cursor
        registrar_movimentacao(cursor, conn, "Saída", sku, lote, quantidade, motivo)

        conn.commit()
        return {"status": "sucesso", "mensagem": "Saída adicionada com sucesso!"}


def registrar_movimentacao(cursor, conn, tipo, sku, lote, quantidade, motivo):
    """Registra uma movimentação no banco de dados."""
    data = datetime.now().strftime('%d/%m/%Y')  # Data no formato dd/mm/aaaa
    cursor.execute('''
    INSERT INTO movimentacoes (data, tipo, sku, lote, quantidade, motivo)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (data, tipo, sku, lote, quantidade, motivo))


def remover_lote(sku, lote):
    """Remove um lote do banco de dados e registra a movimentação."""
    with conectar_bd() as (conn, cursor):
        cursor.execute('DELETE FROM lotes WHERE sku = ? AND lote = ?', (sku, lote))
        conn.commit()
        registrar_movimentacao('Remoção', sku, lote, 0)

def comparar_datas(data1, data2):
    """ Compara duas datas no formato dd/mm/aaaa. Retorna 1 se data1 > data2, -1 se data1 < data2, e 0 se iguais. """
    d1 = datetime.strptime(data1, '%d/%m/%Y')
    d2 = datetime.strptime(data2, '%d/%m/%Y')
    if d1 > d2:
        return 1
    elif d1 < d2:
        return -1
    else:
        return 0

def gerar_relatorio_proximos_da_validade():
    nome_arquivo = "relatorio_proximos_da_validade.pdf"
    doc = SimpleDocTemplate(nome_arquivo, pagesize=letter)
    content = []

    with conectar_bd() as (conn, cursor):
        hoje = datetime.now()
        data_limite = hoje + timedelta(days=90)
        hoje_str = hoje.strftime('%d/%m/%Y')
        data_limite_str = data_limite.strftime('%d/%m/%Y')

        cursor.execute("""
        SELECT p.SKU, p.nome, p.preco, p.fornecedor, l.lote, l.validade, l.quantidade
        FROM produtos p
        JOIN lotes l ON p.SKU = l.SKU
        """)

        produtos = cursor.fetchall()

        produtos_relatorio = []

        for produto in produtos:
            validade_str = produto[5]
            validade = datetime.strptime(validade_str, '%d/%m/%Y')

            if comparar_datas(validade_str, hoje_str) < 0:
                produtos_relatorio.append(produto)
            elif comparar_datas(validade_str, data_limite_str) <= 0:
                produtos_relatorio.append(produto)

        cabecalhos = ['SKU', 'Nome', 'Preço', 'Fornecedor', 'Lote', 'Validade', 'Quantidade']
        dados = [cabecalhos]

        for i, produto in enumerate(produtos_relatorio):
            validade_str = produto[5]
            cor_fundo = obter_cor_fundo(validade_str, hoje_str, data_limite_str)
            dados.append(produto)

        tabela = Table(dados)
        
        estilos = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]
        
        for i, produto in enumerate(produtos_relatorio):
            validade_str = produto[5]
            cor_fundo = obter_cor_fundo(validade_str, hoje_str, data_limite_str)
            estilos.append(('BACKGROUND', (0, i + 1), (-1, i + 1), cor_fundo))
        
        tabela.setStyle(TableStyle(estilos))

        content.append(tabela)

        doc.build(content)

    print(f"Relatório gerado: {nome_arquivo}")

def formatar(data):
    """ Formata a data para o formato dd/mm/aaaa """
    if data:
        try:
            return datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m/%Y')
        except ValueError:
            return data
    return 'Nunca'

def gerar_relatorio_estoque():
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Relatório de Produtos em Estoque', 0, 1, 'C')
    pdf.set_font('Arial', '', 10)

    header = ['Nome', 'SKU', 'Quantidade']
    col_widths = [80, 40, 40]
    
    # Adicionar o cabeçalho da tabela
    pdf.set_fill_color(220, 220, 220)
    for i, col_name in enumerate(header):
        pdf.cell(col_widths[i], 10, col_name, 1, 0, 'C', fill=True)
    pdf.ln()

    with conectar_bd() as (conn, cursor):
        cursor.execute('''
        SELECT p.nome, p.sku, SUM(l.quantidade) AS quantidade_total
        FROM produtos p
        INNER JOIN lotes l ON p.sku = l.sku
        WHERE l.quantidade > 0
        GROUP BY p.sku
        HAVING quantidade_total > 0
        ''')
        
        for row in cursor.fetchall():
            nome, sku, quantidade_total = row
            pdf.cell(col_widths[0], 10, nome, 1)
            pdf.cell(col_widths[1], 10, sku, 1)
            pdf.cell(col_widths[2], 10, str(quantidade_total), 1)
            pdf.ln()
    
    pdf_file_name = f'relatorio_estoque_{datetime.now().strftime("%d%m%Y_%H%M%S")}.pdf'
    pdf.output(pdf_file_name)
    print(f"Relatório gerado: {pdf_file_name}")

def gerar_relatorio_rotatividade_produtos():
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Relatório de Rotatividade de Produtos', 0, 1, 'C')
    pdf.set_font('Arial', '', 10)

    header = ['Nome', 'SKU', 'Preço', 'Fornecedor', 'Total Saídas', 'Última Entrada', 'Última Saída', 'Rotatividade']
    col_widths = [50, 30, 20, 40, 30, 30, 30, 30]
    
    pdf.set_fill_color(220, 220, 220)
    for i, col_name in enumerate(header):
        pdf.cell(col_widths[i], 10, col_name, 1, 0, 'C', fill=True)
    pdf.ln()

    data_atual = datetime.now()
    limite_saida = (data_atual - timedelta(days=90)).strftime('%Y-%m-%d')
    limite_entrada = (data_atual - timedelta(days=30)).strftime('%Y-%m-%d')
    
    with conectar_bd() as (conn, cursor):
        # Corrigindo a consulta para agregar as saídas dos últimos 90 dias
        cursor.execute('''
        SELECT p.nome, p.sku, p.preco, p.fornecedor, 
               COALESCE(SUM(CASE WHEN m.tipo = 'Saída' AND m.motivo = 'Venda' AND m.data >= ? THEN m.quantidade ELSE 0 END), 0) AS total_saidas
        FROM produtos p
        LEFT JOIN movimentacoes m ON p.sku = m.sku AND m.tipo = 'Saída' AND m.motivo = 'Venda' AND m.data >= ?
        GROUP BY p.sku
        ''', (limite_saida, limite_saida))
        
        colors = {
            "Alta Rotatividade": (173, 216, 230),
            "Rotatividade Média": (255, 255, 204),
            "Baixa Rotatividade": (255, 228, 225)
        }

        for row in cursor.fetchall():
            nome, sku, preco, fornecedor, total_saidas = row
            total_saidas = total_saidas if total_saidas else 0

            # Ajuste para pegar a data mais próxima da entrada e saída
            with conectar_bd() as (conn, cursor):
                cursor.execute('''
                SELECT MAX(data) FROM movimentacoes 
                WHERE sku = ? AND tipo = 'Entrada'
                ''', (sku,))
                data_ultima_entrada = cursor.fetchone()[0]

                cursor.execute('''
                SELECT MAX(data) FROM movimentacoes 
                WHERE sku = ? AND tipo = 'Saída'
                ''', (sku,))
                data_ultima_saida = cursor.fetchone()[0]

            data_ultima_entrada = formatar(data_ultima_entrada)
            data_ultima_saida = formatar(data_ultima_saida)

            with conectar_bd() as (conn, cursor):
                cursor.execute('''
                SELECT SUM(l.quantidade) FROM lotes l
                WHERE l.sku = ? AND l.quantidade > 0
                ''', (sku,))
                estoque = cursor.fetchone()[0] or 0

                cursor.execute('''
                SELECT COUNT(*) FROM movimentacoes
                WHERE sku = ? AND tipo = 'Entrada' AND data >= ?
                ''', (sku, limite_entrada))
                teve_entrada_recente = cursor.fetchone()[0] > 0

            if estoque == 0 and not teve_entrada_recente:
                continue

            if total_saidas > 60:
                turnover_type = "Alta"
                color = colors["Alta Rotatividade"]
            elif 20 <= total_saidas <= 60:
                turnover_type = "Média"
                color = colors["Rotatividade Média"]
            else:
                turnover_type = "Baixa"
                color = colors["Baixa Rotatividade"]

            pdf.set_fill_color(*color)
            row_data = [nome, sku, f'{preco:.2f}', fornecedor, str(total_saidas), data_ultima_entrada, data_ultima_saida, turnover_type]
            for i, data in enumerate(row_data):
                pdf.cell(col_widths[i], 10, data, 1, 0, 'C', fill=True)
            pdf.ln()
    
    pdf.output('relatorio_rotatividade_produtos.pdf')

def gerar_relatorio_movimentacoes():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Relatório de Movimentações', 0, 1, 'C')
    pdf.set_font('Arial', '', 10)
    
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(30, 10, 'Data', 1, 0, 'C', 1)
    pdf.cell(30, 10, 'Tipo', 1, 0, 'C', 1)
    pdf.cell(30, 10, 'Motivo', 1, 0, 'C', 1)
    pdf.cell(40, 10, 'SKU', 1, 0, 'C', 1)
    pdf.cell(30, 10, 'Lote', 1, 0, 'C', 1)
    pdf.cell(30, 10, 'Quantidade', 1, 1, 'C', 1)
    
    with conectar_bd() as (conn, cursor):
        cursor.execute('''
        SELECT data, tipo, motivo, sku, lote, quantidade
        FROM movimentacoes
        ORDER BY data
        ''')
        
        color_map = {
            'Compra': (0, 255, 0),
            'Devolução': (255, 255, 0),
            'Venda': (173, 216, 230),
            'Vencido': (255, 165, 0)
        }
        
        for row in cursor.fetchall():
            motivo = row[2]
            fill_color = color_map.get(motivo, (255, 255, 255))
            pdf.set_fill_color(*fill_color)
            
            pdf.cell(30, 10, row[0], 1, 0, 'C', 1)
            pdf.cell(30, 10, row[1], 1, 0, 'C', 1)
            pdf.cell(30, 10, row[2], 1, 0, 'C', 1)
            pdf.cell(40, 10, row[3], 1, 0, 'C', 1)
            pdf.cell(30, 10, row[4], 1, 0, 'C', 1)
            pdf.cell(30, 10, str(row[5]), 1, 1, 'C', 1)
    
    pdf.output('relatorio_movimentacoes.pdf')
    
def obter_cor_fundo(validade_str, hoje_str, data_limite_str):
    """Obtém a cor de fundo para o relatório baseado na validade do produto."""
    validade = datetime.strptime(validade_str, '%d/%m/%Y')
    hoje = datetime.strptime(hoje_str, '%d/%m/%Y')
    data_limite = datetime.strptime(data_limite_str, '%d/%m/%Y')

    if validade < hoje:
        return colors.red
    elif validade <= hoje + timedelta(days=45):
        return colors.orange
    elif validade <= data_limite:
        return colors.yellow
    else:
        return colors.beige
