import random
import matplotlib.pyplot as plt
from time import time
from datetime import datetime, timedelta
import logging
import argparse
import json
import os
import pandas as pd
import sys

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_log.txt'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Configuração de argumentos da linha de comando
parser = argparse.ArgumentParser(description='Bot de Trading de Bitcoin com Simulação Histórica')
parser.add_argument('--montante', type=float, default=10000, help='Montante inicial em reais default: 10000')
parser.add_argument('--qtd_operacoes', type=int, default=30, help='Quantidade de operações default: 30')
parser.add_argument('--meta_lucro', type=float, default=0.1, help='Meta de lucro percentual default: 0.1 = 10%%')
parser.add_argument('--stop_loss', type=float, default=-0.05, help='Stop-loss percentual default: -0.05 = -5%%')
parser.add_argument('--csv_file', type=str, help='Arquivo CSV com dados históricos horários formato Binance')
parser.add_argument('--taxa_cambio', type=float, default=5.5, help='Taxa de câmbio USD/BRL default: 5.5')
parser.add_argument('--cooldown_steps', type=int, default=5, help='Cooldown em steps após stop-loss default: 5')
parser.add_argument('--max_dobrar', type=int, default=3, help='Máximo de dobras consecutivas default: 3')
parser.add_argument('--tranches_buy', nargs='+', type=float, default=[0.2, 0.3, 0.5], help='Frações de tranches para compras parciais (ex: --tranches_buy 0.2 0.3 0.5)')
parser.add_argument('--levels_buy', nargs='+', type=float, default=[-0.01, -0.02, -0.03], help='Níveis percentuais para comprar tranches (ex: --levels_buy -0.01 -0.02 -0.03)')
parser.add_argument('--tranches_sell', nargs='+', type=float, default=[0.2, 0.3, 0.5], help='Frações de tranches para vendas parciais (ex: --tranches_sell 0.2 0.3 0.5)')
parser.add_argument('--levels_sell', nargs='+', type=float, default=[0.01, 0.03, 0.05], help='Níveis percentuais para vender tranches (ex: --levels_sell 0.01 0.03 0.05)')

args = parser.parse_args()

# Validações dos novos parâmetros
try:
    tranches_buy = args.tranches_buy
    levels_buy = args.levels_buy
    tranches_sell = args.tranches_sell
    levels_sell = args.levels_sell

    # Validações
    if abs(sum(tranches_buy) - 1.0) > 1e-6:
        raise ValueError("A soma das tranches de compra deve ser 1.0")
    if abs(sum(tranches_sell) - 1.0) > 1e-6:
        raise ValueError("A soma das tranches de venda deve ser 1.0")
    if len(tranches_buy) != len(levels_buy):
        raise ValueError("Número de tranches_buy deve ser igual ao número de levels_buy")
    if len(tranches_sell) != len(levels_sell):
        raise ValueError("Número de tranches_sell deve ser igual ao número de levels_sell")
    if not all(x < 0 for x in levels_buy):
        raise ValueError("Todos os levels_buy devem ser negativos (dips)")
    if not all(x > 0 for x in levels_sell):
        raise ValueError("Todos os levels_sell devem ser positivos (lucros)")
    if not all(x > 0 for x in tranches_buy + tranches_sell):
        raise ValueError("Todas as tranches devem ser positivas")

except ValueError as e:
    logging.error(f"Erro na validação dos parâmetros: {e}")
    sys.exit(1)

# Variáveis de tempo
max_duration = 24 * 60 * 60  # Duração máxima de cada operação (em segundos)
check_interval = 60  # Intervalo de verificação de preço (em segundos)
min_stop_loss_time = 6 * 60 * 60  # Tempo mínimo para aplicar stop-loss (em segundos)

# Funções mockadas para simular interação com exchange
def mock_get_bitcoin_price():
    """Retorna um preço simulado do Bitcoin com variação realista."""
    try:
        global last_price
        if last_price <= 0:
            raise ValueError("Preço anterior inválido")

        variation = random.uniform(-1, 1.0002)  # Variação do mercado
        new_price = last_price * (1 + (variation / 1000))

        if new_price <= 0:
            raise ValueError("Novo preço calculado é inválido")

        last_price = new_price
        return new_price
    except Exception as e:
        logging.error(f"Erro ao gerar preço do Bitcoin: {e}")
        return last_price  # Retorna último preço válido

