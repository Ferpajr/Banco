import textwrap

def menu():
    menu = """\n
    [s] sacar
    [d] depositar
    [cs] consultar saldo
    [ce] consultar extrato
    [cep] Calcular emprestimo
    [fe] Fazer emprestimo
    [pp] Pagar parcela do emprestimo
    [pte] Pagar todo o emprestimo
    [nu] Novo usuário
    [fu] Filtrar usuário
    [cc] Criar conta
    [lc] Listar contas
    [e] sair
     => """
    return input(textwrap.dedent(menu))

def sacar(*,saldo,valor,extrato,limite,numero_saque,limite_saque):
    excedeu_saldo = valor > saldo
    excedeu_limite = valor > limite
    excedeu_limite_saque = numero_saque >= limite_saque

    if excedeu_saldo:
        print('operacao invalida: saldo insuficiente')

    elif excedeu_limite:
        print('operacao invalida: o valor do saque excede o limite')

    elif excedeu_limite_saque:
        print('operacao invalida: voce excedeu o limite de saques')

    elif valor > 0:
        saldo -= valor
        extrato += f'Saque de R$ {valor:.2f}\n'
        numero_saque += 1
        print('Saque efetuado com sucesso!')

    else:
        print('operacao invalida: valor inválido!')
    return saldo,extrato,numero_saque

def depositar(*,saldo,deposito,extrato):
    if deposito > 0:
        saldo += deposito
        extrato += f'Depósito de R$ {deposito:.2f}\n'
        print('Depósito efetuado com sucesso!')
    else:
        print('Valor inválido!')
    return saldo,extrato

def consultar_saldo(*,saldo):
    print(f'Seu saldo é de R$ {saldo:.2f}')

def consultar_extrato(*,extrato,saldo):
    print('\n========== EXTRATO ==========\n')
    print(extrato if extrato else 'Não foram realizadas movimentações.')
    print(f'\nSaldo atual: R$ {saldo:.2f}')
    print('==============================')

def calcular_emprestimo(*,valor_emprestimo,taxa_juros_anual,anos_pagamento):
    valor_total = valor_emprestimo * (1 + taxa_juros_anual) ** anos_pagamento
    parcela_mensal = valor_total / (anos_pagamento * 12)
    return valor_total,parcela_mensal

def fazer_emprestimo(*,saldo,valor_emprestimo,taxa_juros_anual,anos_pagamento):
    valor_total = valor_emprestimo * (1 + taxa_juros_anual) ** anos_pagamento
    parcela_mensal = valor_total / (anos_pagamento * 12)
    saldo += valor_emprestimo
    print('Empréstimo efetuado com sucesso!')
    print(f'Seu saldo é de R$ {saldo:.2f}')
    return saldo,valor_total,parcela_mensal

def pagar_parcela_emprestimo(*,saldo,parcela_mensal,extrato):
    saldo -= parcela_mensal
    extrato += f'Pagamento de parcela de R$ {parcela_mensal:.2f}\n'
    print('Parcela paga com sucesso!')
    print(f'Seu saldo é de R$ {saldo:.2f}')
    return saldo,extrato

def pagar_todo_emprestimo(*,saldo,valor_total,parcelas_pagas,parcela_mensal,extrato):
    valor_restante = valor_total - (parcelas_pagas * parcela_mensal)
    saldo -= valor_restante
    extrato += f'Pagamento total do empréstimo de R$ {valor_restante:.2f}\n'
    print('Pagamento total do empréstimo efetuado com sucesso!')
    print(f'Seu saldo é de R$ {saldo:.2f}')
    return saldo,extrato

def novo_usuario(usuarios):
    cpf = input('Digite o CPF (somente numeros): ')
    usuario = filtrar_usuario(usuarios,cpf)
    if usuario:
        print('CPF já cadastrado!')
        return
    nome = input('Digite o seu nome completo: ')
    data_nascimento = input('Digite a sua data de nascimento (dd/mm/aaaa): ')
    email = input('Digite o seu email: ')
    endereco = input('Digite o seu endereco (logradouro, nr - bairro - cidade/sigla do estado): ')
    telefone = input('Digite o seu telefone (xx) xxxx-xxxx: ')
    senha = input('Digite a sua senha: ')
    usuarios.append({'cpf':cpf,'nome':nome,'data_nascimento':data_nascimento,'email':email,'endereco':endereco,'telefone':telefone,'senha':senha})
    print('Usuário criado com sucesso!')

