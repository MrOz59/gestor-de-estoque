import os
import shutil
import subprocess
import zipfile
from datetime import datetime

def criar_diretorio(destino):
    """Cria o diretório especificado se ele não existir."""
    if not os.path.exists(destino):
        os.makedirs(destino)

def gerar_dist_com_pyinstaller(script, destino):
    """Gera a distribuição usando PyInstaller para o diretório de destino."""
    try:
        # Comando do PyInstaller para gerar a distribuição
        comando = f'pyinstaller --distpath {destino} --onefile -n Kalymos --icon icon.ico {script}'
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

def executar_hash_generator(caminho_executavel):
    """Executa o hash_generator.exe."""
    try:
        subprocess.run(caminho_executavel, check=True, shell=True)
        print(f"Hash generator executado com sucesso: {caminho_executavel}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar o hash_generator.exe: {e}")

def main():
    # Define as variáveis de caminho e diretório
    data_atual = datetime.now().strftime("%Y-%m-%d")
    diretorio_update = f"kalymos-update-{data_atual}"
    criar_diretorio(diretorio_update)
    
    # Gera a distribuição usando o PyInstaller
    destino_dist = os.path.join(diretorio_update, 'dist')
    criar_diretorio(destino_dist)
    gerar_dist_com_pyinstaller('main.py', destino_dist)
    
    # Compacta os arquivos gerados pelo PyInstaller na pasta dist em um arquivo ZIP chamado update.zip
    zip_destino = os.path.join(diretorio_update, "update.zip")
    compactar_arquivos_em_zip(destino_dist, zip_destino)
    
    # Copia os arquivos hash_generator.exe, update_helper.exe e icon.ico para o diretório raiz
    arquivos_para_copiar = [
        os.path.join('dist', 'hash_generator.exe'),
        os.path.join('dist', 'update_helper.exe'),
        'icon.ico'
    ]
    copiar_arquivos_para_raiz(diretorio_update, arquivos_para_copiar)
    
    # Executa o hash_generator.exe para gerar o hash do arquivo ZIP
    caminho_hash_generator = os.path.join(diretorio_update, 'hash_generator.exe')
    executar_hash_generator(caminho_hash_generator)

if __name__ == "__main__":
    main()
