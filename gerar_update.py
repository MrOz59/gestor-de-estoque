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
        return

def copiar_arquivos_para_raiz(diretorio_raiz, arquivos):
    """Copia os arquivos especificados para o diretório raiz."""
    try:
        for arquivo in arquivos:
            shutil.copy(arquivo, diretorio_raiz)
        print(f"Arquivos copiados com sucesso para {diretorio_raiz}")
    except shutil.Error as e:
        print(f"Erro ao copiar arquivos: {e}")

def compactar_arquivos_em_zip(diretorio_origem, zip_destino, arquivos_extra=[]):
    """Compacta os arquivos do diretório especificado e arquivos extras em um arquivo ZIP."""
    try:
        with zipfile.ZipFile(zip_destino, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(diretorio_origem):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, diretorio_origem)
                    zipf.write(file_path, arcname)
            # Adiciona arquivos extras
            for extra_file in arquivos_extra:
                zipf.write(extra_file, os.path.basename(extra_file))
        print(f"Arquivos do diretório {diretorio_origem} e extras compactados com sucesso em {zip_destino}")
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

def obter_entrada_com_confirmacao(prompt):
    """Solicita a entrada do usuário e confirma se a entrada está correta."""
    while True:
        entrada = input(prompt)
        confirmacao = input(f"Você digitou '{entrada}'. Está correto? (s/n): ").strip().lower()
        if confirmacao == 's':
            return entrada
        elif confirmacao == 'n':
            print("Por favor, digite novamente.")
        else:
            print("Resposta inválida. Digite 's' para sim ou 'n' para não.")

def gerar_config_ini(caminho_arquivo):
    """Gera o arquivo config.ini baseado nas entradas do usuário com confirmação."""
    try:
        owner = obter_entrada_com_confirmacao("Digite o owner (por exemplo, MrOz59): ")
        repo = obter_entrada_com_confirmacao("Digite o repo (por exemplo, kalymos): ")
        version = obter_entrada_com_confirmacao("Digite a versão do aplicativo (por exemplo, v1.4.3): ")
        main_executable = obter_entrada_com_confirmacao("Digite o nome do executável principal (por exemplo, kalymos.exe): ")
        updater_version = obter_entrada_com_confirmacao("Digite a versão do updater (por exemplo, v1.1.0): ")

        with open(caminho_arquivo, 'w') as config_file:
            config_file.write("[config]\n")
            config_file.write(f"owner = {owner}\n")
            config_file.write(f"repo = {repo}\n")
            config_file.write(f"version = {version}\n")
            config_file.write(f"main_executable = {main_executable}\n")
            config_file.write(f"updater_version = {updater_version}\n")
        print(f"Arquivo {caminho_arquivo} gerado com sucesso.")
    except Exception as e:
        print(f"Erro ao gerar o arquivo config.ini: {e}")

def main():
    # Define as variáveis de caminho e diretório
    data_atual = datetime.now().strftime("%Y-%m-%d")
    diretorio_update = f"dist/kalymos-update-{data_atual}"
    criar_diretorio(diretorio_update)
    
    # Gera a distribuição usando o PyInstaller
    destino_dist = os.path.join(diretorio_update, 'dist')
    criar_diretorio(destino_dist)
    gerar_dist_com_pyinstaller('main.py', destino_dist)
    
    # Gera o arquivo config.ini na pasta de destino
    arquivo_config = os.path.join(diretorio_update, 'config.ini')
    gerar_config_ini(arquivo_config)
    
    # Compacta os arquivos gerados pelo PyInstaller na pasta dist em um arquivo ZIP chamado update.zip
    zip_destino = os.path.join(diretorio_update, "update.zip")
    arquivos_extra = [arquivo_config] if os.path.exists(arquivo_config) else []
    compactar_arquivos_em_zip(destino_dist, zip_destino, arquivos_extra=arquivos_extra)
    
    # Copia os arquivos kalymos-updater.exe e icon.ico para o diretório raiz
    arquivos_para_copiar = [
        os.path.join('dist', 'kalymos-updater.exe'),
        'icon.ico'
    ]
    copiar_arquivos_para_raiz(diretorio_update, arquivos_para_copiar)
    
    # Gera o hash do arquivo ZIP
    gerar_metadados_hash(zip_destino, os.path.join(diretorio_update, 'update.zip.sha256'))

if __name__ == "__main__":
    main()
