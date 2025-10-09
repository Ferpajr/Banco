# Banco + ChatBot

Aplicação full‑stack de um banco virtual com API em FastAPI e frontend estático (HTML/CSS/JS). Inclui autenticação JWT, operações bancárias (contas, saldo, extrato, depósitos, saques, empréstimos), chat com roteamento de comandos e UI moderna com abas, tema claro/escuro e modal de confirmação.

## Visão geral

- Backend: FastAPI + Pydantic + JWT (python-jose) + Passlib (pbkdf2_sha256)
- Frontend: HTML/CSS/JS estático servido em `/app`
- Chat: Roteador de comandos e fallback opcional para Gemini (se chave configurada)
- Sessões: Em memória (demo), identificadas por cabeçalho `X-Session-Id`
- Autenticação: JWT (Bearer), exigido na maioria das rotas

Estrutura principal do workspace:

- `banco.py`: Domínio bancário (Cliente, Conta/ContaCorrente, Transações, Empréstimo)
- `bank_service.py`: Camada de serviço `BankApp` sobre o domínio
- `server.py`: API FastAPI, autenticação, rotas e chat
- `frontend/`: UI (index.html, style.css, app.js)

## Requisitos

- Python 3.12+
- Windows PowerShell (instruções abaixo usam PowerShell)

## Instalação (Windows PowerShell)

Crie e ative um ambiente virtual, e instale dependências:

```powershell
# Na raiz do projeto
python -m venv venv
./venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

## Variáveis de ambiente

Crie um arquivo `.env` na raiz (opcional, mas recomendado):

```
# JWT
JWT_SECRET=troque-por-uma-chave-segura
JWT_EXPIRE_MINUTES=60

# Gemini (opcional)
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash-latest
```

Dica: não commitar `.env`. Se houver `.env.example`, copie para `.env` e preencha.

Para gerar uma chave segura:

```powershell
# Gera 32 bytes hexadecimais
python -c "import secrets; print(secrets.token_hex(32))"
```

## Executando o backend

Inicie o servidor FastAPI (uvicorn):

```powershell
uvicorn server:app --reload --host 127.0.0.1 --port 8000
```

- Health: http://127.0.0.1:8000/health (deve retornar `{ "status": "ok" }`)
- Frontend: http://127.0.0.1:8000/app

## Fluxo típico (passo a passo)

1) Criar sessão (UI tem botão "Nova Sessão")
- O backend retorna `sessionId`; a UI envia em `X-Session-Id` e persiste em localStorage.

2) Registrar acesso e obter token (JWT)
- UI: informe CPF e senha e clique em "Registrar Acesso"
- Depois clique em "Obter Token" (token é salvo no localStorage)

3) Criar usuário e fazer login
- "Novo Usuário" (nome, CPF, nascimento, endereço)
- "Login" com CPF (já autenticado via JWT)

4) Criar conta/operar
- "Criar Conta", "Saldo", "Extrato", "Depositar", "Sacar" etc.

5) Empréstimos
- "Simular", "Contratar", "Pagar Parcela", "Quitar Empréstimo"

6) Chat focado em banco
- Digite comandos (ex: `/saldo`, `/depositar 100`) ou frases como "listar minhas contas"

## Principais rotas (resumo)

Headers comuns:
- `Authorization: Bearer <token>`
- `X-Session-Id: <sessionId>`

Auth e sessão:
- `POST /auth/register` { cpf, password }
- `POST /auth/token` { cpf, password } → { access_token, token_type }
- `GET /session` → { sessionId }
- `GET /health` → { status: "ok" }

Usuário e login:
- `POST /user` { nome, cpf, data_nascimento, endereco }
- `POST /login/{cpf}` → { message }
- `POST /logout` → { message }

Contas e operações:
- `POST /conta` → cria nova conta
- `GET /saldo` → saldo atual (texto)
- `GET /extrato` → extrato (texto)
- `GET /contas` → lista de contas (texto)
- `DELETE /conta/{numero}` → remove conta (com validações)
- `POST /depositar` { valor }
- `POST /sacar` { valor }

Empréstimos:
- `POST /simular_emprestimo` { valor, parcelas, taxa }
- `POST /contratar_emprestimo` { valor, parcelas, taxa }
- `POST /pagar_parcela`
- `POST /quitar_emprestimo`

Chat:
- `POST /chat` { message } → roteia comandos e responde

Observação: As rotas retornam `{"message": "..."}` com textos amigáveis.

## Frontend (recursos)

- Abas de navegação: Autenticação, Conta, Chat e Saída
- Tema claro/escuro com persistência (localStorage)
- Toasts, estados de loading e indicador de servidor online/offline
- Tabela de contas com ação inline de remoção (com modal de confirmação)
- Extrato e saldo renderizados de forma amigável na aba Conta
- Chat com enter‑to‑send e copiar resposta com clique

Caminho: `http://127.0.0.1:8000/app`

## Dicas e problemas comuns

- 401 Unauthorized: gere o token (`/auth/token`) e envie `Authorization: Bearer` nas requisições. Alguns endpoints também exigem sessão via `X-Session-Id`.
- Failed to fetch no frontend: certifique‑se de abrir o frontend em `/app` usando a mesma origem do backend (porta 8000), e que o servidor está online (`/health`).
- Variáveis de ambiente: confira `.env` e reinicie o servidor após alterar.
- Senhas/Hash: uso de `pbkdf2_sha256` (não requer compilação nativa no Windows, ao contrário de bcrypt).
- Gemini opcional: sem `GEMINI_API_KEY` a IA fica desabilitada; o chat funciona com comandos fixos.

## Desenvolvimento

- Recarregamento automático: `--reload` no uvicorn
- Localização dos arquivos do frontend: `frontend/` (servido por `server.py` via `StaticFiles`)
- Código do domínio bancário: `banco.py`
- Serviço de orquestração: `bank_service.py`
- API e roteador de chat: `server.py`

## Licença

Projeto educacional/demonstrativo.
