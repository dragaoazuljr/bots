# Bot de Trading de Bitcoin (modular)

Projeto modular para simular operações de compra/venda de Bitcoin, coletar dados históricos e gerar relatórios/gráficos. A estrutura separa coleta de dados, motor de trading, simulador e interfaces de exchange (mock + stubs para futuras integrações).

## Estrutura

```
src/
  main.py              # CLI (fetch/test/real)
  config.py            # Parsing de argumentos e configs
  data_fetcher.py      # Coleta CoinGecko → CSV
  exchange_interface.py# Abstração e Mock de exchange
  trading_engine.py    # Lógica de compra/venda
  simulator.py         # Orquestra modos test/real
  reporter.py          # Logs, relatório e gráfico
  utils.py             # Helpers (estado, CSV, validações)
tests/
  test_exchange_mock.py
  test_trading_engine.py
  test_simulator.py
data/                  # CSVs históricos (ignorados no git)
outputs/               # Logs, estado, relatórios e gráficos (ignorados)
```

## Instalação

```bash
pip install -r requirements.txt
```

## Modos da CLI

Use `python -m src.main <modo> [opções]`.

### 1) Buscar histórico (CoinGecko)
```bash
python -m src.main fetch --days 30
python -m src.main fetch --start-date 2025-12-01 --end-date 2025-12-31
```
Saída: CSV em `data/`.

### 2) Simulação com CSV (modo test)
```bash
python -m src.main test \
  --csv-file data/bitcoin_hourly_usd_last_30days.csv \
  --montante 20000 \
  --qtd-operacoes 10 \
  --meta-lucro 0.15 \
  --stop-loss -0.08 \
  --taxa-cambio 5.8 \
  --cooldown-steps 3 \
  --max-dobrar 2 \
  --tranches-buy 0.25 0.25 0.25 0.25 \
  --levels-buy -0.005 -0.01 -0.015 -0.02 \
  --tranches-sell 0.25 0.25 0.25 0.25 \
  --levels-sell 0.005 0.01 0.02 0.03
```
Gráfico e relatório sempre gerados ao final em `outputs/`.

### 3) Modo real (exchange mock por enquanto)
```bash
python -m src.main real --exchange mock --montante 10000
```
- Gera relatório sempre.
- Gera gráfico diariamente às 00:00:00 (use `--force-graph` para forçar).

## Parâmetros principais

| Parâmetro              | Padrão  | Descrição |
|------------------------|---------|-----------|
| `--montante`           | 10000   | Montante inicial (BRL) |
| `--qtd-operacoes`      | 30      | Nº de operações |
| `--meta-lucro`         | 0.1     | Meta de lucro (10%) |
| `--stop-loss`          | -0.05   | Stop-loss (-5%) |
| `--taxa-cambio`        | 5.5     | USD/BRL para CSV |
| `--cooldown-steps`     | 5       | Cooldown após stop-loss |
| `--max-dobrar`         | 3       | Máx. dobras consecutivas |
| `--tranches-buy`       | 0.2 0.3 0.5 | Frações de compra |
| `--levels-buy`         | -0.01 -0.02 -0.03 | Níveis (%) de compra |
| `--tranches-sell`      | 0.2 0.3 0.5 | Frações de venda |
| `--levels-sell`        | 0.01 0.03 0.05 | Níveis (%) de venda |
| `--max-steps-in`       | 168 | Máx. steps/horas para completar scaling in |

Validações garantem que as tranches somam 1.0 e que níveis de compra são negativos e de venda positivos.

## Formato do CSV (modo test)

Colunas esperadas: `Timestamp_ms`, `Datetime`, `Price_USD` (ou `Close`). Timestamps são convertidos para `datetime`, preços são convertidos para BRL via `--taxa-cambio`.

## Saídas

- `outputs/bot_log.txt`: logs da execução
- `outputs/bot_state.json`: estado persistente
- `outputs/relatorio_final.txt`: relatório final
- `outputs/simulacao_horaria.png`: gráfico

## Testes

```bash
pytest
```