def filtrar_usuario(usuarios, cpf):
    for usuario in usuarios:
        if usuario['cpf'] == cpf:
            return usuario
    return None

def criar_conta(agencia, usuarios, contador_contas):
    cpf = input('Digite o CPF do usuário (somente numeros): ')
    usuario = filtrar_usuario(usuarios,cpf)
    if not usuario:
        print('Usuário não encontrado!')
        return
    numero_conta = f"{contador_contas:06d}"  # Gera um número de conta com 6 dígitos
    conta = {'agencia':agencia,'numero_conta':numero_conta,'cpf':cpf,'saldo':0,'extrato':'','numero_saques':0,'limite_saque':3,'limite':500,'valor_emprestimo':0,'anos_pagamento':0,'parcela_mensal':0,'valor_total':0,'parcelas_pagas':0}
    return conta

def listar_contas(contas):
    for conta in contas:
        linha =f"""\ 
        Agência: {conta['agencia']}
        Número da conta: {conta['numero_conta']}
        titular: {conta['cpf']}
        """
        print("=" * 100)
        print(textwrap.dedent(linha))

def main():
    saldo = 0
    opcao = -1
    limite = 500
    extrato = ""
    numero_saques = 0
    limite_saque = 3
    valor_emprestimo = 0
    anos_pagamento = 0
    parcela_mensal = 0
    valor_total = 0
    parcelas_pagas = 0
    usuarios = []
    contas = []
    agencia = '0001'
    contador_contas = 1

    while True:
        opcao = menu()

        if opcao == 's':
            valor = float(input('Digite o valor do saque: '))
            saldo,extrato,numero_saques = sacar(saldo=saldo,valor=valor,extrato=extrato,limite=limite,numero_saque=numero_saques,limite_saque=limite_saque)
    
        elif opcao == 'd':
            deposito = float(input('Digite o valor do depósito: '))
            saldo,extrato = depositar(saldo=saldo,deposito=deposito,extrato=extrato)
        
        elif opcao == 'cs':
            consultar_saldo(saldo=saldo)

        elif opcao == 'ce':
            consultar_extrato(extrato=extrato,saldo=saldo)
        
        elif opcao == 'cep':
            valor_emprestimo_consulta = float(input('Digite o valor do empréstimo: '))
            taxa_juros_anual = 7.91 / 100
            anos_pagamento_consulta = int(input('Digite a quantidade de anos para pagamento: '))
            valor_total_consulta,parcela_mensal_consulta = calcular_emprestimo(valor_emprestimo=valor_emprestimo_consulta,taxa_juros_anual=taxa_juros_anual,anos_pagamento=anos_pagamento_consulta)
            print(f'O valor total a ser pago no fim do empréstimo é de R$ {valor_total_consulta:.2f}')
            print(f'O valor da parcela mensal é de R$ {parcela_mensal_consulta:.2f}')
        
        elif opcao == 'fe':
            valor_emprestimo = float(input('Digite o valor do empréstimo: '))
            taxa_juros_anual = 7.91 / 100
            anos_pagamento = int(input('Digite a quantidade de anos para pagamento: '))
            saldo,valor_total,parcela_mensal = fazer_emprestimo(saldo=saldo,valor_emprestimo=valor_emprestimo,taxa_juros_anual=taxa_juros_anual,anos_pagamento=anos_pagamento)
        
        elif opcao == 'pp':
            saldo,extrato = pagar_parcela_emprestimo(saldo=saldo,parcela_mensal=parcela_mensal,extrato=extrato)
        
        elif opcao == 'pte':
            saldo,extrato = pagar_todo_emprestimo(saldo=saldo,valor_total=valor_total,parcelas_pagas=parcelas_pagas,parcela_mensal=parcela_mensal,extrato=extrato)
        
        elif opcao == 'nu':
            novo_usuario(usuarios)
        
        elif opcao == 'fu':
            cpf = input('Digite o CPF (somente numeros): ')
            usuario = filtrar_usuario(usuarios, cpf)
            if usuario:
                print(f'Usuário encontrado: {usuario}')
            else:
                print('Usuário não encontrado!')
        
        elif opcao == 'cc':
            conta = criar_conta(agencia, usuarios, contador_contas)
            if conta:
                contas.append(conta)
                contador_contas += 1
                print('Conta criada com sucesso!')
        
        elif opcao == 'lc':
            listar_contas(contas)
        
        elif opcao == 'e':
            break

if __name__ == "__main__":
    main()





