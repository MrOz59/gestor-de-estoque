import time
import os
import shutil
import sys
import ctypes
import psutil

def verificar_e_fechar_aplicacao(nome_processo):
    """Verifica se o processo está em execução e o fecha."""
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == nome_processo:
            try:
                proc.terminate()  # Tenta fechar o processo
                proc.wait(timeout=20)  # Aguarda até 5 segundos para o processo terminar
                time.sleep(20)      
                print(f"Processo {nome_processo} fechado com sucesso.")
            except psutil.NoSuchProcess:
                print(f"Processo {nome_processo} não encontrado.")
            except psutil.AccessDenied:
                print(f"Não foi possível fechar o processo {nome_processo}. Permissões insuficientes.")
            except psutil.TimeoutExpired:
                print(f"Tempo limite expirado ao tentar fechar o processo {nome_processo}.")
            return
    print(f"Processo {nome_processo} não está em execução.")

def substituir_arquivos(diretorio_temp):
    time.sleep(20)   
    """Substitui os arquivos do diretório temporário no diretório principal."""
    try:
        if not os.path.exists(diretorio_temp):
            raise FileNotFoundError(f"O diretório {diretorio_temp} não foi encontrado.")

        # Remover o executável principal para substituição
        app_executable = "kalymos.exe"
        if os.path.exists(app_executable):
            os.remove(app_executable)
            print(f"Arquivo {app_executable} removido com sucesso.")
        else:
            print(f"Arquivo {app_executable} não encontrado para remoção.")

        # Substituir arquivos do diretório temporário no diretório principal
        for item in os.listdir(diretorio_temp):
            source = os.path.join(diretorio_temp, item)
            destination = os.path.join(".", item)

            if os.path.isdir(source):
                if os.path.exists(destination):
                    shutil.rmtree(destination)
                shutil.copytree(source, destination)
            else:
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
        
        # Verificar e fechar o aplicativo principal se estiver aberto
        verificar_e_fechar_aplicacao("kalymos.exe")
        
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
        print("Tentando executar como administrador.")
        executar_como_administrador(sys.executable, *sys.argv)

if __name__ == "__main__":
    main()
