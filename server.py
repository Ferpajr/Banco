from __future__ import annotations
import os
import uuid
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from jose import JWTError, jwt  # type: ignore
from passlib.context import CryptContext  # type: ignore
from fastapi.security import OAuth2PasswordBearer

# .env
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

# Gemini
try:
    import google.generativeai as genai  # type: ignore
except Exception:
    genai = None  # type: ignore

from bank_service import BankApp, help_text

def _get_api_key() -> Optional[str]:
    return os.getenv("GEMINI_API_KEY")

def _setup_gemini() -> Optional[Any]:
    if genai is None:
        return None
    key = _get_api_key()
    if not key:
        return None
    try:
        genai.configure(api_key=key)  # type: ignore[attr-defined]
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")
        return genai.GenerativeModel(model_name)  # type: ignore[attr-defined]
    except Exception:
        return None

app = FastAPI(title="Banco + ChatBot API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sessões simples em memória (apenas demo)
SESSIONS: Dict[str, BankApp] = {}
MODEL = _setup_gemini()
USERS: Dict[str, Dict[str, str]] = {}  # {cpf: {"hashed_password": str}}

# Auth/JWT config
SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

class NewUser(BaseModel):
    nome: str
    cpf: str
    data_nascimento: str
    endereco: str

class Amount(BaseModel):
    valor: float

class Loan(BaseModel):
    valor: float
    parcelas: int
    taxa: float

class ChatMsg(BaseModel):
    message: str
    
class ContaId(BaseModel):
    numero: int

def _get_bank(session_id: Optional[str]) -> BankApp:
    if not session_id or session_id not in SESSIONS:
        # cria nova sessão
        sid = session_id or str(uuid.uuid4())
        SESSIONS[sid] = BankApp()
        return SESSIONS[sid]
    return SESSIONS[session_id]

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any]) -> str:
    from datetime import datetime, timedelta, timezone

    to_encode = data.copy()
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        cpf: Optional[str] = payload.get("sub")
        if cpf is None:
            raise HTTPException(401, "Token inválido")
        if cpf not in USERS:
            raise HTTPException(401, "Usuário não encontrado")
        return cpf
    except JWTError:
        raise HTTPException(401, "Token inválido/expirado")

class AuthRegister(BaseModel):
    cpf: str
    password: str

class AuthLogin(BaseModel):
    cpf: str
    password: str

@app.get("/session")
def new_session() -> Dict[str, str]:
    sid = str(uuid.uuid4())
    SESSIONS[sid] = BankApp()
    return {"sessionId": sid}

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.post("/auth/register")
def auth_register(payload: AuthRegister) -> Dict[str, str]:
    try:
        if not payload.cpf or not payload.password:
            raise HTTPException(400, "CPF e senha são obrigatórios")
        if payload.cpf in USERS:
            raise HTTPException(409, "Usuário já existe")
        USERS[payload.cpf] = {"hashed_password": get_password_hash(payload.password)}
        return {"message": "Usuário de acesso registrado com sucesso."}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, f"Falha ao registrar acesso: {exc}")

@app.post("/auth/token")
def auth_token(payload: AuthLogin) -> Dict[str, str]:
    user = USERS.get(payload.cpf)
    if not user or not verify_password(payload.password, user.get("hashed_password", "")):
        raise HTTPException(401, "CPF ou senha inválidos")
    token = create_access_token({"sub": payload.cpf})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/user")
def create_user(payload: NewUser, x_session_id: Optional[str] = Header(None)) -> Dict[str, str]:
    """Cria um usuário do domínio bancário sem exigir JWT.
    Se não houver `X-Session-Id`, cria uma sessão e a retorna para o cliente persistir.
    """
    if not x_session_id or x_session_id not in SESSIONS:
        sid = x_session_id or str(uuid.uuid4())
        SESSIONS[sid] = BankApp()
        bank = SESSIONS[sid]
        msg = bank.novo_usuario(payload.nome, payload.cpf, payload.data_nascimento, payload.endereco)
        return {"message": msg, "sessionId": sid}
    bank = SESSIONS[x_session_id]
    msg = bank.novo_usuario(payload.nome, payload.cpf, payload.data_nascimento, payload.endereco)
    return {"message": msg}

