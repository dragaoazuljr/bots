import random
import matplotlib.pyplot as plt
from time import time
from datetime import datetime, timedelta

# Variáveis de tempo
max_duration = 24 * 60 * 60  # Duração máxima de cada operação (em segundos)
check_interval = 60  # Intervalo de verificação de preço (em segundos)
min_stop_loss_time = 6 * 60 * 60  # Tempo mínimo para aplicar stop-loss (em segundos)

# Funções mockadas para simular interação com exchange
def mock_get_bitcoin_price():
    """Retorna um preço simulado do Bitcoin com variação realista."""
    global last_price
    variation = random.uniform(-1, 1.0002)  # Variação do mercado
    new_price = last_price * (1 + (variation / 1000))
    last_price = new_price
    return new_price

def mock_buy_bitcoin(montante, preco_compra, timestamp, dobrar_aposta, stop_loss_atual, meta_lucro_atual, max_duration_atual):
    """Simula a compra de Bitcoin, retornando a quantidade comprada."""
    taxa = montante * taxa_transacao
    btc_comprado = (montante - taxa) / preco_compra
    print(f"[MOCK] {timestamp.strftime('%Y-%m-%d %H:%M:%S')} - Comprou {btc_comprado:.5f} BTC por R${preco_compra:,.2f} (taxa: R${taxa:,.2f})" +
          (f" [Dobrar a Aposta: Stop-loss {stop_loss_atual*100:.2f}%, Meta de lucro {meta_lucro_atual*100:.2f}%, Duração {max_duration_atual/(60*60):.1f}h]" if dobrar_aposta else ""))
    return btc_comprado, taxa

def mock_sell_bitcoin(btc_total, preco_venda, timestamp, motivo):
    """Simula a venda de Bitcoin, retornando o valor da venda."""
    valor_venda = btc_total * preco_venda
    taxa = valor_venda * taxa_transacao
    print(f"[MOCK] {timestamp.strftime('%Y-%m-%d %H:%M:%S')} - Vendeu {btc_total:.5f} BTC por R${preco_venda:,.2f} (taxa: R${taxa:,.2f}) Motivo: {motivo}")
    return valor_venda, taxa

# Configurações iniciais
btc_total = 0  # Quantidade inicial de BTC
btc_custo_total = 654139.18  # Custo inicial de 1 BTC
montante = 10000  # Montante inicial para a primeira compra
montante_inicial = montante
last_price = btc_custo_total  # Preço inicial por BTC
qtd_operacoes = 30  # Número de operações
taxa_transacao = 0.002  # Taxa de transação para compra e venda
meta_lucro = 0.1  # Meta de lucro
stop_loss = -0.05  # Stop-loss
lucro_minimo = 0.03  # Lucro mínimo para venda antecipada
time_percentage_to_sell = 0.5  # Percentual do tempo para venda antecipada
dobrar_aposta = False  # Controle do modo "dobrar a aposta"
utilizar_dobrar_aposta = False
ultimo_motivo_venda = None  # Motivo da venda da operação anterior

total_lucro = 0.0
total_imposto = 0.0
total_taxas = 0.0
lucros = []  # Lucros acumulados
precos_venda = []  # Preços de venda (preço do Bitcoin)
variacoes_compra = []  # Variações de compra
variacoes_venda = []  # Variações de venda

# Obtém a data e hora atuais para a primeira operação
current_operation_time = datetime.now()
start_operation_time = current_operation_time

