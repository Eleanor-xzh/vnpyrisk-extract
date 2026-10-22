# -*- coding: utf-8 -*-


# =================================================
# 数据服务独立配置
# =================================================
CONFIG_DATAFEED = {    # ys：各个独立模块变独立配置项后，对应独立模块导入config中该对应配置项，就不需要导入其它无关配置项了，可以控制其可能被误修改的范围？？？
    "enable": True,   # 是否启用；
    "default_datafeed": "tushare1",   # 默认数据源: "tqsdk" | "tushare" | "amazingdata" | "binance"
    "init_config": {
        "query_lock_timeout": 10,  # 查询锁超时时间（秒），超过该时间若拿不到锁则放弃查询
        "max_workers": 16,  # 数据服务器总工作线程数
        "backend_concurrency": {  # 每数据块(账号)并发度，键=块名；0 = 不初始化该块
            "tushare": 4,
            "tqsdk": 4,
            "amazingdata": 0,
            "binance": 4,
        },
    },
    "config_datafeed": {
        # ---- Tushare ----
        "tushare1": {
            "datafeed_type": "tushare",
            "username": "",  # Tushare 用户名（可选）
            "password": "7e0cea1d21041a7bf19b31aec987c685a4d9b6bfe0726bcc64bd2284",  # Tushare API token（必填）
        },
        # ---- 天勤 TQSDK ----
        "tqsdk": {
            "datafeed_type": "tqsdk",
            "phone": "111111111",  # 天勤手机号
            "password": "111111111",  # 天勤密码
        },
        # ---- Binance 币安 ----
        "binance": {
            "datafeed_type": "binance",
            "api_key": "111111111",        # Binance API Key
            "api_secret": "111111111",     # Binance API Secret
        },
        # ---- 银河 AmazingData（专业版） ----
        "amazingdata": {
            "datafeed_type": "amazingdata",
            # 数据服务器地址（必填，向银河证券营业部申请）
            "host": "101.230.159.234",
        },
    },
}

# =================================================
# 数据库配置
# =================================================
CONFIG_DATABASE = {
    "enable": True,   # 是否启用；
    "default_database": "sqlite2",    # 默认值；
    "init_config": {
        "timezone": "Asia/Shanghai",
    },
    "config_database": {
        "sqlite2": {
            "database_type": "sqlite",    # 块名可自定义命名，database_type 标标准类型
            "path": "./data_DB/market_data.db"
        },
        "mysql": {    # ys：mysql可能有多个库，这个名称可以叫mysql_xzh,也可能叫mysql2等等，在下面策略里面给的是这个名字？？？同理，其它的datafeed、gateway都是允许同一个通道有不同的配置的，类似此处？？？xzh:已实现
            "database_type": "mysql",    # 新增？？？xzh:已实现，get_database 按 database_type 分发
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "111111111",
            "database": "vnpy",
            "charset": "utf8mb4",
        },
        "postgresql": {
            "database_type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "111111111",
            "database": "vnpy",
        },
    },
}

