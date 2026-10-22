"""期权电子眼教学样例：由调用方显式安装，不依赖自动扫描。"""

from typing import TYPE_CHECKING

from ..algo import ElectronicEyeAlgo
from .inventory_skew_strategy import InventorySkewStrategy
from .volatility_band_strategy import VolatilityBandStrategy

if TYPE_CHECKING:
    from ..engine import OptionAlgoEngine


EXAMPLE_CLASSES: dict[str, type[ElectronicEyeAlgo]] = {
    "ElectronicEyeAlgo": ElectronicEyeAlgo,
    "VolatilityBandStrategy": VolatilityBandStrategy,
    "InventorySkewStrategy": InventorySkewStrategy,
}


def install_example(
    algo_engine: "OptionAlgoEngine",
    vt_symbol: str,
    name: str,
) -> ElectronicEyeAlgo:
    """替换已经初始化且完全停止的单合约算法，返回新实例。

    先调用原引擎的 init_engine(portfolio_name)，再调用本函数，
    最后通过原引擎的 start_algo_pricing/start_algo_trading 启动。
    此函数不会修改原工厂，也不会自动启动定价或交易。
    """
    if name not in EXAMPLE_CLASSES:
        raise ValueError(f"未知样例 {name!r}，可选项：{', '.join(EXAMPLE_CLASSES)}")

    old_algo = algo_engine.algos.get(vt_symbol)
    if old_algo is None:
        raise KeyError(f"{vt_symbol} 尚未初始化，请先调用 algo_engine.init_engine")

    # 必须通过原引擎停止，确保行情订阅和 active_algos 也已解除。
    if (
        old_algo.pricing_active
        or old_algo.trading_active
        or vt_symbol in algo_engine.active_algos
    ):
        raise RuntimeError(f"请先通过原引擎停止 {vt_symbol} 的交易和定价")

    # 撤单请求不等于撤单完成；旧委托仍在等待回报时不能更换实例。
    if old_algo.long_active_orderids or old_algo.short_active_orderids:
        raise RuntimeError(f"{vt_symbol} 仍有活动委托，请等待撤单或成交回报")

    algo = EXAMPLE_CLASSES[name](algo_engine, old_algo.option)
    algo_engine.algos[vt_symbol] = algo
    return algo


__all__ = [
    "ElectronicEyeAlgo",
    "VolatilityBandStrategy",
    "InventorySkewStrategy",
    "EXAMPLE_CLASSES",
    "install_example",
]
