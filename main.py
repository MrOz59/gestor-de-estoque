from interface import Aplicacao
from db import criar_tabelas
from logs import configurar_logs
import updater

def main():
    versao_atual = "v1.4.2"

    if updater.verificar_atualizacao(versao_atual):
        
        return

    # Configurar logs
    logger = configurar_logs()
    logger.info("Iniciando a aplicação...")

    try:
        criar_tabelas()
        logger.info("Tentando iniciar a interface gráfica.")
        app = Aplicacao(versao_atual)
        app.mainloop()
        logger.info("App encerrando.")
    except Exception as e:
        logger.exception("Erro ao iniciar a aplicação: ")
        raise e
    
if __name__ == "__main__":
    main()