# =================================================
# 默认/共享网关表 (Gateway)
# =================================================
CONFIG_GATEWAY = {    # 网关块：块名可自定义（如 xtp1/xtp2），gateway_type 标标准类型    # 账号统一只放此处
    "enable": True,   # 是否启用；不启用就默认使用模拟盘 vnpy_paperaccount；
    "default_gateway": "xtp1",    # 默认值；
    "init_config": {
    },
    "config_gateway": {
        "xtp1": {
            "gateway_type": "xtp",    # 块内标标准类型，防腐层按此分发
            "账号": "111111111",
            "密码": "111111111",
            "客户号": 1,
            "交易地址": "122.112.139.0",
            "交易端口": 6101,
            "行情地址": "119.3.103.38",
            "行情端口": 6002,
            "行情协议": "TCP",
            "日志级别": "INFO",
            "授权码": "111111111"
        },
        "ctp": {
            "gateway_type": "ctp",
            "用户名": "111111111",
            "密码": "111111111",
            "经纪商代码": "9999",  # SimNow固定为9999
            "交易服务器": "tcp://182.254.243.31:30001",
            "行情服务器": "tcp://182.254.243.31:30011",
            "产品名称": "simnow_client_test",
            "授权编码": "0000000000000000",
            "柜台环境": "测试"
        },
        "tqsdk": {
            "gateway_type": "tqsdk",
            "phone": "111111111",
            "password": "111111111"
        },
        "openctp": {
            "gateway_type": "openctp",
            # 7*24
            # "用户名": "18878",
            # 仿真
            "用户名": "111111111",
            "密码": "111111111",
            "经纪商代码": "9999",
            # 7*24
            # "交易服务器": "tcp://trading.openctp.cn:30001",
            # "行情服务器": "tcp://trading.openctp.cn:30011",
            # 仿真环境
            "交易服务器": "tcp://trading.openctp.cn:30002",
            "行情服务器": "tcp://101.226.249.90:33213",
            "产品名称": "simnow_client_test",
            "授权编码": "0000000000000000",
            "柜台环境": "测试"
        },
    },
}

# =================================================
# 通知配置 (Notice)
# =================================================
CONFIG_NOTICE = {    # 通知类默认值
    "enable": True,
    "default_notice": "email1",
    "init_config": {
    },
    "config_notice": {
        "email1": {
            "smtp_server": "smtp.qq.com",  # 或 smtp.exmail.qq.com
            "smtp_port": 465,
            "sender_name": "111111111",
            "username": "111111111",  # 发信人
            "password": "111111111",  # 注意是授权码不是登录密码
            "receivers": ["111111111@qq.com",
                          "222222222@qq.com"],  # 收信人
            "max_attachment_mb": 5.0  # 超过5MB就压缩
        },
    },
}

# =================================================
# 风控配置 (Risk)
# =================================================
CONFIG_RISK = {    # 风控默认值
    "enable": True,  # 风控总开关
    "init_config": {
    },
    "config_risk": {    # 策略可在 factor_dict 按 config_risk 键覆盖
        # ys：用横向分割（# ------ 管理配置项 -----）那些是管理配置，那些是第一类配置，那些是第二类配置，那些是第三类配置？？？
        # 风控参数
        # “active”:是否启用 “enable”:是否执行

        # 标的黑名单配置
        "symbol_blacklist": {"enable": True, "execute": False, "list": []},
        # 盘口流动性检查
        "tick_liquidity": {"enable": True, "execute": False,},
        # 流动性监测
        "liquidity_config": {"enable": True, "execute": False, "window": 3, "drop_threshold": 0.5},

    },
}

# =================================================
# 止盈止损配置 (Stoploss)
# =================================================
CONFIG_STOPLOSS = {    # 止盈止损默认值，（策略可在 factor_dict 覆盖）
    "enable": True,  # 止盈止损总开关
    "init_config": {
    },
    "config_stoploss": {    # 策略可在 factor_dict 按 config_stoploss 键覆盖
        # 止盈止损配置
        # interval:pandas 频率字符串，如 "1min", "1h", "D", "W"
        # 方法1：百分比最大亏损
        "maxLoss_ratio": {"enable": True, "execute": False, "threshold": 0.1, "benchmark_value": 1.0},
        # 方法2：静态价格止损
        "maxLoss_stastic": {"enable": True, "execute": False, "threshold_value": 0.85},
        # 方法3：最大回撤止损
        "max_loss_MDD": {"enable": True, "execute": False, "loss_threshold": 0.10},
        # 方法4：滚动标准差均值倍数带
        "volatilityMultiple_MA": {"enable": True, "execute": False, "volatility_multiplier": 3, "period": 20, "interval": "1min"},
        # 方法5：滚动标准差的标准差倍数带
        "volatilityMultiple_STD": {"enable": True, "execute": False, "volatility_multiplier": 3, "period": 20, "interval": "1min"},
        # 方法6：ATR 止损/止盈
        "ATR": {"enable": True, "execute": False, "period": 14, "atr_multiplier": 3, "benchmark_value": 1.0, "interval": "1min", "enable_profit": False, "profit_multiplier": 3,}
    },
}

