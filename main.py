import os
import sys
from interface import Aplicacao
from db import criar_tabelas
from logs import configurar_logs
from updater_manager import load_config, ensure_updater

def main():
    ini_file = 'config.ini'
    try:
        updater_version, version = load_config(ini_file)
    except FileNotFoundError as e:
        print(e)
        return

    skip_update_check = True  # Set to True to skip update check for Kalymos-Updater

    # Ensure the updater is present and up-to-date
    updater_needed = ensure_updater(updater_version, skip_update_check)

    if updater_needed:
        # If an update was needed, exit the current application
        print("Updater needed. Please restart the application after the updater has run.")
        sys.exit(0)  # Exit the application to allow the updater to run

    # Configurar logs
    logger = configurar_logs()
    logger.info("Iniciando a aplicação...")
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
