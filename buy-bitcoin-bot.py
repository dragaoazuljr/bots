import random
import matplotlib.pyplot as plt
from time import time
from datetime import datetime, timedelta

# Funções mockadas para simular interação com exchange
def mock_get_bitcoin_price():
    """Retorna um preço simulado do Bitcoin com variação de -5% a +5%."""
    global last_price
    variation = random.uniform(-0.001, 0.001)  # Variação realista do mercado
    new_price = last_price * (1 + variation)
    last_price = new_price
    return new_price

def mock_buy_bitcoin(montante, preco_compra, timestamp):
    """Simula a compra de Bitcoin, retornando a quantidade comprada."""
    taxa = montante * taxa_transacao
    btc_comprado = (montante - taxa) / preco_compra
    print(f"[MOCK] {timestamp.strftime('%Y-%m-%d %H:%M:%S')} - Comprou {btc_comprado:.5f} BTC por R${preco_compra:,.2f} (taxa: R${taxa:,.2f})")
    return btc_comprado, taxa

def mock_sell_bitcoin(btc_total, preco_venda, timestamp):
    """Simula a venda de Bitcoin, retornando o valor da venda."""
    valor_venda = btc_total * preco_venda
    taxa = valor_venda * taxa_transacao
    print(f"[MOCK] {timestamp.strftime('%Y-%m-%d %H:%M:%S')} - Vendeu {btc_total:.5f} BTC por R${preco_venda:,.2f} (taxa: R${taxa:,.2f})")
    return valor_venda, taxa


# Configurações iniciais
btc_total = 0  # Quantidade inicial de BTC
btc_custo_total = 654139.18  # Custo inicial de 1 BTC
montante = 50000  # Montante inicial para a primeira compra
last_price = btc_custo_total  # Preço inicial por BTC
qtd_operacoes = 10  # 30 operações
taxa_transacao = 0.002  # Taxa de 0,2% para compra e venda
meta_lucro = 0.05  # Meta de lucro de 5%
stop_loss = -0.02  # Stop-loss de -1%
lucro_minimo = 0.02  # Lucro mínimo para venda antecipadatotal_lucro = 0.0

total_lucro = 0.0
total_imposto = 0.0
total_taxas = 0.0
lucros = []  # Lucros acumulados
precos_venda = []  # Preços de venda (preço do Bitcoin)
variacoes_compra = []  # Variações de compra
variacoes_venda = []  # Variações de venda


