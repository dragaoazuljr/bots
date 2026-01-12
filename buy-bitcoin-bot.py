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
parser.add_argument('--montante', type=float, default=10000, help='Montante inicial em reais (default: 10000)')
parser.add_argument('--qtd_operacoes', type=int, default=30, help='Quantidade de operações (default: 30)')
parser.add_argument('--meta_lucro', type=float, default=0.1, help='Meta de lucro percentual (default: 0.1 = 10%)')
parser.add_argument('--stop_loss', type=float, default=-0.05, help='Stop-loss percentual (default: -0.05 = -5%)')
parser.add_argument('--csv_file', type=str, help='Arquivo CSV com dados históricos horários (formato Binance)')
parser.add_argument('--taxa_cambio', type=float, default=5.5, help='Taxa de câmbio USD/BRL (default: 5.5)')
parser.add_argument('--cooldown_steps', type=int, default=5, help='Cooldown em steps após stop-loss (default: 5)')
parser.add_argument('--max_dobrar', type=int, default=3, help='Máximo de dobras consecutivas (default: 3)')

args = parser.parse_args()

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

total_lucro = saved_state.get('total_lucro', 0.0) if saved_state else 0.0
total_imposto = saved_state.get('total_imposto', 0.0) if saved_state else 0.0
total_taxas = saved_state.get('total_taxas', 0.0) if saved_state else 0.0
lucros = saved_state.get('lucros', []) if saved_state else []  # Lucros acumulados
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

for op in range(start_op, qtd_operacoes + 1):
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

    # Obtém o preço de compra
    if historical_prices and current_index < len(historical_prices):
        preco_btc_compra = historical_prices[current_index]
        current_index += 1
    else:
        preco_btc_compra = mock_get_bitcoin_price()

    variacao_compra = ((preco_btc_compra - last_price) / last_price) if last_price != 0 else 0.0

    # Compra
    btc_comprado, taxa_compra = mock_buy_bitcoin(montante, preco_btc_compra, simulated_start_time, dobrar_aposta, stop_loss_atual, meta_lucro_atual, max_duration_atual)
    btc_total = btc_comprado
    custo = btc_comprado * preco_btc_compra
    total_taxas += taxa_compra

    # Registra ponto de compra
    buy_points.append((current_index - 1, preco_btc_compra))

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
            cooldown_remaining = args.cooldown_steps  # Inicia cooldown
            sell_points.append((current_index - 1, preco_btc_venda))
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
            sell_points.append((current_index - 1, preco_btc_venda))
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
            sell_points.append((current_index - 1, preco_btc_venda))
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
            logging.info(f"[MOCK] {current_time.strftime('%Y-%m-%d %H:%M:%S')} - Não vendeu: preço atual R${current_price:,.2f}, variação acumulada {variacao_atual*100:.2f}%")

            # Verifica se chegou ao fim dos dados históricos
            if historical_prices and current_index >= len(historical_prices):
                logging.info("Fim dos dados históricos alcançado durante monitoramento")
                # Força venda ao preço atual
                preco_btc_venda = current_price
                variacao_venda = variacao_atual
                valor_venda, taxa_venda = mock_sell_bitcoin(btc_total, preco_btc_venda, current_time, "Fim dos Dados")
                total_taxas += taxa_venda
                lucro = valor_venda - custo
                imposto = lucro * 0.15 if valor_venda > 35000 and lucro > 0 else 0.0
                montante = valor_venda - taxa_venda
                motivo_venda = "Fim dos Dados"
                sell_points.append((current_index - 1, preco_btc_venda))
                sold = True

    # Log da operação completa
    logging.info(f"Operação {op} concluída - Motivo: {motivo_venda}, Lucro: R${lucro:,.2f}, Montante atual: R${montante:,.2f}")

    total_lucro += lucro
    total_imposto += imposto
    lucros.append(total_lucro)
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

    # Salva estado a cada operação
    state = {
        'btc_total': btc_total,
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
def generate_final_report(final_time):
    """Gera relatório detalhado da simulação."""
    report = f"""
=== RELATÓRIO FINAL DA SIMULAÇÃO ===

CONFIGURAÇÕES:
- Montante inicial: R${montante_inicial:,.2f}
- Número de operações: {qtd_operacoes}
- Meta de lucro: {meta_lucro*100:.1f}%
- Stop-loss: {stop_loss*100:.1f}%
- Taxa de transação: {taxa_transacao*100:.2f}%
- Usando dados históricos: {'Sim' if historical_prices else 'Não'}

RESULTADOS FINANCEIROS:
- Montante final: R${montante:,.2f}
- Lucro total: R${montante - montante_inicial:,.2f}
- Soma de todos os lucros: R${total_lucro:,.2f}
- Imposto total pago: R${total_imposto:,.2f}
- Taxas totais pagas: R${total_taxas:,.2f}
- BTC final: {btc_total:.5f} BTC

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

generate_final_report(last_operation_time)

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
