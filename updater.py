import requests
import zipfile
import os
import hashlib
import subprocess
import tkinter as tk
from tkinter import messagebox
import sys
import ctypes

GITHUB_REPO = "https://api.github.com/repos/MrOz59/kalymos"

def obter_ultima_versao():
    """Obtém a última versão disponível do GitHub."""
    try:
        response = requests.get(f"{GITHUB_REPO}/releases/latest")
        response.raise_for_status()
        latest_release = response.json()
        return latest_release['tag_name']
    except requests.RequestException as e:
        print(f"Erro ao verificar a última versão: {e}")
        return None

def verificar_hash(file_path, hash_esperado):
    """Verifica se o hash SHA256 do arquivo corresponde ao esperado."""
    hash_obj = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hash_obj.update(chunk)
        return hash_obj.hexdigest() == hash_esperado
    except Exception as e:
        print(f"Erro ao verificar o hash: {e}")
        return False

def baixar_e_verificar_atualizacao(download_url, hash_url):
    """Baixa o arquivo de atualização e verifica sua integridade com o hash fornecido."""
    try:
        # Baixar o arquivo de atualização
        print(f"Iniciando o download de {download_url}...")
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        # Salvar o arquivo ZIP
        with open("update.zip", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print("Arquivo update.zip baixado com sucesso.")
        
        # Baixar o arquivo de hash
        print(f"Iniciando o download do arquivo de hash de {hash_url}...")
        response = requests.get(hash_url)
        response.raise_for_status()
        hash_esperado = response.text.strip()
        
        # Verificar hash do arquivo
        if not verificar_hash("update.zip", hash_esperado):
            print("A hash do arquivo baixado não confere.")
            return False
        
        return True
    except requests.RequestException as e:
        print(f"Erro ao baixar o arquivo de atualização ou o arquivo de hash: {e}")
        return False
    except Exception as e:
        print(f"Erro ao verificar a atualização: {e}")
        return False

def criar_diretorio(diretorio):
    """Cria o diretório se ele não existir."""
    if not os.path.exists(diretorio):
        os.makedirs(diretorio)

def extrair_atualizacao(caminho_zip, diretorio_destino):
    """Extrai o conteúdo do arquivo ZIP para o diretório de destino."""
    try:
        with zipfile.ZipFile(caminho_zip, "r") as zip_ref:
            print(f"Conteúdo do ZIP: {zip_ref.namelist()}")
            zip_ref.extractall(diretorio_destino)
        print("Arquivo update.zip extraído com sucesso.")
    except zipfile.BadZipFile as e:
        print(f"Erro ao extrair o arquivo ZIP: {e}")

def executar_como_administrador_oculto(executavel, *params):
    """Executa o comando fornecido como administrador, sem mostrar a janela de terminal."""
    params_str = ' '.join([f'"{param}"' for param in params])  # Formata os parâmetros
    try:
        SW_HIDE = 0
        ctypes.windll.shell32.ShellExecuteW(None, "runas", executavel, params_str, None, SW_HIDE)
    except Exception as e:
        print(f"Erro ao executar como administrador: {e}")

def substituir_arquivos():
    """Substitui os arquivos baixados no diretório principal."""
    try:
        # Verifica e cria o diretório temporário, se necessário
        diretorio_temp = "update_temp"
        criar_diretorio(diretorio_temp)

        # Extrai o conteúdo do arquivo zip para o diretório temporário
        extrair_atualizacao("update.zip", diretorio_temp)

        # Executa o helper para substituir os arquivos com privilégios de administrador, sem exibir o terminal
        print("Executando update_helper.exe como administrador (oculto)...")
        executar_como_administrador_oculto("update_helper.exe")

    except Exception as e:
        print(f"Erro ao substituir os arquivos: {e}")

def verificar_atualizacao(versao_atual):
    """Verifica se há uma nova versão disponível e pergunta ao usuário se deseja atualizar."""
    ultima_versao = obter_ultima_versao()
    if not ultima_versao:
        print("Não foi possível obter a última versão.")
        return False

    if versao_atual < ultima_versao:
        # Inicializa o Tkinter para a caixa de diálogo
        root = tk.Tk()
        root.withdraw()  # Oculta a janela principal do Tkinter
        
        # Mostra a caixa de diálogo yes/no
        user_response = messagebox.askyesno(
            "Atualização Disponível",
            f"Uma nova versão ({ultima_versao}) está disponível. Deseja atualizar?"
        )

        if user_response:
            download_url = f"https://github.com/MrOz59/kalymos/releases/download/{ultima_versao}/update.zip"
            hash_url = f"https://github.com/MrOz59/kalymos/releases/download/{ultima_versao}/update.zip.sha256"
            
            if baixar_e_verificar_atualizacao(download_url, hash_url):
                substituir_arquivos()
                root.destroy()
                sys.exit()
            else:
                messagebox.showwarning("Erro na Atualização", "A atualização falhou. O aplicativo será encerrado.")
                root.destroy()
                sys.exit()
        else:
            root.destroy()
            return False
    else:
        print("Você já está na versão mais recente.")
        return False

