from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

from vnpy_ctp import CtpGateway
from vnpy_ctptest import CtptestGateway
from vnpy_tts import TtsGateway
from vnpy_xtp import XtpGateway
# from vnpy_tqsdk import TqsdkGateway
# from vnpy_openctp import OpenctpGateway
# from vnpy_xt import XtGateway
from vnpy_sopt import SoptGateway
from vnpy_sopttest import SopttestGateway
from vnpy_riskmanager import RiskManagerApp
from vnpy_algotrading import AlgoTradingApp
from vnpy_spreadtrading import SpreadTradingApp
from vnpy_scripttrader import ScriptTraderApp
from vnpy_ctastrategy import CtaStrategyApp
from vnpy_datarecorder import DataRecorderApp
from vnpy_datamanager import DataManagerApp
from vnpy_portfoliostrategy import PortfolioStrategyApp
from vnpy_portfoliomanager import PortfolioManagerApp
from vnpy_optionmaster import OptionMasterApp
from vnpy_ctabacktester import CtaBacktesterApp
from vnpy_paperaccount import PaperAccountApp
from vnpy_chartwizard import ChartWizardApp
from vnpy_excelrtd import ExcelRtdApp
from vnpy_webtrader import WebTraderApp


def main() -> None:
    """Start Trader"""
    qapp = create_qapp()

    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)

    main_engine.add_gateway(CtpGateway)
    main_engine.add_gateway(CtptestGateway)
    main_engine.add_gateway(TtsGateway)
    main_engine.add_gateway(XtpGateway)
    # main_engine.add_gateway(TqsdkGateway)
    # main_engine.add_gateway(OpenctpGateway)
    # main_engine.add_gateway(XtGateway)
    main_engine.add_gateway(SoptGateway)
    main_engine.add_gateway(SopttestGateway)

    main_engine.add_app(PaperAccountApp)  # 需要在 riskmanager 前，因为其会更换发单接口send_order；
    main_engine.add_app(DataRecorderApp)
    main_engine.add_app(RiskManagerApp)   # 需要在前，里面要替换主引擎的 send_order；
    main_engine.add_app(AlgoTradingApp)
    main_engine.add_app(CtaStrategyApp)
    main_engine.add_app(SpreadTradingApp)
    main_engine.add_app(OptionMasterApp)
    main_engine.add_app(PortfolioStrategyApp)
    main_engine.add_app(PortfolioManagerApp)

    main_engine.add_app(DataManagerApp)
    main_engine.add_app(ExcelRtdApp)
    main_engine.add_app(ChartWizardApp)

    main_engine.add_app(ScriptTraderApp)
    main_engine.add_app(CtaBacktesterApp)
    main_engine.add_app(WebTraderApp)

    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()

    qapp.exec()


if __name__ == "__main__":
    main()
