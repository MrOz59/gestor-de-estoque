from interface import Aplicacao
from db import criar_tabelas
from logs import configurar_logs
import updater

def main():
    # Versão atual do aplicativo
    versao_atual = "v1.3.0"  # Substitua pela versão real do seu aplicativo

    # Verificar se há uma atualização disponível
    if updater.verificar_atualizacao(versao_atual):
        # Se houver atualização e for aplicada, o aplicativo será reiniciado
        return

    # Configurar logs
    logger = configurar_logs()
    logger.info("Iniciando a aplicação...")

    try:
        criar_tabelas()
        logger.info("Tentando iniciar a interface gráfica.")
        app = Aplicacao()
        app.mainloop()
        logger.info("App encerrando.")
    except Exception as e:
        logger.exception("Erro ao iniciar a aplicação: ")
        raise e
    
if __name__ == "__main__":
    main()
