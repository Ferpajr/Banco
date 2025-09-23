from abc import ABC, abstractmethod
from datetime import datetime
import textwrap


class Cliente:
    def __init__(self, endereco):
        self.endereco = endereco
        self.contas = []

    def realizar_transacao(self, conta, transacao):
        return transacao.registrar(conta)

    def adicionar_conta(self, conta):
        self.contas.append(conta)

class PessoaFisica(Cliente):
    def __init__(self, nome, cpf, data_nascimento, endereco):
        super().__init__(endereco)
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.cpf = cpf

class Historico:
    def __init__(self):
        self._transacoes = []

    @property
    def transacoes(self):
        return self._transacoes

    def adicionar_transacao(self, transacao):
        self._transacoes.append({
            "tipo": transacao.__class__.__name__,
            "valor": transacao.valor,
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

class Conta:
    def __init__(self, numero, cliente):
        self._saldo = 0
        self._numero = numero
        self._agencia = '0001'
        self._cliente = cliente
        self._historico = Historico()

    @classmethod
    def criar_conta(cls, numero, cliente):
        return cls(numero, cliente)
    
    @property
    def saldo(self):
        return self._saldo
    
    @property
    def numero(self):
        return self._numero
    
    @property
    def agencia(self):
        return self._agencia
    
    @property
    def cliente(self):
        return self._cliente
    
    @property
    def historico(self):
        return self._historico
    
    def sacar(self, valor):
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
    
    def depositar(self, valor):
        if valor > 0:
            self._saldo += valor
            print(f'Depósito realizado com sucesso! Novo saldo: {self._saldo}')
            return True
        else:
            print('Operação falhou! O valor informado é inválido.')
            return False

    def debitar_emprestimo(self, valor):
        if valor > 0 and self._saldo >= valor:
            self._saldo -= valor
            return True
        return False

class ContaCorrente(Conta):
    def __init__(self, numero, cliente, limite=1000, limite_saque=3):
        super().__init__(numero, cliente)
        self.limite = limite
        self.limite_saque = limite_saque
        
    def sacar(self, valor):
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

    def __str__(self):
        return f"""\
agência:\t{self.agencia}
C/C: \t\t{self.numero}
cliente:\t{self.cliente.nome}
"""

class Transacao(ABC):
    @property
    @abstractmethod
    def valor(self):
        pass
    
    @classmethod
    @abstractmethod
    def registrar(cls, conta):
        pass

class Saque(Transacao):
    def __init__(self, valor):
        self._valor = valor
    
    @property
    def valor(self):
        return self._valor
    
    def registrar(self, conta):
        sucesso_transacao = conta.sacar(self._valor)
        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)
        return sucesso_transacao

class Deposito(Transacao):
    def __init__(self, valor):
        self._valor = valor
    
    @property
    def valor(self):
        return self._valor
    
    def registrar(self, conta):
        sucesso_transacao = conta.depositar(self._valor)
        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)
        return sucesso_transacao

class PagamentoParcelaEmprestimo(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        # Registrar pagamento de parcela como um saque na conta e adicionar ao histórico
        sucesso_transacao = conta.sacar(self._valor)
        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)
        return sucesso_transacao

class QuitacaoEmprestimo(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        # Registrar quitação do empréstimo como débito direto (se houver saldo) e adicionar ao histórico
        sucesso_transacao = conta.debitar_emprestimo(self._valor)
        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)
        return sucesso_transacao

def menu():
    menu = """\n
=========================MENU=========================
    [d]\t Depositar
    [s]\t Sacar
    [e]\t Extrato
    [nc]\t Nova Conta
    [lc]\t Listar Contas
    [nu]\t Novo Usuário
    [emp]\t Simular/Contratar Empréstimo
    [pagp]\t Pagar Parcela do Empréstimo
    [quit]\t Quitar Empréstimo
    [q]\t Sair
"""
    return input(textwrap.dedent(menu))

def main():
    clientes = []
    contas = []

    cliente_logado = None

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

def filtrar_cliente(cpf, clientes):
    clientes_filtrados = [cliente for cliente in clientes if cliente.cpf == cpf]
    return clientes_filtrados[0] if clientes_filtrados else None

def login(clientes):
    cpf = input('Digite o CPF do cliente (somente números): ')
    cliente = filtrar_cliente(cpf, clientes)
    if not cliente:
        print('Cliente não encontrado!')
        return None
    return cliente

def depositar(cliente):
    if not cliente.contas:
        print("Cliente não possui conta. Crie uma conta antes de depositar.")
        return
    valor = float(input('Digite o valor do depósito: '))
    transacao = Deposito(valor)
    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return
    cliente.realizar_transacao(conta, transacao)