def mock_buy_bitcoin(montante, preco_compra, timestamp, dobrar_aposta, stop_loss_atual, meta_lucro_atual, max_duration_atual):
    """Simula a compra de Bitcoin, retornando a quantidade comprada."""
    try:
        if montante <= 0:
            raise ValueError("Montante deve ser positivo")
        if preco_compra <= 0:
            raise ValueError("Preço de compra deve ser positivo")

        global taxa_transacao
        taxa = montante * taxa_transacao
        btc_comprado = (montante - taxa) / preco_compra

        logging.info(f"[MOCK] {timestamp.strftime('%Y-%m-%d %H:%M:%S')} - Comprou {btc_comprado:.5f} BTC por R${preco_compra:,.2f} (taxa: R${taxa:,.2f})" +
                    (f" [Dobrar a Aposta: Stop-loss {stop_loss_atual*100:.2f}%, Meta de lucro {meta_lucro_atual*100:.2f}%, Duração {max_duration_atual/(60*60):.1f}h]" if dobrar_aposta else ""))
        return btc_comprado, taxa
    except Exception as e:
        logging.error(f"Erro na compra de Bitcoin: {e}")
        return 0, 0

def mock_sell_bitcoin(btc_total, preco_venda, timestamp, motivo):
    """Simula a venda de Bitcoin, retornando o valor da venda."""
    try:
        if btc_total <= 0:
            raise ValueError("Quantidade de BTC deve ser positiva")
        if preco_venda <= 0:
            raise ValueError("Preço de venda deve ser positivo")

        global taxa_transacao
        valor_venda = btc_total * preco_venda
        taxa = valor_venda * taxa_transacao

        logging.info(f"[MOCK] {timestamp.strftime('%Y-%m-%d %H:%M:%S')} - Vendeu {btc_total:.5f} BTC por R${preco_venda:,.2f} (taxa: R${taxa:,.2f}) Motivo: {motivo}")
        return valor_venda, taxa
    except Exception as e:
        logging.error(f"Erro na venda de Bitcoin: {e}")
        return 0, 0

# Funções para persistência de estado
def load_bot_state():
    """Carrega o estado do bot do arquivo JSON."""
    try:
        if os.path.exists('bot_state.json'):
            with open('bot_state.json', 'r') as f:
                state = json.load(f)
            logging.info("Estado do bot carregado com sucesso")
            return state
        else:
            logging.info("Arquivo de estado não encontrado, usando valores padrão")
            return None
    except Exception as e:
        logging.error(f"Erro ao carregar estado do bot: {e}")
        return None

def save_bot_state(state):
    """Salva o estado do bot em arquivo JSON."""
    try:
        with open('bot_state.json', 'w') as f:
            json.dump(state, f, indent=2, default=str)
        logging.info("Estado do bot salvo com sucesso")
    except Exception as e:
        logging.error(f"Erro ao salvar estado do bot: {e}")

# Função para carregar preços históricos
def load_historical_prices(csv_file, taxa_cambio=5.5):
    """Carrega preços históricos e timestamps do arquivo CSV."""
    try:
        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"Arquivo CSV não encontrado: {csv_file}")

        df = pd.read_csv(csv_file)
        df.dropna(inplace=True)  # Remove linhas com NaN

        # Verifica se existe coluna 'Price_USD' (formato fornecido pelo usuário)
        if 'Price_USD' in df.columns:
            price_column = 'Price_USD'
        elif 'Close' in df.columns:
            price_column = 'Close'
        else:
            raise ValueError("Coluna 'Price_USD' ou 'Close' não encontrada no CSV")

        # Verifica se existe coluna de timestamp/datetime
        if 'Datetime' in df.columns:
            # Converte string datetime para objetos datetime
            timestamps = pd.to_datetime(df['Datetime']).tolist()
        elif 'Timestamp_ms' in df.columns:
            # Converte timestamp em ms para datetime
            timestamps = pd.to_datetime(df['Timestamp_ms'], unit='ms').tolist()
        else:
            raise ValueError("Coluna 'Datetime' ou 'Timestamp_ms' não encontrada no CSV")

        # Converte preços para BRL
        historical_prices_brl = (df[price_column] * taxa_cambio).tolist()

        logging.info(f"Carregados {len(historical_prices_brl)} preços e timestamps históricos do CSV")
        return historical_prices_brl, timestamps

    except Exception as e:
        logging.error(f"Erro ao carregar preços históricos: {e}")
        return None, None

