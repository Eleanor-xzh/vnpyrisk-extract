from datetime import timedelta, datetime
from collections.abc import Callable
import traceback
import time
import threading
from pandas import DataFrame
from tqsdk import TqApi, TqAuth

from vnpy.trader.datafeed import BaseDatafeed
from vnpy.trader.constant import Interval
from vnpy.trader.object import BarData, TickData, HistoryRequest
from vnpy.trader.utility import ZoneInfo
from config import CONFIG_DATAFEED


INTERVAL_VT2TQ: dict[Interval, int] = {
    Interval.MINUTE: 60,
    Interval.HOUR: 60 * 60,
    Interval.DAILY: 60 * 60 * 24
}

CHINA_TZ = ZoneInfo("Asia/Shanghai")


class TqsdkDatafeed(BaseDatafeed):
    """天勤TQsdk数据服务接口（连接池版：connections 个 TqApi，各自独立锁+泵线程，历史查询真并发）"""

    def __init__(self, cfg: dict = None, connections: int = 1) -> None:
        """
            连接池构造：connections 个 TqApi 连接，每连接独立 RLock + 常驻泵线程。
        :param cfg, dict: 天勤块配置（phone/password）
        :param connections, int: 连接池大小，与 server 端信号量许可数一致（backend_concurrency）；缺省 1 = 旧行为
        """
        tq_cfg: dict = cfg if cfg else CONFIG_DATAFEED["config_datafeed"].get("tqsdk", {})   # 支持按块名传入多套配置
        self.username: str = tq_cfg.get("phone", "")
        self.password: str = tq_cfg.get("password", "")
        connections = max(1, int(connections or 1))  # 池大小下限 1
        self._conns: list = []  # 每连接一个 dict：{api, lock, stop}；独立 TqAuth（共享会被并发登录写坏 token）
        self._pump_threads: list = []  # 每连接一个泵线程
        for i in range(connections):  # 串行建连：TqApi() 构造阻塞至连接完成（约 1-5s/条）
            self._conns.append(self._connect_one(i))
        for i, conn in enumerate(self._conns):  # 每连接一个常驻泵线程：保持各自 serial 缓存实时
            t = threading.Thread(target=self._pump_loop, args=(conn,), name=f"tqsdk_datafeed_pump_{i}", daemon=True)
            t.start()
            self._pump_threads.append(t)
        self._pick_lock = threading.Lock()  # 轮询序号保护
        self._rr_idx = 0  # 轮询起点

    @property
    def _api(self):  # datafeed.py 用 _api/_lock 建 Dataseek；钉在连接 0（Quote 对象贴连接）
        return self._conns[0]["api"]

    @property
    def _lock(self):  # Dataseek 与连接 0 的泵/查询共用这把锁
        return self._conns[0]["lock"]

    def _connect_one(self, i: int) -> dict:
        """建立第 i 条长连接；失败时关闭已建连接并抛错（all-or-nothing，保 pool==并发数不变量）"""
        try:
            return {
                "api": TqApi(auth=TqAuth(self.username, self.password)),  # 每连接独立 TqAuth（有状态 token 槽，不能共享）
                "lock": threading.RLock(),  # 串行化 wait_update：泵线程与查询互斥
                "stop": threading.Event(),  # 泵线程停止标记
                "pumping": False,  # 泵线程正持锁于 wait_update：_acquire_conn 借此区分泵占用（会释放）与 dataseek/查询占用（可能很久）
            }
        except Exception as e:
            for c in self._conns:  # 关闭已建连接，避免泄漏
                try:
                    c["api"].close()
                except Exception:
                    pass
            raise RuntimeError(f"天勤连接失败(conn {i}): {e}") from e

    def _refresh(self, conn: dict) -> None:
        """驱动天勤事件循环，刷新该连接已缓存 serial 的最新数据"""
        try:
            with conn["lock"]:  # 与泵线程互斥。
                conn["api"].wait_update(deadline=time.time() + 0.3)
        except Exception:
            pass

    def _pump_loop(self, conn: dict) -> None:
        """常驻泵线程：持续驱动事件循环，保持该连接已缓存 serial 一直实时，避免长时间空闲后缓存冻结"""
        while not conn["stop"].is_set():  # 循环泵。
            with conn["lock"]:  # 与查询互斥。
                conn["pumping"] = True  # 持锁标记：供 _acquire_conn 识别泵占用（会释放，可阻塞等）。
                try:
                    conn["api"].wait_update(deadline=time.time() + 0.3)  # 驱动事件循环。
                except Exception:
                    time.sleep(1)  # 连接异常时退避，避免空转。
                conn["pumping"] = False  # 释放前清除标记。

    def _acquire_conn(self) -> dict:
        """取一条空闲连接并持有其锁（调用方 must finally 恰好释放一次）：
        历史查询优先非 0 连接（conn0 是 dataseek 的家：Quote 对象贴连接 0，保证 get_quote 不被重拉阻塞），conn0 仅兜底；
        按序先非阻塞试抢（命中泵释放空档即返回）；全忙则阻塞等"泵正持锁"的连接——泵单轮 wait_update ≤0.3s 且
        排队者轮番竞争必赢，30s 仅防极端长旋转；pumping=False 的占用（dataseek/其它查询）不阻塞直等，跳过；
        全部非泵占用则短暂让出后重试，不钉死单个目标。"""
        n = len(self._conns)
        while True:
            with self._pick_lock:  # 只取本轮扫描起点，并发调用起点错开，不长时间占小锁。
                base = self._rr_idx
                self._rr_idx = (base + 1) % max(1, n - 1)  # 起点只在非 0 连接间轮转。
            if n > 1:  # 扫描顺序：非 0 连接优先（轮转起点），conn0 兜底。
                order = [self._conns[(base + k) % (n - 1) + 1] for k in range(n - 1)] + [self._conns[0]]
            else:
                order = [self._conns[0]]
            for conn in order:  # 非阻塞试抢：命中泵释放空档/空闲连接。
                if conn["lock"].acquire(blocking=False):
                    return conn
            for conn in order:  # 阻塞等泵让出（pumping 标记 = 泵正持锁，必会释放；30s 兜底防无限旋转）。
                if conn["pumping"] and conn["lock"].acquire(timeout=30):
                    return conn
            time.sleep(0.05)  # 全部被非泵占用（dataseek/其它查询）：让出 CPU 稍后再试。

    def query_bar_history(self, req: HistoryRequest, output: Callable = print) -> list[BarData] | None:
        """查询k线数据"""
        interval: int | None = INTERVAL_VT2TQ.get(req.interval, None)
        if not interval:
            output(f"Tqsdk查询K线数据失败：不支持的时间周期{req.interval.value}")
            return []

        # 统一固定为最大值，拉取后自行切片
        data_length: int = 10000

        tq_symbol: str = f"{req.exchange.value}.{req.symbol}"

        # 取一条空闲连接（已持有其锁），在该连接上刷新并拉取
        conn = self._acquire_conn()
        try:
            self._refresh(conn)  # 先驱动事件循环刷新缓存 serial，再拉取数据（RLock 可重入）
            df: DataFrame = conn["api"].get_kline_serial(
                symbol=tq_symbol,
                duration_seconds=interval,
                data_length=data_length,
            ).copy()  # 快照避免遍历时被原地改写
        except Exception:
            output(traceback.format_exc())
            raise
        finally:
            conn["lock"].release()  # 恰好释放一次

        # 解析数据
        bars: list[BarData] = []

        if df is not None:
            start_ns: int = int(req.start.replace(tzinfo=CHINA_TZ).timestamp() * 1_000_000_000)
            end_ns: int = int((req.end + timedelta(days=1)).replace(tzinfo=CHINA_TZ).timestamp() * 1_000_000_000)

            for tp in df.itertuples():
                dt_ns: int = int(tp.datetime)

                # 按请求时间范围过滤
                if dt_ns < start_ns or dt_ns > end_ns:
                    continue
                bar: BarData = BarData(
                    symbol=req.symbol,
                    exchange=req.exchange,
                    interval=req.interval,
                    datetime=datetime.fromtimestamp(dt_ns / 1_000_000_000, tz=CHINA_TZ),
                    open_price=tp.open,
                    high_price=tp.high,
                    low_price=tp.low,
                    close_price=tp.close,
                    volume=tp.volume,
                    open_interest=tp.open_oi,
                    gateway_name="TQ",
                )
                bars.append(bar)
        if not bars:
            output(f"天勤 K线 数据在请求区间内为空: ")
            return []
        return bars

    def query_tick_history(self, req: HistoryRequest, output: Callable = print) -> list[TickData]:
        """查询历史Tick数据"""
        # 天勤 get_tick_serial 单次最多拉取 10000 条最新数据
        data_length: int = 10000

        tq_symbol: str = f"{req.exchange.value}.{req.symbol}"

        # 取一条空闲连接（已持有其锁），在该连接上刷新并拉取
        conn = self._acquire_conn()
        try:
            # 先驱动事件循环刷新缓存 serial，再拉取数据（RLock 可重入）
            self._refresh(conn)
            # 调用天勤拉取Tick的专用接口
            df: DataFrame = conn["api"].get_tick_serial(
                symbol=tq_symbol,
                data_length=data_length,
            ).copy()  # 快照避免遍历时被原地改写
        except Exception:
            output(traceback.format_exc())
            raise
        finally:
            conn["lock"].release()  # 恰好释放一次

        # 解析Tick数据
        ticks: list[TickData] = []

        if df is not None and len(df) > 0:
            start_ns: int = int(req.start.replace(tzinfo=CHINA_TZ).timestamp() * 1_000_000_000)
            end_ns: int = int((req.end + timedelta(days=1)).replace(tzinfo=CHINA_TZ).timestamp() * 1_000_000_000)

            for tp in df.itertuples():
                dt_ns: int = int(tp.datetime)

                # 按请求时间范围过滤
                if dt_ns < start_ns or dt_ns > end_ns:
                    continue

                # 封装成 vn.py 标准的 TickData 对象
                tick: TickData = TickData(
                    # --- TickData 必填核心字段 ---
                    symbol=req.symbol,
                    exchange=req.exchange,
                    datetime=datetime.fromtimestamp(dt_ns / 1_000_000_000, tz=CHINA_TZ),

                    # --- 基础量价数据 ---
                    name=req.symbol,
                    volume=getattr(tp, "volume", 0.0),
                    turnover=getattr(tp, "amount", 0.0),  # 天勤为 amount
                    open_interest=getattr(tp, "open_interest", 0.0),
                    last_price=getattr(tp, "last_price", 0.0),
                    last_volume=getattr(tp, "last_volume", 0.0),  # 天勤Tick暂无该字段，安全获取为0
                    limit_up=getattr(tp, "limit_up", 0.0),  # 天勤Tick暂无该字段，安全获取为0
                    limit_down=getattr(tp, "limit_down", 0.0),  # 天勤Tick暂无该字段，安全获取为0

                    # --- OHLC 极值数据 ---
                    open_price=getattr(tp, "open", 0.0),
                    high_price=getattr(tp, "highest", 0.0),  # 天勤为 highest
                    low_price=getattr(tp, "lowest", 0.0),  # 天勤为 lowest
                    pre_close=getattr(tp, "pre_close", 0.0),  # 天勤Tick暂无该字段，安全获取为0

                    # --- 买方盘口价格 (1-5档) ---
                    bid_price_1=getattr(tp, "bid_price1", 0.0),
                    bid_price_2=getattr(tp, "bid_price2", 0.0),
                    bid_price_3=getattr(tp, "bid_price3", 0.0),
                    bid_price_4=getattr(tp, "bid_price4", 0.0),
                    bid_price_5=getattr(tp, "bid_price5", 0.0),

                    # --- 卖方盘口价格 (1-5档) ---
                    ask_price_1=getattr(tp, "ask_price1", 0.0),
                    ask_price_2=getattr(tp, "ask_price2", 0.0),
                    ask_price_3=getattr(tp, "ask_price3", 0.0),
                    ask_price_4=getattr(tp, "ask_price4", 0.0),
                    ask_price_5=getattr(tp, "ask_price5", 0.0),

                    # --- 买方盘口挂单量 (1-5档) ---
                    bid_volume_1=getattr(tp, "bid_volume1", 0.0),
                    bid_volume_2=getattr(tp, "bid_volume2", 0.0),
                    bid_volume_3=getattr(tp, "bid_volume3", 0.0),
                    bid_volume_4=getattr(tp, "bid_volume4", 0.0),
                    bid_volume_5=getattr(tp, "bid_volume5", 0.0),

                    # --- 卖方盘口挂单量 (1-5档) ---
                    ask_volume_1=getattr(tp, "ask_volume1", 0.0),
                    ask_volume_2=getattr(tp, "ask_volume2", 0.0),
                    ask_volume_3=getattr(tp, "ask_volume3", 0.0),
                    ask_volume_4=getattr(tp, "ask_volume4", 0.0),
                    ask_volume_5=getattr(tp, "ask_volume5", 0.0),

                    # --- 本地时间 ---
                    localtime=None,

                    gateway_name = "TQ",
                )
                # 天勤原始字段 id/average/duration 无 TickData 专列，随 extra 透传，供离线数据重建原值。
                tick.extra = {
                    "tq_id": getattr(tp, "id", None),
                    "tq_average": getattr(tp, "average", None),
                    "tq_duration": getattr(tp, "duration", None),
                }
                ticks.append(tick)
        if not ticks:
            output(f"天勤 Tick 数据在请求区间内为空: ")
            return []
        return ticks
