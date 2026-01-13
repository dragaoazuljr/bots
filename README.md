# Bots de Trading e Análise

Coleção de bots automatizados para trading e análise de criptomoedas, desenvolvidos em Python com foco em modularidade e testes.

## Estrutura do Projeto

```
bots/
├── bitcoin_trader/          # Bot de trading de Bitcoin
│   ├── src/                 # Código fonte principal
│   ├── tests/               # Testes unitários
│   ├── data/                # Dados históricos (ignorados no git)
│   └── outputs/             # Logs, gráficos e relatórios
├── .gitignore
└── requirements.txt
```

## Bitcoin Trader

**Status**: Funcional

Bot de trading automatizado para Bitcoin com estratégia de scaling in/out. Características principais:

- **Estratégia**: Compra em dips (scaling in) e vende em lucros (scaling out)
- **Simulação**: Teste com dados históricos em CSV
- **Modular**: Separação clara entre engine de trading, exchange e dados
- **Configurável**: Parâmetros CLI para estratégia, risco e montante
- **Análise**: Geração automática de gráficos e relatórios detalhados

### Início Rápido

```bash
# Instalar dependências
pip install -r requirements.txt

# Buscar dados históricos
python -m bitcoin_trader.src.main fetch --days 30

# Executar simulação
python -m bitcoin_trader.src.main test --csv-file bitcoin_trader/data/bitcoin_hourly_usd_last_30days.csv --montante 10000

# Ver resultados em outputs/
```

### Funcionalidades

- Simulação histórica com dados reais
- Estratégia de scaling in/out configurável
- Gestão de risco (stop-loss, cooldown)
- Relatórios e gráficos automáticos
- Logging detalhado para debug
- Modo real (mock por enquanto)

Para mais detalhes, consulte `bitcoin_trader/README.md`.

## Tecnologias

- **Python 3.8+**
- **Pandas** - Análise de dados
- **Matplotlib** - Visualização
- **Logging** - Monitoramento
- **Argparse** - CLI

## Licença

Este projeto é para fins educacionais. Use por sua conta e risco.

## Contribuições

Sinta-se à vontade para contribuir com novos bots ou melhorias!