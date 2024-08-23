# Kalymos

Kalymos é um aplicativo para gerenciamento de estoque com foco em pequenas empresas e lojas.

## Descrição

Este repositório contém o código-fonte para um sistema de controle de estoque desenvolvido para pequenas lojas que necessitam de um controle de validade e lotes simples. O aplicativo foi projetado para ajudar a gerenciar o estoque de produtos, controlar entradas e saídas e gerar relatórios para melhorar a eficiência e organização do negócio.

## Funcionalidades

- **Gerenciamento de Produtos**: Adicionar, editar e remover produtos do estoque.
- **Controle de Entrada e Saída**: Registrar entradas e saídas de produtos.
- **Relatórios**: Gerar relatórios de estoque e movimentação de produtos.
- **Busca**: Buscar produtos por nome, SKU, lote ou fornecedor.

## Principais Tecnologias Utilizadas

- **Python**: Linguagem de programação usada para o desenvolvimento do aplicativo.
- **SQLite**: Sistema de banco de dados usado para armazenar informações de produtos e movimentações.
- **Tkinter**: Biblioteca para criação da interface gráfica do usuário.

## Estrutura do Projeto

- **`main.py`**: Arquivo principal que inicia o aplicativo e gerencia a interface gráfica.
- **`interface.py`**: Contém a definição da interface gráfica e gerenciamento das abas.
- **`db.py`**: Gerencia as operações do banco de dados, incluindo consultas e atualizações.
- **`logs.py`**: Responsavel por gerar um log para facilicar a depuração em caso erros ou falhas.

## Atualizações e Scripts
- **`updater.py`**: Integrado no arquivo principal(`Kalymos.exe`), este modulo é responsavel por buscar e baixar novas atualizações.
- **`update_helper.py`**: Este é um modulo externo, distribuido como um executável para auxiliar na instalação das atualizações.
- **`gerar_update.py`**: Script auxiliar que gera uma distro do app([`PyInstaller`](https://github.com/pyinstaller)) faz a compactação, gera a hash SHA256 para que uma atualização possa ser publicada, não disponivel no produto final.

## Licença

Este projeto está licenciado sob a Licença Personalizada de Uso e Distribuição do Software. A licença permite o uso comercial do software, mas proíbe a venda, redistribuição, sublicenciamento ou transferência do software sem permissão expressa. O código-fonte e partes dele não podem ser utilizados sem autorização. Veja o arquivo [LICENSE](LICENSE) para detalhes completos.


## Contato

Para mais informações, entre em contato com:
- **Oswaldo de Souza** - [oswaldo_de_souza@hotmail.com](mailto:oswaldo_de_souza@hotmail.com)

