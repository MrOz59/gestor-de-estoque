from interface import Aplicacao
from db import criar_tabelas
from logs import configurar_logs

def main():
    # Configurar logs
    logger = configurar_logs()
    logger.info("Iniciando a aplicação...")

    try:
        logger.info("Criando tabelas caso não existam")
        criar_tabelas()  # Configuração inicial do banco de dados
        # Cria e inicia a aplicação
        logger.info("Tentando iniciar a interface gráfica.")
        app = Aplicacao()
        app.mainloop()
        logger.info("Interface grafica iniciada.")
    except Exception as e:
        logger.exception("Erro ao iniciar a aplicação: ")
        raise e
    
if __name__ == "__main__":
    main()
