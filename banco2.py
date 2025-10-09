from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
import textwrap

class Cliente:
    def __init__(self, endereco: str):
        self.endereco: str = endereco
        self.contas: List[Conta] = []
        # Nome do cliente (padrão vazio para evitar None)
        self.nome: str = ""
        # Estrutura de empréstimo, quando contratado
        self.emprestimo: Optional[Dict[str, Any]] = None

    def realizar_transacao(self, conta: "Conta", transacao: "Transacao") -> bool:
        return transacao.registrar(conta)

    def adicionar_conta(self, conta: "Conta") -> None:
        self.contas.append(conta)

class PessoaFisica(Cliente):
    def __init__(self, nome: str, cpf: str, data_nascimento: str, endereco: str):
        super().__init__(endereco)
        self.nome: str = nome
        self.data_nascimento: str = data_nascimento
        self.cpf: str = cpf

class Historico:
    def __init__(self):
        self._transacoes: List[Dict[str, Any]] = []

    @property
    def transacoes(self) -> List[Dict[str, Any]]:
        return self._transacoes

    def adicionar_transacao(self, transacao: "Transacao") -> None:
        self._transacoes.append({
            "tipo": transacao.__class__.__name__,
            "valor": transacao.valor,
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

class Conta:
    def __init__(self, numero: int, cliente: Cliente):
        self._saldo: float = 0.0
        self._numero: int = numero
        self._agencia: str = '0001'
        self._cliente: Cliente = cliente
        self._historico: Historico = Historico()

    @classmethod
    def criar_conta(cls, numero: int, cliente: Cliente) -> "Conta":
        return cls(numero, cliente)
    
    @property
    def saldo(self) -> float:
        return float(self._saldo)
    
    @property
    def numero(self) -> int:
        return self._numero
    
    @property
    def agencia(self) -> str:
        return self._agencia
    
    @property
    def cliente(self) -> Cliente:
        return self._cliente
    
    @property
    def historico(self) -> Historico:
        return self._historico
    
    def sacar(self, valor: float) -> bool:
        excedeu_saldo = valor > self._saldo
        
        if excedeu_saldo:
            print('Operação falhou! Você não tem saldo suficiente.')
        elif valor > 0:
            self._saldo -= valor
            print(f'Saque realizado com sucesso! Novo saldo: {self._saldo}')
            return True
        else:
            print('Operação falhou! O valor informado é inválido.')
        return False
    
    def depositar(self, valor: float) -> bool:
        if valor > 0:
            self._saldo += valor
            print(f'Depósito realizado com sucesso! Novo saldo: {self._saldo}')
            return True
        else:
            print('Operação falhou! O valor informado é inválido.')
            return False

    def debitar_emprestimo(self, valor: float) -> float:
        """Debita um valor diretamente do saldo para quitação de empréstimo.
        Retorna o valor efetivamente debitado (0.0 se não houver saldo).
        """
        if valor > 0 and self._saldo >= valor:
            self._saldo -= valor
            return float(valor)
        return 0.0

class ContaCorrente(Conta):
    def __init__(self, numero: int, cliente: Cliente, limite: float = 1000, limite_saque: int = 3):
        super().__init__(numero, cliente)
        self.limite = limite
        self.limite_saque = limite_saque
        
    def sacar(self, valor: float) -> bool:
        numero_saque = len([transacao for transacao in self.historico.transacoes if transacao["tipo"] == "Saque"])
        excedeu_limite = valor > self.limite
        excedeu_saque = numero_saque >= self.limite_saque

        if excedeu_limite:
            print('Operação falhou! O valor do saque excede o limite da conta.')   
        elif excedeu_saque:
            print('Operação falhou! Você excedeu o número de saques permitidos.') 
        else:
            return super().sacar(valor)
        return False

    def __str__(self) -> str:
        nome_cli = self.cliente.nome if hasattr(self.cliente, "nome") and self.cliente.nome else "N/D"
        return f"""\
agência:\t{self.agencia}
C/C: \t\t{self.numero}
cliente:\t{nome_cli}
"""

class Transacao(ABC):
    @property
    @abstractmethod
    def valor(self) -> float:
        """Valor monetário da transação."""
        raise NotImplementedError

    @abstractmethod
    def registrar(self, conta: "Conta") -> bool:
        """Executa a transação sobre a conta e retorna True em caso de sucesso."""
        raise NotImplementedError

class Saque(Transacao):
    def __init__(self, valor: float):
        self._valor = valor
    
    @property
    def valor(self) -> float:
        return self._valor
    
    def registrar(self, conta: "Conta") -> bool:
        sucesso_transacao = conta.sacar(self._valor)
        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)
        return sucesso_transacao

class Deposito(Transacao):
    def __init__(self, valor: float):
        self._valor = valor
    
    @property
    def valor(self) -> float:
        return self._valor
    
    def registrar(self, conta: "Conta") -> bool:
        sucesso_transacao = conta.depositar(self._valor)
        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)
        return sucesso_transacao

