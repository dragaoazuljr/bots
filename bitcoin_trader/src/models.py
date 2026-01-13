from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


@dataclass
class TradingParams:
    """Configurações de trading compartilhadas entre modos."""

    montante: float = 10000.0
    qtd_operacoes: int = 30
    meta_lucro: float = 0.1
    stop_loss: float = -0.05
    taxa_cambio: float = 5.5
    cooldown_steps: int = 5
    max_dobrar: int = 3
    tranches_buy: Sequence[float] = field(default_factory=lambda: (0.2, 0.3, 0.5))
    levels_buy: Sequence[float] = field(default_factory=lambda: (-0.01, -0.02, -0.03))
    tranches_sell: Sequence[float] = field(default_factory=lambda: (0.2, 0.3, 0.5))
    levels_sell: Sequence[float] = field(default_factory=lambda: (0.01, 0.03, 0.05))
    taxa_transacao: float = 0.002
    lucro_minimo: float = 0.03
    time_percentage_to_sell: float = 0.5
    max_duration_hours: int = 24
    min_stop_loss_time_hours: int = 6
    max_steps_in: int = 168


@dataclass
class BotState:
    """Estado persistente do bot entre execuções."""

    btc_total: float = 0.0
    btc_tranches: List[dict] = field(default_factory=list)
    montante: float = 0.0
    last_price: float = 0.0
    total_lucro: float = 0.0
    total_imposto: float = 0.0
    total_taxas: float = 0.0
    lucros: List[float] = field(default_factory=list)
    precos_venda: List[float] = field(default_factory=list)
    variacoes_compra: List[float] = field(default_factory=list)
    variacoes_venda: List[float] = field(default_factory=list)
    buy_points: List[Tuple[int, float]] = field(default_factory=list)
    sell_points: List[Tuple[int, float]] = field(default_factory=list)
    saldo_history: List[float] = field(default_factory=list)
    current_index: int = 0
    current_operation_time: datetime = field(default_factory=datetime.now)
    last_operation_time: datetime = field(default_factory=datetime.now)
    current_operation: int = 1
    ultimo_motivo_venda: Optional[str] = None
    consecutive_losses: int = 0
    cooldown_remaining: int = 0


@dataclass
class MarketData:
    """Série temporal de preços/timestamps."""

    prices: List[float]
    timestamps: List[datetime]

    def has_data(self) -> bool:
        return bool(self.prices)

    def length(self) -> int:
        return len(self.prices)


@dataclass
class Paths:
    """Caminhos padrão do projeto."""

    root: Path
    data_dir: Path
    outputs_dir: Path
    state_file: Path
    log_file: Path


@dataclass
class FetchConfig:
    """Configuração para coleta de dados históricos."""

    days: int = 30
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@dataclass
class AppConfig:
    """Configuração geral da CLI."""

    mode: str
    trading: TradingParams
    fetch: FetchConfig
    csv_file: Optional[Path] = None
    exchange: str = "mock"
    output_graph: bool = True
    force_graph: bool = False
