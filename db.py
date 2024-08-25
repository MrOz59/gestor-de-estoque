import sqlite3
from datetime import datetime, timedelta
from fpdf import FPDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
import os
from logs import configurar_logs

logger = configurar_logs()

class ConexaoBD:
    def __init__(self, db_path="Kalymos_estoque.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def __enter__(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return self.conn, self.cursor
        except Exception as e:
            logger.error("Erro ao tentar se conectar ao banco de dados: ")
            raise e

    def __exit__(self, exc_type, exc_val, exc_tb):
        
        if self.conn:
            self.conn.close()
            logger.info("Conexão com o banco de dados encerrada.")

def conectar_bd():
    logger.info("Conectando ao banco de dados.")
    return ConexaoBD()

def criar_tabelas():
    logger.info("Criando tabelas no banco de dados.")
    with conectar_bd() as (conn, cursor):
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            sku TEXT UNIQUE NOT NULL,
            preco REAL NOT NULL,
            fator FLOAT NOT NULL,
            fornecedor TEXT NOT NULL
        )
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS lotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL,
            lote TEXT NOT NULL,
            validade DATE NOT NULL,
            quantidade INTEGER NOT NULL,
            UNIQUE(sku, lote)
        )
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data DATE NOT NULL,
            tipo TEXT NOT NULL,
            sku TEXT NOT NULL,
            lote TEXT,
            quantidade INTEGER NOT NULL,
            valor FLOAT NOT NULL,
            motivo TEXT NOT NULL,
            FOREIGN KEY (sku) REFERENCES produtos(sku),
            FOREIGN KEY (lote) REFERENCES lotes(lote)
        )
        """
        )
        conn.commit()
        logger.info("Tabelas criadas com sucesso.")

def buscar_produtos_e_lotes():
    logger.info("Buscando todos os produtos e lotes do banco de dados.")
    query = """
    SELECT p.nome, p.sku, p.fornecedor, p.preco, p.fator, l.lote, l.validade, l.quantidade
    FROM produtos p
    LEFT JOIN lotes l ON p.sku = l.sku
    ORDER BY p.nome, l.lote
    """
    with conectar_bd() as (conn, cursor):
        cursor.execute(query)
        resultados = cursor.fetchall()

    # Adiciona o cálculo do preço de venda a cada produto/lote
    produtos_com_preco_venda = []
    for resultado in resultados:
        nome, sku, fornecedor, preco, fator, lote, validade, quantidade = resultado
        preco_venda = preco * fator  # Calcula o preço de venda
        preco_venda = round(preco_venda, 2)
        produtos_com_preco_venda.append(
            (nome, sku, fornecedor, preco, preco_venda, lote, validade, quantidade)
        )

    logger.info(f"Produtos e lotes encontrados: {len(produtos_com_preco_venda)} registros.")
    return produtos_com_preco_venda

def buscar_produtos_por_criterio(valor):

    logger.info(f"Buscando produtos por critério: {valor}.")
    # Consulta SQL para buscar produtos com base no critério
    query = """
    SELECT p.nome, p.sku, p.preco, p.fornecedor, l.lote, l.validade, l.quantidade
    FROM produtos p
    LEFT JOIN lotes l ON p.sku = l.sku
    WHERE p.nome LIKE ? OR p.sku LIKE ? OR l.lote LIKE ? OR p.fornecedor LIKE ?
    """
    
    valor_param = f"%{valor}%"
    
    # Executa a consulta e captura os resultados
    with conectar_bd() as (conn, cursor):
        cursor.execute(query, (valor_param, valor_param, valor_param, valor_param))
        resultados = cursor.fetchall()
    
    logger.info(f"Produtos encontrados por critério: {len(resultados)} registros.")
    return resultados

def editar_produto_base(nome, sku, preco, fornecedor,fator):
    logger.info(f"Editando produto: {sku}.")
    try:
        with conectar_bd() as (conn, cursor):
            # Verificar se o SKU existe
            cursor.execute("SELECT SKU FROM produtos WHERE SKU = ?", (sku,))
            if not cursor.fetchone():
                logger.error(f"Produto com SKU {sku} não encontrado.")
                return {"status": "erro", "mensagem": "Produto com SKU não encontrado."}

            # Verificar se já existe um produto com o mesmo nome e SKU diferente
            cursor.execute(
                "SELECT SKU FROM produtos WHERE nome = ? AND SKU != ?", (nome, sku)
            )
            if cursor.fetchone():
                logger.error(f"Produto com o mesmo nome já existe: {nome}.")
                return {
                    "status": "erro",
                    "mensagem": "Produto com o mesmo nome já existe.",
                }

            # Atualizar o produto
            cursor.execute(
                """
                UPDATE produtos
                SET nome = ?, preco = ?, fornecedor = ?, fator = ?
                WHERE SKU = ?
            """,
                (nome, preco, fornecedor,fator, sku),
            )

            # Confirmar as mudanças
            conn.commit()
            logger.info(f"Produto {sku} atualizado com sucesso.")

            return {"status": "sucesso", "mensagem": "Produto atualizado com sucesso!"}
    except Exception as e:
        logger.error(f"Erro ao atualizar produto {sku}: {e}")
        return {"status": "erro", "mensagem": f"Ocorreu um erro: {e}"}

def buscar_produto_db(sku):
    # Conectar ao banco de dados
    logger.info(f"Buscando produto pelo SKU: {sku}.")
    with conectar_bd() as (conn, cursor):
        # Executar a consulta para buscar o produto pelo SKU
        cursor.execute(
            """
            SELECT nome, preco, fornecedor,fator
            FROM produtos
            WHERE SKU = ?
        """,
            (sku,),
        )

        # Obter o resultado
        resultado = cursor.fetchone()

        # Se o resultado existir, retornar como um dicionário
        if resultado:
            nome, preco, fornecedor, fator = resultado
            logger.info(f"Produto encontrado: {sku}.")
            return {"nome": nome, "preco": preco, "fornecedor": fornecedor,"fator": fator}
        else:
            logger.warning(f"Produto não encontrado: {sku}.")
            # Se o produto não for encontrado, retornar None
            return None

def adicionar_produto_base(nome, sku, preco, fornecedor,fator):
    logger.info(f"Adicionando produto: {sku}.")
    if not nome.strip():
        logger.error("O campo 'Nome' não pode estar em branco.")
        return {
            "status": "erro",
            "mensagem": "O campo 'Nome' não pode estar em branco.",
        }
    if not sku.strip():
        logger.error("O campo 'SKU' não pode estar em branco.")
        return {"status": "erro", "mensagem": "O campo 'SKU' não pode estar em branco."}
    if not preco.strip():
        logger.error("O campo 'Preço' não pode estar em branco.")
        return {
            "status": "erro",
            "mensagem": "O campo 'Preço' não pode estar em branco.",
        }
    if not fator.strip():
        logger.error("O campo 'Fator' não pode estar em branco.")
        return {
            "status": "erro",
            "mensagem": "O campo 'Fator' não pode estar em branco.",
        }
    if not fornecedor.strip():
        logger.error("O campo 'Fornecedor' não pode estar em branco.")
        return {
            "status": "erro",
            "mensagem": "O campo 'Fornecedor' não pode estar em branco.",
        }
    with conectar_bd() as (conn, cursor):
        try:
            cursor.execute("SELECT COUNT(*) FROM produtos WHERE sku = ?", (sku,))
            sku_existe = cursor.fetchone()[0] > 0

            cursor.execute("SELECT COUNT(*) FROM produtos WHERE nome = ?", (nome,))
            nome_existe = cursor.fetchone()[0] > 0

            if sku_existe:
                logger.error(f"Produto com SKU {sku} já existe.")
                return {"status": "erro", "mensagem": "Produto com SKU já existe."}
            elif nome_existe:
                logger.error(f"Produto com o mesmo nome já existe: {nome}.")
                return {
                    "status": "erro",
                    "mensagem": "Produto com o mesmo nome já existe.",
                }

            cursor.execute(
                "INSERT INTO produtos (nome, sku, preco, fornecedor,fator) VALUES (?, ?, ?, ?,?)",
                (nome, sku, preco, fornecedor,fator),
            )
            conn.commit()
            logger.info(f"Produto {sku} adicionado com sucesso.")
            return {"status": "sucesso", "mensagem": "Produto adicionado com sucesso!"}

        except Exception as e:
            logger.error(f"Erro ao adicionar produto {sku}: {e}")
            return {"status": "erro", "mensagem": f"Ocorreu um erro: {e}"}

def adicionar_entrada(sku, lote, validade, quantidade, motivo, substituir):
    logger.info(f"Adicionando entrada: SKU {sku}, Lote {lote}.")
    with conectar_bd() as (conn, cursor):
        # Verificar se o SKU existe
        cursor.execute("SELECT COUNT(*) FROM produtos WHERE sku = ?", (sku,))
        if cursor.fetchone()[0] == 0:
            logger.error(f"SKU não existe: {sku}.")
            return {"status": "erro", "mensagem": "SKU não existe."}

        # Buscar o preço do produto pelo SKU
        cursor.execute("SELECT preco FROM produtos WHERE sku = ?", (sku,))
        preco = cursor.fetchone()
        if preco is None:
            logger.error(f"Preço não encontrado para SKU {sku}.")
            return {"status": "erro", "mensagem": "Preço não encontrado para o SKU."}
        valor = preco[0]

        # Verificar se o lote já existe
        cursor.execute(
            """
        SELECT quantidade, validade FROM lotes WHERE sku = ? AND lote = ?
        """,
            (sku, lote),
        )
        resultado = cursor.fetchone()

        if resultado:
            quantidade_existente, validade_existente = resultado
            if validade != validade_existente and substituir != 1:
                # Retorna a validade existente para a interface gráfica
                logger.warning(
                    f"A data de validade {validade} é diferente da cadastrada {validade_existente}. Solicitando confirmação"
                )
                return {
                    "status": "erro",
                    "mensagem": "A data de validade é diferente da cadastrada. Deseja substituir?",
                    "validade_existente": validade_existente,
                }
            # Atualizar quantidade do lote existente
            nova_quantidade = quantidade_existente + int(quantidade)
            cursor.execute(
                """
            UPDATE lotes
            SET quantidade = ?, validade = ?
            WHERE sku = ? AND lote = ?
            """,
                (nova_quantidade, validade, sku, lote),
            )
        else:
            # Inserir novo lote
            cursor.execute(
                """
            INSERT INTO lotes (sku, lote, validade, quantidade)
            VALUES (?, ?, ?, ?)
            """,
                (sku, lote, validade, quantidade),
            )

        # Registrar movimentação de entrada utilizando a mesma conexão e cursor
        registrar_movimentacao(cursor, "Entrada", sku, lote, quantidade, motivo, valor)
        logger.info(f"Entrada atualizada: SKU {sku}, Lote {lote}.")
        conn.commit()
        return {"status": "sucesso", "mensagem": "Entrada adicionada com sucesso!"}

def adicionar_saida(sku, lote, quantidade, motivo):
    logger.info(f"Adicionando saída: SKU {sku}, Lote {lote}.")
    with conectar_bd() as (conn, cursor):
        # Verificar se o SKU existe
        cursor.execute("SELECT COUNT(*) FROM produtos WHERE sku = ?", (sku,))
        if cursor.fetchone()[0] == 0:
            logger.error(f"SKU: {sku} não foi encontrado.")
            return {"status": "erro", "mensagem": "SKU não existe."}

        # Verificar quantidade disponível no lote
        cursor.execute(
            """
            SELECT quantidade FROM lotes WHERE sku = ? AND lote = ?
            """,
            (sku, lote),
        )
        resultado = cursor.fetchone()

        if not resultado:
            logger.error(f"Lote: {lote} não foi encontrado.")
            return {"status": "erro", "mensagem": "Lote não encontrado."}

        quantidade_disponivel = resultado[0]
        if int(quantidade) > quantidade_disponivel:
            logger.error(
                f"Quantidade solicitada {quantidade} excede a quantidade existente {quantidade_disponivel}."
            )
            return {
                "status": "erro",
                "mensagem": "Quantidade solicitada excede a quantidade disponível.",
            }

        # Atualizar quantidade no lote
        nova_quantidade = quantidade_disponivel - int(quantidade)
        cursor.execute(
            """
            UPDATE lotes
            SET quantidade = ?
            WHERE sku = ? AND lote = ?
            """,
            (nova_quantidade, sku, lote),
        )

        # Registrar a movimentação de saída
        cursor.execute("SELECT preco FROM produtos WHERE sku = ?", (sku,))
        preco = cursor.fetchone()[0]
        registrar_movimentacao(cursor, "Saída", sku, lote, quantidade, motivo, preco)
        logger.info(f"Saída registrada: SKU {sku}, Lote {lote}.")

        # Verificar se a nova quantidade é zero e remover o lote se necessário
        if nova_quantidade == 0:
            logger.info(f"Quantidade do lote {lote} para SKU {sku} é zero. Removendo lote.")
            remover_lote(sku, lote, cursor)
        
        conn.commit()
        return {"status": "sucesso", "mensagem": "Saída adicionada com sucesso!"}

def registrar_movimentacao(cursor, tipo, sku, lote, quantidade, motivo,valor):
    logger.info(
        f"Registrandomovimentção de estoque: Tipo:{tipo}, SKU:{sku}, Lote:{lote}, Quantidade:{quantidade}, Motivo:{motivo}"
    )
    data = datetime.now().strftime("%d/%m/%Y")
    cursor.execute(
        """
    INSERT INTO movimentacoes (data, tipo, sku, lote, quantidade, motivo, valor)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (data, tipo, sku, lote, quantidade, motivo, valor),
    )