for op in range(1, qtd_operacoes + 1):
    # Simula o início da operação
    start_time = time()
    simulated_start_time = current_operation_time

    # Define parâmetros com base em "dobrar a aposta"
    dobrar_aposta = (ultimo_motivo_venda == "Stop-loss")
    stop_loss_atual = stop_loss * 2 if dobrar_aposta and utilizar_dobrar_aposta else stop_loss
    meta_lucro_atual = meta_lucro * 2 if dobrar_aposta and utilizar_dobrar_aposta else meta_lucro
    max_duration_atual = max_duration * 2 if dobrar_aposta and utilizar_dobrar_aposta else max_duration

    # Obtém o preço de compra
    preco_btc_compra = mock_get_bitcoin_price()
    variacao_compra = ((preco_btc_compra - last_price) / last_price) if last_price != 0 else 0.0

    # Compra
    btc_comprado, taxa_compra = mock_buy_bitcoin(montante, preco_btc_compra, simulated_start_time, dobrar_aposta, stop_loss_atual, meta_lucro_atual, max_duration_atual)
    btc_total = btc_comprado
    custo = btc_comprado * preco_btc_compra
    total_taxas += taxa_compra

    # Monitora o preço por até max_duration_atual (24h ou 48h)
    elapsed_time = 0
    sold = False
    preco_btc_venda = preco_btc_compra
    variacao_venda = 0.0
    valor_venda = 0.0
    taxa_venda = 0.0
    lucro = 0.0
    imposto = 0.0
    motivo_venda = None

    # while elapsed_time < max_duration_atual and not sold:
    while not sold:
        # Simula a passagem de 1 minuto
        elapsed_time += check_interval
        current_time = simulated_start_time + timedelta(seconds=elapsed_time)
        current_price = mock_get_bitcoin_price()

        # Calcula a variação atual em relação ao preço de compra
        variacao_atual = (current_price - preco_btc_compra) / preco_btc_compra

        # Verifica condições de venda
        if variacao_atual <= stop_loss_atual and elapsed_time >= max_duration_atual - min_stop_loss_time:
            # Stop-loss: vende se caiu além do limite nas últimas 6 horas
            preco_btc_venda = current_price
            variacao_venda = variacao_atual
            valor_venda, taxa_venda = mock_sell_bitcoin(btc_total, preco_btc_venda, current_time, "Stop-loss")
            total_taxas += taxa_venda
            lucro = valor_venda - custo
            imposto = lucro * 0.15 if valor_venda > 35000 and lucro > 0 else 0.0
            montante = valor_venda - taxa_venda  # Apenas taxa é descontada
            motivo_venda = "Stop-loss"
            sold = True
        elif variacao_atual >= meta_lucro_atual:
            # Meta de lucro: vende se atingiu a meta
            preco_btc_venda = current_price
            variacao_venda = variacao_atual
            valor_venda, taxa_venda = mock_sell_bitcoin(btc_total, preco_btc_venda, current_time, "Meta de Lucro")
            total_taxas += taxa_venda
            lucro = valor_venda - custo
            imposto = lucro * 0.15 if valor_venda > 35000 and lucro > 0 else 0.0
            montante = valor_venda - taxa_venda
            motivo_venda = "Meta de Lucro"
            sold = True
        elif elapsed_time >= max_duration_atual * time_percentage_to_sell and variacao_atual >= lucro_minimo:
            # Venda antecipada: vende com lucro mínimo após 90% do tempo
            preco_btc_venda = current_price
            variacao_venda = variacao_atual
            valor_venda, taxa_venda = mock_sell_bitcoin(btc_total, preco_btc_venda, current_time, "Venda Antecipada")
            total_taxas += taxa_venda
            lucro = valor_venda - custo
            imposto = lucro * 0.15 if valor_venda > 35000 and lucro > 0 else 0.0
            montante = valor_venda - taxa_venda
            motivo_venda = "Venda Antecipada"
            sold = True
        # elif elapsed_time >= max_duration_atual:
        #     # Fim do período: vende ao preço atual
        #     preco_btc_venda = current_price
        #     variacao_venda = variacao_atual
        #     valor_venda, taxa_venda = mock_sell_bitcoin(btc_total, preco_btc_venda, current_time, f"Fim das {max_duration_atual/(60*60):.1f}h")
        #     total_taxas += taxa_venda
        #     lucro = valor_venda - custo
        #     imposto = lucro * 0.15 if valor_venda > 35000 and lucro > 0 else 0.0
        #     montante = valor_venda - taxa_venda
        #     motivo_venda = f"Fim das {max_duration_atual/(60*60):.1f}h"
        #     sold = True
        else:
            # Não vende: espera o próximo ciclo
            print(f"[MOCK] {current_time.strftime('%Y-%m-%d %H:%M:%S')} - Não vendeu: preço atual R${current_price:,.2f}, variação acumulada {variacao_atual*100:.2f}%")

    # Cabeçalho do print antes de cada operação
    print(f"{'Op':<3} {'Hora':<20} {'Preço Compra':<12} {'Taxa Compra R$':<14} {'BTC Comprado':<12} {'Custo R$':<12} {'Var Compra (%)':<14} {'Preço Venda':<12} {'Var Venda (%)':<14} {'Venda R$':<12} {'Lucro R$':<12} {'Imposto R$':<12} {'Taxa Venda R$':<14} {'Montante R$':<12} {'BTC Total'}")
    print(f"{op:<3} {current_time.strftime('%Y-%m-%d %H:%M:%S'):<20} R${preco_btc_compra:,.2f}   R${taxa_compra:,.2f}     {btc_comprado:.5f} BTC   R${custo:,.2f}   {variacao_compra*100:.2f}%      R${preco_btc_venda:,.2f}   {variacao_venda*100:.2f}%      R${valor_venda:,.2f}   R${lucro:,.2f}   R${imposto:,.2f}   R${taxa_venda:,.2f}     R${montante:,.2f}   {btc_total:.5f} BTC")

    total_lucro += lucro
    total_imposto += imposto
    lucros.append(total_lucro)
    precos_venda.append(preco_btc_venda)
    variacoes_compra.append(variacao_compra * 100)
    variacoes_venda.append(variacao_venda * 100)

    # Atualiza o motivo da venda para a próxima iteração
    ultimo_motivo_venda = motivo_venda

    # Atualiza o tempo para a próxima operação (tempo da venda + 1 segundo)
    current_operation_time = current_time + timedelta(seconds=1)

    # Atualiza o preço atual para a próxima iteração
    last_price = preco_btc_venda

