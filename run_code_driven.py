# 纯代码驱动，不走GUI和web，直接用引擎注册策略
# 四类样例：CTA、价差、组合、算法

import logging
from time import sleep

from vnpy.event import EventEngine
from vnpy.trader.constant import Direction, Offset
from vnpy.trader.engine import MainEngine

from vnpy_ctp import CtpGateway
from vnpy_paperaccount import PaperAccountApp
from vnpy_riskmanager import RiskManagerApp
from vnpy_algotrading import AlgoTradingApp
from vnpy_spreadtrading import SpreadTradingApp
from vnpy_ctastrategy import CtaStrategyApp
from vnpy_portfoliostrategy import PortfolioStrategyApp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger()


def main():
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    main_engine.add_gateway(CtpGateway)

    # paper account 要在 riskmanager 前面，riskmanager 会替换 send_order
    main_engine.add_app(PaperAccountApp)
    main_engine.add_app(RiskManagerApp)
    main_engine.add_app(AlgoTradingApp)
    main_engine.add_app(CtaStrategyApp)
    main_engine.add_app(SpreadTradingApp)
    main_engine.add_app(PortfolioStrategyApp)

    cta_engine = main_engine.get_engine("CtaStrategy")
    spread_engine = main_engine.get_engine("SpreadTrading")
    portfolio_engine = main_engine.get_engine("PortfolioStrategy")
    algo_engine = main_engine.get_engine("AlgoTrading")

    # 纯代码模式下引擎不会自动init（GUI下是主窗口触发的），手动调一次
    for engine in (cta_engine, spread_engine, portfolio_engine, algo_engine):
        if hasattr(engine, "init_engine"):
            engine.init_engine()
            if hasattr(engine, "load_strategy_class"):
                engine.load_strategy_class()

    # CTA样例
    cta_list = [
        ("DoubleMa_Example", "DoubleMaStrategy", "IF2612.CFFEX",
         {"fast_window": 10, "slow_window": 30, "trailing_stop": 30, "fixed_size": 1}),
        ("BollChannel_Example", "BollChannelStrategy", "rb2605.SHFE",
         {"boll_window": 18, "stdev_dev": 3.4, "trailing_stop": 80, "fixed_size": 1}),
        ("AtrRsi_Example", "AtrRsiStrategy", "cu2612.SHFE",
         {"atr_window": 22, "rsi_window": 5, "rsi_buy": 35, "rsi_sell": 65, "trailing_stop": 200, "fixed_size": 1}),
        ("KingKeltner_Example", "KingKeltnerStrategy", "m2605.DCE",
         {"kk_length": 38, "kk_dev": 2.6, "trailing_size": 12, "fixed_size": 1}),
    ]
    for name, class_name, vt_symbol, setting in cta_list:
        try:
            cta_engine.add_strategy(class_name, name, vt_symbol, setting)
            log.info("CTA: %s(%s) %s", name, class_name, vt_symbol)
        except Exception as e:
            log.warning("CTA %s 失败: %s", name, e)

    # 价差：先建价差合约再加策略
    try:
        spread_engine.add_spread(
            name="IF_IH_1x1",
            leg_settings=[
                {"vt_symbol": "IF2612.CFFEX", "variable": "IF", "trading_multiplier": 1, "trading_direction": 1},
                {"vt_symbol": "IH2612.CFFEX", "variable": "IH", "trading_multiplier": 1, "trading_direction": -1},
            ],
            price_formula="IF - IH",
            active_symbol="IF2612.CFFEX",
            min_volume=1,
        )
        spread_engine.add_strategy("BasicSpreadStrategy", "BasicSpread_Example", "IF_IH_1x1",
                                   {"buy_price": 0, "sell_price": 99999, "cover_price": 0, "short_price": -99999,
                                    "max_pos": 1, "payup": 10, "interval": 10})
        spread_engine.add_strategy("StatisticalArbitrageStrategy", "StatArb_Example", "IF_IH_1x1",
                                   {"boll_window": 30, "boll_dev": 2, "max_pos": 1, "payup": 10, "interval": 10})
        log.info("价差: BasicSpread / StatArb")
    except Exception as e:
        log.warning("价差失败: %s", e)

    # 组合样例
    try:
        portfolio_engine.add_strategy("PortfolioBollChannelStrategy", "PortfolioBoll_Example",
                                      ["IF2612.CFFEX", "IH2612.CFFEX"], {"boll_window": 18, "stdev_dev": 3.4})
        portfolio_engine.add_strategy("TrendFollowingStrategy", "TrendFollow_Example",
                                      ["rb2605.SHFE"],
                                      {"fast_window": 10, "slow_window": 30, "trailing_stop": 80, "fixed_size": 1})
        log.info("组合: PortfolioBoll / TrendFollow")
    except Exception as e:
        log.warning("组合失败: %s", e)

    # 算法样例，没连行情会报找不到合约，正常
    algo_list = [
        ("TwapAlgo", "IF2612.CFFEX", Direction.LONG, Offset.OPEN, 0.0, 1, {"interval": 10, "trader_num": 6}),
        ("IcebergAlgo", "rb2605.SHFE", Direction.LONG, Offset.OPEN, 0.0, 10, {"display_volume": 2, "interval": 6}),
        ("SniperAlgo", "m2605.DCE", Direction.SHORT, Offset.OPEN, 0.0, 1, {}),
    ]
    for template_name, vt_symbol, direction, offset, price, volume, setting in algo_list:
        try:
            algo_engine.start_algo(template_name, vt_symbol, direction, offset, price, volume, setting)
            log.info("算法: %s @ %s", template_name, vt_symbol)
        except Exception as e:
            log.warning("算法 %s 未启动(无行情连接): %s", template_name, e)

    log.info("启动完成")
    log.info("CTA: %s", list(cta_engine.strategies.keys()))
    log.info("价差: %s", list(spread_engine.strategies.keys()))
    log.info("组合: %s", list(portfolio_engine.strategies.keys()))

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        log.info("退出，停止策略")
        cta_engine.stop_all_strategies()
        portfolio_engine.stop_all_strategies()
        main_engine.close()


if __name__ == "__main__":
    main()
