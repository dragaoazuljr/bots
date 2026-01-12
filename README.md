# Bot de Trading de Bitcoin - Simulação Melhorada

Este script simula operações de compra e venda de Bitcoin com estratégias de take-profit, stop-loss e dados históricos reais.

##  Funcionalidades

- **Simulação com Dados Históricos**: Usa preços reais do Bitcoin em granularidade horária
- **Scaling In/Out Avançado**: Compra em tranches progressivas durante dips e vende em níveis de lucro
- **Gestão de Risco Avançada**: Stop-loss, take-profit, cooldown e limite de dobras consecutivas
- **Persistência de Estado**: Salva/carrega estado entre execuções (incluindo tranches pendentes)
- **Logging Estruturado**: Logs detalhados em arquivo e console
- **Relatórios Detalhados**: Análise completa dos resultados incluindo posições abertas
- **Gráficos Interativos**: Visualização de preços, pontos de buy/sell e evolução do saldo
- **Configuração Flexível**: Parâmetros via linha de comando

## Pré-requisitos

```bash
pip install -r requirements.txt
```

## Como Usar

### Execução Básica com Dados Históricos
```bash
python buy-bitcoin-bot.py --csv_file bitcoin_hourly_usd_last_30days.csv
```

### Execução com Parâmetros Personalizados
```bash
python buy-bitcoin-bot.py \
  --montante 20000 \
  --qtd_operacoes 10 \
  --meta_lucro 0.15 \
  --stop_loss -0.08 \
  --csv_file bitcoin_hourly_usd_last_30days.csv \
  --taxa_cambio 5.8 \
  --cooldown_steps 3 \
  --max_dobrar 2
```

### Execução com Scaling In/Out
```bash
python buy-bitcoin-bot.py \
  --csv_file bitcoin_hourly_usd_last_30days.csv \
  --tranches_buy 0.25 0.25 0.25 0.25 \
  --levels_buy -0.005 -0.01 -0.015 -0.02 \
  --tranches_sell 0.25 0.25 0.25 0.25 \
  --levels_sell 0.005 0.01 0.02 0.03
```

### Execução sem Dados Históricos (Preços Sintéticos)
```bash
python buy-bitcoin-bot.py --montante 10000 --qtd_operacoes 30
```

## Parâmetros

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `--montante` | 10000 | Montante inicial em BRL |
| `--qtd_operacoes` | 30 | Número de operações |
| `--meta_lucro` | 0.1 | Meta de lucro (10%) |
| `--stop_loss` | -0.05 | Stop-loss (-5%) |
| `--csv_file` | None | Arquivo CSV com dados históricos |
| `--taxa_cambio` | 5.5 | USD/BRL |
| `--cooldown_steps` | 5 | Cooldown após stop-loss |
| `--max_dobrar` | 3 | Máximo de dobras consecutivas |
| `--tranches_buy` | 0.2 0.3 0.5 | Frações para compras parciais |
| `--levels_buy` | -0.01 -0.02 -0.03 | Níveis % para comprar tranches |
| `--tranches_sell` | 0.2 0.3 0.5 | Frações para vendas parciais |
| `--levels_sell` | 0.01 0.03 0.05 | Níveis % para vender tranches |

## Formato do CSV

O arquivo CSV deve ter as colunas:
- `Timestamp_ms`: Timestamp em milissegundos
- `Datetime`: Data/hora formatada
- `Price_USD`: Preço em USD

Exemplo:
```
Timestamp_ms,Datetime,Price_USD
1765634509734,2025-12-13 11:01:49,90256.15
1765638088897,2025-12-13 12:01:28,90105.01
```

## Arquivos Gerados

- `bot_log.txt`: Logs detalhados da execução
- `bot_state.json`: Estado salvo para continuar simulações
- `relatorio_final.txt`: Relatório completo dos resultados
- `simulacao_horaria.png`: Gráfico da simulação

## Testes

Execute os testes unitários:
```bash
python test_bot.py
```

## Estratégia de Trading

### Scaling In (Compras Parciais)
1. **Compra Progressiva**: Divide o montante em tranches compradas em diferentes níveis de dip
2. **Exemplo**: Com `--tranches_buy 0.2 0.3 0.5` e `--levels_buy -0.01 -0.02 -0.03`:
   - Compra 20% do montante quando preço cai 1%
   - Compra mais 30% quando cai 2%
   - Compra os 50% restantes quando cai 3%

### Scaling Out (Vendas Parciais)
3. **Venda Progressiva**: Vende tranches em níveis de lucro crescentes usando FIFO
4. **Exemplo**: Com `--tranches_sell 0.2 0.3 0.5` e `--levels_sell 0.01 0.03 0.05`:
   - Vende 20% quando lucro atinge 1%
   - Vende mais 30% quando atinge 3%
   - Vende os 50% restantes quando atinge 5%

### Condições de Venda Automática
5. **Stop-loss Total**: Vende tudo se perde mais que o limite configurado
6. **Meta de Lucro Total**: Completa quando todas as tranches são vendidas
7. **Venda Antecipada**: Vende tudo com lucro mínimo após 50% do tempo
8. **Fim dos Dados**: Mantém posições abertas (não força venda) e calcula lucro potencial

### Gestão de Risco
9. **Dobrar Aposta**: Após stop-loss (máx. 3 vezes consecutivas)
10. **Cooldown**: Pausa após stop-loss
11. **Imposto**: 15% para vendas > R$35k com lucro

## Logs e Debugging

Os logs incluem:
- Operações de compra/venda
- Decisões de trading
- Erros e validações
- Estatísticas finais

Para debug mais detalhado, ajuste o nível de logging no código.

## Avisos

- Script para fins educacionais/simulação
- Não use para trading real sem validação
- Consulte assessoria financeira para investimentos
- Impostos calculados conforme legislação brasileira

## Contribuições

Sinta-se à vontade para melhorar o código e adicionar funcionalidades!
