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

while True:
    
    opcao = int(input('[1] sacar\n[2] depositar\n[3] consultar saldo\n[4] consultar extrato\n[5] Calcular emprestimo\n[6] Fazer emprestimo\n[7] Pagar parcela do emprestimo\n[8] Pagar todo o emprestimo\n[0] sair\n:'))

    if opcao == 1:
        valor = float(input('Digite o valor do saque: '))

        excedeu_saldo = valor > saldo

        excedeu_limite = valor > limite

        excedeu_limite_saque = numero_saques >= limite_saque

        if excedeu_saldo:
            print('operacao invalida: saldo insuficiente')

        elif excedeu_limite:
            print('operacao invalida: o valor do saque excede o limite')

        elif excedeu_limite_saque:
            print('operacao invalida: voce excedeu o limite de saques')


        elif valor > 0:
            saldo -= valor
            extrato += f'Saque de R$ {valor:.2f}\n'
            numero_saques += 1
            print('Saque efetuado com sucesso!')

        else:
            print('operacao invalida: valor inválido!')
    
    elif opcao == 2:
        deposito = float(input('Digite o valor do depósito: '))
        if deposito > 0:
            saldo += deposito
            extrato += f'Depósito de R$ {deposito:.2f}\n'
            print('Depósito efetuado com sucesso!')
        else:
            print('Valor inválido!')
   
    elif opcao == 3:
        print(f'Seu saldo é de R$ {saldo:.2f}')

    elif opcao == 4:
        print('\n========== EXTRATO ==========\n')
        print('Não foram realizadas movimentacoes.' if not extrato else extrato)
        print(f'Saldo atual: R$ {saldo:.2f}')
        print('\n=============================\n')
    
    elif opcao == 5:
        valor_emprestimo_consulta = float(input('Digite o valor do empréstimo: '))
        taxa_juros_anual = 7.91 / 100
        anos_pagamento_consulta = int(input('Digite a quantidade de anos para pagamento: '))

        #calcular o valor total a ser pago no fim do emprestimo
        valor_total_consulta = valor_emprestimo_consulta * (1 + taxa_juros_anual) ** anos_pagamento_consulta
        print(f'O valor total a ser pago no fim do empréstimo é de R$ {valor_total_consulta:.2f}')
        parcela_mensal_consulta = valor_total_consulta / (anos_pagamento_consulta * 12)
        print(f'O valor da parcela mensal é de R$ {parcela_mensal_consulta:.2f}')
    
    elif opcao == 6:
        valor_emprestimo = float(input('Digite o valor do empréstimo: '))
        taxa_juros_anual = 7.91 / 100
        anos_pagamento = int(input('Digite a quantidade de anos para pagamento: '))

        #calcular o valor total a ser pago no fim do emprestimo
        valor_total = valor_emprestimo * (1 + taxa_juros_anual) ** anos_pagamento
        parcela_mensal = valor_total / (anos_pagamento * 12)
        parcelas_pagas = 0

        saldo += valor_emprestimo
        extrato += f'Empréstimo de R$ {valor_emprestimo:.2f}\n'
        print('Empréstimo efetuado com sucesso!')
        print(f'Seu saldo é de R$ {saldo:.2f}')
    
    elif opcao == 7:
        if parcela_mensal > 0:
            saldo -= parcela_mensal
            extrato += f'Pagamento de parcela de R$ {parcela_mensal:.2f}\n'
            parcelas_pagas += 1
            print('Parcela paga com sucesso!')
            print(f'Seu saldo é de R$ {saldo:.2f}')
        else:
            print('Você não possui parcelas para pagar!')

    elif opcao == 8:
        if valor_total > 0:
            valor_restante = valor_total - (parcelas_pagas * parcela_mensal)
            saldo -= valor_restante
            extrato += f'Pagamento total do empréstimo de R$ {valor_restante:.2f}\n'
            print('Pagamento total do empréstimo efetuado com sucesso!')
            print(f'Seu saldo é de R$ {saldo:.2f}')
            # Resetar os valores do empréstimo
            valor_emprestimo = 0
            anos_pagamento = 0
            parcela_mensal = 0
            valor_total = 0
            parcelas_pagas = 0
        else:
            print('Você não possui empréstimos para pagar!')

    elif opcao == 0:
        print('Obrigado por utilizar o banco!')
        break
    
    else:
        print('Opção inválida!')
