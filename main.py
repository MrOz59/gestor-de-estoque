from interface import Aplicacao
from db import criar_tabelas

def main():
    
    # Cria as tabelas no banco de dados
    criar_tabelas()
    
    # Cria e inicia a aplicação
    app = Aplicacao()
    app.mainloop()

if __name__ == "__main__":
    main()