@app.post("/login/{cpf}")
def login(cpf: str, x_session_id: Optional[str] = Header(None), current_user: str = Depends(get_current_user)) -> Dict[str, str]:
    bank = _get_bank(x_session_id)
    msg = bank.login(cpf)
    return {"message": msg}

@app.post("/logout")
def logout(x_session_id: Optional[str] = Header(None), current_user: str = Depends(get_current_user)) -> Dict[str, str]:
    bank = _get_bank(x_session_id)
    msg = bank.logout()
    return {"message": msg}

@app.post("/conta")
def nova_conta(x_session_id: Optional[str] = Header(None), current_user: str = Depends(get_current_user)) -> Dict[str, str]:
    bank = _get_bank(x_session_id)
    return {"message": bank.nova_conta()}

@app.get("/saldo")
def saldo(x_session_id: Optional[str] = Header(None), current_user: str = Depends(get_current_user)) -> Dict[str, str]:
    bank = _get_bank(x_session_id)
    return {"message": bank.saldo()}

@app.get("/extrato")
def extrato(x_session_id: Optional[str] = Header(None), current_user: str = Depends(get_current_user)) -> Dict[str, str]:
    bank = _get_bank(x_session_id)
    return {"message": bank.extrato()}

@app.get("/contas")
def listar_contas(x_session_id: Optional[str] = Header(None), current_user: str = Depends(get_current_user)) -> Dict[str, str]:
    bank = _get_bank(x_session_id)
    return {"message": bank.listar_contas()}

@app.post("/depositar")
def depositar(payload: Amount, x_session_id: Optional[str] = Header(None), current_user: str = Depends(get_current_user)) -> Dict[str, str]:
    bank = _get_bank(x_session_id)
    return {"message": bank.depositar(payload.valor)}

@app.post("/sacar")
def sacar(payload: Amount, x_session_id: Optional[str] = Header(None), current_user: str = Depends(get_current_user)) -> Dict[str, str]:
    bank = _get_bank(x_session_id)
    return {"message": bank.sacar(payload.valor)}

@app.delete("/conta/{numero}")
def remover_conta(numero: int, x_session_id: Optional[str] = Header(None), current_user: str = Depends(get_current_user)) -> Dict[str, str]:
    bank = _get_bank(x_session_id)
    return {"message": bank.remover_conta(numero)}

@app.post("/simular_emprestimo")
def simular_emprestimo(payload: Loan, x_session_id: Optional[str] = Header(None), current_user: str = Depends(get_current_user)) -> Dict[str, str]:
    bank = _get_bank(x_session_id)
    return {"message": bank.simular_emprestimo(payload.valor, payload.parcelas, payload.taxa)}

@app.post("/contratar_emprestimo")
def contratar_emprestimo(payload: Loan, x_session_id: Optional[str] = Header(None), current_user: str = Depends(get_current_user)) -> Dict[str, str]:
    bank = _get_bank(x_session_id)
    return {"message": bank.contratar_emprestimo(payload.valor, payload.parcelas, payload.taxa)}

@app.post("/pagar_parcela")
def pagar_parcela(x_session_id: Optional[str] = Header(None), current_user: str = Depends(get_current_user)) -> Dict[str, str]:
    bank = _get_bank(x_session_id)
    return {"message": bank.pagar_parcela()}

@app.post("/quitar_emprestimo")
def quitar_emprestimo(x_session_id: Optional[str] = Header(None), current_user: str = Depends(get_current_user)) -> Dict[str, str]:
    bank = _get_bank(x_session_id)
    return {"message": bank.quitar_emprestimo()}