def remover_lote(sku, lote,cursor):
        logger.info(f"Removendo lote: SKU {sku}, Lote {lote}.")
        cursor.execute(
            """
            DELETE FROM lotes WHERE sku = ? AND lote = ?
            """,
            (sku, lote),
        )
        logger.info(f"Lote removido: SKU {sku}, Lote {lote}.")

def comparar_datas(data1, data2):
    d1 = datetime.strptime(data1, "%d/%m/%Y")
    d2 = datetime.strptime(data2, "%d/%m/%Y")
    if d1 > d2:
        return 1
    elif d1 < d2:
        return -1
    else:
        return 0

def gerar_relatorio_proximos_da_validade():
    logger.info(f"Gerando relatorio de validade")
    nome_arquivo = "Kalymos_relatorio_proximos_da_validade.pdf"
    doc = SimpleDocTemplate(nome_arquivo, pagesize=letter)
    content = []

    with conectar_bd() as (conn, cursor):
        hoje = datetime.now()
        data_limite = hoje + timedelta(days=90)
        hoje_str = hoje.strftime("%d/%m/%Y")
        data_limite_str = data_limite.strftime("%d/%m/%Y")

        cursor.execute(
            """
        SELECT p.SKU, p.nome, p.preco, p.fornecedor, l.lote, l.validade, l.quantidade
        FROM produtos p
        JOIN lotes l ON p.SKU = l.SKU
        """
        )

        produtos = cursor.fetchall()

        produtos_relatorio = []

        for produto in produtos:
            validade_str = produto[5]

            if comparar_datas(validade_str, hoje_str) < 0:
                produtos_relatorio.append(produto)
            elif comparar_datas(validade_str, data_limite_str) <= 0:
                produtos_relatorio.append(produto)

        cabecalhos = [
            "SKU",
            "Nome",
            "Preço",
            "Fornecedor",
            "Lote",
            "Validade",
            "Quantidade",
        ]
        dados = [cabecalhos]

        for i, produto in enumerate(produtos_relatorio):
            validade_str = produto[5]
            cor_fundo = obter_cor_fundo(validade_str, hoje_str, data_limite_str)
            dados.append(produto)

        tabela = Table(dados)

        estilos = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]

        for i, produto in enumerate(produtos_relatorio):
            validade_str = produto[5]
            cor_fundo = obter_cor_fundo(validade_str, hoje_str, data_limite_str)
            estilos.append(("BACKGROUND", (0, i + 1), (-1, i + 1), cor_fundo))

        tabela.setStyle(TableStyle(estilos))

        content.append(tabela)

        doc.build(content)

    print(f"Relatório gerado: {nome_arquivo}")
    os.startfile({nome_arquivo})

