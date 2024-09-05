import os
import argparse
from interface import Aplicacao
from db import criar_tabelas
from logs import configurar_logs
from updater_manager import ensure_updater

def main():
     # Configurar logs
    logger = configurar_logs()
    logger.info("Iniciando a aplicação...")
    version = 'v1.5.5'
    os.environ['Version'] = version
    os.environ['SkipUpdate'] = 'False'
    os.environ['Updater'] = 'v1.1.1'
    os.environ['Owner'] = 'MrOz59'
    os.environ['Repo'] = 'kalymos'
    os.environ['MainExecutable'] = 'Kalymos.exe'
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Kalymos Application')
    parser.add_argument('--updated', action='store_true', help='Indicates that the application has been updated.')
    args = parser.parse_args()
    
    if args.updated:
        logger.info("Argumento encontrado")
        # Ignora a verificação de atualização se --updated for encontrado
    else:
        logger.info("Argumento não encontrado")
        ensure_updater()
    
    try:
        criar_tabelas()
        logger.info("Tentando iniciar a interface gráfica.")
        app = Aplicacao(version)
        app.mainloop()
        logger.info("App encerrando.")
    except Exception as e:
        logger.exception("Erro ao iniciar a aplicação: ")
        raise e

if __name__ == "__main__":
    main()
