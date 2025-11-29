# Trabalho Final de Engenharia de Software 2

Este projeto é uma aplicação web simples desenvolvida como trabalho final para a disciplina de Engenharia de Software 2. A aplicação consiste em um backend desenvolvido com FastAPI (Python) e um frontend com HTML, TailwindCSS e JavaScript.

## Estrutura do Projeto

O projeto está dividido em duas partes principais: `backend` e `frontend`.

```
/
├── backend/
│   └── bd_add_code_template.py  # Aplicação FastAPI
├── frontend/
│   ├── cadastrar.html           # Página de cadastro de usuário
│   ├── esqueci_minha_senha.html # Página de recuperação de senha
│   └── login.html               # Página de login
├── .env                         # Arquivo de variáveis de ambiente (não versionado)
└── README.md                    # Este arquivo
```

## Funcionalidades

### Backend

O backend é uma API RESTful construída com **FastAPI** que gerencia as seguintes entidades:
- **Gerentes**
- **Vendedores**
- **Clientes**

Principais características:
- Conexão com banco de dados **PostgreSQL** utilizando `asyncpg`.
- Endpoints para criar e listar as entidades.
- Validação de dados de entrada com Pydantic.
- Pool de conexões assíncronas com o banco de dados.
- Tratamento de erros, como emails duplicados.

### Frontend

O frontend é composto por páginas estáticas que simulam a interação de um usuário com o sistema:
- **Página de Login (`login.html`):** Formulário para autenticação do usuário.
- **Página de Cadastro (`cadastrar.html`):** Formulário para registro de novos usuários.
- **Página de Recuperação de Senha (`esqueci_minha_senha.html`):** Formulário para que o usuário possa redefinir sua senha.

As páginas foram estilizadas com **TailwindCSS** e contêm JavaScript para validações básicas de formulário no lado do cliente.

## Como Executar

### Pré-requisitos

- Python 3.10+
- Um servidor de banco de dados PostgreSQL em execução.

### Backend

1.  **Navegue até a pasta do backend:**
    ```bash
    cd backend
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install "fastapi[all]" asyncpg
    ```

4.  **Configure o banco de dados:**
    - Crie um arquivo `.env` na raiz do projeto (`TrabalhoFinalEngenhariaSoftware2/`).
    - Adicione a sua string de conexão do PostgreSQL ao arquivo:
      ```
      DATABASE_URL="postgresql://USUARIO:SENHA@HOST:PORTA/NOME_DO_BANCO"
      ```
    - Você precisará criar as tabelas `gerente`, `vendedor` e `cliente` no seu banco de dados para que a aplicação funcione.

5.  **Inicie o servidor:**
    ```bash
    uvicorn bd_add_code_template:app --reload
    ```
    O servidor estará disponível em `http://127.0.0.1:8000`.

### Frontend

1.  Abra qualquer um dos arquivos `.html` da pasta `frontend/` diretamente no seu navegador.
    ```bash
    # Exemplo no macOS
    open frontend/login.html
    ```
    As páginas são estáticas e não requerem um servidor web, mas as interações com o backend (login, cadastro, etc.) são simuladas e precisam ser implementadas para se conectar à API do FastAPI.

## Autores

- Seu Nome
- Nome do Colega
