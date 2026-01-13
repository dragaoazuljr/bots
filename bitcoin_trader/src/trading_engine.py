from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Tuple

import logging

from .exchange_interface import ExchangeInterface
from .models import BotState, MarketData, TradingParams


@dataclass
class OperationOutcome:
    lucro: float
    imposto: float
    taxa_total: float
    preco_compra: float
    preco_venda: float
    variacao_compra: float
    variacao_venda: float
    motivo_venda: str
    operacao_realizada: bool


class TradingEngine:
    """Motor principal com a lógica de compra/venda."""

    def __init__(self, params: TradingParams, exchange: ExchangeInterface, logger: logging.Logger):
        self.params = params
        self.exchange = exchange
        self.logger = logger

    def run_operations(self, market: Optional[MarketData], state: BotState) -> BotState:
        """Executa as operações configuradas, atualizando o estado."""
        start_op = state.current_operation
        for op in range(start_op, self.params.qtd_operacoes + 1):
            outcome = self._run_single_operation(op, market, state)
            if len(state.lucros) < op:
                state.lucros.append(0.0)
            state.lucros[op - 1] = outcome.lucro
            state.total_lucro += outcome.lucro
            state.total_imposto += outcome.imposto
            state.total_taxas += outcome.taxa_total
            state.precos_venda.append(outcome.preco_venda)
            state.variacoes_compra.append(outcome.variacao_compra * 100)
            state.variacoes_venda.append(outcome.variacao_venda * 100)
            state.ultimo_motivo_venda = outcome.motivo_venda
            state.current_operation += 1

            if market and state.current_index >= market.length():
                self.logger.info("Fim dos dados históricos alcançado. Finalizando simulação.")
                break

        return state

    def _run_single_operation(self, op: int, market: Optional[MarketData], state: BotState) -> OperationOutcome:
        params = self.params
        operacao_realizada = False

        # Cooldown
        if state.cooldown_remaining > 0:
            self.logger.info(
                f"Em cooldown após stop-loss. Pulando operação {op}. Cooldown restante: {state.cooldown_remaining} steps"
            )
            state.cooldown_remaining -= 1
            state.current_index = min(state.current_index + 1, market.length() if market else state.current_index + 1)
            return OperationOutcome(0.0, 0.0, 0.0, state.last_price, state.last_price, 0.0, 0.0, "Cooldown", False)

        # Modo "dobrar a aposta"
        dobrar_aposta = state.ultimo_motivo_venda == "Stop-loss Total" and state.consecutive_losses < params.max_dobrar
        stop_loss_atual = params.stop_loss * 2 if dobrar_aposta else params.stop_loss
        meta_lucro_atual = params.meta_lucro * 2 if dobrar_aposta else params.meta_lucro
        max_duration_atual = params.max_duration_hours * 2 if dobrar_aposta else params.max_duration_hours

        if dobrar_aposta:
            state.consecutive_losses += 1
            self.logger.info(f"Dobrando aposta (perda consecutiva #{state.consecutive_losses})")
        else:
            state.consecutive_losses = 0

        # Compra (scaling in)
        (
            btc_tranches,
            btc_total,
            custo_total,
            total_taxas_compra,
            preco_btc_compra,
            variacao_compra,
            start_time,
            comprou_algo,
        ) = self._scale_in(market, state, stop_loss_atual, meta_lucro_atual, max_duration_atual, op)

        total_taxas = total_taxas_compra
        imposto = 0.0
        preco_btc_venda = preco_btc_compra
        variacao_venda = 0.0
        motivo_venda = "Sem Compra"
        lucro = 0.0
        taxa_venda = 0.0
        current_time = start_time

        # Monitora a posição e realiza vendas
        (
            btc_tranches,
            btc_total,
            total_taxas,
            lucro,
            imposto,
            preco_btc_venda,
            variacao_venda,
            motivo_venda,
            operacao_realizada_monitor,
            current_time,
        ) = self._monitor_position(
            market,
            state,
            btc_tranches,
            btc_total,
            custo_total,
            total_taxas,
            preco_btc_compra,
            stop_loss_atual,
            meta_lucro_atual,
            max_duration_atual,
        )

        operacao_realizada = operacao_realizada or operacao_realizada_monitor or comprou_algo

        if motivo_venda == "Stop-loss Total":
            state.cooldown_remaining = params.cooldown_steps

        # Armazenar detalhes da operação
        if operacao_realizada:
            operation_detail = {
                "operation_id": op,
                "lucro": lucro,
                "preco_compra": preco_btc_compra,
                "preco_venda": preco_btc_venda,
                "motivo_venda": motivo_venda,
                "btc_comprado": btc_total,
                "custo_total": custo_total,
                "start_time": start_time,
                "end_time": current_time,
            }
            state.operation_details.append(operation_detail)
            state.saldo_history.append(state.montante)

        state.last_operation_time = current_time
        state.last_price = preco_btc_venda

        # Próximo timestamp para operação seguinte
        if market and state.current_index < market.length():
            state.current_operation_time = market.timestamps[state.current_index]
        else:
            state.current_operation_time = current_time + timedelta(hours=1)

        self.logger.info(
            f"Operação {op} concluída - Motivo: {motivo_venda}, Lucro: R${lucro:,.2f}, Montante atual: R${state.montante:,.2f}"
        )

        return OperationOutcome(
            lucro=lucro,
            imposto=imposto,
            taxa_total=total_taxas,
            preco_compra=preco_btc_compra,
            preco_venda=preco_btc_venda,
            variacao_compra=variacao_compra,
            variacao_venda=variacao_venda,
            motivo_venda=motivo_venda,
            operacao_realizada=operacao_realizada,
        )

    def _scale_in(
        self,
        market: Optional[MarketData],
        state: BotState,
        stop_loss_atual: float,
        meta_lucro_atual: float,
        max_duration_atual: float,
        op: int,
    ) -> Tuple[list, float, float, float, float, float, datetime, bool]:
        params = self.params
        btc_tranches: list = []
        tranches_compradas = set()
        preco_base_compra: Optional[float] = None
        total_custo_compra = 0.0
        total_taxa_compra = 0.0
        steps_in = 0
        max_steps_in = params.max_steps_in
        simulated_start_time = state.current_operation_time
        comprou_algo = False

        # Salva montante inicial da operação para alocação fixa de tranches
        initial_montante = state.montante

        # Controle para forçar avanço mínimo de steps entre tranches
        steps_since_last_tranche = float('inf')  # Permite primeira tranche imediatamente
        min_steps_between_tranches = 1  # Mínimo 1 step entre tranches

        self.logger.info(f"Iniciando operação {op} - Tentando comprar {len(params.tranches_buy)} tranches em dips")

        while len(tranches_compradas) < len(params.tranches_buy) and steps_in < max_steps_in:
            preco_atual, current_time = self._next_price(market, state, simulated_start_time, steps_in)
            if preco_base_compra is None:
                preco_base_compra = preco_atual
                simulated_start_time = current_time

            variacao_acumulada = (preco_atual - preco_base_compra) / preco_base_compra if preco_base_compra else 0.0
            tranche_comprada_neste_step = False
            steps_since_last_tranche += 1

            for i, (tranche_fraction, level) in enumerate(zip(params.tranches_buy, params.levels_buy)):
                if i not in tranches_compradas and variacao_acumulada <= level and steps_since_last_tranche >= min_steps_between_tranches:
                    # Usa montante inicial da operação se fixed_tranche_allocation estiver ativo
                    montante_base = initial_montante if params.fixed_tranche_allocation else state.montante
                    montante_tranche = montante_base * tranche_fraction
                    btc_tranche, taxa_tranche = self.exchange.buy(
                        montante_tranche, preco_atual, simulated_start_time
                    )
                    btc_tranches.append({"btc": btc_tranche, "preco_compra": preco_atual, "tranche_idx": i})
                    total_custo_compra += btc_tranche * preco_atual
                    total_taxa_compra += taxa_tranche
                    state.montante -= montante_tranche + taxa_tranche
                    tranches_compradas.add(i)
                    state.buy_points.append((max(state.current_index - 1, 0), preco_atual))
                    self.logger.info(
                        f"Tranche {i+1}/{len(params.tranches_buy)} comprada: {btc_tranche:.5f} BTC a R${preco_atual:,.2f} "
                        f"(dip {variacao_acumulada*100:.2f}%)"
                    )
                    self.logger.info(f"Tranche {i+1}: Alocando R${montante_tranche:,.2f} do montante base R${montante_base:,.2f}")
                    tranche_comprada_neste_step = True
                    comprou_algo = True
                    steps_since_last_tranche = 0  # Reseta contador para próxima tranche
                    break

            if not tranche_comprada_neste_step:
                self.logger.debug(
                    f"Step {steps_in}: Preço atual R${preco_atual:,.2f}, Variação acumulada {variacao_acumulada*100:.2f}%"
                )
                steps_in += 1

            if market and state.current_index >= market.length():
                break

        btc_total = sum(tranche["btc"] for tranche in btc_tranches)
        preco_btc_compra = btc_tranches[0]["preco_compra"] if btc_tranches else (preco_base_compra or state.last_price)
        variacao_compra = ((preco_btc_compra - state.last_price) / state.last_price) if state.last_price else 0.0

        if not btc_tranches:
            self.logger.warning(
                f"Operação {op} - Nenhuma tranche comprada! Motivo: Não atingiu níveis de dip suficientes em {max_steps_in} steps"
            )
        elif len(tranches_compradas) < len(params.tranches_buy):
            self.logger.warning(
                f"Operação {op} - Apenas {len(tranches_compradas)}/{len(params.tranches_buy)} tranches compradas (limite {max_steps_in} steps atingido)"
            )
        else:
            self.logger.info(
                f"Operação {op} - Compra concluída: {len(tranches_compradas)}/{len(params.tranches_buy)} tranches, total {btc_total:.5f} BTC, custo total R${total_custo_compra:,.2f}"
            )

        return (
            btc_tranches,
            btc_total,
            total_custo_compra,
            total_taxa_compra,
            preco_btc_compra,
            variacao_compra,
            simulated_start_time,
            comprou_algo,
        )

    def _monitor_position(
        self,
        market: Optional[MarketData],
        state: BotState,
        btc_tranches: list,
        btc_total: float,
        custo: float,
        total_taxas: float,
        preco_btc_compra: float,
        stop_loss_atual: float,
        meta_lucro_atual: float,
        max_duration_atual: float,
    ):
        params = self.params
        elapsed_time = 0
        sold = False
        motivo_venda = "Sem Compra (Operação Vazia)" if not btc_tranches else "Em aberto"
        preco_btc_venda = preco_btc_compra
        variacao_venda = 0.0
        lucro = 0.0
        imposto = 0.0
        taxa_venda = 0.0
        operacao_realizada = False
        current_time = state.current_operation_time

        # se não há tranches, nada a monitorar
        if not btc_tranches:
            return (
                btc_tranches,
                btc_total,
                total_taxas,
                lucro,
                imposto,
                preco_btc_venda,
                variacao_venda,
                motivo_venda,
                operacao_realizada,
                current_time,
            )

        while elapsed_time < max_duration_atual * 3600 and not sold:
            preco_atual, tempo_atual = self._next_price(
                market, state, state.current_operation_time, elapsed_time // 3600
            )
            current_time = tempo_atual
            elapsed_time += 3600

            variacao_atual = (preco_atual * btc_total - custo) / custo if custo > 0 else 0.0

            if variacao_atual <= stop_loss_atual and elapsed_time >= (max_duration_atual - params.min_stop_loss_time_hours) * 3600:
                preco_btc_venda = preco_atual
                variacao_venda = variacao_atual
                valor_venda, taxa_venda = self.exchange.sell(btc_total, preco_btc_venda, tempo_atual, "Stop-loss Total")
                total_taxas += taxa_venda
                lucro = valor_venda - custo
                imposto = lucro * 0.15 if valor_venda > 35000 and lucro > 0 else 0.0
                state.montante += valor_venda - taxa_venda
                motivo_venda = "Stop-loss Total"
                state.cooldown_remaining = params.cooldown_steps
                state.sell_points.append((max(state.current_index - 1, 0), preco_btc_venda))
                sold = True
                operacao_realizada = True
                btc_total = 0
                btc_tranches = []

                # Log detalhado da venda por stop-loss
                self.logger.info(
                    f"VENDA STOP-LOSS - {tempo_atual.strftime('%Y-%m-%d %H:%M:%S')} - "
                    f"Lucro: R${lucro:,.2f} ({variacao_venda*100:.2f}%) - "
                    f"Compra média: R${preco_btc_compra:,.2f} - Venda: R${preco_btc_venda:,.2f} - "
                    f"BTC: {btc_total:.5f} - Valor venda: R${valor_venda:,.2f}"
                )

            elif variacao_atual >= meta_lucro_atual and btc_tranches:
                preco_btc_venda = preco_atual
                variacao_venda = variacao_atual
                valor_venda, taxa_venda = self.exchange.sell(
                    btc_total, preco_btc_venda, tempo_atual, "Meta de Lucro Total"
                )
                total_taxas += taxa_venda
                lucro = valor_venda - custo
                imposto = lucro * 0.15 if valor_venda > 35000 and lucro > 0 else 0.0
                state.montante += valor_venda - taxa_venda
                motivo_venda = "Meta de Lucro Total"
                state.sell_points.append((max(state.current_index - 1, 0), preco_btc_venda))
                sold = True
                operacao_realizada = True
                btc_total = 0
                btc_tranches = []

                # Log detalhado da venda por meta de lucro
                self.logger.info(
                    f"VENDA META LUCRO - {tempo_atual.strftime('%Y-%m-%d %H:%M:%S')} - "
                    f"Lucro: R${lucro:,.2f} ({variacao_venda*100:.2f}%) - "
                    f"Compra média: R${preco_btc_compra:,.2f} - Venda: R${preco_btc_venda:,.2f} - "
                    f"BTC: {btc_total:.5f} - Valor venda: R${valor_venda:,.2f}"
                )

            elif btc_tranches:
                tranches_vendidas = []
                for tranche in sorted(btc_tranches[:], key=lambda x: x["tranche_idx"]):
                    variacao_tranche = (preco_atual - tranche["preco_compra"]) / tranche["preco_compra"]
                    for i, (tranche_sell_fraction, level_sell) in enumerate(zip(params.tranches_sell, params.levels_sell)):
                        if variacao_tranche >= level_sell:
                            btc_vendido = tranche["btc"]
                            valor_vendido = btc_vendido * preco_atual
                            taxa_venda_tranche = valor_vendido * params.taxa_transacao
                            state.montante += valor_vendido - taxa_venda_tranche
                            total_taxas += taxa_venda_tranche
                            lucro_parcial = (valor_vendido - taxa_venda_tranche) - (btc_vendido * tranche["preco_compra"])
                            lucro += lucro_parcial
                            state.sell_points.append((max(state.current_index - 1, 0), preco_atual))
                            tranches_vendidas.append(tranche)
                            operacao_realizada = True

                            # Log detalhado da venda parcial por tranche
                            self.logger.info(
                                f"VENDA TRANCHE {tranche['tranche_idx']+1} - {tempo_atual.strftime('%Y-%m-%d %H:%M:%S')} - "
                                f"Lucro parcial: R${lucro_parcial:,.2f} ({variacao_tranche*100:.2f}%) - "
                                f"Compra: R${tranche['preco_compra']:,.2f} - Venda: R${preco_atual:,.2f} - "
                                f"BTC: {btc_vendido:.5f} - Valor venda: R${valor_vendido:,.2f}"
                            )
                            break

                for tranche in tranches_vendidas:
                    btc_tranches.remove(tranche)

                btc_total = sum(t["btc"] for t in btc_tranches)

                if not btc_tranches:
                    variacao_venda = (preco_atual - preco_btc_compra) / preco_btc_compra if preco_btc_compra else 0.0
                    motivo_venda = "Meta de Lucro Total (Scaling Out)"
                    sold = True

                    # Log detalhado do scaling out (todas as tranches vendidas)
                    self.logger.info(
                        f"SCALING OUT COMPLETO - {tempo_atual.strftime('%Y-%m-%d %H:%M:%S')} - "
                        f"Lucro total: R${lucro:,.2f} ({variacao_venda*100:.2f}%) - "
                        f"Compra média: R${preco_btc_compra:,.2f} - Última venda: R${preco_atual:,.2f}"
                    )

            elif elapsed_time >= max_duration_atual * params.time_percentage_to_sell and variacao_atual >= params.lucro_minimo:
                preco_btc_venda = preco_atual
                variacao_venda = variacao_atual
                valor_venda, taxa_venda = self.exchange.sell(
                    btc_total, preco_btc_venda, tempo_atual, "Venda Antecipada Total"
                )
                total_taxas += taxa_venda
                lucro = valor_venda - custo
                imposto = lucro * 0.15 if valor_venda > 35000 and lucro > 0 else 0.0
                state.montante += valor_venda - taxa_venda
                motivo_venda = "Venda Antecipada Total"
                state.sell_points.append((max(state.current_index - 1, 0), preco_btc_venda))
                sold = True
                operacao_realizada = True
                btc_total = 0
                btc_tranches = []

                # Log detalhado da venda antecipada
                self.logger.info(
                    f"VENDA ANTECIPADA - {tempo_atual.strftime('%Y-%m-%d %H:%M:%S')} - "
                    f"Lucro: R${lucro:,.2f} ({variacao_venda*100:.2f}%) - "
                    f"Compra média: R${preco_btc_compra:,.2f} - Venda: R${preco_btc_venda:,.2f} - "
                    f"BTC: {btc_total:.5f} - Valor venda: R${valor_venda:,.2f}"
                )

            if market and state.current_index >= market.length():
                motivo_venda = "Fim dos Dados (Posição Aberta)"
                variacao_venda = variacao_atual
                sold = True

        if not sold:
            ultimo_preco = locals().get("preco_atual", preco_btc_compra)
            preco_btc_venda = ultimo_preco
            variacao_venda = (ultimo_preco - preco_btc_compra) / preco_btc_compra if preco_btc_compra else 0.0
            motivo_venda = "Monitoramento encerrado sem venda"

        return (
            btc_tranches,
            btc_total,
            total_taxas,
            lucro,
            imposto,
            preco_btc_venda,
            variacao_venda,
            motivo_venda,
            operacao_realizada,
            current_time,
        )

    def _next_price(
        self,
        market: Optional[MarketData],
        state: BotState,
        base_time: datetime,
        step_hours: int,
    ) -> Tuple[float, datetime]:
        """Obtém próximo preço/timestamp de histórico ou exchange."""
        if market and state.current_index < market.length():
            price = market.prices[state.current_index]
            ts = market.timestamps[state.current_index]
            state.current_index += 1
            return price, ts

        synthetic_time = base_time + timedelta(hours=step_hours)
        price = self.exchange.get_current_price()
        return price, synthetic_time