# Resumo final
print("\n--- Resumo Final ---")
print(f"Montante inicial:            R${montante_inicial:,.2f}")
print(f"Montante final:              R${montante:,.2f}")
print(f"Lucro total:                 R${montante - montante_inicial:,.2f}")
print(f"Soma de todos os Lucros:     R${total_lucro:,.2f}")
print(f"Imposto total:               R${total_imposto:,.2f}")
print(f"Taxas totais:                R${total_taxas:,.2f}")
print(f"BTC final:                   {btc_total:.5f} BTC")
print(f"Data início:                 {start_operation_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Data fim:                    {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

# Gráfico
fig, ax1 = plt.subplots()

# Eixo y principal: Lucro acumulado e preço do Bitcoin
ax1.plot(range(1, qtd_operacoes + 1), lucros, marker='o', linestyle='-', color='b', label='Lucro Acumulado (R$)')
ax1.plot(range(1, qtd_operacoes + 1), precos_venda, marker='s', linestyle='-', color='g', label='Preço do Bitcoin (R$)')
ax1.set_xlabel('Operação')
ax1.set_ylabel('Lucro (R$) / Preço BTC (R$)', color='b')
ax1.tick_params(axis='y', labelcolor='b')
ax1.grid(True)
ax1.legend(loc='upper left')

# Eixo y secundário: Variações de compra e venda
ax2 = ax1.twinx()
ax2.plot(range(1, qtd_operacoes + 1), variacoes_compra, marker='^', linestyle='--', color='r', label='Variação Compra (%)')
ax2.plot(range(1, qtd_operacoes + 1), variacoes_venda, marker='v', linestyle='--', color='m', label='Variação Venda (%)')
ax2.set_ylabel('Variação (%)', color='r')
ax2.tick_params(axis='y', labelcolor='r')
ax2.legend(loc='upper right')

plt.title('Evolução do Lucro, Preço do Bitcoin e Variações de Compra/Venda')
# plt.show()
