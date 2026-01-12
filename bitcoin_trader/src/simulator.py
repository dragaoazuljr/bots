from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import logging

from .models import BotState, MarketData, Paths, TradingParams
from .trading_engine import TradingEngine
from .utils import load_csv_prices, load_state, reset_state_if_new_run, save_state


class Simulator:
    """Orquestra a simulação nos modos teste e real."""

    def __init__(self, engine: TradingEngine, paths: Paths, logger: logging.Logger):
        self.engine = engine
        self.paths = paths
        self.logger = logger

    def run_test(self, csv_file: Path, trading: TradingParams) -> Tuple[BotState, MarketData, datetime]:
        market = load_csv_prices(csv_file, trading.taxa_cambio)
        state = load_state(self.paths.state_file) or BotState()
        state = reset_state_if_new_run(state, trading)
        start_time = state.current_operation_time

        state = self.engine.run_operations(market, state)
        save_state(state, self.paths.state_file)
        return state, market, start_time

    def run_real(self, trading: TradingParams) -> Tuple[BotState, Optional[MarketData], datetime]:
        state = load_state(self.paths.state_file) or BotState()
        state = reset_state_if_new_run(state, trading)
        start_time = state.current_operation_time

        state = self.engine.run_operations(None, state)
        save_state(state, self.paths.state_file)
        return state, None, start_time