# Carrega estado salvo se existir
saved_state = load_bot_state()

# Configurações iniciais (usando argumentos ou valores salvos)
btc_total = saved_state.get('btc_total', 0) if saved_state else 0
btc_tranches = saved_state.get('btc_tranches', []) if saved_state else []  # Adicionado para scaling
btc_custo_total = 654139.18  # Custo inicial de 1 BTC
montante = args.montante if not saved_state else saved_state.get('montante', args.montante)
montante_inicial = montante
last_price = saved_state.get('last_price', btc_custo_total) if saved_state else btc_custo_total
qtd_operacoes = args.qtd_operacoes
taxa_transacao = 0.002  # Taxa de transação para compra e venda
meta_lucro = args.meta_lucro  # Meta de lucro
stop_loss = args.stop_loss  # Stop-loss
lucro_minimo = 0.03  # Lucro mínimo para venda antecipada
time_percentage_to_sell = 0.5  # Percentual do tempo para venda antecipada
dobrar_aposta = False  # Controle do modo "dobrar a aposta"
utilizar_dobrar_aposta = False
ultimo_motivo_venda = saved_state.get('ultimo_motivo_venda', None) if saved_state else None
consecutive_losses = saved_state.get('consecutive_losses', 0) if saved_state else 0
cooldown_remaining = saved_state.get('cooldown_remaining', 0) if saved_state else 0

# Carrega preços históricos se CSV foi fornecido
historical_prices = None
historical_timestamps = None
if args.csv_file:
    historical_prices, historical_timestamps = load_historical_prices(args.csv_file, args.taxa_cambio)
    if historical_prices is None:
        logging.error("Falha ao carregar preços históricos. Saindo...")
        sys.exit(1)
    # Verifica se há dados suficientes para as operações
    min_data_points = args.qtd_operacoes * 10  # Estimativa conservadora
    if len(historical_prices) < min_data_points:
        logging.warning(f"Dados históricos insuficientes: {len(historical_prices)} pontos, mínimo estimado: {min_data_points}")
        adjusted_qtd = len(historical_prices) // 10
        if adjusted_qtd < args.qtd_operacoes:
            logging.warning(f"Ajustando qtd_operacoes de {args.qtd_operacoes} para {adjusted_qtd}")
            qtd_operacoes = adjusted_qtd

total_lucro = saved_state.get('total_lucro', 0.0) if saved_state else 0.0
total_imposto = saved_state.get('total_imposto', 0.0) if saved_state else 0.0
total_taxas = saved_state.get('total_taxas', 0.0) if saved_state else 0.0
lucros = [float(l) for l in (saved_state.get('lucros', []) if saved_state else [])]  # Lucros acumulados (garante floats)
precos_venda = saved_state.get('precos_venda', []) if saved_state else []  # Preços de venda (preço do Bitcoin)
variacoes_compra = saved_state.get('variacoes_compra', []) if saved_state else []  # Variações de compra
variacoes_venda = saved_state.get('variacoes_venda', []) if saved_state else []  # Variações de venda
buy_points = saved_state.get('buy_points', []) if saved_state else []  # Pontos de compra (índice, preço)
sell_points = saved_state.get('sell_points', []) if saved_state else []  # Pontos de venda (índice, preço)
saldo_history = saved_state.get('saldo_history', []) if saved_state else []  # Histórico do saldo
current_index = saved_state.get('current_index', 0) if saved_state else 0  # Índice atual nos preços históricos

# Obtém a data e hora atuais para a primeira operação
if saved_state and 'current_operation_time' in saved_state:
    # Converte string do JSON de volta para datetime
    current_operation_time = datetime.fromisoformat(saved_state['current_operation_time'])
elif historical_timestamps:
    # Usa o primeiro timestamp do CSV como início
    current_operation_time = historical_timestamps[0]
else:
    current_operation_time = datetime.now()

start_operation_time = current_operation_time
last_operation_time = saved_state.get('last_operation_time', start_operation_time) if saved_state else start_operation_time

# Determina o número da operação inicial
start_op = saved_state.get('current_operation', 1) if saved_state else 1

# Converte last_operation_time de string para datetime se necessário
if saved_state and 'last_operation_time' in saved_state:
    if isinstance(saved_state['last_operation_time'], str):
        last_operation_time = datetime.fromisoformat(saved_state['last_operation_time'])
    else:
        last_operation_time = saved_state['last_operation_time']