def sacar(cliente):
    if not cliente.contas:
        print("Cliente não possui conta. Crie uma conta antes de sacar.")
        return
    valor = float(input('Digite o valor do saque: '))
    transacao = Saque(valor)
    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return
    cliente.realizar_transacao(conta, transacao)

def exibir_extrato(cliente):
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

def criar_conta(numero, clientes, contas):
    cpf = input('Digite o CPF do cliente (somente números): ')
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print('Cliente não encontrado!')
        return
    
    conta = ContaCorrente.criar_conta(cliente=cliente, numero=numero)
    contas.append(conta)
    cliente.contas.append(conta)
    print(f'Conta criada com sucesso! Número da conta: {conta.numero}, Agência: {conta.agencia}')

def listar_contas(contas):
    for conta in contas:
        print("=" * 100)
        print(textwrap.dedent(str(conta)))

def criar_cliente(clientes):
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

def contratar_emprestimo(cliente, valor, parcelas, taxa_juros):
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

def simular_emprestimo(valor, parcelas, taxa_juros):
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

def calcular_emprestimo(cliente, valor, parcelas, taxa_juros):
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

def pagar_parcela_emprestimo(cliente):
    """
    Paga uma parcela do empréstimo, se houver saldo devedor.
    """
    if not hasattr(cliente, "emprestimo") or cliente.emprestimo["saldo_devedor"] <= 0:
        print("Nenhum empréstimo ativo para este cliente.")
        return

    if cliente.emprestimo["parcelas_pagas"] >= cliente.emprestimo["parcelas"]:
        print("Todas as parcelas já foram pagas!")
        return

    conta = recuperar_conta_cliente(cliente)
    valor_parcela = cliente.emprestimo["valor_parcela"]

    # Usar a transação para garantir registro no histórico
    transacao = PagamentoParcelaEmprestimo(valor_parcela)
    sucesso = cliente.realizar_transacao(conta, transacao)
    if not sucesso:
        print("Saldo insuficiente para pagar a parcela do empréstimo.")
        return

    # Atualiza estado do empréstimo somente se a transação foi bem sucedida
    cliente.emprestimo["parcelas_pagas"] += 1
    cliente.emprestimo["saldo_devedor"] -= valor_parcela
    if cliente.emprestimo["saldo_devedor"] < 0:
        cliente.emprestimo["saldo_devedor"] = 0

    print(f"Parcela paga com sucesso! Parcelas pagas: {cliente.emprestimo['parcelas_pagas']}/{cliente.emprestimo['parcelas']}")
    print(f"Saldo devedor atual: R$ {cliente.emprestimo['saldo_devedor']:.2f}")

def quitar_emprestimo(cliente):
    """
    Quita o valor total do empréstimo, considerando parcelas já pagas e saldo disponível.
    Não registra como saque no histórico da conta.
    """
    if not hasattr(cliente, "emprestimo") or cliente.emprestimo["saldo_devedor"] <= 0:
        print("Nenhum empréstimo ativo para este cliente.")
        return

    conta = recuperar_conta_cliente(cliente)
    saldo_devedor = cliente.emprestimo["saldo_devedor"]

    # Usar transação de quitação para registrar no histórico
    transacao = QuitacaoEmprestimo(saldo_devedor)
    sucesso = cliente.realizar_transacao(conta, transacao)
    if not sucesso:
        # tentativa parcial de debitar: debitar_emprestimo retorna False se não houver saldo suficiente
        valor_debitado = conta.debitar_emprestimo(saldo_devedor)
        if valor_debitado:
            cliente.emprestimo["saldo_devedor"] -= valor_debitado
            print(f"Foi debitado R$ {valor_debitado:.2f} do saldo. Ainda falta R$ {cliente.emprestimo['saldo_devedor']:.2f} para quitar.")
        else:
            print("Saldo insuficiente para quitar o empréstimo.")
        return

    # Se sucesso, atualiza estado do empréstimo
    cliente.emprestimo["saldo_devedor"] = 0
    cliente.emprestimo["parcelas_pagas"] = cliente.emprestimo["parcelas"]
    print(f"Valor para quitação: R$ {saldo_devedor:.2f}")
    print("Empréstimo quitado com sucesso!")
    print(f"Saldo atual após quitação: R$ {conta.saldo:.2f}")

def recuperar_conta_cliente(cliente):
    """
    Retorna a primeira conta do cliente, se existir.
    """
    if not cliente.contas:
        print("Cliente não possui conta cadastrada.")
        return None
    return cliente.contas[0]

if __name__ == "__main__":
    main()
