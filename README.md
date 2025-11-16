# Trabalho Final Engenharia de Software 2

Este projeto contém um backend em FastAPI e um frontend simples.

## Como executar com Docker

Para executar o projeto, você precisa ter o Docker e o Docker Compose instalados.

1.  **Clone o repositório:**

    ```bash
    git clone <url-do-repositorio>
    cd TrabalhoFinalEngenhariaSoftware2
    ```

2.  **Crie um arquivo `.env`** na raiz do projeto e adicione as seguintes variáveis de ambiente:

    ```
    POSTGRES_USER=user
    POSTGRES_PASSWORD=senha
    POSTGRES_DB=meu_bd
    DATABASE_URL=postgresql://user:senha@db:5432/meu_bd
    ```

3.  **Execute o Docker Compose:**

    ```bash
    docker-compose up -d
    ```

    Este comando irá construir as imagens, criar e iniciar os containers.

    *   O backend estará disponível em `http://localhost:8000`
    *   O frontend estará disponível em `http://localhost:8080`
    *   O banco de dados estará disponível na porta `5432`

4.  **Para parar a execução:**

    ```bash
    docker-compose down
    ```

## Estrutura

*   `backend/`: Contém a aplicação FastAPI.
    *   `Dockerfile`: Define a imagem Docker para o backend.
    *   `requirements.txt`: Lista as dependências Python.
    *   `main.py`: O código da aplicação.
*   `frontend/`: Contém os arquivos HTML estáticos.
*   `.env`: Arquivo de configuração com as variáveis de ambiente.
*   `docker-compose.yml`: Orquestra os serviços de backend, frontend e banco de dados.

## Endpoints da API

*   `POST /gerentes`: Cria um novo gerente.
*   `POST /vendedores`: Cria um novo vendedor.
*   `POST /clientes`: Cria um novo cliente.
*   `GET /clientes`: Lista todos os clientes.