for op in range(start_op, qtd_operacoes + 1):
    # Inicializa lucro da operação atual
    if len(lucros) < op:
        lucros.extend([0.0] * (op - len(lucros)))

    # Simula o início da operação
    start_time = time()
    simulated_start_time = current_operation_time

    # Define parâmetros com base em "dobrar a aposta"
    dobrar_aposta = (ultimo_motivo_venda == "Stop-loss" and consecutive_losses < args.max_dobrar)
    stop_loss_atual = stop_loss * 2 if dobrar_aposta and utilizar_dobrar_aposta else stop_loss
    meta_lucro_atual = meta_lucro * 2 if dobrar_aposta and utilizar_dobrar_aposta else meta_lucro
    max_duration_atual = max_duration * 2 if dobrar_aposta and utilizar_dobrar_aposta else max_duration

    if dobrar_aposta:
        consecutive_losses += 1
        logging.info(f"Dobrando aposta (perda consecutiva #{consecutive_losses})")
    else:
        consecutive_losses = 0

    # Verifica cooldown
    if cooldown_remaining > 0:
        logging.info(f"Em cooldown após stop-loss. Pulando operação {op}. Cooldown restante: {cooldown_remaining} steps")
        cooldown_remaining -= 1
        current_index += 1  # Avança no histórico mesmo em cooldown
        if current_index >= len(historical_prices):
            logging.info("Fim dos dados históricos alcançado")
            break
        continue

    # === SCALING IN: Compra em tranches progressivas ===
    btc_tranches = []  # Lista de tranches compradas: [{'btc': qtd, 'preco_compra': preco, 'tranche_idx': idx}]
    preco_base_compra = last_price  # Preço base para calcular variações de dip
    tranches_compradas = set()  # Índices das tranches já compradas
    total_custo_compra = 0.0
    total_taxa_compra = 0.0
    max_steps_in = 24  # Limite de steps para scaling in
    steps_in = 0

    # Loop de scaling in até todas as tranches serem compradas ou limite atingido
    while len(tranches_compradas) < len(tranches_buy) and steps_in < max_steps_in:
        # Obtém o preço atual
        if historical_prices and current_index < len(historical_prices):
            preco_atual = historical_prices[current_index]
            current_index += 1
        else:
            preco_atual = mock_get_bitcoin_price()

        # Calcula variação acumulada desde o início da operação
        variacao_acumulada = (preco_atual - preco_base_compra) / preco_base_compra if preco_base_compra != 0 else 0.0

        # Log reduzido: só variações significativas ou a cada 6 steps
        if abs(variacao_acumulada) > 0.005 or steps_in % 6 == 0:
            logging.debug(f"Scaling In Step {steps_in}: preço R${preco_atual:,.2f}, variação {variacao_acumulada*100:.2f}%")

        # Verifica se deve comprar alguma tranche não comprada
        tranche_comprada_neste_step = False
        for i, (tranche_fraction, level) in enumerate(zip(tranches_buy, levels_buy)):
            if i not in tranches_compradas and variacao_acumulada <= level:
                # Compra esta tranche
                montante_tranche = montante * tranche_fraction
                btc_tranche, taxa_tranche = mock_buy_bitcoin(montante_tranche, preco_atual, simulated_start_time,
                                                            dobrar_aposta, stop_loss_atual, meta_lucro_atual, max_duration_atual)

                # Registra a tranche
                btc_tranches.append({
                    'btc': btc_tranche,
                    'preco_compra': preco_atual,
                    'tranche_idx': i
                })

                # Atualiza totais
                total_custo_compra += btc_tranche * preco_atual
                total_taxa_compra += taxa_tranche
                tranches_compradas.add(i)

                # Desconta montante após compra (FIX: inconsistência de montante)
                montante -= montante_tranche + taxa_tranche

                # Registra ponto de compra
                buy_points.append((current_index - 1, preco_atual))

                logging.info(f"Tranche {i+1}/{len(tranches_buy)} comprada: {btc_tranche:.5f} BTC a R${preco_atual:,.2f} (dip {variacao_acumulada*100:.2f}%)")
                tranche_comprada_neste_step = True
                break

        # Avança step se não comprou tranche neste step
        if not tranche_comprada_neste_step:
            steps_in += 1

        # Se chegou ao fim dos dados históricos durante scaling in, para
        if historical_prices and current_index >= len(historical_prices):
            break

    # Calcula totais finais da compra
    btc_total = sum(tranche['btc'] for tranche in btc_tranches)
    custo = total_custo_compra
    total_taxas += total_taxa_compra

    # Se não conseguiu comprar todas as tranches, continua com o que tem
    if len(tranches_compradas) < len(tranches_buy):
        logging.warning(f"Apenas {len(tranches_compradas)}/{len(tranches_buy)} tranches compradas (limite {max_steps_in} steps atingido)")

    # Define preco_btc_compra como o preço da primeira tranche (para compatibilidade)
    preco_btc_compra = btc_tranches[0]['preco_compra'] if btc_tranches else preco_base_compra
    variacao_compra = ((preco_btc_compra - last_price) / last_price) if last_price != 0 else 0.0

    # Monitora o preço por até max_duration_atual (24h ou 48h)
    elapsed_time = 0
    sold = False
    preco_btc_venda = preco_btc_compra
    variacao_venda = 0.0
    valor_venda = 0.0
    taxa_venda = 0.0
    lucro = 0.0  # Inicializa lucro da operação
    imposto = 0.0
    motivo_venda = None
    steps_sem_log = 0

    # while elapsed_time < max_duration_atual and not sold:
    while not sold:
        # Avança para o próximo timestamp (1 hora)
        if historical_timestamps and current_index < len(historical_timestamps):
            current_time = historical_timestamps[current_index]
            current_price = historical_prices[current_index] if historical_prices else mock_get_bitcoin_price()
            current_index += 1
            elapsed_time += 3600  # Ainda conta o tempo para verificações de limite
        else:
            # Fallback para simulação quando não há mais dados históricos
            elapsed_time += 3600  # 1 hora em segundos
            current_time = simulated_start_time + timedelta(seconds=elapsed_time)
            current_price = mock_get_bitcoin_price()

        # === SCALING OUT: Verifica vendas parciais em níveis de lucro ===

        # Calcula variação média ponderada para stop-loss (baseada no custo total)
        variacao_atual = (current_price * btc_total - custo) / custo if custo > 0 else 0.0

        # Verifica stop-loss total: vende tudo se perdeu demais
        if variacao_atual <= stop_loss_atual and elapsed_time >= max_duration_atual - min_stop_loss_time:
            preco_btc_venda = current_price
            variacao_venda = variacao_atual
            valor_venda, taxa_venda = mock_sell_bitcoin(btc_total, preco_btc_venda, current_time, "Stop-loss Total")
            total_taxas += taxa_venda
            lucro = valor_venda - custo
            imposto = lucro * 0.15 if valor_venda > 35000 and lucro > 0 else 0.0
            montante += valor_venda - taxa_venda  # FIX: soma valor_venda - taxa
            motivo_venda = "Stop-loss Total"
            cooldown_remaining = args.cooldown_steps  # Inicia cooldown
            sell_points.append((current_index - 1, preco_btc_venda))
            sold = True
            btc_total = 0
            btc_tranches = []  # FIX: zera btc_tranches

        # Scaling out: verifica vendas parciais em níveis de lucro (FIFO)
        elif btc_tranches:  # Só se ainda há tranches para vender
            tranches_vendidas_neste_step = []

            for tranche in sorted(btc_tranches[:], key=lambda x: x['tranche_idx']):  # FIFO: ordena por tranche_idx
                # Calcula variação desta tranche específica
                variacao_tranche = (current_price - tranche['preco_compra']) / tranche['preco_compra']

                # Verifica se deve vender esta tranche em algum nível
                for i, (tranche_sell_fraction, level_sell) in enumerate(zip(tranches_sell, levels_sell)):
                    if variacao_tranche >= level_sell:
                        # Vende esta tranche (usa FIFO, então vende a primeira disponível)
                        btc_vendido = tranche['btc']
                        valor_vendido = btc_vendido * current_price
                        taxa_venda_tranche = valor_vendido * taxa_transacao

                        logging.info(f"[MOCK] {current_time.strftime('%Y-%m-%d %H:%M:%S')} - Vendeu tranche {tranche['tranche_idx']+1} (FIFO): "
                                   f"{btc_vendido:.5f} BTC por R${current_price:,.2f} (taxa: R${taxa_venda_tranche:,.2f}) "
                                   f"Motivo: Scaling Out Level {i+1} (+{level_sell*100:.1f}%)")

                        # Atualiza totais (FIX: só soma valor_vendido - taxa, não custo total)
                        montante += valor_vendido - taxa_venda_tranche
                        total_taxas += taxa_venda_tranche
                        lucro_parcial = (valor_vendido - taxa_venda_tranche) - (btc_vendido * tranche['preco_compra'])
                        lucro += lucro_parcial
                        lucros[op-1] += lucro_parcial  # Adiciona ao lucro da operação atual

                        # Registra ponto de venda
                        sell_points.append((current_index - 1, current_price))

                        # Remove tranche da lista
                        tranches_vendidas_neste_step.append(tranche)
                        break

            # Remove tranches vendidas
            for tranche in tranches_vendidas_neste_step:
                btc_tranches.remove(tranche)

            # Atualiza btc_total
            btc_total = sum(t['btc'] for t in btc_tranches)

            # Verifica se todas as tranches foram vendidas (meta de lucro total atingida)
            if not btc_tranches:
                variacao_venda = (current_price - preco_btc_compra) / preco_btc_compra
                motivo_venda = "Meta de Lucro Total (Scaling Out)"
                sold = True

        # Venda antecipada: vende tudo se passou muito tempo e tem lucro mínimo
        elif elapsed_time >= max_duration_atual * time_percentage_to_sell and variacao_atual >= lucro_minimo and btc_tranches:
            preco_btc_venda = current_price
            variacao_venda = variacao_atual
            valor_venda, taxa_venda = mock_sell_bitcoin(btc_total, preco_btc_venda, current_time, "Venda Antecipada Total")
            total_taxas += taxa_venda
            lucro = valor_venda - custo
            imposto = lucro * 0.15 if valor_venda > 35000 and lucro > 0 else 0.0
            montante += valor_venda - taxa_venda  # FIX: soma valor_venda - taxa
            motivo_venda = "Venda Antecipada Total"
            sell_points.append((current_index - 1, preco_btc_venda))
            sold = True
            btc_total = 0
            btc_tranches = []  # FIX: zera btc_tranches
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
            # Não vende: espera o próximo ciclo (log reduzido)
            steps_sem_log += 1
            if abs(variacao_atual) > 0.005 or steps_sem_log >= 6:  # Log só variações >0.5% ou a cada 6 steps
                logging.debug(f"[MOCK] {current_time.strftime('%Y-%m-%d %H:%M:%S')} - Não vendeu: preço atual R${current_price:,.2f}, variação acumulada {variacao_atual*100:.2f}%")
                steps_sem_log = 0

            # Verifica se chegou ao fim dos dados históricos
            if historical_prices and current_index >= len(historical_prices):
                logging.info("Fim dos dados históricos alcançado durante monitoramento - posição mantida aberta")
                # Calcula lucro potencial das tranches restantes
                if btc_tranches:
                    valor_potencial = sum(tranche['btc'] * current_price for tranche in btc_tranches)
                    custo_restante = sum(tranche['btc'] * tranche['preco_compra'] for tranche in btc_tranches)
                    taxa_estimada = valor_potencial * taxa_transacao
                    lucro_potencial = valor_potencial - custo_restante - taxa_estimada
                    variacao_potencial = (valor_potencial - custo_restante) / custo_restante if custo_restante > 0 else 0

                    logging.info(f"Posição aberta mantida: {btc_total:.5f} BTC, lucro potencial R${lucro_potencial:,.2f} "
                               f"({variacao_potencial*100:.2f}%) baseado no último preço R${current_price:,.2f}")

                # Não força venda - mantém posição aberta
                motivo_venda = "Fim dos Dados (Posição Aberta)"
                variacao_venda = variacao_atual
                sold = True  # Termina o monitoramento mas não vende

    # Atualiza lucro da operação atual (já foi inicializado no início do loop)
    lucros[op-1] = lucro

    # Log da operação completa
    logging.info(f"Operação {op} concluída - Motivo: {motivo_venda}, Lucro: R${lucro:,.2f}, Montante atual: R${montante:,.2f}")

    total_lucro += lucro
    total_imposto += imposto
    precos_venda.append(preco_btc_venda)
    variacoes_compra.append(variacao_compra * 100)
    variacoes_venda.append(variacao_venda * 100)
    saldo_history.append(montante)

    # Atualiza o motivo da venda para a próxima iteração
    ultimo_motivo_venda = motivo_venda

    # Atualiza o tempo para a próxima operação
    if historical_timestamps and current_index < len(historical_timestamps):
        # Usa o próximo timestamp do CSV
        current_operation_time = historical_timestamps[current_index]
    else:
        # Fallback: tempo da venda + 1 hora
        current_operation_time = current_time + timedelta(hours=1)

    # Atualiza o preço atual para a próxima iteração
    last_price = preco_btc_venda

    # Atualiza o último tempo de operação para o relatório
    last_operation_time = current_time

    # Converte last_operation_time para datetime se for string (do estado salvo)
    if isinstance(last_operation_time, str):
        last_operation_time = datetime.fromisoformat(last_operation_time)

    # Salva estado a cada operação
    state = {
        'btc_total': btc_total,
        'btc_tranches': btc_tranches,  # Adicionado para scaling
        'montante': montante,
        'last_price': last_price,
        'ultimo_motivo_venda': ultimo_motivo_venda,
        'consecutive_losses': consecutive_losses,
        'cooldown_remaining': cooldown_remaining,
        'total_lucro': total_lucro,
        'total_imposto': total_imposto,
        'total_taxas': total_taxas,
        'lucros': lucros,
        'precos_venda': precos_venda,
        'variacoes_compra': variacoes_compra,
        'variacoes_venda': variacoes_venda,
        'buy_points': buy_points,
        'sell_points': sell_points,
        'saldo_history': saldo_history,
        'current_index': current_index,
        'current_operation_time': current_operation_time,
        'last_operation_time': last_operation_time,
        'current_operation': op + 1
    }
    save_bot_state(state)

    # Verifica se chegou ao fim dos dados históricos
    if historical_prices and current_index >= len(historical_prices):
        logging.info("Fim dos dados históricos alcançado. Finalizando simulação.")
        break

