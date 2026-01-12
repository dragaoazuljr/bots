import os
import time
import csv
import argparse
from datetime import datetime, timedelta
from pycoingecko import CoinGeckoAPI

parser = argparse.ArgumentParser(description='Buscar dados do bitcoin')
parser.add_argument('--days', type=int, default=30, help='Quantidade de dias a buscar (default: 30)')
parser.add_argument('--start-date', type=str, help='Data inicial no formato YYYY-MM-DD')
parser.add_argument('--end-date', type=str, help='Data final no formato YYYY-MM-DD')

args = parser.parse_args()

# Validação das datas
if args.start_date and args.end_date:
    try:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        if start_date >= end_date:
            raise ValueError("A data inicial deve ser anterior à data final")
    except ValueError as e:
        print(f"Erro nas datas fornecidas: {e}")
        print("Use o formato YYYY-MM-DD para as datas")
        exit(1)
elif args.start_date or args.end_date:
    print("Erro: Você deve fornecer tanto --start-date quanto --end-date")
    exit(1)
else:
    # Usa o modo antigo com --days
    start_date = datetime.now() - timedelta(days=args.days)
    end_date = datetime.now()

# Pega a chave da variável de ambiente (opcional - Pro API)
api_key = os.getenv('COINGECKO_API_KEY')

# Cria o client (com ou sem chave Pro)
cg = CoinGeckoAPI(api_key) if api_key else CoinGeckoAPI()

# Calcula os timestamps baseado nas datas fornecidas
from_timestamp = int(start_date.timestamp())
to_timestamp = int(end_date.timestamp())

print(f"Buscando dados de {start_date} até {end_date}")

# Busca os dados históricos (preço, market cap, volume)
# A API retorna automaticamente granularidade:
#   - minutely (até ~1-2 dias)
#   - hourly   (até ~90 dias)
#   - daily    (mais de 90 dias)
data = cg.get_coin_market_chart_range_by_id(
    id='bitcoin',
    vs_currency='usd',
    from_timestamp=from_timestamp,
    to_timestamp=to_timestamp
)

# Os preços vêm em: [[timestamp_ms, price], ...]
prices = data['prices']

# Nome do arquivo CSV
if args.start_date and args.end_date:
    filename = f"bitcoin_data_{args.start_date}_to_{args.end_date}.csv"
else:
    filename = f'bitcoin_hourly_usd_last_{args.days}days.csv'
 
# Escreve no CSV
with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Timestamp_ms', 'Datetime', 'Price_USD'])
    
    for ts_ms, price in prices:
        # Converte timestamp milissegundos → segundos → data legível
        dt = datetime.fromtimestamp(ts_ms / 1000)
        datetime_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        
        writer.writerow([ts_ms, datetime_str, round(price, 2)])  # arredonda pra 2 casas

print(f"Arquivo CSV gerado com sucesso: '{filename}'")
print(f"Total de pontos coletados: {len(prices)}")

# Mensagem informativa baseada no modo usado
if args.start_date and args.end_date:
    days_diff = (end_date - start_date).days
    if days_diff <= 90:
        print("Para intervalos de até 90 dias, os dados são retornados hora a hora.")
    else:
        print("Para intervalos maiores que 90 dias, os dados são retornados diariamente.")
else:
    print("Para o último mês inteiro, você deve ter ~720 linhas (~hora em hora).")
