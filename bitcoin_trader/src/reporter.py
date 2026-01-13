from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import matplotlib
import matplotlib.pyplot as plt

from .models import BotState, MarketData, TradingParams

# Usa backend não interativo
matplotlib.use("Agg")


def setup_logging(log_file: Path) -> logging.Logger:
    logger = logging.getLogger("bitcoin-bot")
    logger.setLevel(logging.INFO)

    # Evita duplicar handlers em execuções subsequentes
    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


def generate_report(
    state: BotState,
    params: TradingParams,
    montante_inicial: float,
    start_operation_time: datetime,
    final_time: datetime,
    outputs_dir: Path,
    historical_used: bool,
) -> str:
    report = f"""
=== RELATÓRIO FINAL DA SIMULAÇÃO ===

CONFIGURAÇÕES:
- Montante inicial: R${montante_inicial:,.2f}
- Número de operações: {params.qtd_operacoes}
- Meta de lucro: {params.meta_lucro*100:.1f}%
- Stop-loss: {params.stop_loss*100:.1f}%
- Taxa de transação: {params.taxa_transacao*100:.2f}%
- Usando dados históricos: {'Sim' if historical_used else 'Não'}
- Tranches de compra: {' '.join(map(str, params.tranches_buy))} (níveis: {' '.join(map(str, params.levels_buy))})
- Tranches de venda: {' '.join(map(str, params.tranches_sell))} (níveis: {' '.join(map(str, params.levels_sell))})

RESULTADOS FINANCEIROS:
- Montante final: R${state.montante:,.2f}
- Lucro total: R${state.montante - montante_inicial:,.2f}
- Soma de todos os lucros: R${sum(state.lucros):,.2f}
- Imposto total pago: R${state.total_imposto:,.2f}
- Taxas totais pagas: R${state.total_taxas:,.2f}
- BTC final: {state.btc_total:.5f} BTC

ESTATÍSTICAS:
- Total de operações realizadas: {len(state.lucros)}
- Operações com lucro: {sum(1 for l in state.lucros if l > 0)}
- Operações com prejuízo: {sum(1 for l in state.lucros if l < 0)}
- Pontos de compra: {len(state.buy_points)}
- Pontos de venda: {len(state.sell_points)}

PERÍODO:
- Data início: {start_operation_time.strftime('%Y-%m-%d %H:%M:%S')}
- Data fim: {final_time.strftime('%Y-%m-%d %H:%M:%S')}
- Duração total: {(final_time - start_operation_time).total_seconds() / 3600:.1f} horas

GESTÃO DE RISCO:
- Máximo de dobras consecutivas: {params.max_dobrar}
- Cooldown após stop-loss: {params.cooldown_steps} steps
- Taxa de câmbio USD/BRL: {params.taxa_cambio}
"""
    # Adicionar detalhes das operações
    if state.operation_details:
        report += "\nDETALHES DAS OPERAÇÕES:\n"
        for op_detail in state.operation_details:
            report += f"""
Operação #{op_detail['operation_id']}:
- Motivo venda: {op_detail['motivo_venda']}
- Lucro: R${op_detail['lucro']:,.2f}
- Compra média: R${op_detail['preco_compra']:,.2f} | Venda média: R${op_detail['preco_venda']:,.2f}
- BTC total: {op_detail['btc_comprado']:.5f} | Custo total: R${op_detail['custo_total']:,.2f}
- Período: {op_detail['start_time'].strftime('%Y-%m-%d %H:%M:%S')} até {op_detail['end_time'].strftime('%Y-%m-%d %H:%M:%S')}
"""

    outputs_dir.mkdir(parents=True, exist_ok=True)
    (outputs_dir / "relatorio_final.txt").write_text(report, encoding="utf-8")
    return report


def create_graph(state: BotState, market: Optional[MarketData], outputs_dir: Path) -> Path:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))

    if market and market.prices:
        x_prices = range(len(market.prices))
        ax1.plot(x_prices, market.prices, color="blue", linewidth=1, label="Preço BTC Histórico (R$)")
        if state.buy_points:
            buy_indices, buy_prices = zip(*state.buy_points)
            ax1.scatter(buy_indices, buy_prices, color="green", s=100, marker="^", label="Compras", zorder=5)
        if state.sell_points:
            sell_indices, sell_prices = zip(*state.sell_points)
            ax1.scatter(sell_indices, sell_prices, color="red", s=100, marker="v", label="Vendas", zorder=5)
        ax1.set_ylabel("Preço BTC (R$)", color="blue")
        ax1.set_title("Simulação do Bot com Dados Históricos")
        ax1.legend(loc="upper left")
        ax1.grid(True, alpha=0.3)
    else:
        ax1.plot(range(1, len(state.lucros) + 1), state.precos_venda, marker="s", linestyle="-", color="g", label="Preço BTC (R$)")
        ax1.set_ylabel("Preço BTC (R$)")
        ax1.set_title("Simulação do Bot (Dados Sintéticos)")
        ax1.legend()

    if state.saldo_history:
        x_saldo = range(1, len(state.saldo_history) + 1)
        ax2.plot(x_saldo, state.saldo_history, color="orange", linewidth=2, marker="o", markersize=4, label="Saldo (R$)")
        ax2.fill_between(x_saldo, state.saldo_history, alpha=0.3, color="orange")
        ax2.set_xlabel("Operações Executadas")
        ax2.set_ylabel("Saldo (R$)", color="orange")
        ax2.set_title("Evolução do Saldo por Operação Executada")
    else:
        ax2.text(0.5, 0.5, "Nenhuma operação executada", ha="center", va="center", transform=ax2.transAxes)
        ax2.set_xlabel("Operações Executadas")
        ax2.set_ylabel("Saldo (R$)", color="orange")
        ax2.set_title("Evolução do Saldo por Operação Executada")
    ax2.legend(loc="upper left")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    outputs_dir.mkdir(parents=True, exist_ok=True)
    graph_path = outputs_dir / "simulacao_horaria.png"
    plt.savefig(graph_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return graph_path


def graph_due_real(force: bool = False) -> bool:
    now = datetime.now()
    if force:
        return True
    # janela curta próxima da meia-noite
    return now.hour == 0
