import akshare as ak
import pandas as pd
import time
from tenacity import retry, stop_after_attempt, wait_fixed
from config import settings

class DataProvider:
    """
    数据适配层：隔离 AkShare 的不稳定性
    所有业务代码只调用这里的方法
    """

    @staticmethod
    @retry(stop=stop_after_attempt(settings.DATA_RETRY_ATTEMPTS), wait=wait_fixed(settings.DATA_RETRY_WAIT))
    def get_history_price(symbol, start_date, end_date, adjust="qfq"):
        """
        获取个股历史行情 (带重试)
        返回: pd.Series (Index=Date, Value=Close)
        """
        try:
            # AkShare 接口
            df = ak.stock_zh_a_hist(symbol=symbol, start_date=start_date, end_date=end_date, adjust=adjust)
            if df.empty: return pd.Series()
            
            # 标准化清洗
            df['日期'] = pd.to_datetime(df['日期'])
            series = df.set_index('日期')['收盘']
            series.name = symbol
            
            # 防封IP休眠
            time.sleep(settings.DATA_REQUEST_SLEEP)
            return series
        except Exception:
            return pd.Series()

    @staticmethod
    @retry(stop=stop_after_attempt(settings.DATA_RETRY_ATTEMPTS), wait=wait_fixed(settings.DATA_RETRY_WAIT))
    def get_sector_list():
        """获取全市场板块列表"""
        df = ak.stock_board_industry_name_em()
        return df['板块名称'].tolist()

    @staticmethod
    @retry(stop=stop_after_attempt(settings.DATA_RETRY_ATTEMPTS), wait=wait_fixed(settings.DATA_RETRY_WAIT))
    def get_sector_stocks(sector_name):
        """获取板块成分股，并清洗字段名"""
        df = ak.stock_board_industry_cons_em(symbol=sector_name)
        # 统一重命名，防止 AkShare 变动
        df = df.rename(columns={
            '代码': 'symbol', '名称': 'name', '最新价': 'price',
            '市盈率-动态': 'pe', '总市值': 'market_cap', '换手率': 'turnover'
        })
        time.sleep(settings.DATA_REQUEST_SLEEP)
        return df

    @staticmethod
    @retry(stop=stop_after_attempt(settings.DATA_RETRY_ATTEMPTS), wait=wait_fixed(settings.DATA_RETRY_WAIT))
    def get_index_daily(symbol="sh000300"):
        """获取指数数据用于风控"""
        df = ak.stock_zh_index_daily(symbol=symbol)
        df['date'] = pd.to_datetime(df['date'])
        return df

    @staticmethod
    def get_news_summary(symbol):
        """获取新闻 (不重试，失败就算了)"""
        try:
            df = ak.stock_news_em(symbol=symbol)
            return "\n".join(df['新闻标题'].head(3).tolist())
        except:
            return ""

# 导出单例
data_provider = DataProvider()