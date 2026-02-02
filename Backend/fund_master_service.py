# -*- coding: UTF-8 -*-
"""
Fund-Master 核心功能服务模块
移植自 fund-master/fund.py，提供实时市场数据获取能力
包含：7x24快讯、行业板块排行、实时金价、历史金价、A股成交量、上证指数、市场指数汇总
"""

import datetime
import json
import time
import threading
import requests
import urllib3

try:
    from curl_cffi import requests as curl_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False
    curl_requests = None

urllib3.disable_warnings()

class FundMasterService:
    """Fund-Master 核心数据服务"""
    
    # 内存缓存（带过期时间）
    _cache = {}
    _cache_lock = threading.Lock()
    
    # 缓存过期时间配置（秒）
    CACHE_TTL = {
        'flash_news': 60,           # 快讯 1分钟
        'sector_rank': 300,         # 板块排行 5分钟
        'market_index': 60,         # 市场指数 1分钟
        'gold_realtime': 60,        # 实时金价 1分钟
        'gold_history': 3600,       # 历史金价 1小时
        'a_volume_7days': 300,      # 7日成交量 5分钟
        'sse_30min': 60,            # 上证30分钟 1分钟
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.baidu_session = None
        self._init_baidu_session()
    
    def _init_baidu_session(self):
        """初始化百度股市通会话（使用 curl_cffi 绕过反爬）"""
        if CURL_CFFI_AVAILABLE:
            self.baidu_session = curl_requests.Session(impersonate="chrome")
            self.baidu_session.headers = {
                "accept": "application/vnd.finance-web.v1+json",
                "accept-language": "zh-CN,zh;q=0.9",
                "origin": "https://gushitong.baidu.com",
                "referer": "https://gushitong.baidu.com/",
                "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
            }
            # 预热会话
            try:
                self.baidu_session.get(
                    "https://gushitong.baidu.com/index/ab-000001",
                    headers={"user-agent": self.baidu_session.headers["user-agent"]},
                    timeout=10, 
                    verify=False
                )
            except Exception:
                pass
        else:
            # 降级使用普通 requests
            self.baidu_session = self.session
    
    def _get_cache(self, key: str):
        """获取缓存数据"""
        with self._cache_lock:
            if key in self._cache:
                data, expire_time = self._cache[key]
                if time.time() < expire_time:
                    return data
                else:
                    del self._cache[key]
        return None
    
    def _set_cache(self, key: str, data, ttl_key: str):
        """设置缓存数据"""
        with self._cache_lock:
            ttl = self.CACHE_TTL.get(ttl_key, 60)
            self._cache[key] = (data, time.time() + ttl)
    
    # ==================== 7x24 快讯 ====================
    def get_flash_news(self, count: int = 20) -> dict:
        """
        获取7x24小时快讯
        数据源：百度股市通
        
        Args:
            count: 获取快讯数量，默认20条
            
        Returns:
            dict: {'success': bool, 'data': list, 'update_time': str}
        """
        cache_key = f'flash_news_{count}'
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        try:
            url = f"https://finance.pae.baidu.com/selfselect/expressnews?rn={count}&pn=0&tag=A股&finClientType=pc"
            response = self.baidu_session.get(url, timeout=10, verify=False)
            
            if response.json().get("ResultCode") == "0":
                news_list = response.json()["Result"]["content"]["list"]
                result = []
                
                for item in news_list:
                    evaluate = item.get("evaluate", "")
                    title = item.get("title", "")
                    if not title and item.get("content", {}).get("items"):
                        title = item["content"]["items"][0].get("data", "")
                    
                    publish_time = item.get("publish_time", "")
                    if publish_time:
                        publish_time = datetime.datetime.fromtimestamp(
                            int(publish_time)
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 相关股票
                    entities = item.get("entity", [])
                    related_stocks = [
                        {
                            "code": e.get("code", "").strip(),
                            "name": e.get("name", "").strip(),
                            "ratio": e.get("ratio", "").strip()
                        }
                        for e in entities if e.get("code")
                    ]
                    
                    result.append({
                        "title": title,
                        "evaluate": evaluate,  # 利好/利空/空
                        "publish_time": publish_time,
                        "related_stocks": related_stocks
                    })
                
                data = {
                    "success": True,
                    "data": result,
                    "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self._set_cache(cache_key, data, 'flash_news')
                return data
            
            return {"success": False, "error": "获取快讯失败", "data": []}
        
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}
    
    # ==================== 行业板块排行 ====================
    def get_sector_rank(self, limit: int = 50) -> dict:
        """
        获取行业板块排行（按主力净流入排序）
        数据源：东方财富
        
        Args:
            limit: 返回板块数量，默认50
            
        Returns:
            dict: {'success': bool, 'data': list, 'update_time': str}
        """
        cache_key = f'sector_rank_{limit}'
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        try:
            url = "https://push2.eastmoney.com/api/qt/clist/get"
            params = {
                "cb": "",
                "fid": "f62",
                "po": "1",
                "pz": str(limit),
                "pn": "1",
                "np": "1",
                "fltt": "2",
                "invt": "2",
                "ut": "8dec03ba335b81bf4ebdf7b29ec27d15",
                "fs": "m:90 t:2",
                "fields": "f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205,f124,f1,f13"
            }
            headers = {
                "Referer": "https://fund.eastmoney.com/daogou/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10, verify=False)
            resp_data = response.json()
            
            if resp_data.get("data"):
                result = []
                for bk in resp_data["data"]["diff"]:
                    # 主力净流入（转换为亿）
                    main_inflow = bk.get("f62", 0)
                    main_inflow_str = f"{round(main_inflow / 100000000, 2)}亿" if main_inflow else "0亿"
                    
                    # 小单净流入（转换为亿）
                    small_inflow = bk.get("f84", 0)
                    small_inflow_str = f"{round(small_inflow / 100000000, 2)}亿" if small_inflow else "0亿"
                    
                    result.append({
                        "name": bk.get("f14", ""),
                        "change_pct": f"{bk.get('f3', 0)}%",
                        "main_inflow": main_inflow_str,
                        "main_inflow_pct": f"{round(bk.get('f184', 0), 2)}%",
                        "small_inflow": small_inflow_str,
                        "small_inflow_pct": f"{round(bk.get('f87', 0), 2)}%",
                        "raw_change": bk.get('f3', 0),
                        "raw_main_inflow": main_inflow
                    })
                
                # 按涨跌幅排序
                result.sort(key=lambda x: x['raw_change'], reverse=True)
                
                data = {
                    "success": True,
                    "data": result,
                    "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self._set_cache(cache_key, data, 'sector_rank')
                return data
            
            return {"success": False, "error": "获取板块数据失败", "data": []}
        
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}
    
    # ==================== 市场指数汇总 ====================
    def get_market_index(self) -> dict:
        """
        获取市场指数汇总（A股主要指数 + 全球指数）
        数据源：东方财富（更稳定）
        
        Returns:
            dict: {'success': bool, 'data': list, 'update_time': str}
        """
        cache_key = 'market_index'
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        result = []
        try:
            # 使用东方财富 API 获取主要指数
            # A股主要指数
            a_share_indices = [
                ("1.000001", "上证指数", "A股"),
                ("0.399001", "深证成指", "A股"),
                ("0.399006", "创业板指", "A股"),
                ("0.399005", "中小100", "A股"),
                ("1.000016", "上证50", "A股"),
                ("1.000300", "沪深300", "A股"),
            ]
            
            # 全球主要指数
            global_indices = [
                ("100.HSI", "恒生指数", "港股"),
                ("100.HSCEI", "国企指数", "港股"),
                ("100.NDX", "纳斯达克", "美股"),
                ("100.DJIA", "道琼斯", "美股"),
                ("100.SPX", "标普500", "美股"),
            ]
            
            all_indices = a_share_indices + global_indices
            codes = ",".join([idx[0] for idx in all_indices])
            
            url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
            params = {
                "fltt": "2",
                "invt": "2", 
                "fields": "f2,f3,f4,f12,f14",
                "secids": codes,
                "_": str(int(time.time() * 1000))
            }
            headers = {
                "Referer": "https://quote.eastmoney.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10, verify=False)
            resp_data = response.json()
            
            if resp_data.get("data") and resp_data["data"].get("diff"):
                idx_map = {idx[0].split(".")[1]: (idx[1], idx[2]) for idx in all_indices}
                
                for item in resp_data["data"]["diff"]:
                    code = item.get("f12", "")
                    name_market = idx_map.get(code)
                    if name_market:
                        price = item.get("f2", "-")
                        change_pct = item.get("f3", 0)
                        
                        # 格式化价格
                        if isinstance(price, (int, float)):
                            price = f"{price:.2f}"
                        
                        # 格式化涨跌幅
                        if isinstance(change_pct, (int, float)):
                            change_pct_str = f"{'+' if change_pct >= 0 else ''}{change_pct:.2f}%"
                        else:
                            change_pct_str = str(change_pct)
                        
                        result.append({
                            "name": name_market[0],
                            "price": str(price),
                            "change_pct": change_pct_str,
                            "market": name_market[1],
                            "raw_change": change_pct if isinstance(change_pct, (int, float)) else 0
                        })
            
            # 如果东方财富也失败，尝试新浪财经作为备选
            if not result:
                result = self._get_market_index_sina()
            
            if result:
                data = {
                    "success": True,
                    "data": result,
                    "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self._set_cache(cache_key, data, 'market_index')
                return data
            
            return {"success": False, "error": "获取指数数据失败", "data": []}
        
        except Exception as e:
            return {"success": False, "error": str(e), "data": result}
    
    # ==================== 实时贵金属价格 ====================
    def get_gold_realtime(self) -> dict:
        """
        获取实时贵金属价格
        数据源：金投网/集金号
        
        Returns:
            dict: {'success': bool, 'data': list, 'update_time': str}
        """
        cache_key = 'gold_realtime'
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        try:
            headers = {
                "accept": "*/*",
                "referer": "https://quote.cngold.org/gjs/gjhj.html",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
            }
            
            url = "https://api.jijinhao.com/quoteCenter/realTime.htm"
            params = {
                "codes": "JO_71,JO_92233,JO_92232,JO_75",
                "_": str(int(time.time() * 1000))
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10, verify=False)
            raw = response.text.replace("var quote_json = ", "")
            data = json.loads(raw)
            
            result = []
            if data:
                code_map = {
                    "JO_71": "黄金T+D",
                    "JO_92233": "国际黄金",
                    "JO_92232": "国际白银",
                    "JO_75": "白银T+D"
                }
                
                for code in ["JO_71", "JO_92233", "JO_92232"]:
                    if code in data:
                        d = data[code]
                        update_time = ""
                        if d.get("time"):
                            update_time = datetime.datetime.fromtimestamp(
                                d["time"] / 1000
                            ).strftime("%Y-%m-%d %H:%M:%S")
                        
                        result.append({
                            "name": d.get("showName", code_map.get(code, code)),
                            "price": round(d.get("q63", 0), 2),
                            "change": round(d.get("q70", 0), 2),
                            "change_pct": f"{round(d.get('q80', 0), 2)}%",
                            "open": round(d.get("q1", 0), 2),
                            "high": round(d.get("q3", 0), 2),
                            "low": round(d.get("q4", 0), 2),
                            "prev_close": round(d.get("q2", 0), 2),
                            "update_time": update_time,
                            "unit": d.get("unit", "")
                        })
            
            data = {
                "success": True,
                "data": result,
                "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self._set_cache(cache_key, data, 'gold_realtime')
            return data
        
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}
    
    # ==================== 黄金历史价格 ====================
    def get_gold_history(self, days: int = 10) -> dict:
        """
        获取黄金历史价格
        数据源：金投网/集金号
        
        Args:
            days: 获取天数，默认10天
            
        Returns:
            dict: {'success': bool, 'data': list, 'update_time': str}
        """
        cache_key = f'gold_history_{days}'
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        try:
            headers = {
                "accept": "*/*",
                "referer": "https://quote.cngold.org/gjs/swhj_zghj.html",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            }
            
            # 中国黄金基础金价
            url = "https://api.jijinhao.com/quoteCenter/history.htm"
            params = {
                "code": "JO_52683",
                "style": "3",
                "pageSize": str(days),
                "needField": "128,129,70",
                "currentPage": "1",
                "_": int(time.time() * 1000)
            }
            response = requests.get(url, headers=headers, params=params, timeout=10, verify=False)
            data1 = json.loads(response.text.replace("var quote_json = ", ""))["data"]
            
            # 周大福金价
            params["code"] = "JO_42660"
            response = requests.get(url, headers=headers, params=params, timeout=10, verify=False)
            data2 = json.loads(response.text.replace("var quote_json = ", ""))["data"]
            
            result = []
            for i in range(len(data1)):
                gold = data1[i]
                t = gold.get("time", 0)
                date = datetime.datetime.fromtimestamp(t / 1000).strftime("%Y-%m-%d") if t else ""
                
                gold2 = data2[i] if i < len(data2) else {}
                
                result.append({
                    "date": date,
                    "china_gold_price": gold.get("q1", "N/A"),
                    "china_gold_change": str(gold.get("q70", "N/A")),
                    "zhoudafu_price": gold2.get("q1", "N/A"),
                    "zhoudafu_change": str(gold2.get("q70", "N/A"))
                })
            
            # 按日期倒序（最新的在前）
            result = result[::-1]
            
            data = {
                "success": True,
                "data": result,
                "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self._set_cache(cache_key, data, 'gold_history')
            return data
        
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}
    
    # ==================== 近7日A股成交量 ====================
    def get_a_volume_7days(self) -> dict:
        """
        获取近7日A股成交量（沪深北三市）
        数据源：百度股市通
        
        Returns:
            dict: {'success': bool, 'data': list, 'update_time': str}
        """
        cache_key = 'a_volume_7days'
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        try:
            url = "https://finance.pae.baidu.com/sapi/v1/metrictrend"
            params = {
                "financeType": "index",
                "market": "ab",
                "code": "000001",
                "targetType": "market",
                "metric": "amount",
                "finClientType": "pc"
            }
            
            response = self.baidu_session.get(url, params=params, timeout=10, verify=False)
            
            if str(response.json().get("ResultCode")) == "0":
                trend = response.json()["Result"]["trend"]
                result = []
                
                # 近8天的日期（包括今天）
                today = datetime.datetime.now()
                dates = [(today - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(8)]
                
                for date in dates:
                    total = trend[0]
                    sh = trend[1]
                    sz = trend[2]
                    bj = trend[3]
                    
                    total_data = [x for x in total["content"] if x["marketDate"] == date]
                    sh_data = [x for x in sh["content"] if x["marketDate"] == date]
                    sz_data = [x for x in sz["content"] if x["marketDate"] == date]
                    bj_data = [x for x in bj["content"] if x["marketDate"] == date]
                    
                    if total_data and sh_data and sz_data and bj_data:
                        result.append({
                            "date": date,
                            "total": total_data[0]["data"]["amount"] + "亿",
                            "shanghai": sh_data[0]["data"]["amount"] + "亿",
                            "shenzhen": sz_data[0]["data"]["amount"] + "亿",
                            "beijing": bj_data[0]["data"]["amount"] + "亿"
                        })
                
                data = {
                    "success": True,
                    "data": result,
                    "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self._set_cache(cache_key, data, 'a_volume_7days')
                return data
            
            return {"success": False, "error": "获取成交量数据失败", "data": []}
        
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}
    
    # ==================== 市场指数分时数据 ====================
    def _get_eastmoney_intraday(self, secid: str, name: str) -> list:
        """
        获取东方财富分时数据（内部通用方法）
        """
        try:
            url = "http://push2.eastmoney.com/api/qt/stock/trends2/get"
            params = {
                "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13",
                "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
                "secid": secid,
                "ndays": "1",
                "iscr": "0",
                "iscca": "0"
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data and data.get("data") and data["data"].get("trends"):
                trends = data["data"]["trends"]
                pre_close = data["data"].get("prePrice", 0)
                
                result = []
                for point in trends:
                    # 格式: time, open, close, high, low, volume, amount, avg
                    parts = point.split(",")
                    if len(parts) >= 3:
                        time_str = parts[0].split(" ")[1] # 取 HH:MM
                        price = float(parts[2])
                        
                        # 计算涨跌
                        change = 0
                        change_pct = "0.00%"
                        if pre_close:
                            change = round(price - pre_close, 2)
                            pct = (change / pre_close) * 100
                            change_pct = f"{round(pct, 2)}%"
                        
                        # 成交量处理
                        volume = parts[5]
                        try:
                            vol_num = float(volume)
                            if vol_num > 10000:
                                volume = f"{round(vol_num / 10000, 2)}万"
                        except:
                            pass
                            
                        result.append({
                            "time": time_str,
                            "price": str(price),
                            "change": f"{'+' if change > 0 else ''}{change}",
                            "change_pct": change_pct,
                            "volume": volume
                        })
                return result
            return []
        except Exception as e:
            print(f"Error fetching intraday for {secid}: {e}")
            return []

    def get_indices_intraday(self) -> dict:
        """
        获取多指数分时数据（上证、深证、沪深300）
        
        Returns:
            dict: {'sh': [], 'sz': [], 'hs300': [], 'update_time': str}
        """
        cache_key = 'indices_intraday'
        cached = self._get_cache(cache_key)
        if cached:
            return cached
            
        sh_data = self._get_eastmoney_intraday("1.000001", "上证指数")
        sz_data = self._get_eastmoney_intraday("0.399001", "深证成指")
        hs300_data = self._get_eastmoney_intraday("1.000300", "沪深300")
        
        data = {
            "success": True,
            "data": {
                "sh": sh_data,
                "sz": sz_data,
                "hs300": hs300_data
            },
            "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self._set_cache(cache_key, data, 'sse_30min') # 复用 sse_30min 的 TTL (1分钟)
        return data

    def get_sse_30min(self) -> dict:
        """
        获取上证指数分时数据（兼容旧接口，但提供全天数据）
        """
        # 直接复用新的分时数据获取逻辑，但只返回上证数据
        full_data = self.get_indices_intraday()
        if full_data["success"]:
            return {
                "success": True,
                "data": full_data["data"]["sh"],
                "update_time": full_data["update_time"]
            }
        return {"success": False, "error": "获取上证指数数据失败", "data": []}
    
    # ==================== 汇总数据接口 ====================
    def get_market_overview(self) -> dict:
        """
        获取市场概览（汇总所有关键数据）
        
        Returns:
            dict: 包含所有市场数据的汇总
        """
        return {
            "success": True,
            "market_index": self.get_market_index(),
            "gold_realtime": self.get_gold_realtime(),
            "sector_rank": self.get_sector_rank(limit=20),
            "a_volume_7days": self.get_a_volume_7days(),
            "sse_30min": self.get_sse_30min(),
            "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


# 全局单例
_fund_master_service = None

def get_fund_master_service() -> FundMasterService:
    """获取 FundMasterService 单例"""
    global _fund_master_service
    if _fund_master_service is None:
        _fund_master_service = FundMasterService()
    return _fund_master_service
