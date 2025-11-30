Documentação do Sistema de E-commerce
1. Visão Geral do Projeto
O projeto consiste em uma plataforma web de E-commerce desenvolvida como requisito para a disciplina de Engenharia de Software 2. O sistema foi projetado para gerenciar o fluxo de venda de produtos eletrônicos, contemplando desde a visualização de vitrine pelo cliente até a gestão administrativa de estoques e produtos.

A aplicação segue uma arquitetura moderna baseada em microsserviços containerizados, separando claramente as responsabilidades entre interface de usuário (Frontend), lógica de negócios (Backend) e persistência de dados (Banco de Dados).

2. Arquitetura do Sistema
O sistema utiliza uma arquitetura em camadas (Layered Architecture) no backend para garantir a separação de interesses e facilitar a manutenibilidade e testabilidade do código.

Frontend: Servido via Nginx, consiste em páginas estáticas responsivas que consomem a API.

Backend: API RESTful desenvolvida em Python (FastAPI), responsável por processar as requisições, aplicar regras de negócio e comunicar-se com o banco de dados.

Banco de Dados: PostgreSQL para dados relacionais (produtos, categorias) e Redis (planejado) para gestão de sessões.

Infraestrutura: Orquestração de containers via Docker Compose.

3. Tecnologias Utilizadas
Backend
Linguagem: Python 3.11

Framework: FastAPI (Alta performance e validação automática de dados).

Banco de Dados: PostgreSQL (via driver assíncrono asyncpg).

Padrões de Projeto: Service-Repository Pattern, Dependency Injection.

Testes: Pytest (Testes de integração e unitários).

Servidor de Aplicação: Uvicorn/Gunicorn.

Frontend
Estrutura: HTML5 e JavaScript (Vanilla).

Estilização: Tailwind CSS (Framework Utility-First) e CSS customizado.

Design: Interface responsiva adaptada para dispositivos móveis e desktop, utilizando a fonte 'Inter'.

DevOps & Infraestrutura
Docker: Containerização dos serviços.

Docker Compose: Orquestração dos ambientes (DB, Backend, Frontend).

4. Funcionalidades Principais
Módulo do Cliente (Frontend)
Autenticação: Telas de Login, Cadastro e Recuperação de Senha.

Navegação: Página inicial com destaques, listagem de produtos com filtros e página de detalhes do produto.

Fluxo de Compra: Carrinho de compras interativo e checkout com simulação de endereço e pagamento.

Painel do Usuário: Histórico de pedidos, acompanhamento de status de entrega (timeline visual) e lista de desejos.

Módulo Administrativo (Backoffice)
Dashboard: Visão geral com métricas de faturamento, novos usuários e alertas de estoque.

Gestão de Produtos: Listagem, cadastro e remoção de produtos (CRUD).

Controle de Estoque: Visualização de itens com estoque baixo.

API (Backend)
Gerenciamento de Produtos: Endpoints para criar, listar, atualizar e deletar produtos (/produtos).

Categorização: Gestão de categorias de produtos (/categorias).

Validações: Tratamento de erros para itens duplicados ou não encontrados, garantindo integridade referencial.

5. Estrutura de Código (Backend)
O backend foi organizado seguindo boas práticas de Engenharia de Software:

main.py: Ponto de entrada da aplicação e definição de rotas.

services.py: Camada de serviço que contém a lógica de negócio (ex: verificar se categoria existe antes de criar produto).

repositories.py: Camada de acesso a dados (Data Access Layer), responsável pelas queries SQL diretas.

schemas.py: Modelos de dados (DTOs) utilizando Pydantic para validação de entrada e saída.

database.py: Gerenciamento do pool de conexões com o PostgreSQL.