@app.post("/chat")
def chat(payload: ChatMsg, x_session_id: Optional[str] = Header(None), current_user: str = Depends(get_current_user)) -> Dict[str, str]:
    """Chat focado no banco: primeiro tenta interpretar comandos/intenções e executar no BankApp.
    Fallback: usar LLM com um prompt restrito ao domínio bancário.
    """
    bank = _get_bank(x_session_id)
    text = payload.message.strip()

    # 1) Comandos explícitos com barra
    import shlex
    parts = shlex.split(text)
    if parts:
        cmd = parts[0].lower()
        args = parts[1:]
        try:
            if cmd in {"/help", "help"}:
                return {"message": help_text()}
            if cmd in {"/listar_contas", "listar_contas"}:
                return {"message": bank.listar_contas()}
            if cmd in {"/login", "login"} and len(args) >= 1:
                return {"message": bank.login(args[0])}
            if cmd in {"/logout", "logout"}:
                return {"message": bank.logout()}
            if cmd in {"/remover_conta", "remover_conta"} and len(args) >= 1:
                try:
                    numero = int(args[0])
                except ValueError:
                    return {"message": "Uso: /remover_conta <numero> (número da conta)"}
                return {"message": bank.remover_conta(numero)}
            if cmd in {"/nova_conta", "nova_conta"}:
                return {"message": bank.nova_conta()}
            if cmd in {"/saldo", "saldo"}:
                return {"message": bank.saldo()}
            if cmd in {"/extrato", "extrato"}:
                return {"message": bank.extrato()}
            if cmd in {"/depositar", "depositar"} and len(args) >= 1:
                valor = float(str(args[0]).replace(',', '.'))
                return {"message": bank.depositar(valor)}
            if cmd in {"/sacar", "sacar"} and len(args) >= 1:
                valor = float(str(args[0]).replace(',', '.'))
                return {"message": bank.sacar(valor)}
            if cmd in {"/simular_emprestimo", "simular_emprestimo"} and len(args) >= 3:
                valor = float(str(args[0]).replace(',', '.'))
                parcelas = int(args[1])
                taxa = float(str(args[2]).replace(',', '.'))
                return {"message": bank.simular_emprestimo(valor, parcelas, taxa)}
            if cmd in {"/contratar_emprestimo", "contratar_emprestimo"} and len(args) >= 3:
                valor = float(str(args[0]).replace(',', '.'))
                parcelas = int(args[1])
                taxa = float(str(args[2]).replace(',', '.'))
                return {"message": bank.contratar_emprestimo(valor, parcelas, taxa)}
            if cmd in {"/pagar_parcela", "pagar_parcela"}:
                return {"message": bank.pagar_parcela()}
            if cmd in {"/quitar_emprestimo", "quitar_emprestimo"}:
                return {"message": bank.quitar_emprestimo()}
        except Exception as exc:
            return {"message": f"Não consegui executar o comando. Erro: {exc}"}

    # 2) Heurísticas simples de intenção sem barra
    t = text.lower()
    try:
        if "saldo" in t:
            return {"message": bank.saldo()}
        if "extrato" in t:
            return {"message": bank.extrato()}
        if ("listar" in t or "mostrar" in t) and "conta" in t:
            return {"message": bank.listar_contas()}
        if "deposit" in t or "depositar" in t:
            import re
            m = re.search(r"(\d+[\.,]?\d*)", t)
            if m:
                valor = float(m.group(1).replace(',', '.'))
                return {"message": bank.depositar(valor)}
        if "sac" in t:  # saque/sacar
            import re
            m = re.search(r"(\d+[\.,]?\d*)", t)
            if m:
                valor = float(m.group(1).replace(',', '.'))
                return {"message": bank.sacar(valor)}
        if "simul" in t and "emprest" in t:
            import re
            nums = re.findall(r"\d+[\.,]?\d*", t)
            if len(nums) >= 3:
                valor = float(nums[0].replace(',', '.'))
                parcelas = int(float(nums[1]))
                taxa = float(nums[2].replace(',', '.'))
                return {"message": bank.simular_emprestimo(valor, parcelas, taxa)}
    except Exception:
        pass

    # 3) Fallback: LLM focado no domínio bancário
    if MODEL is None:
        return {"message": (
            "comandos do banco (ex: /help, /saldo, /extrato, /depositar 100)."
        )}
    try:
        system = (
            "Você é um assistente bancário para um banco virtual com comandos fixos. "
            "Seja objetivo, responda em pt-br. Quando possível, oriente a usar os comandos: "
            "/help, /login <cpf>, /logout, /nova_conta, /saldo, /extrato, /depositar <valor>, /sacar <valor>, "
            "/simular_emprestimo <valor> <parcelas> <taxa>, /contratar_emprestimo <valor> <parcelas> <taxa>, "
            "/pagar_parcela, /quitar_emprestimo. Não fale de assuntos que não sejam bancários."
        )
        prompt = f"{system}\nUsuário: {payload.message}\nAssistente:"
        resp = MODEL.generate_content(prompt)  # type: ignore[attr-defined]
        text = getattr(resp, "text", str(resp))
        return {"message": text}
    except Exception as exc:
        return {"message": f"Falha no chat: {exc}"}

# Servir o frontend estático em /app
app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")
