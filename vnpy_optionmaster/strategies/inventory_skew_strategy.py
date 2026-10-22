"""根据净持仓偏离目标的数量，平移原电子眼的定价中心。"""

from math import isfinite
from typing import TYPE_CHECKING

from vnpy.trader.object import TickData
from vnpy.trader.utility import round_to

from ..algo import ElectronicEyeAlgo
from ..base import OptionData

if TYPE_CHECKING:
    from ..engine import OptionAlgoEngine


class InventorySkewStrategy(ElectronicEyeAlgo):
    """每偏离目标持仓一手，就按 inventory_ticks 个最小价位调整中心。"""

    def __init__(
        self,
        algo_engine: "OptionAlgoEngine",
        option: OptionData,
    ) -> None:
        super().__init__(algo_engine, option)
        self.inventory_ticks: float = 2.0

    def start_trading(self, params: dict) -> bool:
        """读入偏移强度，继承原算法对方向、持仓和委托数量的处理。"""
        if self.trading_active:
            return False

        try:
            inventory_ticks = float(params.get("inventory_ticks", 2.0))
        except (TypeError, ValueError, OverflowError):
            self.write_log("inventory_ticks 必须是有限的非负数")
            return False

        if not isfinite(inventory_ticks) or inventory_ticks < 0:
            self.write_log("inventory_ticks 必须是有限的非负数")
            return False

        self.inventory_ticks = inventory_ticks
        started = super().start_trading(params)
        if started:
            # target_pos 由父类读入，因此启动成功后按新目标重新定价一次。
            self.calculate_price()
        return started

    def calculate_price(self) -> None:
        """保留原价差公式，只在理论中心价中加入库存偏移。"""
        option = self.option
        self.pricing_impv = option.pricing_impv

        theoretical_price = option.calculate_ref_price()
        inventory_offset = (
            (option.net_pos - self.target_pos)
            * self.inventory_ticks
            * self.pricetick
        )
        # 多仓超目标时中心下移，降低继续买入的意愿，并更容易触发卖出。
        # 空仓超目标时方向相反；inventory_ticks=0 时恢复原定价公式。
        ref_price = theoretical_price - inventory_offset
        self.ref_price = round_to(ref_price, self.pricetick)

        algo_spread = max(
            self.price_spread,
            self.volatility_spread * option.theo_vega / option.size,
        )
        half_spread = algo_spread / 2
        self.algo_bid_price = round_to(ref_price - half_spread, self.pricetick)
        self.algo_ask_price = round_to(ref_price + half_spread, self.pricetick)
        self.algo_spread = round_to(algo_spread, self.pricetick)

        # 只发布一次最终定价；不先调用父类 calculate_price，避免发布未偏移价格。
        self.put_pricing_event()

    def on_option_tick(self, tick: TickData) -> None:
        """在下一次期权行情中使用最新持仓定价，然后沿用原交易入口。"""
        # 原引擎的算法成交回调先于组合持仓更新，因此不在 on_trade 中定价。
        # 标的行情的重新定价已由父类 on_underlying_tick 负责。
        if self.pricing_active:
            self.calculate_price()
        # 父类只进入一次 do_trading，仍使用原活动委托、开平仓和限仓检查。
        super().on_option_tick(tick)
