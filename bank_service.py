from __future__ import annotations
from typing import List, Optional

# Reuso das classes e funções do módulo banco
from banco import (
    PessoaFisica,
    Conta,
    ContaCorrente,
    Deposito,
    Saque,
    simular_emprestimo,
    contratar_emprestimo,
    pagar_parcela_emprestimo,
    quitar_emprestimo,
    recuperar_conta_cliente,
    filtrar_cliente,
)

class BankApp:
    """Camada de serviço para operações bancárias em memória.
    Mantém estado simples (clientes, contas e cliente logado).
    """

    def __init__(self) -> None:
        self.clientes: List[PessoaFisica] = []
        self.contas: List[Conta] = []
        self._cliente_logado: Optional[PessoaFisica] = None

    # ---------- Sessão/Autenticação ----------
    def login(self, cpf: str) -> str:
        cliente = filtrar_cliente(cpf, self.clientes)
        if not cliente:
            return "Cliente não encontrado. Crie um novo usuário com /novo_usuario."
        self._cliente_logado = cliente
        return f"Login efetuado como {cliente.nome} (CPF {cliente.cpf})."

    def logout(self) -> str:
        self._cliente_logado = None
        return "Logout realizado."

    # ---------- Cadastro ----------
    def novo_usuario(self, nome: str, cpf: str, data_nascimento: str, endereco: str) -> str:
        existente = filtrar_cliente(cpf, self.clientes)
        if existente:
            return "CPF já cadastrado. Tente /login <cpf> ou use outro CPF."
        cliente = PessoaFisica(nome=nome, cpf=cpf, data_nascimento=data_nascimento, endereco=endereco)
        self.clientes.append(cliente)
        return f"Usuário criado: {nome} (CPF {cpf}). Faça /login {cpf} e /nova_conta."

    # ---------- Contas ----------
    def nova_conta(self) -> str:
        if not self._cliente_logado:
            return "Faça login antes: /login <cpf>."
        numero_conta = len(self.contas) + 1
        conta = ContaCorrente.criar_conta(cliente=self._cliente_logado, numero=numero_conta)
        self.contas.append(conta)
        self._cliente_logado.contas.append(conta)
        return f"Conta criada! Agência {conta.agencia}, Número {conta.numero}."

    def saldo(self) -> str:
        if not self._cliente_logado:
            return "Faça login antes: /login <cpf>."
        conta = recuperar_conta_cliente(self._cliente_logado)
        if not conta:
            return "Você não possui conta. Crie com /nova_conta."
        return f"Saldo atual: R$ {conta.saldo:.2f}."

    def extrato(self) -> str:
        if not self._cliente_logado:
            return "Faça login antes: /login <cpf>."
        conta = recuperar_conta_cliente(self._cliente_logado)
        if not conta:
            return "Você não possui conta. Crie com /nova_conta."
        linhas: List[str] = []
        for t in conta.historico.transacoes:
            linhas.append(f"{t['data']} - {t['tipo']}: R$ {t['valor']:.2f}")
        if not linhas:
            return "Extrato: sem movimentações. " + self.saldo()
        return "Extrato:\n" + "\n".join(linhas) + f"\n{self.saldo()}"

    def listar_contas(self) -> str:
        if not self._cliente_logado:
            return "Faça login antes: /login <cpf>."
        if not self._cliente_logado.contas:
            return "Você não possui conta. Crie com /nova_conta."
        linhas: List[str] = []
        for c in self._cliente_logado.contas:
            linhas.append(str(c))
        return ("Contas do usuário:\n" + ("\n" + ("-"*40) + "\n").join(linhas)).strip()

    # ---------- Movimentações ----------
    def depositar(self, valor: float) -> str:
        if not self._cliente_logado:
            return "Faça login antes: /login <cpf>."
        conta = recuperar_conta_cliente(self._cliente_logado)
        if not conta:
            return "Você não possui conta. Crie com /nova_conta."
        tx = Deposito(valor)
        ok = self._cliente_logado.realizar_transacao(conta, tx)
        if ok:
            return f"Depósito de R$ {valor:.2f} realizado. {self.saldo()}"
        return "Depósito não realizado. Valor inválido?"

    def sacar(self, valor: float) -> str:
        if not self._cliente_logado:
            return "Faça login antes: /login <cpf>."
        conta = recuperar_conta_cliente(self._cliente_logado)
        if not conta:
            return "Você não possui conta. Crie com /nova_conta."
        tx = Saque(valor)
        ok = self._cliente_logado.realizar_transacao(conta, tx)
        if ok:
            return f"Saque de R$ {valor:.2f} realizado. {self.saldo()}"
        return "Saque não realizado. Saldo insuficiente, limite excedido ou valor inválido."

    # ---------- Empréstimos ----------
    def simular_emprestimo(self, valor: float, parcelas: int, taxa: float) -> str:
        if not self._cliente_logado:
            return "Faça login antes: /login <cpf>."
        vt, vp = simular_emprestimo(valor, parcelas, taxa)
        return f"Simulação: total R$ {vt:.2f}; {parcelas} x R$ {vp:.2f} (juros {taxa*100:.2f}% a.m.)."

    def contratar_emprestimo(self, valor: float, parcelas: int, taxa: float) -> str:
        if not self._cliente_logado:
            return "Faça login antes: /login <cpf>."
        contratar_emprestimo(self._cliente_logado, valor, parcelas, taxa)
        return "Empréstimo contratado. " + self.saldo()

    def pagar_parcela(self) -> str:
        if not self._cliente_logado:
            return "Faça login antes: /login <cpf>."
        pagar_parcela_emprestimo(self._cliente_logado)
        return "(Se havia parcela e saldo, pagamento foi processado.)"

    def quitar_emprestimo(self) -> str:
        if not self._cliente_logado:
            return "Faça login antes: /login <cpf>."
        quitar_emprestimo(self._cliente_logado)
        return "(Se havia saldo devedor, tentativa de quitação foi processada.)"

    # ---------- Manutenção de contas ----------
    def remover_conta(self, numero: int) -> str:
        """Remove uma conta do cliente logado com validações:
        - É necessário estar logado
        - Cliente deve possuir mais de uma conta (não remover a última)
        - Conta alvo deve existir e pertencer ao cliente logado
        - Saldo da conta deve ser zero
        - Não pode haver empréstimo ativo (saldo_devedor > 0) no cliente
        """
        if not self._cliente_logado:
            return "Faça login antes: /login <cpf>."

        # Deve manter ao menos uma conta
        if len(self._cliente_logado.contas) <= 1:
            return "Não é possível remover a última conta. Mantenha ao menos uma conta ativa."

        # Localiza a conta pelo número dentro do cliente
        conta_alvo = None
        for c in self._cliente_logado.contas:
            if getattr(c, "numero", None) == numero:
                conta_alvo = c
                break
        if not conta_alvo:
            return f"Conta {numero} não encontrada para o usuário logado."

        # Saldo deve ser zero (com tolerância para ruídos de ponto flutuante)
        saldo_atual = float(getattr(conta_alvo, "saldo", 0.0))
        EPS = 1e-9  # tolerância numérica
        if abs(saldo_atual) > EPS:
            return "Não é possível remover uma conta com saldo. Zere o saldo antes."

        # Empréstimo ativo bloqueia remoção (para evitar inconsistência)
        emp = getattr(self._cliente_logado, "emprestimo", None)
        if emp and float(emp.get("saldo_devedor", 0.0)) > 0.0:
            return "Existe empréstimo ativo. Quite ou pague o saldo devedor antes de remover contas."

        # Remove da lista de contas do cliente
        self._cliente_logado.contas = [c for c in self._cliente_logado.contas if getattr(c, "numero", None) != numero]
        # Remove também do registro global de contas da aplicação
        self.contas = [c for c in self.contas if getattr(c, "numero", None) != numero]

        return f"Conta {numero} removida com sucesso."

def help_text() -> str:
    return (
        "Comandos disponíveis:\n"
        "/help — mostra esta ajuda\n"
        "/novo_usuario — cadastra novo usuário (vai perguntar dados)\n"
        "/login <cpf> — autentica usuário\n"
        "/logout — encerra sessão\n"
        "/nova_conta — cria conta corrente\n"
        "/listar_contas — exibe contas do usuário\n"
        "/remover_conta <numero> — remove uma conta sem saldo e sem empréstimo ativo\n"
        "/saldo — exibe saldo\n"
        "/extrato — exibe extrato\n"
        "/depositar <valor> — faz depósito\n"
        "/sacar <valor> — faz saque\n"
        "/simular_emprestimo <valor> <parcelas> <taxa> — simula\n"
        "/contratar_emprestimo <valor> <parcelas> <taxa> — contrata e deposita\n"
        "/pagar_parcela — paga 1 parcela (se houver)\n"
        "/quitar_emprestimo — tenta quitar total\n"
        "/exit — sai do chat\n"
    )