def formatar(data):
    if data:
        try:
            return datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            return data
    return "Nunca"

def gerar_relatorio_estoque():
    logger.info(f"Gerando relatorio de estoque")
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Relatório de Produtos em Estoque", 0, 1, "C")
    pdf.set_font("Arial", "", 10)

    header = ["Nome", "SKU", "Quantidade"]
    col_widths = [80, 40, 40]

    # Adicionar o cabeçalho da tabela
    pdf.set_fill_color(220, 220, 220)
    for i, col_name in enumerate(header):
        pdf.cell(col_widths[i], 10, col_name, 1, 0, "C", fill=True)
    pdf.ln()

    with conectar_bd() as (conn, cursor):
        cursor.execute(
            """
        SELECT p.nome, p.sku, SUM(l.quantidade) AS quantidade_total
        FROM produtos p
        INNER JOIN lotes l ON p.sku = l.sku
        WHERE l.quantidade > 0
        GROUP BY p.sku
        HAVING quantidade_total > 0
        """
        )

        for row in cursor.fetchall():
            nome, sku, quantidade_total = row
            pdf.cell(col_widths[0], 10, nome, 1)
            pdf.cell(col_widths[1], 10, sku, 1)
            pdf.cell(col_widths[2], 10, str(quantidade_total), 1)
            pdf.ln()

    pdf_file_name = f'Kalymos_relatorio_estoque_{datetime.now().strftime("%d%m%Y_%H%M%S")}.pdf'
    pdf.output(pdf_file_name)
    print(f"Relatório gerado: {pdf_file_name}")
    os.startfile({pdf_file_name})