class PagamentoParcelaEmprestimo(Transacao):
    def __init__(self, valor: float):
        self._valor = valor

    @property
    def valor(self) -> float:
        return self._valor

    def registrar(self, conta: "Conta") -> bool:
        # Registrar pagamento de parcela como um saque na conta e adicionar ao histórico
        sucesso_transacao = conta.sacar(self._valor)
        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)
        return sucesso_transacao

class QuitacaoEmprestimo(Transacao):
    def __init__(self, valor: float):
        self._valor = valor

    @property
    def valor(self) -> float:
        return self._valor

    def registrar(self, conta: "Conta") -> bool:
        """Tenta quitar integralmente o empréstimo debitando o valor total.
        Somente registra no histórico se a quitação for total.
        """
        if conta.saldo >= self._valor:
            debited = conta.debitar_emprestimo(self._valor)
            if debited >= self._valor:
                conta.historico.adicionar_transacao(self)
                return True
        return False

def menu() -> str:
    menu = """\n
=========================MENU=========================
    [d]\t Depositar
    [s]\t Sacar
    [e]\t Extrato
    [ec]\t Excluir Conta
    [nc]\t Nova Conta
    [lc]\t Listar Contas
    [nu]\t Novo Usuário
    [emp]\t Simular/Contratar Empréstimo
    [pagp]\t Pagar Parcela do Empréstimo
    [quit]\t Quitar Empréstimo
    [q]\t Sair
"""
    return input(textwrap.dedent(menu))

def main() -> None:
    clientes: List[PessoaFisica] = []
    contas: List[Conta] = []

    cliente_logado: Optional[PessoaFisica] = None

    while True:
        if not cliente_logado:
            print("\nBem-vindo! Escolha uma opção:")
            print("[nu] Novo Usuário")
            print("[q]  Sair")
            print("[login] Fazer login")
            escolha = input("Opção: ").strip().lower()

            if escolha == 'nu':
                criar_cliente(clientes)
                continue
            elif escolha == 'q':
                print("Saindo do sistema...")
                break
            elif escolha == 'login':
                cliente_logado = login(clientes)
                continue
            else:
                print("Opção inválida!")
                continue

        opcao = menu()

        if opcao == 'd':
            depositar(cliente_logado)
        elif opcao == 's':
            sacar(cliente_logado)
        elif opcao == 'e':
            exibir_extrato(cliente_logado)
        elif opcao == 'nc':
            numero_conta = len(contas) + 1
            criar_conta(numero_conta, clientes, contas)
        elif opcao == 'ec':
            excluir_conta(contas, clientes)
        elif opcao == 'lc':
            listar_contas(contas)
        elif opcao == 'nu':
            criar_cliente(clientes)
        elif opcao == 'emp':
            valor = float(input("Valor do empréstimo: "))
            parcelas = int(input("Quantidade de parcelas: "))
            taxa = float(input("Taxa de juros mensal (ex: 0.02 para 2%): "))
            simular_emprestimo(valor, parcelas, taxa)
            contratar = input("Deseja contratar este empréstimo? (s/n): ")
            if contratar == 's':
                contratar_emprestimo(cliente_logado, valor, parcelas, taxa)
        elif opcao == 'pagp':
            pagar_parcela_emprestimo(cliente_logado)
        elif opcao == 'quit':
            quitar_emprestimo(cliente_logado)
        elif opcao == 'q':
            print("Saindo do sistema...")
            break
        elif opcao == 'logout':
            cliente_logado = None

def filtrar_cliente(cpf: str, clientes: List[PessoaFisica]) -> Optional[PessoaFisica]:
    clientes_filtrados = [cliente for cliente in clientes if cliente.cpf == cpf]
    return clientes_filtrados[0] if clientes_filtrados else None

def login(clientes: List[PessoaFisica]) -> Optional[PessoaFisica]:
    cpf = input('Digite o CPF do cliente (somente números): ')
    cliente = filtrar_cliente(cpf, clientes)
    if not cliente:
        print('Cliente não encontrado!')
        return None
    return cliente

