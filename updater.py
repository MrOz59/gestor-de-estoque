import requests
import zipfile
import os
import hashlib
import tkinter as tk
from tkinter import messagebox
import sys
import ctypes

GITHUB_REPO = "https://api.github.com/repos/MrOz59/kalymos"

def obter_ultima_versao():
    try:
        response = requests.get(f"{GITHUB_REPO}/releases/latest")
        response.raise_for_status()
        latest_release = response.json()
        return latest_release
    except requests.RequestException as e:
        print(f"Erro ao verificar a última versão: {e}")
        return None

def verificar_hash(file_path, hash_esperado):
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
    try:
        print(f"Iniciando o download de {download_url}...")
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        with open("update.zip", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print("Arquivo update.zip baixado com sucesso.")
        
        print(f"Iniciando o download do arquivo de hash de {hash_url}...")
        response = requests.get(hash_url)
        response.raise_for_status()
        hash_esperado = response.text.strip()
        
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

def baixar_update_helper(versao_atual):
    try:
        release_info = obter_ultima_versao()
        if not release_info:
            return False
        
        assets = release_info.get('assets', [])
        for asset in assets:
            if asset['name'] == 'update_helper.exe':
                update_helper_url = asset['browser_download_url']
                print(f"Iniciando o download de {update_helper_url}...")
                response = requests.get(update_helper_url, stream=True)
                response.raise_for_status()
                
                with open("update_helper.exe", "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print("update_helper.exe baixado com sucesso.")
                return True
        return False
    except requests.RequestException as e:
        print(f"Erro ao baixar o update_helper.exe: {e}")
        return False

def criar_diretorio(diretorio):
    if not os.path.exists(diretorio):
        os.makedirs(diretorio)

def extrair_atualizacao(caminho_zip, diretorio_destino):
    try:
        with zipfile.ZipFile(caminho_zip, "r") as zip_ref:
            print(f"Conteúdo do ZIP: {zip_ref.namelist()}")
            zip_ref.extractall(diretorio_destino)
        print("Arquivo update.zip extraído com sucesso.")
    except zipfile.BadZipFile as e:
        print(f"Erro ao extrair o arquivo ZIP: {e}")

def executar_como_administrador(executavel, *params):
    params_str = ' '.join([f'"{param}"' for param in params])
    try:
        SW_HIDE = 0
        ctypes.windll.shell32.ShellExecuteW(None, "runas", executavel, params_str, None, SW_HIDE)
    except Exception as e:
        print(f"Erro ao executar como administrador: {e}")

def substituir_arquivos():
    try:
        diretorio_temp = "update_temp"
        criar_diretorio(diretorio_temp)
        extrair_atualizacao("update.zip", diretorio_temp)
        print("Fechando o aplicativo...")
        print("Executando update_helper.exe como administrador...")
        executar_como_administrador("update_helper.exe")
        sys.exit()
    except Exception as e:
        print(f"Erro ao substituir os arquivos: {e}")

def verificar_atualizacao(versao_atual):
    """Verifica se há uma nova versão disponível e pergunta ao usuário se deseja atualizar."""
    release_info = obter_ultima_versao()
    if not release_info:
        print("Não foi possível obter a última versão.")
        return False
    
    ultima_versao = release_info.get('tag_name')
    if versao_atual < ultima_versao:
        root = tk.Tk()
        root.withdraw()
        user_response = messagebox.askyesno(
            "Atualização Disponível",
            f"Uma nova versão ({ultima_versao}) está disponível. Deseja atualizar?"
        )

        if user_response:
            if baixar_update_helper(versao_atual):
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
                messagebox.showwarning("Erro no Atualizador", "O arquivo update_helper.exe não pôde ser baixado.")
                root.destroy()
                sys.exit()
        else:
            root.destroy()
            return False
    else:
        print("Você já está na versão mais recente.")
        return False
