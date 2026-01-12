from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Tuple

import pandas as pd

from .models import BotState, MarketData, Paths, TradingParams


def ensure_dirs(paths: Paths) -> None:
    """Garante que pastas de dados e outputs existam."""
    paths.data_dir.mkdir(parents=True, exist_ok=True)
    paths.outputs_dir.mkdir(parents=True, exist_ok=True)


def validate_tranches(params: TradingParams) -> None:
    """Validações básicas dos vetores de tranches/níveis."""
    if abs(sum(params.tranches_buy) - 1.0) > 1e-6:
        raise ValueError("A soma das tranches de compra deve ser 1.0")
    if abs(sum(params.tranches_sell) - 1.0) > 1e-6:
        raise ValueError("A soma das tranches de venda deve ser 1.0")
    if len(params.tranches_buy) != len(params.levels_buy):
        raise ValueError("Número de tranches_buy deve ser igual ao número de levels_buy")
    if len(params.tranches_sell) != len(params.levels_sell):
        raise ValueError("Número de tranches_sell deve ser igual ao número de levels_sell")
    if not all(x < 0 for x in params.levels_buy):
        raise ValueError("Todos os levels_buy devem ser negativos (dips)")
    if not all(x > 0 for x in params.levels_sell):
        raise ValueError("Todos os levels_sell devem ser positivos (lucros)")
    if not all(x > 0 for x in list(params.tranches_buy) + list(params.tranches_sell)):
        raise ValueError("Todas as tranches devem ser positivas")


def load_csv_prices(csv_file: Path, taxa_cambio: float) -> MarketData:
    """Carrega preços históricos em USD e converte para BRL."""
    if not csv_file.exists():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {csv_file}")

    df = pd.read_csv(csv_file)
    df.dropna(inplace=True)

    if "Price_USD" in df.columns:
        price_column = "Price_USD"
    elif "Close" in df.columns:
        price_column = "Close"
    else:
        raise ValueError("Coluna 'Price_USD' ou 'Close' não encontrada no CSV")

    if "Datetime" in df.columns:
        timestamps = pd.to_datetime(df["Datetime"]).tolist()
    elif "Timestamp_ms" in df.columns:
        timestamps = pd.to_datetime(df["Timestamp_ms"], unit="ms").tolist()
    else:
        raise ValueError("Coluna 'Datetime' ou 'Timestamp_ms' não encontrada no CSV")

    prices_brl = (df[price_column] * taxa_cambio).tolist()
    return MarketData(prices=prices_brl, timestamps=timestamps)


def state_to_dict(state: BotState) -> dict:
    """Serializa BotState para JSON."""
    return {
        "btc_total": state.btc_total,
        "btc_tranches": state.btc_tranches,
        "montante": state.montante,
        "last_price": state.last_price,
        "total_lucro": state.total_lucro,
        "total_imposto": state.total_imposto,
        "total_taxas": state.total_taxas,
        "lucros": state.lucros,
        "precos_venda": state.precos_venda,
        "variacoes_compra": state.variacoes_compra,
        "variacoes_venda": state.variacoes_venda,
        "buy_points": state.buy_points,
        "sell_points": state.sell_points,
        "saldo_history": state.saldo_history,
        "current_index": state.current_index,
        "current_operation_time": state.current_operation_time.isoformat(),
        "last_operation_time": state.last_operation_time.isoformat(),
        "current_operation": state.current_operation,
        "ultimo_motivo_venda": state.ultimo_motivo_venda,
        "consecutive_losses": state.consecutive_losses,
        "cooldown_remaining": state.cooldown_remaining,
    }


def state_from_dict(data: dict) -> BotState:
    """Desserializa dict em BotState."""
    return BotState(
        btc_total=data.get("btc_total", 0.0),
        btc_tranches=data.get("btc_tranches", []),
        montante=data.get("montante", 0.0),
        last_price=data.get("last_price", 0.0),
        total_lucro=data.get("total_lucro", 0.0),
        total_imposto=data.get("total_imposto", 0.0),
        total_taxas=data.get("total_taxas", 0.0),
        lucros=[float(x) for x in data.get("lucros", [])],
        precos_venda=data.get("precos_venda", []),
        variacoes_compra=data.get("variacoes_compra", []),
        variacoes_venda=data.get("variacoes_venda", []),
        buy_points=data.get("buy_points", []),
        sell_points=data.get("sell_points", []),
        saldo_history=data.get("saldo_history", []),
        current_index=data.get("current_index", 0),
        current_operation_time=_parse_dt(data.get("current_operation_time")),
        last_operation_time=_parse_dt(data.get("last_operation_time")),
        current_operation=data.get("current_operation", 1),
        ultimo_motivo_venda=data.get("ultimo_motivo_venda"),
        consecutive_losses=data.get("consecutive_losses", 0),
        cooldown_remaining=data.get("cooldown_remaining", 0),
    )


def _parse_dt(raw: str | None) -> datetime:
    if not raw:
        return datetime.now()
    try:
        return datetime.fromisoformat(raw)
    except Exception:
        return datetime.now()


def load_state(state_file: Path) -> BotState | None:
    """Carrega estado do arquivo se existir."""
    if not state_file.exists():
        return None
    data = json.loads(state_file.read_text())
    return state_from_dict(data)


def save_state(state: BotState, state_file: Path) -> None:
    """Salva estado em JSON (ISO para datas)."""
    payload = state_to_dict(state)
    state_file.write_text(json.dumps(payload, indent=2, default=str))


def reset_state_if_new_run(state: BotState, trading: TradingParams) -> BotState:
    """Inicializa valores caso estado seja vazio."""
    if state.montante <= 0:
        state.montante = trading.montante
    if state.last_price <= 0:
        state.last_price = 100000.0  # preço base aproximado em BRL
    return state
