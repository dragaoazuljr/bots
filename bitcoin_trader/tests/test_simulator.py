from pathlib import Path

from src.exchange_interface import MockExchange
from src.models import Paths, TradingParams
from src.simulator import Simulator
from src.trading_engine import TradingEngine
from src.utils import ensure_dirs


def test_simulator_run_real(tmp_path):
    data_dir = tmp_path / "data"
    outputs_dir = tmp_path / "outputs"
    ensure_dirs(
        Paths(
            root=tmp_path,
            data_dir=data_dir,
            outputs_dir=outputs_dir,
            state_file=outputs_dir / "state.json",
            log_file=outputs_dir / "log.txt",
        )
    )

    params = TradingParams(
        montante=5000,
        qtd_operacoes=1,
        tranches_buy=(1.0,),
        levels_buy=(0.0,),
        tranches_sell=(1.0,),
        levels_sell=(0.01,),
        taxa_transacao=0.0,
        max_duration_hours=2,
    )
    exchange = MockExchange(taxa_transacao=0.0, start_price=100000, logger=_silent_logger())
    engine = TradingEngine(params, exchange, _silent_logger())
    paths = Paths(
        root=tmp_path,
        data_dir=data_dir,
        outputs_dir=outputs_dir,
        state_file=outputs_dir / "state.json",
        log_file=outputs_dir / "log.txt",
    )
    simulator = Simulator(engine, paths, _silent_logger())

    state, market, start_time = simulator.run_real(params)
    assert paths.state_file.exists()
    assert state.current_operation >= 2  # executou pelo menos uma operação
    assert market is None
    assert start_time is not None


def _silent_logger():
    import logging

    logger = logging.getLogger("simulator-test")
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    return logger
