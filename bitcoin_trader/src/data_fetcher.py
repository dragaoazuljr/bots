from __future__ import annotations

import csv
import os
from datetime import datetime, timedelta
from pathlib import Path

from pycoingecko import CoinGeckoAPI

from .models import FetchConfig, Paths


class DataFetcher:
    """Responsável por buscar dados históricos de preço do Bitcoin."""

    def __init__(self, paths: Paths):
        self.paths = paths

    def fetch(self, cfg: FetchConfig) -> Path:
        start_date, end_date = self._resolve_dates(cfg)
        api_key = os.getenv("COINGECKO_API_KEY")
        cg = CoinGeckoAPI(api_key) if api_key else CoinGeckoAPI()

        from_timestamp = int(start_date.timestamp())
        to_timestamp = int(end_date.timestamp())

        data = cg.get_coin_market_chart_range_by_id(
            id="bitcoin",
            vs_currency="usd",
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
        )
        prices = data.get("prices", [])

        filename = (
            f"bitcoin_data_{start_date.strftime('%Y-%m-%d')}_to_{end_date.strftime('%Y-%m-%d')}.csv"
            if cfg.start_date and cfg.end_date
            else f"bitcoin_hourly_usd_last_{cfg.days}days.csv"
        )
        target_file = self.paths.data_dir / filename

        with target_file.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Timestamp_ms", "Datetime", "Price_USD"])
            for ts_ms, price in prices:
                dt = datetime.fromtimestamp(ts_ms / 1000)
                writer.writerow([ts_ms, dt.strftime("%Y-%m-%d %H:%M:%S"), round(price, 2)])

        return target_file

    def _resolve_dates(self, cfg: FetchConfig) -> tuple[datetime, datetime]:
        if cfg.start_date and cfg.end_date:
            start_date = datetime.strptime(cfg.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(cfg.end_date, "%Y-%m-%d")
            if start_date >= end_date:
                raise ValueError("A data inicial deve ser anterior à data final")
            return start_date, end_date

        end_date = datetime.now()
        start_date = end_date - timedelta(days=cfg.days)
        return start_date, end_date