# Salva relatório final
def generate_final_report(final_time, btc_tranches_final, last_price_final):
    """Gera relatório detalhado da simulação."""
    # Calcula informações sobre posições abertas
    posicoes_abertas_info = ""
    if btc_tranches_final:
        btc_aberto = sum(t['btc'] for t in btc_tranches_final)
        custo_total_aberto = sum(t['btc'] * t['preco_compra'] for t in btc_tranches_final)
        valor_atual_aberto = btc_aberto * last_price_final
        taxa_estimada_aberta = valor_atual_aberto * taxa_transacao
        lucro_potencial = valor_atual_aberto - custo_total_aberto - taxa_estimada_aberta
        variacao_potencial = (valor_atual_aberto - custo_total_aberto) / custo_total_aberto if custo_total_aberto > 0 else 0

        # Detalhes por tranche
        tranches_detail = []
        for t in sorted(btc_tranches_final, key=lambda x: x['tranche_idx']):
            var_tranche = (last_price_final - t['preco_compra']) / t['preco_compra']
            lucro_tranche = (last_price_final * t['btc']) - (t['preco_compra'] * t['btc']) - (last_price_final * t['btc'] * taxa_transacao)
            tranches_detail.append(f"  Tranche {t['tranche_idx']+1}: {t['btc']:.5f} BTC @ R${t['preco_compra']:,.2f} "
                                 f"(var: {var_tranche*100:.2f}%, lucro pot: R${lucro_tranche:,.2f})")

        posicoes_abertas_info = f"""
POSIÇÕES ABERTAS:
- BTC em posição aberta: {btc_aberto:.5f} BTC
- Custo total das posições abertas: R${custo_total_aberto:,.2f}
- Valor atual estimado: R${valor_atual_aberto:,.2f}
- Lucro potencial não realizado: R${lucro_potencial:,.2f} ({variacao_potencial*100:.2f}%)
- Último preço usado: R${last_price_final:,.2f}
- Número de tranches abertas: {len(btc_tranches_final)}
- Detalhes por tranche:
{chr(10).join(tranches_detail)}"""

    report = f"""
=== RELATÓRIO FINAL DA SIMULAÇÃO ===

CONFIGURAÇÕES:
- Montante inicial: R${montante_inicial:,.2f}
- Número de operações: {qtd_operacoes}
- Meta de lucro: {meta_lucro*100:.1f}%
- Stop-loss: {stop_loss*100:.1f}%
- Taxa de transação: {taxa_transacao*100:.2f}%
- Usando dados históricos: {'Sim' if historical_prices else 'Não'}
- Tranches de compra: {' '.join(map(str, args.tranches_buy))} (níveis: {' '.join(map(str, args.levels_buy))})
- Tranches de venda: {' '.join(map(str, args.tranches_sell))} (níveis: {' '.join(map(str, args.levels_sell))})

RESULTADOS FINANCEIROS:
- Montante final: R${montante:,.2f}
- Lucro total: R${montante - montante_inicial:,.2f}  # Montante final - inicial
- Soma de todos os lucros: R${sum(lucros):,.2f}  # Soma dos lucros por operação (incluindo parciais)
- Imposto total pago: R${total_imposto:,.2f}
- Taxas totais pagas: R${total_taxas:,.2f}
- BTC final: {btc_total:.5f} BTC{posicoes_abertas_info}

ESTATÍSTICAS:
- Total de operações realizadas: {len(lucros)}
- Operações com lucro: {sum(1 for l in lucros if l > 0)}
- Operações com prejuízo: {sum(1 for l in lucros if l < 0)}
- Pontos de compra: {len(buy_points)}
- Pontos de venda: {len(sell_points)}

PERÍODO:
- Data início: {start_operation_time.strftime('%Y-%m-%d %H:%M:%S')}
- Data fim: {final_time.strftime('%Y-%m-%d %H:%M:%S')}
- Duração total: {(final_time - start_operation_time).total_seconds() / 3600:.1f} horas

GESTÃO DE RISCO:
- Máximo de dobras consecutivas: {args.max_dobrar}
- Cooldown após stop-loss: {args.cooldown_steps} steps
- Taxa de câmbio USD/BRL: {args.taxa_cambio}
"""

    # Salva relatório em arquivo
    with open('relatorio_final.txt', 'w', encoding='utf-8') as f:
        f.write(report)

    logging.info("Relatório final salvo em 'relatorio_final.txt'")
    print(report)  # Também mostra no console

