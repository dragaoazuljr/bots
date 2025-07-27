import random
import matplotlib.pyplot as plt

# Configurações iniciais
btc_total = 1.0  # Quantidade inicial de BTC
btc_custo_total = 654139.18  # Custo inicial de 1 BTC
aporte = 50000.00  # Montante inicial para a primeira compra
lucro_anterior = 38158
montante = aporte + lucro_anterior  # Montante inicial para a primeira compra
preco_btc_atual = btc_custo_total / btc_total  # Preço inicial por BTC
qtd_operacoes = 30  # 30 operações
taxa_transacao = 0.002  # Taxa de 0,2% para compra e venda

total_lucro = 0.0
total_imposto = 0.0
total_taxas = 0.0
lucros = []  # Lista para armazenar lucros acumulados
precos_venda = []  # Lista para armazenar preços de venda (preço do Bitcoin)
variacoes_compra = []  # Lista para armazenar variações de compra
variacoes_venda = []  # Lista para armazenar variações de venda

print(f"{'Op':<3} {'Preço Compra':<12} {'Taxa Compra R$':<14} {'BTC Comprado':<12} {'Custo R$':<12} {'Var Compra (%)':<14} {'Preço Venda':<12} {'Var Venda (%)':<14} {'Venda R$':<12} {'Lucro R$':<12} {'Imposto R$':<12} {'Taxa Venda R$':<14} {'Montante R$':<12} {'BTC Total'}")
for op in range(1, qtd_operacoes + 1):
    # Variação de preço para compra (-3% a +3% em relação ao preço atual)
    variacao_compra = random.uniform(-0.2, 0.03)
    preco_btc_compra = preco_btc_atual * (1 + variacao_compra)

    # Taxa de compra (0,2% do montante disponível)
    taxa_compra = montante * taxa_transacao
    total_taxas += taxa_compra

    # Compra: Quantidade de BTC que pode ser comprada com o montante disponível após taxa
    btc_comprado = (montante - taxa_compra) / preco_btc_compra
    btc_total = btc_comprado  # Atualiza a quantidade total de BTC
    custo = btc_comprado * preco_btc_compra  # Custo da compra

    # Variação de preço de venda (+1% a +5% acima do preço de compra)
    variacao_venda = random.uniform(0.001, 0.05)
    preco_btc_venda = preco_btc_compra * (1 + variacao_venda)

    # Cálculos da venda
    valor_venda = btc_total * preco_btc_venda

    # Taxa de venda (0,2%)
    taxa_venda = valor_venda * taxa_transacao
    total_taxas += taxa_venda

    # Lucro da venda
    lucro = valor_venda - custo

    # Imposto (15% do lucro se venda > R$35.000 e lucro > 0)
    imposto = lucro * 0.15 if valor_venda > 35000 and lucro > 0 else 0.0
    total_imposto += imposto

    # Montante disponível após venda (valor da venda menos imposto e taxa)
    montante = valor_venda - imposto - taxa_venda

    total_lucro += lucro
    lucros.append(total_lucro)  # Adiciona o lucro acumulado
    precos_venda.append(preco_btc_venda)  # Adiciona o preço de venda
    variacoes_compra.append(variacao_compra * 100)  # Converte para percentual
    variacoes_venda.append(variacao_venda * 100)  # Converte para percentual

    print(f"{op:<3} R${preco_btc_compra:,.2f}   R${taxa_compra:,.2f}     {btc_comprado:.5f} BTC   R${custo:,.2f}   {variacao_compra*100:.2f}%      R${preco_btc_venda:,.2f}   {variacao_venda*100:.2f}%      R${valor_venda:,.2f}   R${lucro:,.2f}   R${imposto:,.2f}   R${taxa_venda:,.2f}     R${montante:,.2f}   {btc_total:.5f} BTC")

    # Atualiza o preço do BTC para a próxima iteração
    preco_btc_atual = preco_btc_venda

# Resumo final
print("\n--- Resumo Final ---")
print(f"Lucro total:     R${total_lucro:,.2f}")
print(f"Imposto total:   R${total_imposto:,.2f}")
print(f"Taxas totais:    R${total_taxas:,.2f}")
print(f"Montante final:  R${montante:,.2f}")
print(f"Lucro liquido final:  R${montante - aporte:,.2f}")
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