# =================================================
# 盘口数据录制 (Tick Recorder)
# =================================================
CONFIG_DATARECORDER = {    # 盘口录制默认值，参与 deep_merge 合并链（策略可在 STRATEGY_MAP 覆盖）
    "enable": False,  # 盘口录制总开关
    "init_config": {
        "flush_interval_seconds": 3,  # 批量落盘间隔（秒），映射为 timer_interval
        "max_buffer_size": 100000,  # 缓冲上限（条），达到强制落盘
        "default_database": "sqlite",
        # 录制目标库: sqlite/mysql/postgresql；空=跟随 CONFIG_DATABASE["config_database"]["default_database"]
    },
    "config_datarecorder": {
    },
}

# =================================================
# 抢单配置 (Taker)
# =================================================
CONFIG_TAKER = {    # 抢单默认值（策略可在 factor_dict 覆盖）
    "enable": False,  # 抢单总开关
    "init_config": {
    },
    "config_taker": {
        # 按照方法配，同一个方法放在同一个字典里面，通用的配置可以放外面
        "slippage_scan": {                 # 方法：滑点限制内逐档扫盘吃单（现有方法整体包裹）
            "enable": True,                # 方法开关：False 时不启用该方法
            "slippage": {  # 滑点控制
                "mode": "percent",               # "tick" (固定跳数) 或 "percent" (百分比)
                "tick_size": 2,                  # mode="tick" 时生效：允许追的最大跳数
                "percent": 0.005,                # mode="percent" 时生效：允许追的最大百分比 (0.005 = 0.5%)
            },
            "max_depth": 5,                      # 扫描盘口深度（档位数）
            "volume_rule": {  # 量规则
                "mode": "ratio",                 # "fixed" | "ratio" | "full"
                "specified_volume": 10.0,        # mode="fixed" 时生效：对手盘累计量 ≥ 此值
                "volume_ratio": 0.8,             # mode="ratio" 时生效：对手盘累计量 ≥ 本单量 × 此比例
            },
        },
    },
}

# =================================================
# 日志配置 (Logger)
# =================================================
CONFIG_LOGGER = {    # 日志默认值，
    "enable": True,  # 日志开关：
    "init_config": {
    },
    "config_logger": {    # 开关由 logger 内部判断
        "enable": True,    # 日志开关：多 context 同进程只开一个，其余关掉（不新建文件）
        "log_dir": "./log",    # 日志目录（日志名 = context 名）
    },
}

# =================================================
# 绩效评价配置 (Cal Metric)
# =================================================
CONFIG_CAL_METRIC = {    # 绩效评价默认值（策略可在 factor_dict 覆盖）
    "enable": True,  # 绩效评价总开关
    "init_config": {
    },
    "config_cal_metric": {
        "metric_windows": [1, 5, 10, 20],   # 绩效评价滚动窗口大小列表（对应 cal_metric 模块）
    },
}

# =================================================
# 全局默认配置 (Global Defaults)
# =================================================
GLOBAL_DEFAULTS = {
    "paths": {
        "base_result_dir": "./result",
    },
    # 通用参数
    "params": {
        # CSV 最大文件大小，单位 MB
        "max_csv_size_mb": 20,
        # 每日结算时间 (HH:MM)
        "settlement_time": "15:30",
    }
}