def depositar(cliente: PessoaFisica) -> None:
    if not cliente.contas:
        print("Cliente não possui conta. Crie uma conta antes de depositar.")
        return
    valor = float(input('Digite o valor do depósito: '))
    transacao = Deposito(valor)
    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return
    cliente.realizar_transacao(conta, transacao)

def sacar(cliente: PessoaFisica) -> None:
    if not cliente.contas:
        print("Cliente não possui conta. Crie uma conta antes de sacar.")
        return
    valor = float(input('Digite o valor do saque: '))
    transacao = Saque(valor)
    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return
    cliente.realizar_transacao(conta, transacao)

def exibir_extrato(cliente: PessoaFisica) -> None:
    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return
    print("\n=========================EXTRATO=========================")
    transacoes = conta.historico.transacoes
    extrato = ""
    if not transacoes:
        extrato = "Não foram realizadas transações."
    else:
        for transacao in transacoes:
            extrato += f"\n{transacao['tipo']}:\n\tR$ {transacao['valor']:.2f}"
    print(extrato)
    print(f"\nSaldo: R$ {conta.saldo:.2f}")
    print("=========================================================")

def criar_conta(numero: int, clientes: List[PessoaFisica], contas: List[Conta]) -> None:
    cpf = input('Digite o CPF do cliente (somente números): ')
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print('Cliente não encontrado!')
        return
    
    conta = ContaCorrente.criar_conta(cliente=cliente, numero=numero)
    contas.append(conta)
    cliente.contas.append(conta)
    print(f'Conta criada com sucesso! Número da conta: {conta.numero}, Agência: {conta.agencia}')

def listar_contas(contas: List[Conta]) -> None:
    for conta in contas:
        print("=" * 100)
        print(textwrap.dedent(str(conta)))

def excluir_conta(contas: List[Conta], clientes: List[PessoaFisica]) -> None:
    cpf = input('Digite o CPF do cliente (somente números): ')
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print('Cliente não encontrado!')
        return

    if not cliente.contas:
        print("Cliente não possui conta para excluir.")
        return

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    if len(cliente.contas) > 1:
        print("Cliente possui mais de uma conta. Exclua manualmente a conta desejada.")
        return
      
    else:
        print(f"Excluindo conta número {conta.numero} do cliente {cliente.nome} (CPF {cliente.cpf})")
        print(f'Conta excluída com sucesso!')

    contas.remove(conta)
    cliente.contas.remove(conta)
    print(f'Conta número {conta.numero} excluída com sucesso!')

def criar_cliente(clientes: List[PessoaFisica]) -> None:
    cpf = input('Digite o CPF do cliente (somente números): ')
    cliente = filtrar_cliente(cpf, clientes)

    if cliente:
        print('CPF já cadastrado!')
        return
    
    nome = input('Digite o nome completo do cliente: ')
    data_nascimento = input('Digite a data de nascimento do cliente (dd/mm/aaaa): ')
    endereco = input('Digite o endereço do cliente (logradouro, nr - bairro - cidade/sigla do estado): ')

    cliente = PessoaFisica(nome=nome, cpf=cpf, data_nascimento=data_nascimento, endereco=endereco)
    clientes.append(cliente)

    print('Cliente criado com sucesso!')

def contratar_emprestimo(cliente: PessoaFisica, valor: float, parcelas: int, taxa_juros: float) -> None:
    if not cliente.contas:
        print("Cliente não possui conta. Crie uma conta antes de contratar empréstimo.")
        return
    valor_total = valor * (1 + taxa_juros * parcelas)
    valor_parcela = valor_total / parcelas
    cliente.emprestimo = {
        "valor_total": valor_total,
        "parcelas": parcelas,
        "valor_parcela": valor_parcela,
        "parcelas_pagas": 0,
        "saldo_devedor": valor_total
    }
    conta = recuperar_conta_cliente(cliente)
    if conta:
        conta.depositar(valor)
        print(f"Valor de R$ {valor:.2f} depositado na conta referente ao empréstimo.")
    print(f"Empréstimo contratado com sucesso!")
    print(f"Valor total: R$ {valor_total:.2f}")
    print(f"Parcelas: {parcelas} de R$ {valor_parcela:.2f}")

def simular_emprestimo(valor: float, parcelas: int, taxa_juros: float):
    """
    Apenas simula o valor total e o valor de cada parcela do empréstimo.
    Não altera nada no cliente.
    """
    valor_total = valor * (1 + taxa_juros * parcelas)
    valor_parcela = valor_total / parcelas
    print(f"Simulação de Empréstimo:")
    print(f"Valor total: R$ {valor_total:.2f}")
    print(f"Parcelas: {parcelas} de R$ {valor_parcela:.2f}")
    return valor_total, valor_parcela