def gerar_relatorio_rotatividade_produtos():
    logger.info(f"Gerando relatorio de rotatividade")
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Relatório de Rotatividade de Produtos", 0, 1, "C")
    pdf.set_font("Arial", "", 10)

    header = [
        "Nome",
        "SKU",
        "Preço",
        "Fornecedor",
        "Total Saídas",
        "Última Entrada",
        "Última Saída",
        "Rotatividade",
    ]
    col_widths = [50, 30, 20, 40, 30, 30, 30, 30]

    pdf.set_fill_color(220, 220, 220)
    for i, col_name in enumerate(header):
        pdf.cell(col_widths[i], 10, col_name, 1, 0, "C", fill=True)
    pdf.ln()

    data_atual = datetime.now()
    limite_saida = (data_atual - timedelta(days=90)).strftime("%Y-%m-%d")
    limite_entrada = (data_atual - timedelta(days=30)).strftime("%Y-%m-%d")

    with conectar_bd() as (conn, cursor):
        cursor.execute(
            """
        SELECT p.nome, p.sku, p.preco, p.fornecedor, 
               COALESCE(SUM(CASE WHEN m.tipo = 'Saída' AND m.motivo = 'Venda' AND m.data >= ? THEN m.quantidade ELSE 0 END), 0) AS total_saidas
        FROM produtos p
        LEFT JOIN movimentacoes m ON p.sku = m.sku AND m.tipo = 'Saída' AND m.motivo = 'Venda' AND m.data >= ?
        GROUP BY p.sku
        """,
            (limite_saida, limite_saida),
        )

        colors = {
            "Alta Rotatividade": (173, 216, 230),
            "Rotatividade Média": (255, 255, 204),
            "Baixa Rotatividade": (255, 228, 225),
        }

        for row in cursor.fetchall():
            nome, sku, preco, fornecedor, total_saidas = row
            total_saidas = total_saidas if total_saidas else 0

            with conectar_bd() as (conn, cursor):
                cursor.execute(
                    """
                SELECT MAX(data) FROM movimentacoes 
                WHERE sku = ? AND tipo = 'Entrada'
                """,
                    (sku,),
                )
                data_ultima_entrada = cursor.fetchone()[0]

                cursor.execute(
                    """
                SELECT MAX(data) FROM movimentacoes 
                WHERE sku = ? AND tipo = 'Saída'
                """,
                    (sku,),
                )
                data_ultima_saida = cursor.fetchone()[0]

            data_ultima_entrada = formatar(data_ultima_entrada)
            data_ultima_saida = formatar(data_ultima_saida)

            with conectar_bd() as (conn, cursor):
                cursor.execute(
                    """
                SELECT SUM(l.quantidade) FROM lotes l
                WHERE l.sku = ? AND l.quantidade > 0
                """,
                    (sku,),
                )
                estoque = cursor.fetchone()[0] or 0

                cursor.execute(
                    """
                SELECT COUNT(*) FROM movimentacoes
                WHERE sku = ? AND tipo = 'Entrada' AND data >= ?
                """,
                    (sku, limite_entrada),
                )
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
            row_data = [
                nome,
                sku,
                f"{preco:.2f}",
                fornecedor,
                str(total_saidas),
                data_ultima_entrada,
                data_ultima_saida,
                turnover_type,
            ]
            for i, data in enumerate(row_data):
                pdf.cell(col_widths[i], 10, data, 1, 0, "C", fill=True)
            pdf.ln()

    pdf.output("Kalymos_relatorio_rotatividade_produtos.pdf")
    os.startfile('Kalymos_relatorio_rotatividade_produtos.pdf')

