import time
import random
import datetime
import json
import os
import threading

# Função para carregar estado do bot a partir de um arquivo JSON
def carregar_estado():
    global saldo_reais, saldo_bitcoin, preco_referencia, bitcoin_price, compras, etapas_sem_comprar
    if os.path.exists("compras_pendentes.json"):
        with open("compras_pendentes.json", "r") as file:
            estado = json.load(file)
            saldo_reais = estado.get("saldo_reais", 10000.00)
            saldo_bitcoin = estado.get("saldo_bitcoin", 0.0)
            preco_referencia = estado.get("preco_referencia", 655500.00)
            bitcoin_price = estado.get("bitcoin_price", 655500.00)
            compras = estado.get("compras", [])
            etapas_sem_comprar = estado.get("etapas_sem_comprar", 0)
        print("Estado carregado do arquivo compras_pendentes.json")
    else:
        print("Nenhum arquivo de estado encontrado. Iniciando com valores padrão.")

# Função para salvar estado do bot em um arquivo JSON
def salvar_estado():
    estado = {
        "saldo_reais": saldo_reais,
        "saldo_bitcoin": saldo_bitcoin,
        "preco_referencia": preco_referencia,
        "bitcoin_price": bitcoin_price,
        "compras": compras,
        "etapas_sem_comprar": etapas_sem_comprar
    }
    with open("compras_pendentes.json", "w") as file:
        json.dump(estado, file, indent=4)
    print("Estado salvo em compras_pendentes.json")

# Função para exibir compras pendentes de forma legível
def exibir_compras_pendentes():
    if not compras:
        print("Compras pendentes: Nenhuma")
    else:
        print("Compras pendentes:")
        for i, compra in enumerate(compras, 1):
            print(f"{i}. {compra['quantidade']:.8f} BTC comprado a R$ {compra['preco_compra']:,.2f}")

# Valor inicial do Bitcoin em reais
bitcoin_price = 655500.00
# Saldo inicial em reais
saldo_reais = 10000.00
# Quantidade inicial de Bitcoin
saldo_bitcoin = 0.0
# Taxa de transação (0,02% = 0.0002)
taxa_transacao = 0.0002
# Quantidade fixa de Bitcoin a comprar por transação
quantidade_compra = 0.0005
# Limites para compra e venda
limite_compra = 1 - 0.01    # Compra se o preço cair 0,09% do preço de referência
limite_venda = 1 + 0.2     # Vende se o preço subir 10% do preço de compra do lote
preco_referencia = bitcoin_price
etapas_sem_comprar = 0
# Lista para rastrear compras
compras = []
# Variável para controlar a tendência de preço
tendencia = "neutra"

pode_comprar = True

# Carregar estado inicial do arquivo JSON, se existir
carregar_estado()

# Função para atualizar o preço do Bitcoin com base na tendência
def atualizar_preco(preco_atual):
    if tendencia == "alta":
        variacao_percentual = random.uniform(-0.01, 0.012)  # Tendência de alta
    elif tendencia == "baixa":
        variacao_percentual = random.uniform(-0.012, 0.01)  # Tendência de baixa
    else:
        variacao_percentual = random.uniform(-0.01, 0.01)  # Variação padrão
    novo_preco = preco_atual * (1 + variacao_percentual)
    return round(novo_preco, 2)

# Função para calcular a taxa de transação
def calcular_taxa(valor_transacao):
    return round(valor_transacao * taxa_transacao, 2)

# Função para exibir o status atual
def exibir_status(tempo, preco, saldo_reais, saldo_bitcoin, etapas_sem_comprar):
    print(f"[{tempo}] Preço do Bitcoin: R$ {preco:,.2f} | Saldo: R$ {saldo_reais:,.2f} | Bitcoin: {saldo_bitcoin:.8f} | Tendência: {tendencia} | Etapas sem comprar: {etapas_sem_comprar}")

# Função para capturar comandos do usuário em uma thread separada
def capturar_comandos():
    global tendencia, saldo_reais, pode_comprar
    while True:
        comando = input().strip().lower()
        if comando == "a":
            tendencia = "alta"
            print(f"Tendência alterada para: {tendencia}")
        elif comando == "b":
            tendencia = "baixa"
            print(f"Tendência alterada para: {tendencia}")
        elif comando == "d":
            saldo_reais += 1000.00
            print("Saldo atualizado com +R$ 10.000,00")
        elif comando == "n":
            tendencia = "neutra"
            print("Tendência alterada para: {tendencia}")
        elif comando == "c":
            pode_comprar = True if pode_comprar == False else False 
            print("Pode Comprar alterado para:", "True" if pode_comprar else "False")