# =================================================
# 策略注册表
# =================================================
factor_dict = [
    # 参数形式要对照回测框架中的factor_dict（config_factor_dict）的结构设计：形式改为list，字典执行顺序无法固定
    {"func_name_factor": "stra_1_stock",
     "config_gateway": "xtp",
     "config_datafeed": "tushare",
     },
    {"func_name_factor": "stra_1_future",
     "config_gateway": ["ctp", "xtp"],  # ys：考虑可以支持list形式，即一个策略里面可能需要多个交易通道，但是需要考虑策略里面交易的时候需要指定交易通道？？？    # ys：账号信息不要放在factor中，还是放在CONFIG_GATEWAY这里指定对应名称？？？
     "config_datafeed": ["tqsdk"],  # ys：考虑可以支持list形式，即一个策略里面可能需要多个数据通道，但是需要考虑使用的时候需要指定具体通道？？？
     },
    {"func_name_factor": "cs2_signal",
     "config_gateway": "tqsdk",
     "config_datafeed": "tqsdk",
     "config_risk": {
         "total_order_count": {"enable": True, "execute": False, "threshold": 1},
         "total_cancel_count": {"enable": True, "execute": False, "threshold": 1},
     },
     "str1": {
         "param": {}
     },
     "str2": {
         "param": {}
     }
     },
    {"func_name_factor": "stra_1_openctp",
     "config_gateway": "openctp"
     },
    {"func_name_factor": "HO_IH_Arbitrage",
     "config_gateway": "tqsdk",
     "config_datafeed": "tqsdk",
     # ---- 期权链构建参数 ----
     "option_chains_params": {
         "symbol": "HO",  # 期权品种代码
         "symbol_type": "option",  # 资产类型
         "date_range": ("2026-07-16", "2026-08-24"),  # 时间窗口
     },
     "factor_params": {
         # ---- 核心参数 ----
         "CONTRACT_RATIO": 3,  # HO : IH = 3 : 1
         "RISK_FREE_RATE": 0.015,  # 年化无风险利率
         "OPTION_FEE_PER_SIDE": 18.0,  # 15.0 * 1.2
         "IH_OPEN_RATE": 0.000023,  # 开仓费率
         "IH_CLOSE_TODAY_RATE": 0.00023,  # 平今费率
         "ENTRY_SLIPPAGE_BUFFER_MONEY": 180.0,  # 滑点缓冲（元），补偿盘口吃单滑点
         "ENTRY_EXECUTION_RISK_BUFFER_MONEY": 120.0,  # 执行风险缓冲（元），补偿流动性不足风险
         "ENTRY_THRESHOLD_SMALLEST": -12.0,  # 最小开仓阈值（指数点数），低于此值不开仓
         "EXIT_PROFIT_EDGE": 0.5,  # 止盈阈值（指数点数），价差≥此值平仓
         "STOP_LOSS_EDGE": -2.0,  # 止损阈值（指数点数），价差≤此值平仓
     }
     },
    # HO chain0 level4 CS2 因子套利(策略7)
    {"func_name_factor": "HO_level4_cs2",
     "config_gateway": "tqsdk",
     "config_datafeed": {"default_datafeed": "tqsdk"},
     # ---- 期权链构建参数 ----
     "option_chains_params": {
         "symbol": "HO",  # 期权品种代码
         "symbol_type": "option",  # 资产类型
         "date_range": ("2025-09-01", "2026-09-30"),  # 建链时间窗口(覆盖全年原始数据，带教16用366天回溯)
     },
     "factor_params": {
         # ---- 信号/持仓 ----
         "SIGNAL_DAY": 43200,  # cs2_signal rolling day（约一整天 tick 数）
         "SIGNAL_WINDOW_SIZE": 57000,  # 固定信号窗口行数(覆盖 shift/zscore_prev)
         "SIGNAL_SLOW_SECONDS": 0.3,  # cs2_signal 单次计算耗时阈值(秒)，超时打 WARNING
         "LOOP_SLOW_SECONDS": 0.5,  # 主循环单轮业务处理耗时阈值(秒)，超时打 WARNING
         "SIGNAL_CONFIRMATIONS": 10,  # 连续非零持仓信号达到该次数才开仓
         "ORDER_VOLUME": 1,  # 每条腿目标持仓绝对手数
         "LEVEL": "level4",  # 链档位(ATM 下方第4档)
         "LOGICAL_COLUMNS": ("HO_chain0_C_level4", "HO_chain0_P_level4"),  # cs2_signal 两列逻辑名(C,P)
         # ---- 时段门控 ----
         "CHAIN_FLAT_HOUR": 14,  # 换月日强平平仓小时
         "CHAIN_FLAT_MINUTE": 30,  # 换月日强平分钟
         "ENABLE_1457_PRICE_CHECK": True,  # 14:57 起三时间戳价格确认
         "PRICE_CHECK_HOUR": 14,  # 尾盘价格检查开始小时
         "PRICE_CHECK_MINUTE": 57,  # 尾盘价格检查开始分钟
         "PRICE_CONFIRM_TIMESTAMPS": 3,  # 候选价需连续三个不同时间戳确认
         "PRICE_MAX_CHANGE_RATIO": 0.10,  # 相邻时间戳价格变化<10%
         "STOP_HOUR": 15,  # 15:00 后停止行情判断
         "STOP_MINUTE": 0,
     },
     "offline_params": {
         # 相对 account_1_strategy_7/
         "dataSrc_derivativeContract_root": "data/dataSrc_derivativeContract_dir",
         "dataSrc_spot_root": "data/dataSrc_spot_dir",
         "chain_output_dir": "data/result/HO",
         "pull_times": ["11:50", "15:20"],  # 盘中/收盘增量拉取时刻（普通天勤号，推后避开行情延迟）
         "HISTORY_INITIAL_DAYS": 365,  # 拉取起止范围/首次回溯天数（带教16：366 被 HISTORY_MAX_DAYS=365 封顶，取有效值 365）
         "REBUILD_CHAIN0_MONTH_ONLY": False,  # False 拉/建全部未到期月份（带教16默认）；True 只重建 chain0 所在月
     }
     }
]