print(f"{'Op':<3} {'Hora':<20} {'Preço Compra':<12} {'Taxa Compra R$':<14} {'BTC Comprado':<12} {'Custo R$':<12} {'Var Compra (%)':<14} {'Preço Venda':<12} {'Var Venda (%)':<14} {'Venda R$':<12} {'Lucro R$':<12} {'Imposto R$':<12} {'Taxa Venda R$':<14} {'Montante R$':<12} {'BTC Total'}")
for op in range(1, qtd_operacoes + 1):
    # Simula o início da operação (tempo inicial)
    start_time = time()
    simulated_start_time = datetime(2025, 7, 27, 10, 0)  # Data inicial fixa para simulação

    # Obtém o preço de compra
    preco_btc_compra = mock_get_bitcoin_price()
    variacao_compra = ((preco_btc_compra - last_price) / last_price) if last_price != 0 else 0.0

    # Compra
    btc_comprado, taxa_compra = mock_buy_bitcoin(montante, preco_btc_compra, simulated_start_time)
    btc_total = btc_comprado
    custo = btc_comprado * preco_btc_compra
    total_taxas += taxa_compra

    # Monitora o preço por até 24 horas (simulado em 24 intervalos)
    max_duration = 24 * 60 * 60  # 24 horas em segundos
    check_interval = 300 # Checa a cada 5 min
    elapsed_time = 0
    sold = False
    preco_btc_venda = preco_btc_compra
    variacao_venda = 0.0
    valor_venda = 0.0
    taxa_venda = 0.0
    lucro = 0.0
    imposto = 0.0

    while elapsed_time < max_duration and not sold:
        # Simula a passagem de 1 hora
        elapsed_time += check_interval
        current_time = simulated_start_time + timedelta(seconds=elapsed_time)
        current_price = mock_get_bitcoin_price()

        # Calcula a variação atual em relação ao preço de compra
        variacao_atual = (current_price - preco_btc_compra) / preco_btc_compra

        # Verifica condições de venda
        if variacao_atual <= stop_loss:
            # Stop-loss: vende se caiu mais de 1%
            preco_btc_venda = current_price
            variacao_venda = variacao_atual
            valor_venda, taxa_venda = mock_sell_bitcoin(btc_total, preco_btc_venda, current_time)
            total_taxas += taxa_venda
            lucro = valor_venda - custo
            imposto = lucro * 0.15 if valor_venda > 35000 and lucro > 0 else 0.0
            montante = valor_venda - taxa_venda  # Apenas taxa é descontada
            sold = True
        elif variacao_atual >= meta_lucro:
            # Meta de lucro: vende se atingiu 5%
            preco_btc_venda = current_price
            variacao_venda = variacao_atual
            valor_venda, taxa_venda = mock_sell_bitcoin(btc_total, preco_btc_venda, current_time)
            total_taxas += taxa_venda
            lucro = valor_venda - custo
            imposto = lucro * 0.15 if valor_venda > 35000 and lucro > 0 else 0.0
            montante = valor_venda - taxa_venda
            sold = True
        elif elapsed_time >= max_duration * 0.9 and variacao_atual >= lucro_minimo:
            # Venda antecipada: vende com lucro ≥2% após 90% do tempo
            preco_btc_venda = current_price
            variacao_venda = variacao_atual
            valor_venda, taxa_venda = mock_sell_bitcoin(btc_total, preco_btc_venda, current_time)
            total_taxas += taxa_venda
            lucro = valor_venda - custo
            imposto = lucro * 0.15 if valor_venda > 35000 and lucro > 0 else 0.0
            montante = valor_venda - taxa_venda
            sold = True
        elif elapsed_time >= max_duration:
            # Fim das 24h: vende ao preço atual
            preco_btc_venda = current_price
            variacao_venda = variacao_atual
            valor_venda, taxa_venda = mock_sell_bitcoin(btc_total, preco_btc_venda, current_time)
            total_taxas += taxa_venda
            lucro = valor_venda - custo
            imposto = lucro * 0.15 if valor_venda > 35000 and lucro > 0 else 0.0
            montante = valor_venda - taxa_venda
            sold = True
        else:
            # Não vende: espera o próximo ciclo
            print(f"[MOCK] {current_time.strftime('%Y-%m-%d %H:%M:%S')} - Não vendeu: preço atual R${current_price:,.2f}, variação {variacao_atual*100:.2f}%")

    total_lucro += lucro
    total_imposto += imposto
    lucros.append(total_lucro)
    precos_venda.append(preco_btc_venda)
    variacoes_compra.append(variacao_compra * 100)
    variacoes_venda.append(variacao_venda * 100)

    print(f"{op:<3} {current_time.strftime('%Y-%m-%d %H:%M:%S'):<20} R${preco_btc_compra:,.2f}   R${taxa_compra:,.2f}     {btc_comprado:.5f} BTC   R${custo:,.2f}   {variacao_compra*100:.2f}%      R${preco_btc_venda:,.2f}   {variacao_venda*100:.2f}%      R${valor_venda:,.2f}   R${lucro:,.2f}   R${imposto:,.2f}   R${taxa_venda:,.2f}     R${montante:,.2f}   {btc_total:.5f} BTC")

    # Atualiza o preço atual para a próxima iteração
    last_price = preco_btc_venda

# Resumo final
print("\n--- Resumo Final ---")
print(f"Lucro total:     R${total_lucro:,.2f}")
print(f"Imposto total:   R${total_imposto:,.2f}")
print(f"Taxas totais:    R${total_taxas:,.2f}")
print(f"Montante final:  R${montante:,.2f}")
print(f"BTC final:       {btc_total:.5f} BTC")
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
#plt.show()