# Função principal do bot
def bot_compra_venda():
    global bitcoin_price, saldo_reais, saldo_bitcoin, preco_referencia, compras, etapas_sem_comprar, tendencia
    
    print("Iniciando o bot de compra e venda de Bitcoin...")
    print(f"Preço inicial do Bitcoin: R$ {bitcoin_price:,.2f}")
    print(f"Saldo inicial: R$ {saldo_reais:,.2f} | Bitcoin: {saldo_bitcoin:.8f}")
    print(f"Taxa de transação: {taxa_transacao*100:.2f}% por transação")
    print(f"Quantidade de Bitcoin por compra: {quantidade_compra:.8f} BTC")
    print("Digite 'a' para tendência de alta, 'b' para tendência de baixa, 'n' para neutra, 'd' para adicionar R$ 10.000,00")
    exibir_compras_pendentes()
    print()
    
    # Iniciar thread para capturar comandos
    threading.Thread(target=capturar_comandos, daemon=True).start()

    while True:
        # Obter o tempo atual
        tempo_atual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Atualizar o preço do Bitcoin
        bitcoin_price = atualizar_preco(bitcoin_price)
        
        # Exibir o status atual
        exibir_status(tempo_atual, bitcoin_price, saldo_reais, saldo_bitcoin, etapas_sem_comprar)
        
        # Lógica de compra
        if bitcoin_price <= preco_referencia * limite_compra and saldo_reais > 0 and pode_comprar:
            # Calcular custo da compra para a quantidade fixa
            custo = quantidade_compra * bitcoin_price
            taxa = calcular_taxa(custo)
            custo_total = custo + taxa
            if custo_total <= saldo_reais:
                saldo_reais -= custo_total
                saldo_bitcoin += quantidade_compra
                # Registrar a compra na lista
                compras.append({"quantidade": quantidade_compra, "preco_compra": bitcoin_price})
                preco_referencia = bitcoin_price
                etapas_sem_comprar = 0
                print(f"[{tempo_atual}] Compra realizada: {quantidade_compra:.8f} BTC por R$ {custo:,.2f} + Taxa R$ {taxa:,.2f} = R$ {custo_total:,.2f}")
            else:
                print(f"[{tempo_atual}] Saldo insuficiente para comprar {quantidade_compra:.8f} BTC (Custo total: R$ {custo_total:,.2f})")
        
        # Lógica de venda
        elif saldo_bitcoin > 0 and compras:
            etapas_sem_comprar += 1

            # Percorrer a lista de compras (FIFO)
            for i, compra in enumerate(compras):
                if bitcoin_price >= compra["preco_compra"] * limite_venda:
                    quantidade_venda = compra["quantidade"]
                    ganho = quantidade_venda * bitcoin_price
                    taxa = calcular_taxa(ganho)
                    ganho_liquido = ganho - taxa
                    saldo_reais += ganho_liquido
                    saldo_bitcoin -= quantidade_venda
                    compras.pop(i)
                    print(f"[{tempo_atual}] Venda realizada: {quantidade_venda:.8f} BTC por R$ {ganho:,.2f} - Taxa R$ {taxa:,.2f} = R$ {ganho_liquido:,.2f}")
                    break  # Processa uma venda por iteração
        
        # Contador de etapas sem comprar
        if etapas_sem_comprar > 1000:
            print("Nenhuma compra realizada em 500 etapas. Reiniciando o preço de referência.")
            preco_referencia = bitcoin_price
            etapas_sem_comprar = 0
        else:
            etapas_sem_comprar += 1

        # Aguardar 0,01 segundos
        time.sleep(0.01)

# Executar o bot
try:
    bot_compra_venda()
except KeyboardInterrupt:
    print("\nBot interrompido pelo usuário.")
    print(f"Saldo final: R$ {saldo_reais:,.2f} | Bitcoin: {saldo_bitcoin:.8f}")
    exibir_compras_pendentes()
    salvar_estado()
