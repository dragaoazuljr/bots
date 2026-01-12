# Bot de Trading de Bitcoin - Simulação Melhorada

Este script simula operações de compra e venda de Bitcoin com estratégias de take-profit, stop-loss e dados históricos reais.

##  Funcionalidades

- **Simulação com Dados Históricos**: Usa preços reais do Bitcoin em granularidade horária
- **Gestão de Risco Avançada**: Stop-loss, take-profit, cooldown e limite de dobras consecutivas
- **Persistência de Estado**: Salva/carrega estado entre execuções
- **Logging Estruturado**: Logs detalhados em arquivo e console
- **Relatórios Detalhados**: Análise completa dos resultados
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

1. **Compra**: Início de cada operação
2. **Monitoramento**: Verificação horária por até 24h (48h se dobrar)
3. **Venda Automática**:
   - Take-profit: +10% (ou +20% se dobrar)
   - Stop-loss: -5% (ou -10% se dobrar)
   - Venda antecipada: +3% após 50% do tempo
   - Fim do período: vende ao preço atual
4. **Gestão de Risco**:
   - Dobrar aposta após stop-loss (máx. 3 vezes)
   - Cooldown de 5 horas após stop-loss
   - Imposto de 15% para vendas > R$35k com lucro

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