def gerar_relatorio_movimentacoes():
    logger.info(f"Gerando relatorio de movimentações de estoque")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Relatório de Movimentações", 0, 1, "C")
    pdf.set_font("Arial", "", 10)

    pdf.set_fill_color(200, 220, 255)
    pdf.cell(30, 10, "Data", 1, 0, "C", 1)
    pdf.cell(30, 10, "Tipo", 1, 0, "C", 1)
    pdf.cell(30, 10, "Motivo", 1, 0, "C", 1)
    pdf.cell(40, 10, "SKU", 1, 0, "C", 1)
    pdf.cell(30, 10, "Lote", 1, 0, "C", 1)
    pdf.cell(30, 10, "Quantidade", 1, 1, "C", 1)

    with conectar_bd() as (conn, cursor):
        cursor.execute(
            """
        SELECT data, tipo, motivo, sku, lote, quantidade
        FROM movimentacoes
        ORDER BY data
        """
        )

        color_map = {
            "Compra": (0, 255, 0),
            "Devolução": (255, 255, 0),
            "Venda": (173, 216, 230),
            "Vencido": (255, 165, 0),
            "Perda/Avaria":(255, 165, 0),
            "Balanço":(0, 235, 35)
            
        }

        for row in cursor.fetchall():
            motivo = row[2]
            fill_color = color_map.get(motivo, (255, 255, 255))
            pdf.set_fill_color(*fill_color)

            pdf.cell(30, 10, row[0], 1, 0, "C", 1)
            pdf.cell(30, 10, row[1], 1, 0, "C", 1)
            pdf.cell(30, 10, row[2], 1, 0, "C", 1)
            pdf.cell(40, 10, row[3], 1, 0, "C", 1)
            pdf.cell(30, 10, row[4], 1, 0, "C", 1)
            pdf.cell(30, 10, str(row[5]), 1, 1, "C", 1)

    pdf.output("Kalymos_relatorio_movimentacoes.pdf")
    os.startfile('Kalymos_relatorio_movimentacoes.pdf')

