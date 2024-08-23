import os
import shutil
import sys
import ctypes

def substituir_arquivos(diretorio_temp):
    """Substitui os arquivos do diretório temporário no diretório principal."""
    try:
        # Verifica se o diretório temporário existe
        if not os.path.exists(diretorio_temp):
            raise FileNotFoundError(f"O diretório {diretorio_temp} não foi encontrado.")

        for item in os.listdir(diretorio_temp):
            source = os.path.join(diretorio_temp, item)
            destination = os.path.join(".", item)

            # Se for um diretório, substitua o diretório de destino
            if os.path.isdir(source):
                if os.path.exists(destination):
                    shutil.rmtree(destination)
                shutil.copytree(source, destination)
            else:
                # Se for um arquivo, substitua o arquivo de destino
                shutil.copy2(source, destination)
        
        print("Arquivos substituídos com sucesso.")
    except Exception as e:
        print(f"Erro ao substituir arquivos: {e}")

def is_admin():
    """Verifica se o script está sendo executado com privilégios de administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def executar_como_administrador(executavel, *params):
    """Executa o comando fornecido como administrador."""
    params_str = ' '.join([f'"{param}"' for param in params])  # Formata os parâmetros
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", executavel, params_str, None, 1)
    except Exception as e:
        print(f"Erro ao executar como administrador: {e}")

def main():
    if is_admin():
        print("Executando como administrador.")
        temp_dir = "update_temp"
        substituir_arquivos(temp_dir)

        # Limpeza após a substituição
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Diretório {temp_dir} removido com sucesso.")
        else:
            print(f"O diretório {temp_dir} não foi encontrado para remoção.")

        # Reinicie o aplicativo principal
        app_executable = "kalymos.exe"
        if os.path.exists(app_executable):
            print(f"Reiniciando o aplicativo principal: {app_executable}")
            os.execv(app_executable, [app_executable] + sys.argv[1:])
        else:
            print(f"O aplicativo principal {app_executable} não foi encontrado.")
    else:
        # Se o script não estiver sendo executado como administrador, tente reiniciá-lo como administrador
        print("Tentando executar como administrador.")
        executar_como_administrador(sys.executable, *sys.argv)

if __name__ == "__main__":
    main()
