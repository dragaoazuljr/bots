from __future__ import annotations

import random
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Tuple

import logging


class ExchangeInterface(ABC):
    """Abstração mínima para integrar exchanges reais."""

    @abstractmethod
    def get_current_price(self, symbol: str = "BTCUSDT") -> float:
        raise NotImplementedError

    @abstractmethod
    def buy(self, montante_brl: float, price_brl: float, ts: datetime) -> Tuple[float, float]:
        """Retorna (btc_comprado, taxa_pagada)."""
        raise NotImplementedError

    @abstractmethod
    def sell(self, btc_total: float, price_brl: float, ts: datetime, reason: str) -> Tuple[float, float]:
        """Retorna (valor_venda_brl, taxa_pagada)."""
        raise NotImplementedError


class MockExchange(ExchangeInterface):
    """Implementação mockada com variação aleatória e taxa fixa."""

    def __init__(self, taxa_transacao: float = 0.002, start_price: float = 654139.18, logger: logging.Logger | None = None):
        self.taxa_transacao = taxa_transacao
        self.last_price = start_price
        self.logger = logger or logging.getLogger(__name__)

    def get_current_price(self, symbol: str = "BTCUSDT") -> float:
        variation = random.uniform(-1, 1.0002)
        new_price = self.last_price * (1 + (variation / 1000))
        self.last_price = max(new_price, 1.0)
        return self.last_price

    def buy(self, montante_brl: float, price_brl: float, ts: datetime) -> Tuple[float, float]:
        if montante_brl <= 0 or price_brl <= 0:
            return 0.0, 0.0
        taxa = montante_brl * self.taxa_transacao
        btc = (montante_brl - taxa) / price_brl
        self.logger.info(
            f"[MOCK] {ts.strftime('%Y-%m-%d %H:%M:%S')} - Comprou {btc:.5f} BTC por R${price_brl:,.2f} (taxa: R${taxa:,.2f})"
        )
        return btc, taxa

    def sell(self, btc_total: float, price_brl: float, ts: datetime, reason: str) -> Tuple[float, float]:
        if btc_total <= 0 or price_brl <= 0:
            return 0.0, 0.0
        valor = btc_total * price_brl
        taxa = valor * self.taxa_transacao
        self.logger.info(
            f"[MOCK] {ts.strftime('%Y-%m-%d %H:%M:%S')} - Vendeu {btc_total:.5f} BTC por R${price_brl:,.2f} (taxa: R${taxa:,.2f}) Motivo: {reason}"
        )
        return valor, taxa


class BinanceExchange(ExchangeInterface):
    """Placeholder para integração futura com Binance (ccxt)."""

    def get_current_price(self, symbol: str = "BTCUSDT") -> float:  # pragma: no cover - placeholder
        raise NotImplementedError("Integração com Binance pendente")

    def buy(self, montante_brl: float, price_brl: float, ts: datetime) -> Tuple[float, float]:  # pragma: no cover - placeholder
        raise NotImplementedError("Integração com Binance pendente")

    def sell(self, btc_total: float, price_brl: float, ts: datetime, reason: str) -> Tuple[float, float]:  # pragma: no cover - placeholder
        raise NotImplementedError("Integração com Binance pendente")


class CoinbaseExchange(ExchangeInterface):
    """Placeholder para integração futura com Coinbase."""

    def get_current_price(self, symbol: str = "BTCUSDT") -> float:  # pragma: no cover - placeholder
        raise NotImplementedError("Integração com Coinbase pendente")

    def buy(self, montante_brl: float, price_brl: float, ts: datetime) -> Tuple[float, float]:  # pragma: no cover - placeholder
        raise NotImplementedError("Integração com Coinbase pendente")

    def sell(self, btc_total: float, price_brl: float, ts: datetime, reason: str) -> Tuple[float, float]:  # pragma: no cover - placeholder
        raise NotImplementedError("Integração com Coinbase pendente")