def obter_cor_fundo(validade_str, hoje_str, data_limite_str):
    validade = datetime.strptime(validade_str, "%d/%m/%Y")
    hoje = datetime.strptime(hoje_str, "%d/%m/%Y")
    data_limite = datetime.strptime(data_limite_str, "%d/%m/%Y")

    if validade < hoje:
        return colors.red
    elif validade <= hoje + timedelta(days=45):
        return colors.orange
    elif validade <= data_limite:
        return colors.yellow
    else:
        return colors.beige
    
def obter_movimentacoes_ultimos_30_dias():
    query = """
    SELECT 
        m.motivo, 
        m.tipo, 
        p.sku,
        p.preco, 
        m.quantidade,
        (p.preco * m.quantidade) as total_valor_perda,
        (p.preco * p.fator * m.quantidade) as total_valor_venda,
        (p.preco * p.fator) as valor_venda
    FROM movimentacoes m
    JOIN produtos p ON m.sku = p.sku
    WHERE m.data >= ?
    ORDER BY m.tipo, m.motivo
    """
    
    data_limite = datetime.now() - timedelta(days=30)
    
    with conectar_bd() as (conn, cursor):
        cursor.execute(query, (data_limite,))
        resultados = cursor.fetchall()
    
    return resultados

def gerar_relatorio_pl():
    movimentacoes = obter_movimentacoes_ultimos_30_dias()
    logger.info("Gerando relatorio P&L")

    # Configuração do PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(200, 10, 'Relatório P&L (Últimos 30 dias)', ln=True, align='C')
    
    pdf.set_font('Arial', '', 12)
    pdf.ln(10)  # Espaço entre título e tabela

    # Cabeçalho da tabela
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(40, 10, 'Motivo', border=1)
    pdf.cell(30, 10, 'Tipo', border=1)
    pdf.cell(30, 10, 'SKU', border=1)
    pdf.cell(30, 10, 'Preço Unitário', border=1)
    pdf.cell(30, 10, 'Quantidade', border=1)
    pdf.cell(40, 10, 'Valor Total', border=1, ln=1)
    
    total_ganhos = 0
    total_perdas = 0

    pdf.set_font('Arial', '', 12)
    for movimento in movimentacoes:
        motivo, tipo, sku, preco_unitario, quantidade, total_valor_perda, total_valor_venda, valor_venda = movimento

        if motivo == "Venda" or "Devolução":
            preco_utilizado = valor_venda
            valor_total = total_valor_venda
            total_ganhos += valor_total
            if motivo =="Venda":
                pdf.set_fill_color(200, 255, 200)
            else:
                pdf.set_fill_color(255, 200, 200)  
        elif motivo == "Balanço":
            preco_utilizado = preco_unitario
            valor_total = total_valor_venda
            pdf.set_fill_color(200, 255, 200)
            total_ganhos += valor_total
        else:
            preco_utilizado = preco_unitario  
            valor_total = total_valor_perda
            pdf.set_fill_color(255, 200, 200)  
            total_perdas += valor_total

        pdf.cell(40, 10, motivo, border=1, ln=0, fill=True)
        pdf.cell(30, 10, tipo, border=1, ln=0, fill=True)
        pdf.cell(30, 10, sku, border=1, ln=0, fill=True)
        pdf.cell(30, 10, f'R$ {preco_utilizado:.2f}', border=1, ln=0, fill=True) 
        pdf.cell(30, 10, str(quantidade), border=1, ln=0, fill=True)
        pdf.cell(40, 10, f'R$ {valor_total:.2f}', border=1, ln=1, fill=True)

    # Totalizadores
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(80, 10, 'Total Ganhos:', border=1, ln=0)
    pdf.cell(40, 10, f'R$ {total_ganhos:.2f}', border=1, ln=1)

    pdf.cell(80, 10, 'Total Perdas:', border=1, ln=0)
    pdf.cell(40, 10, f'R$ {total_perdas:.2f}', border=1, ln=1)

    diferenca = total_ganhos - total_perdas
    if diferenca >= 0:
        pdf.set_fill_color(200, 255, 200)  
    else:
        pdf.set_fill_color(255, 200, 200)  

    pdf.cell(80, 10, 'Diferença Total:', border=1, ln=0, fill=True)
    pdf.cell(40, 10, f'R$ {diferenca:.2f}', border=1, ln=1, fill=True)

    # Salvar o PDF
    pdf.output('kalymos_relatorio_pl.pdf')
    os.startfile('kalymos_relatorio_pl.pdf')
    print("Relatório P&L gerado com sucesso!")