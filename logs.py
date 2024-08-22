import logging
import os
from logging.handlers import RotatingFileHandler

def configurar_logs():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)  # Cria o diretório de logs se não existir

    log_file = os.path.join(log_dir, "app.log")

    # Configuração do logger principal
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Configurar o nível de log global

    # Formato do log
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Handler para o console (opcional)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para arquivo com rotação
    file_handler = RotatingFileHandler(log_file, maxBytes=10**6, backupCount=5)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# Chame esta função no início do seu aplicativo para configurar o logging
