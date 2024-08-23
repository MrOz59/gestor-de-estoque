import os
import shutil
import subprocess
import zipfile
from datetime import datetime
import hashlib

def criar_diretorio(destino):
    """Cria o diretório especificado se ele não existir."""
    if not os.path.exists(destino):
        os.makedirs(destino)

def gerar_dist_com_pyinstaller(script, destino):
    """Gera a distribuição usando PyInstaller para o diretório de destino."""
    try:
        # Comando do PyInstaller para gerar a distribuição
        comando = f'pyinstaller --distpath {destino} --onefile --windowed -n Kalymos --icon icon.ico {script}'
        subprocess.run(comando, check=True, shell=True)
        print(f"Distribuição gerada com sucesso em: {destino}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao gerar a distribuição com PyInstaller: {e}")

def copiar_arquivos_para_raiz(diretorio_raiz, arquivos):
    """Copia os arquivos especificados para o diretório raiz."""
    try:
        for arquivo in arquivos:
            shutil.copy(arquivo, diretorio_raiz)
        print(f"Arquivos copiados com sucesso para {diretorio_raiz}")
    except shutil.Error as e:
        print(f"Erro ao copiar arquivos: {e}")

def compactar_arquivos_em_zip(diretorio_origem, zip_destino):
    """Compacta os arquivos do diretório especificado em um arquivo ZIP."""
    try:
        with zipfile.ZipFile(zip_destino, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(diretorio_origem):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, diretorio_origem)
                    zipf.write(file_path, arcname)
        print(f"Arquivos do diretório {diretorio_origem} compactados com sucesso em {zip_destino}")
    except Exception as e:
        print(f"Erro ao compactar os arquivos: {e}")

def calcular_hash_arquivo(arquivo):
    """Calcula o hash SHA-256 do arquivo especificado."""
    hash_sha256 = hashlib.sha256()
    try:
        with open(arquivo, "rb") as f:
            while chunk := f.read(8192):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        print(f"Erro ao calcular hash do arquivo: {e}")
        return None

def gerar_metadados_hash(arquivo, arquivo_saida):
    """Gera um arquivo com o hash do arquivo especificado."""
    hash_calculado = calcular_hash_arquivo(arquivo)
    if hash_calculado:
        try:
            with open(arquivo_saida, "w") as f:
                f.write(hash_calculado)
            print(f"Hash do arquivo {arquivo} gerado com sucesso em {arquivo_saida}")
        except Exception as e:
            print(f"Erro ao salvar o hash em {arquivo_saida}: {e}")

def main():
    # Define as variáveis de caminho e diretório
    data_atual = datetime.now().strftime("%Y-%m-%d")
    diretorio_update = f"dist/kalymos-update-{data_atual}"
    criar_diretorio(diretorio_update)
    
    # Gera a distribuição usando o PyInstaller
    destino_dist = os.path.join(diretorio_update, 'dist')
    criar_diretorio(destino_dist)
    gerar_dist_com_pyinstaller('main.py', destino_dist)
    
    # Compacta os arquivos gerados pelo PyInstaller na pasta dist em um arquivo ZIP chamado update.zip
    zip_destino = os.path.join(diretorio_update, "update.zip")
    compactar_arquivos_em_zip(destino_dist, zip_destino)
    
    # Copia os arquivos update_helper.exe e icon.ico para o diretório raiz
    arquivos_para_copiar = [
        os.path.join('dist', 'update_helper.exe'),
        'icon.ico'
    ]
    copiar_arquivos_para_raiz(diretorio_update, arquivos_para_copiar)
    
    # Gera o hash do arquivo ZIP
    gerar_metadados_hash(zip_destino, os.path.join(diretorio_update, 'update.zip.sha256'))

if __name__ == "__main__":
    main()
