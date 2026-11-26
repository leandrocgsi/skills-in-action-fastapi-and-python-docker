# skills-in-action-fastapi-and-python-docker
### Base de código da API REST de pessoas e livros em Python 3.14 e FastAPI, com HATEOAS, paginação, autenticação JWT, arquivos no S3, e-mail e Swagger, usada como ponto de partida para dockerizar a aplicação com o Claude Code.

![Forks](https://img.shields.io/github/forks/leandrocgsi/skills-in-action-fastapi-and-python-docker)
![Stars](https://img.shields.io/github/stars/leandrocgsi/skills-in-action-fastapi-and-python-docker)
[![Donate with PayPal](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/donate/?hosted_button_id=ZJ4NQJXEKQ63A)

[![Image](https://raw.githubusercontent.com/leandrocgsi/blog-images/refs/heads/main/formacoes_github/09-docker.png "Formação Docker e Kubernetes 2026: do Zero à Inteligência Artificial com MCP Catalog e Docker Model Runner")](https://pub.erudio.com.br/formacao-docker-kubernetes-do-zero-a-inteligencia-artificial-com-mcp?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker)

Este repositório serve de base para o conteúdo da série *skills in action*. Ele é relacionado à [Formação Docker e Kubernetes 2026](https://pub.erudio.com.br/formacao-docker-kubernetes-do-zero-a-inteligencia-artificial-com-mcp?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker), mas não é o código do curso.

# Cursos Relacionados

[![Image](https://raw.githubusercontent.com/leandrocgsi/blog-images/refs/heads/main/formacoes_github/01-hm-claude-code-java.png "Formação Claude Code para DEVs Java e Spring Boot: Produtividade 10x, Agentes de IA, MCPs e Aplicações do Mundo Real")](https://pub.erudio.com.br/formacao-dev10x-claude-code-para-devs-java-e-spring-boot?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker)

[![Image](https://raw.githubusercontent.com/leandrocgsi/blog-images/refs/heads/main/formacoes_github/07-rest-java.png "Formação Spring Boot 2026: do Zero ao Deploy na AWS e GCP com Java, Docker e Kubernetes")](https://pub.erudio.com.br/formacao-spring-boot-2026-do-zero-ao-continuous-deployment-na-aws-e-gcp-com-java-docker-e-kubernetes?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker)

[![Image](https://raw.githubusercontent.com/leandrocgsi/blog-images/refs/heads/main/formacoes_github/14-microservices-java.png "Formação Microsserviços 2026: do Zero ao Deploy na Google Cloud com Spring Boot, Kubernetes e Docker")](https://pub.erudio.com.br/formacao-microsservicos-2026-do-zero-ao-deploy-na-google-cloud-com-spring-boot-kubernetes-e-docker?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker)

[![Image](https://raw.githubusercontent.com/leandrocgsi/blog-images/refs/heads/main/formacoes_github/31-spring-ai-java.png "Formação Spring AI 2026: Inteligência Artificial com Java, Spring Boot, ChatGPT, DeepSeek, Claude e MCP")](https://pub.erudio.com.br/formacao-spring-ai-2026-inteligencia-artificial-com-java-spring-boot-chatgpt-deepseek-claude-e-mcp?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker)

[![Image](https://raw.githubusercontent.com/leandrocgsi/blog-images/refs/heads/main/formacoes_github/09-docker.png "Formação Docker e Kubernetes 2026: do Zero à Inteligência Artificial com MCP Catalog e Docker Model Runner")](https://pub.erudio.com.br/formacao-docker-kubernetes-do-zero-a-inteligencia-artificial-com-mcp?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker)

[![Image](https://raw.githubusercontent.com/leandrocgsi/blog-images/refs/heads/main/formacoes_github/24-tests-java.png "Formação Java Testing 2026: Testes Automatizados com JUnit, Mockito, Spring Boot, TDD e TestContainers")](https://pub.erudio.com.br/formacao-java-testing-2026-testes-automatizados-com-junit-mockito-spring-boot-tdd-e-testcontainers?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker)

[![Image](https://raw.githubusercontent.com/leandrocgsi/blog-images/refs/heads/main/formacoes_github/29-cdpl-java-gcp.png "Formação Continuous Deployment: do Zero ao Deploy com Java, Spring Boot, Docker, Kubernetes, Google Cloud (GCP) e GitHub Actions")](https://pub.erudio.com.br/formacao-continuous-deployment-java-kubernetes-gcp-github-actions?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker)

[![Image](https://raw.githubusercontent.com/leandrocgsi/blog-images/refs/heads/main/formacoes_github/27-cicd-java-aws.png "Formação Continuous Integration e Delivery: do Zero ao Deploy com Java, Spring Boot, Docker, Amazon AWS e GitHub Actions")](https://pub.erudio.com.br/formacao-continuous-integration-delivery-java-aws-github-actions?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker)

[![Image](https://raw.githubusercontent.com/leandrocgsi/blog-images/refs/heads/main/formacoes_github/28-cicd-java-azure.png "Formação Continuous Integration e Delivery: do Zero ao Deploy com Java, Spring Boot, Docker, Microsoft Azure e GitHub Actions")](https://pub.erudio.com.br/formacao-continuous-integration-delivery-java-azure-github-actions?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker)

[![Image](https://raw.githubusercontent.com/leandrocgsi/blog-images/refs/heads/main/formacoes_github/18-rest-spring-kotlin.png "Formação Spring Boot com Kotlin: REST APIs Profissionais do Zero ao Deploy na AWS com Docker e Kubernetes")](https://pub.erudio.com.br/formacao-spring-boot-com-kotlin-rest-apis-profissionais-do-zero-ao-deploy-na-aws-com-docker-e-kubernetes?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker)

[![Image](https://raw.githubusercontent.com/leandrocgsi/blog-images/refs/heads/main/formacoes_github/22-ms-kotlin.png "Formação Microsserviços com Spring Cloud, Spring Boot, Kotlin, Docker e Zookeeper")](https://pub.erudio.com.br/formacao-microsservicos-com-spring-cloud-spring-boot-kotlin-docker-e-zookeeper?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker)

[![Image](https://raw.githubusercontent.com/leandrocgsi/blog-images/refs/heads/main/formacoes_github/32-code-ai-kspring.png "Formação Spring AI 2026: Inteligência Artificial com Kotlin, Spring Boot, ChatGPT, DeepSeek, Claude e MCP")](https://pub.erudio.com.br/formacao-spring-ai-2026-inteligencia-artificial-com-kotlin-spring-boot-chatgpt-deepseek-claude-e-mcp?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker)

[![Image](https://raw.githubusercontent.com/leandrocgsi/blog-images/refs/heads/main/formacoes_github/10-docker-to-aws.png "Formação Docker e Kubernetes 2026: do Zero ao Deploy Profissional na AWS, Azure e GCP com GitHub Actions")](https://pub.erudio.com.br/docker-e-kubernetes-2026-do-zero-ao-deploy-profissional-na-aws-azure-e-gcp-com-github-actions?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker)

[![Image](https://raw.githubusercontent.com/leandrocgsi/blog-images/refs/heads/main/formacoes_github/13-career.png "Carreira em TI do Zero ao Exterior: Currículo, Entrevistas, Negociação e Crescimento Profissional")](https://pub.erudio.com.br/carreira-em-ti-do-zero-ao-exterior-curriculo-entrevistas-negociacao-e-crescimento-profissional?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker)

# Sobre este repositório

Este repositório é o ponto de partida de um vídeo da série *skills in action*, em que o **Claude Code** e **skills** são usados para **dockerizar** uma API REST em Python já existente. A base é uma API completa em **Python 3.14 e FastAPI**, mas sem nada de Docker: sem `Dockerfile`, sem Docker Compose e sem pipeline de CI/CD.

## O que tem aqui hoje (ponto de partida)

* CRUD de pessoas e livros, com paginação e links HATEOAS
* Negociação de conteúdo em JSON (HAL), XML e YAML pelos headers `Content-Type` e `Accept`
* Autenticação com JWT e hashes de senha Argon2id
* Importação e exportação de pessoas em CSV e XLSX
* Upload e download de arquivos no S3
* Envio de e-mail, com e sem anexo
* CORS configurável
* Documentação com Swagger UI e OpenAPI 3.1
* SQLAlchemy 2 (async), migrations com Alembic e MySQL 9.7
* Testes unitários e de integração (Testcontainers) com pytest e collection do Postman

## Resultado final dos vídeos

Ao final da gravação a aplicação deve estar dockerizada, na pasta `02-docker-after`.

## Como usar o código

### Pré-requisitos

* Python 3.14 e [uv](https://docs.astral.sh/uv/)
* MySQL 9.7 rodando em `localhost:3306` com usuário `root` e senha `admin123` (ajuste no `.env` se for diferente)
* Um S3 compatível em `http://localhost:4566` (LocalStack). A API cria o bucket na inicialização, então ele precisa estar no ar antes dela. Para usar a AWS real, deixe `AWS_S3_ENDPOINT` em branco no `.env`
* Docker em execução, necessário apenas para os testes de integração com Testcontainers

### Estrutura: before e after

* `01-docker-before`: o ponto de partida, deixado intacto para você comparar
* `02-docker-after`: começa idêntica à pasta before e é nela que a dockerização é adicionada durante o vídeo

Cada pasta é um projeto Python completo. Entre em uma delas (`cd 02-docker-after`) antes de executar os comandos abaixo.

### Passo a passo

1. Crie o banco de dados (os hífens exigem crase): ``CREATE DATABASE `rest-with-fastapi-and-python-erudio-2026`;``
2. Copie o arquivo de configuração: `cp .env.example .env`
3. Instale as dependências: `uv sync`
4. Crie e popule as tabelas: `uv run alembic upgrade head`
5. Execute a aplicação: `uv run uvicorn erudio.main:create_app --factory --reload`
6. Abra o Swagger UI em `http://localhost:8000/swagger-ui/index.html`. O login do seed é `leandro` / `admin123`
7. Rode os testes com `uv run pytest --cov`. Eles sobem o MySQL e o LocalStack com Testcontainers, e o gate de cobertura é 90%
8. Para rodar só os testes unitários: `uv run pytest tests/unit`
9. Abra a pasta `02-docker-after` no Claude Code e siga o vídeo para dockerizar a aplicação

## O que a API faz

| Área | Endpoints |
|---|---|
| Auth | `POST /auth/signin`, `PUT /auth/refresh/{username}`, `POST /auth/createUser` (JWT, hashes de senha Argon2id) |
| People | `GET/POST/PUT /api/person/v1`, `GET/PATCH/DELETE /api/person/v1/{id}`, `GET /api/person/v1/findPeopleByName/{name}`, `POST /api/person/v1/massCreation` (CSV ou XLSX), `GET /api/person/v1/exportPage` (CSV ou XLSX) |
| Books | `GET/POST/PUT /api/book/v1`, `GET/DELETE /api/book/v1/{id}` |
| Files | `POST /api/file/v1/uploadFile`, `POST /api/file/v1/uploadMultipleFiles`, `GET /api/file/v1/downloadFile/{name}` |
| e-Mail | `POST /api/email/v1`, `POST /api/email/v1/withAttachment` |
| Outros | `GET /api/test/v1` (um log por nível), Swagger UI, OpenAPI 3.1 |

Tudo em `/api` exige `Authorization: Bearer <accessToken>`. Os endpoints de dados leem e escrevem JSON (HAL), XML e YAML,
de acordo com `Content-Type` e `Accept`. Relatórios em PDF não são suportados nesta API.

### Configuração

Variáveis de ambiente (ou `.env`); apenas as duas primeiras são obrigatórias.

| Variável | Padrão | Significado |
|---|---|---|
| `DATABASE_URL` | | `mysql+asyncmy://user:pass@host:3306/rest-with-fastapi-and-python-erudio-2026?charset=utf8mb4` |
| `JWT_SECRET_KEY` | | pelo menos 32 bytes |
| `JWT_EXPIRE_MILLISECONDS` | `3600000` | validade do access token (o refresh token dura três vezes mais) |
| `CORS_ORIGINS` | `http://localhost:8080,http://localhost:3000,https://www.erudio.com.br` | separadas por vírgula |
| `AWS_S3_BUCKET` | `erudio-files` | bucket S3 onde os uploads são salvos |
| `AWS_S3_REGION` | `us-east-1` | |
| `AWS_S3_ENDPOINT` | `http://localhost:4566` | LocalStack em dev; em branco usa a AWS real com a credential chain padrão |
| `AWS_S3_ACCESS_KEY` / `AWS_S3_SECRET_KEY` | `test` / `test` | credenciais fixas aceitas pelo LocalStack; ignoradas quando `AWS_S3_ENDPOINT` está em branco |
| `MAX_FILE_SIZE_MB` / `MAX_REQUEST_SIZE_MB` | `200` / `215` | limites de upload (413 acima deles) |
| `MAIL_HOST` / `MAIL_PORT` / `MAIL_STARTTLS` | `smtp.gmail.com` / `587` / `true` | servidor SMTP |
| `EMAIL_USERNAME` / `EMAIL_PASSWORD` | | remetente e login SMTP; em branco fica sem valor, e sem username nenhum e-mail é enviado |
| `EMAIL_DEFAULT_SUBJECT` / `EMAIL_DEFAULT_MESSAGE` | `Default Subject` / `Default Message` | usados quando a requisição não informa esses campos |
| `LOG_LEVEL` | `INFO` | |

# Outros Cursos Erudio

[![Image](https://raw.githubusercontent.com/leandrocgsi/blog-images/refs/heads/main/formacoes_github/01-rest-asp-net.png "Formação ASP.NET 2026: do Zero ao Deploy na Azure e GCP com .NET 10, Docker e Kubernetes")](https://pub.erudio.com.br/asp-net-2026-do-0-a-azure-e-gcp-com-asp-net-10-docker-e-kubernetes?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker)

[![Image](https://raw.githubusercontent.com/leandrocgsi/blog-images/refs/heads/main/formacoes_github/33-dotnet-ai.png "Inteligência Artificial com .NET AI e .NET 10: Aplicações Inteligentes com ChatGPT, OpenAI, DeepSeek e Ollama")](https://pub.erudio.com.br/inteligencia-artificial-com-dotnet-ai-e-dotnet-10-apps-inteligentes-com-chatgpt-openai-deepseek-e-ollama?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker)

[![Image](https://raw.githubusercontent.com/leandrocgsi/blog-images/refs/heads/main/formacoes_github/15-microservices-asp-net.png "Formação Microsserviços 2026: do 0 ao Deploy na Google Cloud com ASP.NET, .NET 10, Kubernetes e Docker")](https://pub.erudio.com.br/meus-cursos?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker)

[![Image](https://raw.githubusercontent.com/leandrocgsi/blog-images/refs/heads/main/formacoes_github/20-kotlin.png "Kotlin para DEV's Java: Domine Lambdas, Generics, Reflections, Programação Funcional e Spring Boot")](https://pub.erudio.com.br/kotlin-para-desenvolvedores-java-domine-sintaxe-lambdas-generics-reflections-programacao-funcional-e-spring-boot?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker)

[![Image](https://raw.githubusercontent.com/leandrocgsi/blog-images/refs/heads/main/formacoes_github/30-jasper.png "Crie Relatórios Profissionais com JasperReports, Java, Spring Boot e JasperSoft Studio")](https://pub.erudio.com.br/crie-relatorios-profissionais-com-jasperreports-java-spring-boot-e-jaspersoft-studio?utm_source=github&utm_medium=organic&utm_campaign=readme&utm_content=sia-python-docker)
