from datetime import datetime

from src.exchange_interface import MockExchange


def test_mock_exchange_buy_sell_roundtrip():
    exchange = MockExchange(taxa_transacao=0.001, start_price=100000)
    price = exchange.get_current_price()
    btc, taxa_buy = exchange.buy(1000, price, datetime.now())
    assert btc > 0
    assert taxa_buy > 0

    valor, taxa_sell = exchange.sell(btc, price * 1.02, datetime.now(), "teste")
    assert valor > 0
    assert taxa_sell > 0
