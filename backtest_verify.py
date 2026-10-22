# CTA样例策略回测校对
# 数据用akshare下的日线（新浪接口），存进vnpy的sqlite，再用回测引擎跑一遍

import importlib
from datetime import datetime

import akshare as ak
import pandas as pd

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.database import get_database
from vnpy.trader.object import BarData
from vnpy_ctastrategy.backtesting import BacktestingEngine

DB = get_database()

START = datetime(2024, 1, 1)
END = datetime(2026, 10, 21)


def load_cls(module, name):
    m = importlib.import_module(f"vnpy_ctastrategy.strategies.{module}")
    return getattr(m, name)


# (策略, 合约, 交易所, 新浪代码, 参数, 合约乘数, 滑点)
TASKS = [
    (load_cls("double_ma_strategy", "DoubleMaStrategy"), "rb2605.SHFE", Exchange.SHFE, "RB2605",
     {"fast_window": 10, "slow_window": 30, "trailing_stop": 80, "fixed_size": 1}, 10, 1),
    (load_cls("boll_channel_strategy", "BollChannelStrategy"), "rb2605.SHFE", Exchange.SHFE, "RB2605",
     {"boll_window": 18, "stdev_dev": 3.4, "trailing_stop": 80, "fixed_size": 1}, 10, 1),
    (load_cls("atr_rsi_strategy", "AtrRsiStrategy"), "cu2612.SHFE", Exchange.SHFE, "CU2612",
     {"atr_window": 22, "rsi_window": 5, "rsi_buy": 35, "rsi_sell": 65, "trailing_stop": 200, "fixed_size": 1}, 5, 2),
    (load_cls("king_keltner_strategy", "KingKeltnerStrategy"), "m2605.DCE", Exchange.DCE, "M2605",
     {"kk_length": 38, "kk_dev": 2.6, "trailing_size": 12, "fixed_size": 1}, 10, 1),
]


def download_bars(ak_symbol, symbol, exchange):
    """新浪日线 -> vnpy数据库"""
    df = ak.futures_zh_daily_sina(symbol=ak_symbol)
    df = df.rename(columns={"date": "datetime", "open": "open_price", "high": "high_price",
                            "low": "low_price", "close": "close_price", "volume": "volume",
                            "hold": "open_interest"})
    df["datetime"] = pd.to_datetime(df["datetime"]).dt.tz_localize("Asia/Shanghai")
    df = df[(df["datetime"] >= pd.Timestamp(START, tz="Asia/Shanghai"))
            & (df["datetime"] <= pd.Timestamp(END, tz="Asia/Shanghai"))]
    bars = []
    for _, row in df.iterrows():
        bars.append(BarData(
            symbol=symbol, exchange=exchange, datetime=row["datetime"].to_pydatetime(),
            interval=Interval.DAILY,
            open_price=float(row["open_price"]), high_price=float(row["high_price"]),
            low_price=float(row["low_price"]), close_price=float(row["close_price"]),
            volume=float(row["volume"]), open_interest=float(row.get("open_interest") or 0),
            turnover=0.0, gateway_name="DB",
        ))
    DB.save_bar_data(bars)
    print(f"{ak_symbol} -> {symbol}.{exchange.value}: {len(bars)} 根日线")


def main():
    print("--- 下载数据 ---")
    for _, vt_symbol, exchange, ak_symbol, _, _, _ in TASKS:
        symbol, _ = vt_symbol.split(".")
        try:
            download_bars(ak_symbol, symbol, exchange)
        except Exception as e:
            print(f"{ak_symbol} 下载失败: {e}")

    print("--- 回测 ---")
    results = []
    for strategy_class, vt_symbol, exchange, _, setting, size, slippage in TASKS:
        engine = BacktestingEngine()
        engine.set_parameters(
            vt_symbol=vt_symbol, interval=Interval.DAILY,
            start=START, end=END,
            rate=1.0 / 10000, slippage=slippage, size=size, pricetick=1, capital=1_000_000,
        )
        engine.add_strategy(strategy_class, setting)
        try:
            engine.load_data()
            engine.run_backtesting()
            engine.calculate_result()
            st = engine.calculate_statistics(output=False)
            results.append({
                "strategy": strategy_class.__name__,
                "symbol": vt_symbol,
                "total_return_%": round(st.get("total_return", 0), 2),
                "annual_return_%": round(st.get("annual_return", 0), 2),
                "max_dd_%": round(st.get("max_ddpercent", 0), 2),
                "sharpe": round(st.get("sharpe_ratio", 0), 2),
                "trade_count": st.get("total_trade_count", 0),
                "win_rate_%": round(st.get("winning_rate", 0), 2),
            })
            print(f"{strategy_class.__name__} @ {vt_symbol} 完成")
        except Exception as e:
            print(f"{strategy_class.__name__} @ {vt_symbol} 失败: {e}")

    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    df.to_csv("backtest_results.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
