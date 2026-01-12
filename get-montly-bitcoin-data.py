import os
import time
import csv
import argparse
from datetime import datetime, timedelta
from pycoingecko import CoinGeckoAPI

parser = argparse.ArgumentParser(description='Buscar dados do bitcoin')
parser.add_argument('--days', type=int, default=30, help='Quantidade de dias a buscar (default: 30)')

args = parser.parse_args()
days = args.days

# Pega a chave da variável de ambiente (opcional - Pro API)
api_key = os.getenv('COINGECKO_API_KEY')

# Cria o client (com ou sem chave Pro)
cg = CoinGeckoAPI(api_key) if api_key else CoinGeckoAPI()

# Calcula o intervalo: último mês (~30 dias)
to_timestamp = int(time.time())                  # agora
from_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())

print(f"Buscando dados de {datetime.fromtimestamp(from_timestamp)} até {datetime.fromtimestamp(to_timestamp)}")

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
filename = 'bitcoin_hourly_usd_last_'+ str(days) +'days.csv'
 
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
print("Para o último mês inteiro, você deve ter ~720 linhas (~hora em hora).")
