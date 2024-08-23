import hashlib

def calcular_hash_arquivo(arquivo):
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
    hash_calculado = calcular_hash_arquivo(arquivo)
    if hash_calculado:
        with open(arquivo_saida, "w") as f:
            f.write(hash_calculado)

if __name__ == "__main__":
    gerar_metadados_hash("update.zip", "update.zip.sha256")