# =================================================
# 运维路径注册表 (Flat Architecture)
# 键名(Key)可以自己取，值(Value)必须是结果文件夹的相对路径
# =================================================
DEPLOYMENT_MAPPING = {    # ys：没看懂什么用途？？？xzh:ops_control下单时通过映射把指令发送到对应目录下面；聚合器通过映射找到策略的四张表所在位置
    # 对应 CTP 期货通道
    "acc_1_ctp": "./account_1_strategy_1/result/stra_1_future",
    # 对应 OpenCTP 仿真通道
    "acc_1_openctp": "./account_1_strategy_2/result/stra_1_openctp",
    # 对应 天勤 通道
    "acc_1_tq": "./account_1_strategy_3/result/stra_1_tq",
    # 对应 XTP 股票通道
    "acc_1_xtp": "./account_1_strategy_4/result/stra_1_stock",
}

# =================================================
# 聚合器监控配置
# 可选择聚合 DEPLOYMENT_MAPPING 中的任意账户进行汇总监控
# =================================================
AGGREGATOR_MAP = {
    # accounts 填 DEPLOYMENT_MAPPING 中的部署名（如 acc_1_ctp），路径由该表映射，不直接写完整目录
    "Aggregator_Acc1": {
        "accounts": [
            "acc_1_ctp",
            "acc_1_openctp",
        ],
        # 通用参数
        "params": {
            # 每日结算时间 (HH:MM)
            "settlement_time": "15:35",
        },
    },
    "Aggregator_Acc2": {
        "accounts": [
            "acc_1_tq",
            "acc_1_xtp",
        ],
        # 通用参数
        "params": {
            # 每日结算时间 (HH:MM)
            "settlement_time": "15:35",
        },
    }
}
