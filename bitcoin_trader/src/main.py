from __future__ import annotations

import sys
from pathlib import Path

from .config import parse_args
from .data_fetcher import DataFetcher
from .exchange_interface import BinanceExchange, CoinbaseExchange, MockExchange
from .reporter import create_graph, generate_report, graph_due_real, setup_logging
from .simulator import Simulator
from .trading_engine import TradingEngine
from .utils import ensure_dirs, validate_tranches


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    app_cfg, paths = parse_args(project_root)
    ensure_dirs(paths)

    logger = setup_logging(paths.log_file)

    try:
        validate_tranches(app_cfg.trading)
    except ValueError as exc:
        logger.error(f"Erro na validação dos parâmetros: {exc}")
        sys.exit(1)

    if app_cfg.mode == "fetch":
        fetcher = DataFetcher(paths)
        try:
            target_file = fetcher.fetch(app_cfg.fetch)
            logger.info(f"Arquivo CSV gerado com sucesso: '{target_file}'")
            print(f"CSV salvo em {target_file}")
        except Exception as exc:  # pragma: no cover - caminho feliz coberto
            logger.error(f"Falha ao buscar dados: {exc}")
            sys.exit(1)
        return

    exchange = _resolve_exchange(app_cfg.exchange, app_cfg.trading.taxa_transacao, logger)
    engine = TradingEngine(app_cfg.trading, exchange, logger)
    simulator = Simulator(engine, paths, logger)

    if app_cfg.mode == "test":
        if not app_cfg.csv_file:
            logger.error("Modo test requer --csv-file")
            sys.exit(1)
        state, market, start_time = simulator.run_test(app_cfg.csv_file, app_cfg.trading)
        report = generate_report(
            state,
            app_cfg.trading,
            app_cfg.trading.montante,
            start_time,
            state.last_operation_time,
            paths.outputs_dir,
            historical_used=True,
        )
        print(report)
        if app_cfg.output_graph:
            graph_path = create_graph(state, market, paths.outputs_dir)
            logger.info(f"Gráfico salvo em {graph_path}")

    elif app_cfg.mode == "real":
        state, market, start_time = simulator.run_real(app_cfg.trading)
        report = generate_report(
            state,
            app_cfg.trading,
            app_cfg.trading.montante,
            start_time,
            state.last_operation_time,
            paths.outputs_dir,
            historical_used=False,
        )
        print(report)
        if app_cfg.output_graph and graph_due_real(app_cfg.force_graph):
            graph_path = create_graph(state, market, paths.outputs_dir)
            logger.info(f"Gráfico (modo real) salvo em {graph_path}")
        elif app_cfg.output_graph:
            logger.info("Gráfico não gerado (modo real) - janela diária é 00:00:00. Use --force-graph para forçar.")


def _resolve_exchange(name: str, taxa_transacao: float, logger):
    if name == "mock":
        return MockExchange(taxa_transacao=taxa_transacao, logger=logger)
    if name == "binance":
        return BinanceExchange()
    if name == "coinbase":
        return CoinbaseExchange()
    raise ValueError(f"Exchange desconhecida: {name}")


if __name__ == "__main__":
    main()