def calcular_emprestimo(cliente: PessoaFisica, valor: float, parcelas: int, taxa_juros: float) -> None:
    """
    Calcula o valor total do empréstimo e o valor de cada parcela.
    Salva o empréstimo no cliente.
    """
    valor_total = valor * (1 + taxa_juros * parcelas)
    valor_parcela = valor_total / parcelas
    cliente.emprestimo = {
        "valor_total": valor_total,
        "parcelas": parcelas,
        "valor_parcela": valor_parcela,
        "parcelas_pagas": 0,
        "saldo_devedor": valor_total
    }
    print(f"Empréstimo aprovado!\nValor total: R$ {valor_total:.2f}\nParcelas: {parcelas} de R$ {valor_parcela:.2f}")

def pagar_parcela_emprestimo(cliente: PessoaFisica) -> None:
    """
    Paga uma parcela do empréstimo, se houver saldo devedor.
    """
    if not cliente.emprestimo or cliente.emprestimo.get("saldo_devedor", 0) <= 0:
        print("Nenhum empréstimo ativo para este cliente.")
        return

    if cliente.emprestimo.get("parcelas_pagas", 0) >= cliente.emprestimo.get("parcelas", 0):
        print("Todas as parcelas já foram pagas!")
        return

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        print("Cliente não possui conta cadastrada.")
        return

    valor_parcela = float(cliente.emprestimo.get("valor_parcela", 0))

    # Usar a transação para garantir registro no histórico
    transacao = PagamentoParcelaEmprestimo(valor_parcela)
    sucesso = cliente.realizar_transacao(conta, transacao)
    if not sucesso:
        print("Saldo insuficiente para pagar a parcela do empréstimo.")
        return

    # Atualiza estado do empréstimo somente se a transação foi bem sucedida
    cliente.emprestimo["parcelas_pagas"] = cliente.emprestimo.get("parcelas_pagas", 0) + 1
    cliente.emprestimo["saldo_devedor"] = max(0.0, cliente.emprestimo.get("saldo_devedor", 0.0) - valor_parcela)

    print(f"Parcela paga com sucesso! Parcelas pagas: {cliente.emprestimo['parcelas_pagas']}/{cliente.emprestimo['parcelas']}")
    print(f"Saldo devedor atual: R$ {cliente.emprestimo['saldo_devedor']:.2f}")

def quitar_emprestimo(cliente: PessoaFisica) -> None:
    """
    Quita o valor total do empréstimo, considerando parcelas já pagas e saldo disponível.
    Não registra como saque no histórico da conta.
    """
    if not cliente.emprestimo or cliente.emprestimo.get("saldo_devedor", 0) <= 0:
        print("Nenhum empréstimo ativo para este cliente.")
        return

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        print("Cliente não possui conta cadastrada.")
        return

    saldo_devedor = float(cliente.emprestimo.get("saldo_devedor", 0.0))

    # Usar transação de quitação para registrar no histórico
    transacao = QuitacaoEmprestimo(saldo_devedor)
    sucesso = cliente.realizar_transacao(conta, transacao)
    if not sucesso:
        # tentativa parcial de débito
        valor_debitado = conta.debitar_emprestimo(saldo_devedor)
        if valor_debitado > 0:
            cliente.emprestimo["saldo_devedor"] = max(0.0, cliente.emprestimo.get("saldo_devedor", 0.0) - valor_debitado)
            print(f"Foi debitado R$ {valor_debitado:.2f} do saldo. Ainda falta R$ {cliente.emprestimo['saldo_devedor']:.2f} para quitar.")
        else:
            print("Saldo insuficiente para quitar o empréstimo.")
        return

    # Se sucesso, atualiza estado do empréstimo
    cliente.emprestimo["saldo_devedor"] = 0.0
    cliente.emprestimo["parcelas_pagas"] = cliente.emprestimo.get("parcelas", 0)
    print(f"Valor para quitação: R$ {saldo_devedor:.2f}")
    print("Empréstimo quitado com sucesso!")
    print(f"Saldo atual após quitação: R$ {conta.saldo:.2f}")

def recuperar_conta_cliente(cliente: PessoaFisica) -> Optional[Conta]:
    """
    Retorna a primeira conta do cliente, se existir.
    """
    if not cliente.contas:
        print("Cliente não possui conta cadastrada.")
        return None
    return cliente.contas[0]

if __name__ == "__main__":
    main()
