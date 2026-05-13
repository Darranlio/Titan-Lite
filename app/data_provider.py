import yfinance as ticker_info
import yfinance as yf
import pandas as pd
import time
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_fixed
from datetime import datetime, timedelta
from config import settings

class DataProvider:
    """
    Titan-Lite V2 数据适配层 (美港股优先)
    基于 yfinance 和自定义爬虫获取行情与投行目标价
    """

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_history_price(symbol, start_date=None, end_date=None, interval="1d"):
        """
        获取个股历史行情 (yfinance)
        :param symbol: 股票代码 (如 'AAPL', '0700.HK')
        """
        try:
            # 自动处理未来日期
            real_today = pd.Timestamp.now().strftime("%Y-%m-%d")
            if not end_date or end_date > real_today:
                end_date = real_today
            
            # yfinance 获取数据
            ticker = yf.Ticker(symbol)
            # 增加对 period 的防御性处理
            df = ticker.history(start=start_date, end=end_date, interval=interval)
            
            # 如果依然拿不到，尝试拿最近 1 天
            if df.empty:
                df = ticker.history(period="1d")

            if df.empty: return pd.Series()
            
            # 标准化清洗
            series = df['Close']
            series.name = symbol
            return series
        except Exception as e:
            print(f"yfinance 获取行情失败 {symbol}: {e}")
            return pd.Series()

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_analyst_info(symbol):
        """
        获取投行目标价与评级 (Analyst Targets)
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 提取关键估值字段
            result = {
                'currentPrice': info.get('currentPrice') or info.get('previousClose'),
                'targetMeanPrice': info.get('targetMeanPrice'),
                'targetLowPrice': info.get('targetLowPrice'),
                'targetHighPrice': info.get('targetHighPrice'),
                'recommendationKey': info.get('recommendationKey'), # e.g., 'buy', 'strong_buy'
                'numberOfAnalystOpinions': info.get('numberOfAnalystOpinions'),
                'peRatioTTM': info.get('trailingPE'),
                'roeTTM': info.get('returnOnEquity'),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown')
            }
            
            # 计算潜在涨幅
            if result['currentPrice'] and result['targetMeanPrice']:
                result['upside'] = (result['targetMeanPrice'] - result['currentPrice']) / result['currentPrice']
            else:
                result['upside'] = 0
                
            return result
        except Exception as e:
            print(f"获取分析师数据失败 {symbol}: {e}")
            return {}

    @staticmethod
    def get_company_news(symbol, limit=5):
        """
        获取公司最新新闻
        """
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            return news[:limit]
        except:
            return []

    @staticmethod
    def get_market_benchmarks():
        """获取全球核心指数表现"""
        indices = {
            "S&P 500": "SPY",
            "Nasdaq 100": "QQQ",
            "Dow Jones": "DIA",
            "Hang Seng": "^HSI"
        }
        results = {}
        for name, symbol in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                # 获取过去 5 天数据看趋势
                hist = ticker.history(period="5d")
                if not hist.empty:
                    change = (hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]
                    results[name] = f"{change:.2%}"
            except:
                results[name] = "Data N/A"
        return results

    @staticmethod
    def get_company_details(symbol):
        """获取公司深度简介与业务背景 (自动翻译为中文)"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            summary_en = info.get('longBusinessSummary', 'No summary available.')
            
            # 使用 LLM 进行专业翻译
            summary_cn = summary_en
            if summary_en and summary_en != 'No summary available.':
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
                    prompt = f"请将以下这段股票业务简介翻译为专业的金融中文。要求：准确、精炼、符合中文表达习惯，不需要多余的解释。\n\n原文：\n{summary_en}"
                    resp = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}], temperature=0.1)
                    summary_cn = resp.choices[0].message.content.strip()
                except Exception as e:
                    print(f"翻译简介失败: {e}")
            
            return {
                "summary": summary_cn,
                "full_name": info.get('longName', symbol),
                "website": info.get('website', '#'),
                "employees": info.get('fullTimeEmployees', 'N/A')
            }
        except: return {"summary": "获取失败", "full_name": symbol}

    @staticmethod
    def get_financial_highlights(symbol):
        """获取财务报表核心亮点 (成长性与盈利能力)"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                "rev_growth": info.get('revenueGrowth'), # 营收增长
                "net_margin": info.get('profitMargins'),  # 利润率
                "fcf": info.get('freeCashflow'),         # 自由现金流
                "ebitda_margin": info.get('ebitdaMargins'),
                "debt_to_equity": info.get('debtToEquity')
            }
        except: return {}

    @staticmethod
    def get_exchange_rates():
        """获取实时汇率 (USDHKD, USDCNY)"""
        rates = {"USD": 1.0, "HKD": 7.8, "CNY": 7.2} # 默认值
        try:
            # 抓取雅虎财经汇率
            pairs = ["USDHKD=X", "USDCNY=X"]
            for pair in pairs:
                ticker = yf.Ticker(pair)
                hist = ticker.history(period="1d")
                if not hist.empty:
                    currency = pair[3:6]
                    rates[currency] = hist['Close'].iloc[-1]
            return rates
        except: return rates

# 导出单例
data_provider = DataProvider()