generate_final_report(last_operation_time, btc_tranches, last_price)

# Gráfico melhorado
def create_enhanced_graph():
    """Cria gráfico melhorado com preços históricos, pontos de buy/sell e saldo."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

    # Gráfico superior: Preços históricos com pontos de buy/sell
    if historical_prices:
        x_prices = range(len(historical_prices))
        ax1.plot(x_prices, historical_prices, color='blue', linewidth=1, label='Preço BTC Histórico (R$)')

        # Pontos de compra (verde)
        if buy_points:
            buy_indices, buy_prices = zip(*buy_points)
            ax1.scatter(buy_indices, buy_prices, color='green', s=100, marker='^', label='Compras', zorder=5)

        # Pontos de venda (vermelho)
        if sell_points:
            sell_indices, sell_prices = zip(*sell_points)
            ax1.scatter(sell_indices, sell_prices, color='red', s=100, marker='v', label='Vendas', zorder=5)

        ax1.set_ylabel('Preço BTC (R$)', color='blue')
        ax1.set_title('Simulação do Bot com Dados Históricos Horários (Dez/2025 - Jan/2026)')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
    else:
        # Fallback para gráfico original se não houver dados históricos
        ax1.plot(range(1, len(lucros) + 1), precos_venda, marker='s', linestyle='-', color='g', label='Preço do Bitcoin (R$)')
        ax1.set_ylabel('Preço BTC (R$)')
        ax1.set_title('Simulação do Bot (Dados Sintéticos)')
        ax1.legend()

    # Gráfico inferior: Evolução do saldo
    x_saldo = range(1, len(saldo_history) + 1)
    ax2.plot(x_saldo, saldo_history, color='orange', linewidth=2, marker='o', markersize=4, label='Saldo (R$)')
    ax2.fill_between(x_saldo, saldo_history, alpha=0.3, color='orange')
    ax2.set_xlabel('Operação / Step')
    ax2.set_ylabel('Saldo (R$)', color='orange')
    ax2.set_title('Evolução do Saldo ao Longo da Simulação')
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)

    # Formatação
    plt.tight_layout()
    plt.savefig('simulacao_horaria.png', dpi=300, bbox_inches='tight')
    logging.info("Gráfico salvo como 'simulacao_horaria.png'")
    plt.show()

create_enhanced_graph()
