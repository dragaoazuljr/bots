from __future__ import annotations

import argparse
from pathlib import Path
from typing import Tuple

from .models import AppConfig, FetchConfig, Paths, TradingParams


def default_paths(project_root: Path) -> Paths:
    outputs_dir = project_root / "outputs"
    data_dir = project_root / "data"
    return Paths(
        root=project_root,
        data_dir=data_dir,
        outputs_dir=outputs_dir,
        state_file=outputs_dir / "bot_state.json",
        log_file=outputs_dir / "bot_log.txt",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bots de trading e coleta de dados do Bitcoin")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # Subcomando: fetch
    fetch_parser = subparsers.add_parser("fetch", help="Baixar histórico de preços do Bitcoin (CoinGecko)")
    fetch_parser.add_argument("--days", type=int, default=30, help="Quantidade de dias a buscar (default: 30)")
    fetch_parser.add_argument("--start-date", type=str, help="Data inicial YYYY-MM-DD")
    fetch_parser.add_argument("--end-date", type=str, help="Data final YYYY-MM-DD")

    # Subcomando: test (simulação com CSV)
    test_parser = subparsers.add_parser("test", help="Rodar simulação com dados históricos (CSV)")
    _add_trading_arguments(test_parser)
    test_parser.add_argument("--csv-file", type=Path, required=True, help="Arquivo CSV com preços históricos")

    # Subcomando: real (modo real usando exchange - mock por enquanto)
    real_parser = subparsers.add_parser("real", help="Rodar em modo real (usa exchange mock por ora)")
    _add_trading_arguments(real_parser)
    real_parser.add_argument("--exchange", choices=["mock", "binance", "coinbase"], default="mock")
    real_parser.add_argument(
        "--force-graph",
        action="store_true",
        help="Força geração de gráfico mesmo fora do horário planejado (meia-noite)",
    )

    return parser


def _add_trading_arguments(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument("--montante", type=float, default=10000, help="Montante inicial em reais")
    subparser.add_argument("--qtd-operacoes", type=int, default=30, help="Quantidade de operações")
    subparser.add_argument("--meta-lucro", type=float, default=0.1, help="Meta de lucro percentual (0.1 = 10%)")
    subparser.add_argument("--stop-loss", type=float, default=-0.05, help="Stop-loss percentual (-0.05 = -5%)")
    subparser.add_argument("--taxa-cambio", type=float, default=5.5, help="Taxa de câmbio USD/BRL")
    subparser.add_argument("--cooldown-steps", type=int, default=5, help="Cooldown em steps após stop-loss")
    subparser.add_argument("--max-dobrar", type=int, default=3, help="Máximo de dobras consecutivas")
    subparser.add_argument(
        "--tranches-buy",
        nargs="+",
        type=float,
        default=[0.2, 0.3, 0.5],
        help="Frações de tranches para compras parciais",
    )
    subparser.add_argument(
        "--levels-buy",
        nargs="+",
        type=float,
        default=[-0.01, -0.02, -0.03],
        help="Níveis percentuais para comprar tranches",
    )
    subparser.add_argument(
        "--tranches-sell",
        nargs="+",
        type=float,
        default=[0.2, 0.3, 0.5],
        help="Frações de tranches para vendas parciais",
    )
    subparser.add_argument(
        "--levels-sell",
        nargs="+",
        type=float,
        default=[0.01, 0.03, 0.05],
        help="Níveis percentuais para vender tranches",
    )
    subparser.add_argument(
        "--max-steps-in",
        type=int,
        default=168,
        help="Máximo de steps/horas para completar scaling in. Default: 168",
    )


def parse_args(project_root: Path) -> Tuple[AppConfig, Paths]:
    parser = build_parser()
    args = parser.parse_args()

    trading = TradingParams(
        montante=args.montante if hasattr(args, "montante") else 10000.0,
        qtd_operacoes=args.qtd_operacoes if hasattr(args, "qtd_operacoes") else 30,
        meta_lucro=args.meta_lucro if hasattr(args, "meta_lucro") else 0.1,
        stop_loss=args.stop_loss if hasattr(args, "stop_loss") else -0.05,
        taxa_cambio=args.taxa_cambio if hasattr(args, "taxa_cambio") else 5.5,
        cooldown_steps=args.cooldown_steps if hasattr(args, "cooldown_steps") else 5,
        max_dobrar=args.max_dobrar if hasattr(args, "max_dobrar") else 3,
        tranches_buy=tuple(args.tranches_buy) if hasattr(args, "tranches_buy") else (0.2, 0.3, 0.5),
        levels_buy=tuple(args.levels_buy) if hasattr(args, "levels_buy") else (-0.01, -0.02, -0.03),
        tranches_sell=tuple(args.tranches_sell) if hasattr(args, "tranches_sell") else (0.2, 0.3, 0.5),
        levels_sell=tuple(args.levels_sell) if hasattr(args, "levels_sell") else (0.01, 0.03, 0.05),
        max_steps_in=args.max_steps_in if hasattr(args, "max_steps_in") else 168,
    )

    fetch_cfg = FetchConfig(
        days=getattr(args, "days", 30),
        start_date=getattr(args, "start_date", None),
        end_date=getattr(args, "end_date", None),
    )

    app_cfg = AppConfig(
        mode=args.mode,
        trading=trading,
        fetch=fetch_cfg,
        csv_file=getattr(args, "csv_file", None),
        exchange=getattr(args, "exchange", "mock"),
        force_graph=getattr(args, "force_graph", False),
        output_graph=True,
    )

    return app_cfg, default_paths(project_root)
