"""在原电子眼的价格条件之前增加隐含波动率偏离条件。"""

from math import isfinite
from typing import TYPE_CHECKING

from ..algo import ElectronicEyeAlgo
from ..base import OptionData

if TYPE_CHECKING:
    from ..engine import OptionAlgoEngine


class VolatilityBandStrategy(ElectronicEyeAlgo):
    """只在盘口隐波偏离定价隐波足够远时，进入原电子眼抢单流程。"""

    def __init__(
        self,
        algo_engine: "OptionAlgoEngine",
        option: OptionData,
    ) -> None:
        super().__init__(algo_engine, option)
        # 隐波采用小数单位，0.03 表示 3 个波动率百分点。
        self.impv_edge: float = 0.03

    def start_trading(self, params: dict) -> bool:
        """读取样例参数，其余交易参数仍交给原算法处理。"""
        if self.trading_active:
            return False

        try:
            impv_edge = float(params.get("impv_edge", 0.03))
        except (TypeError, ValueError, OverflowError):
            self.write_log("impv_edge 必须是有限的非负数")
            return False

        if not isfinite(impv_edge) or impv_edge < 0:
            self.write_log("impv_edge 必须是有限的非负数")
            return False

        self.impv_edge = impv_edge
        return super().start_trading(params)

    def do_trading(self) -> None:
        """先检查隐波与盘口，再复用原价格检查、持仓限制及开平仓逻辑。"""
        if not self.trading_active:
            return

        option = self.option
        tick = option.tick
        if tick is None:
            return

        # 0 通常表示定价隐波尚未配置，不能据此产生交易信号。
        if not isfinite(self.pricing_impv) or self.pricing_impv <= 0:
            return

        if (
            self.long_allowed
            and self.check_long_finished()
            and isfinite(tick.ask_price_1)
            and tick.ask_price_1 > 0
            and isfinite(tick.ask_volume_1)
            and tick.ask_volume_1 > 0
            and isfinite(option.ask_impv)
            and option.ask_impv > 0
            and option.ask_impv < self.pricing_impv - self.impv_edge
        ):
            # 隐波便宜只是额外门槛，原 snipe_long 仍要求价格和仓位满足条件。
            self.snipe_long()

        if (
            self.short_allowed
            and self.check_short_finished()
            and isfinite(tick.bid_price_1)
            and tick.bid_price_1 > 0
            and isfinite(tick.bid_volume_1)
            and tick.bid_volume_1 > 0
            and isfinite(option.bid_impv)
            and option.bid_impv > 0
            and option.bid_impv > self.pricing_impv + self.impv_edge
        ):
            self.snipe_short()
