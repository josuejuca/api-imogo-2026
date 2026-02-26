# imoGo API

API do **imoGo** para atender o app mobile e o site.

## Visao geral

- Framework: FastAPI
- Banco: MySQL (via SQLAlchemy + PyMySQL)
- Auth: JWT + API Key
- Versionamento atual: `v2`
- Prefixo das rotas de autenticacao: `/api/v2/auth`

## Funcionalidades atuais

- Cadastro de usuario
- Login com e-mail e senha
- Login social
- Renovacao de token
- Consulta de perfil (`/me`)
- Recuperacao de senha com envio de senha temporaria

## Instalacao

1. Criar e ativar ambiente virtual:

```bash
python -m venv venv
venv\Scripts\activate
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Configurar ambiente:

```bash
copy .env.example .env
```

4. Ajustar valores do `.env`.

## Variaveis de ambiente

```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/auth_db
SECRET_KEY=sua-chave-secreta
JWT_EXPIRES_DAYS=7
```

- `DATABASE_URL`: conexao com MySQL.
- `SECRET_KEY`: chave usada para assinar JWT.
- `JWT_EXPIRES_DAYS`: validade do token em dias.

## Executando o projeto

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Endpoints uteis:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/api/docs`
- Health: `http://localhost:8000/health`

## Estrutura do projeto

```text
.
|-- main.py
|-- requirements.txt
|-- src
|   |-- core
|   |   |-- config.py
|   |   `-- security.py
|   |-- db
|   |   |-- session.py
|   |   `-- init_db.py
|   |-- routes
|   |   `-- auth.py
|   |-- models.py
|   `-- schemas.py
`-- .env.example
```

## Banco de dados

No startup, a API:

1. Garante a existencia do banco (quando driver for MySQL).
2. Cria as tabelas definidas em `models.py` (`user` e `external_id`).

## Autenticacao

A API usa dois mecanismos:

- `token` JWT (retornado em login/social/renew)
- `X-API-Key` (retornado em login/social e exigido em rotas protegidas por chave)

## Endpoints

Base URL local: `http://localhost:8000`

### Health

- `GET /health`
- Resposta:

```json
{ "status": "ok" }
```

### Auth

#### Registrar usuario

- `POST /api/v2/auth/register`

Body:

```json
{
  "name": "Maria Silva",
  "phone": "11999999999",
  "email": "maria@email.com",
  "password": "123456",
  "origin": 10,
  "device": 10
}
```

Resposta `201`:

```json
{
  "public_id": "100102260001",
  "message": "User created successfully."
}
```

Observacoes:

- `device` aceito: `10` (mobile) ou `20` (desktop).
- `email` e `phone` sao unicos.

#### Login

- `POST /api/v2/auth/login`

Body:

```json
{
  "email": "maria@email.com",
  "password": "123456"
}
```

Resposta `200`:

```json
{
  "token": "<jwt>",
  "key": "<api_key>"
}
```

#### Login social

- `POST /api/v2/auth/social`

Body:

```json
{
  "provider": "google",
  "type": "oauth",
  "provider_id": "google-user-123",
  "email": "maria@email.com",
  "device": 10,
  "photo_url": "https://...",
  "name": "Maria Silva"
}
```

Resposta `200`:

```json
{
  "token": "<jwt>",
  "key": "<api_key>"
}
```

#### Renovar token

- `POST /api/v2/auth/renew`
- Header obrigatorio: `X-API-Key: <api_key>`

Resposta `200`:

```json
{
  "token": "<novo_jwt>"
}
```

#### Meu perfil

- `GET /api/v2/auth/me`
- Header obrigatorio: `X-API-Key: <api_key>`

Resposta `200`:

```json
{
  "photo": "https://...",
  "phone": "11999999999",
  "email": "maria@email.com",
  "name": "Maria Silva",
  "status": 1,
  "public_id": "100102260001",
  "profile": 1
}
```

#### Esqueci minha senha

- `POST /api/v2/auth/forgot-password`

Body:

```json
{
  "email": "maria@email.com"
}
```

Resposta `200`:

```json
{
  "message": "temporary password sent"
}
```

Observacao:

- Esta rota envia uma senha temporaria via servico SMTP externo configurado no codigo.

## Codigos de erro comuns

- `400`: dados invalidos (ex.: `device` fora de 10/20)
- `401`: credenciais invalidas ou `X-API-Key` ausente
- `403`: `X-API-Key` invalido
- `404`: e-mail nao encontrado (forgot-password)
- `409`: conflito de recurso (e-mail/telefone/provider ja em uso)
- `502`: falha na chamada do servico SMTP
