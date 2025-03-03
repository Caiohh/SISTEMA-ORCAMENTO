Sistema de Orçamentos
Este é um sistema web simples para criação de orçamentos, desenvolvido com Python, Flask e MySQL. Ele permite configurar valores fixos (como custo de combustível e preço de insumos) e criar orçamentos com base em variáveis como distância percorrida.

Pré-requisitos
Antes de começar, certifique-se de que você tem os seguintes itens instalados:

Python 3.8 ou superior

MySQL Server (ou um serviço de banco de dados MySQL)

1. Criar um Ambiente Virtual
Crie um ambiente virtual para isolar as dependências do projeto:

bash
Copy
python -m venv venv
Ative o ambiente virtual:

No Windows:

bash
Copy
venv\Scripts\activate
No Linux/Mac:

bash
Copy
source venv/bin/activate

2. Instalar as Dependências
Instale as dependências listadas no arquivo requirements.txt:

bash
Copy
pip install -r requirements.txt
3. Configurar o Banco de Dados
Crie um banco de dados MySQL chamado orcamentos.

Execute o seguinte comando SQL para criar as tabelas necessárias em BD-ORCAMENTO

4. Executar o Projeto
Com o ambiente virtual ativado e o banco de dados configurado, execute o servidor Flask:

bash
Copy
python app.py
O servidor estará disponível em http://localhost:5000.



Licença
Este projeto está licenciado sob a licença MIT. Consulte o arquivo LICENSE para mais detalhes.