from datetime import datetime, timedelta

from src.exchange_interface import ExchangeInterface
from src.models import BotState, MarketData, TradingParams
from src.trading_engine import TradingEngine


class DummyExchange(ExchangeInterface):
    """Exchange determinística para testes."""

    def __init__(self, prices):
        self.prices = prices
        self.idx = 0
        self.taxa_transacao = 0.0

    def get_current_price(self, symbol: str = "BTCUSDT") -> float:
        price = self.prices[min(self.idx, len(self.prices) - 1)]
        self.idx += 1
        return price

    def buy(self, montante_brl: float, price_brl: float, ts: datetime):
        taxa = montante_brl * self.taxa_transacao
        btc = (montante_brl - taxa) / price_brl
        return btc, taxa

    def sell(self, btc_total: float, price_brl: float, ts: datetime, reason: str):
        valor = btc_total * price_brl
        taxa = valor * self.taxa_transacao
        return valor, taxa


def test_trading_engine_runs_with_market():
    params = TradingParams(
        montante=10000,
        qtd_operacoes=1,
        meta_lucro=0.02,
        stop_loss=-0.1,
        tranches_buy=(1.0,),
        levels_buy=(0.0,),  # compra imediatamente
        tranches_sell=(1.0,),
        levels_sell=(0.01,),
        taxa_transacao=0.0,
        max_duration_hours=4,
    )
    prices = [100000, 99000, 102000, 103000, 104000]
    timestamps = [datetime.now() + timedelta(hours=i) for i in range(len(prices))]
    market = MarketData(prices=prices, timestamps=timestamps)

    exchange = DummyExchange(prices)
    engine = TradingEngine(params, exchange, logger=_silent_logger())
    state = BotState(montante=params.montante, last_price=prices[0])

    final_state = engine.run_operations(market, state)
    assert final_state.montante > 0
    assert len(final_state.sell_points) >= 0
    assert final_state.current_operation == 2  # completou 1 operação


def _silent_logger():
    import logging

    logger = logging.getLogger("test-trading-engine")
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    return logger
