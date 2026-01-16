import requests
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Union

# --- 数据清洗器 (原 api_handler.py) ---

class FundDataCleaner:
    def __init__(self):
        self.cleaned_data = {}
    
    def clean_js_variable(self, value: str) -> Any:
        """清洗JavaScript变量值"""
        if value is None:
            return None
            
        value_str = str(value).strip()
        
        # 处理布尔值
        if value_str.lower() in ['true', 'false']:
            return value_str.lower() == 'true'
        
        # 处理数字
        if re.match(r'^-?\d+\.?\d*$', value_str):
            try:
                return float(value_str) if '.' in value_str else int(value_str)
            except (ValueError, TypeError):
                return value_str
        
        # 处理字符串（去除引号）
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]
        
        return value_str
    
    def parse_timestamp(self, timestamp: int) -> str:
        """将时间戳转换为日期字符串"""
        try:
            return datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            return str(timestamp)
    
    def clean_rate(self, value: Any) -> Any:
        """清洗费率数据，统一返回数字或 None"""
        if value is None:
            return None
        value_str = str(value).strip()
        if not value_str or value_str in ['--', '-', 'null', 'undefined']:
            return None
        value_str = value_str.replace('%', '').strip()
        try:
            return float(value_str)
        except (ValueError, TypeError):
            return None

    def clean_array_data(self, data: Any, data_type: str = 'general') -> Any:
        """清洗数组数据"""
        if not data:
            return []
            
        if data_type == 'net_worth':
            # 处理单位净值走势数据
            cleaned = []
            for item in data:
                if isinstance(item, dict):
                    cleaned.append({
                        'date': self.parse_timestamp(item.get('x')),
                        'net_worth': item.get('y'),
                        'equity_return': item.get('equityReturn'),
                        'dividend': item.get('unitMoney')
                    })
            return cleaned
            
        elif data_type == 'position':
            # 处理股票仓位数据
            cleaned = []
            for item in data:
                if isinstance(item, list) and len(item) >= 2:
                    cleaned.append({
                        'date': self.parse_timestamp(item[0]),
                        'position_percentage': item[1]
                    })
            return cleaned
            
        elif data_type == 'performance':
            # 处理业绩比较数据
            cleaned = []
            for item in data:
                if isinstance(item, dict):
                    series_data = []
                    for data_point in item.get('data', []):
                        if isinstance(data_point, list) and len(data_point) >= 2:
                            series_data.append({
                                'date': self.parse_timestamp(data_point[0]),
                                'value': data_point[1]
                            })
                    
                    cleaned.append({
                        'name': item.get('name'),
                        'data': series_data
                    })
            return cleaned
            
        elif data_type == 'ranking':
            # 处理排名数据
            cleaned = []
            for item in data:
                if isinstance(item, dict):
                    cleaned.append({
                        'date': self.parse_timestamp(item.get('x')),
                        'rank': item.get('y'),
                        'total_funds': item.get('sc')
                    })
            return cleaned
            
        else:
            # 通用数组处理
            return [self.clean_js_variable(item) for item in data]
    
    def clean_fund_info(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗基金基本信息"""
        info = {
            'fund_name': self.clean_js_variable(raw_data.get('fS_name')),
            'fund_code': self.clean_js_variable(raw_data.get('fS_code')),
            'fund_type': '混合型',
            'original_rate': self.clean_rate(raw_data.get('fund_sourceRate')),
            'current_rate': self.clean_rate(raw_data.get('fund_Rate')),
            'min_subscription_amount': self.clean_js_variable(raw_data.get('fund_minsg')),
            'is_hb': self.clean_js_variable(raw_data.get('ishb'))
        }
        return info
    
    def clean_performance_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗业绩数据"""
        performance = {
            '1_year_return': self.clean_js_variable(raw_data.get('syl_1n')),
            '6_month_return': self.clean_js_variable(raw_data.get('syl_6y')),
            '3_month_return': self.clean_js_variable(raw_data.get('syl_3y')),
            '1_month_return': self.clean_js_variable(raw_data.get('syl_1y'))
        }
        return performance
    
    def clean_portfolio_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗投资组合数据"""
        portfolio = {
            'stock_codes': self.clean_array_data(raw_data.get('stockCodes')),
            'bond_codes': self.clean_array_data(raw_data.get('zqCodes')),
            'stock_codes_new': self.clean_array_data(raw_data.get('stockCodesNew')),
            'bond_codes_new': self.clean_array_data(raw_data.get('zqCodesNew'))
        }
        return portfolio
    
    def clean_asset_allocation(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗资产配置数据"""
        asset_data = raw_data.get('Data_assetAllocation', {})
        cleaned = {
            'categories': asset_data.get('categories', []),
            'series': []
        }
        
        for series in asset_data.get('series', []):
            cleaned_series = {
                'name': series.get('name'),
                'type': series.get('type'),
                'data': series.get('data', []),
                'yAxis': series.get('yAxis')
            }
            cleaned['series'].append(cleaned_series)
        
        return cleaned
    
    def clean_fund_manager(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """清洗基金经理数据"""
        managers_data = raw_data.get('Data_currentFundManager', [])
        cleaned_managers = []
        
        for manager in managers_data:
            cleaned_manager = {
                'id': manager.get('id'),
                'name': manager.get('name'),
                'photo_url': manager.get('pic'),
                'star_rating': manager.get('star'),
                'work_experience': manager.get('workTime'),
                'managed_fund_size': manager.get('fundSize'),
                'ability_assessment': {
                    'average_score': manager.get('power', {}).get('avr'),
                    'categories': manager.get('power', {}).get('categories', []),
                    'scores': manager.get('power', {}).get('data', []),
                    'assessment_date': manager.get('power', {}).get('jzrq')
                },
                'performance': {
                    'categories': manager.get('profit', {}).get('categories', []),
                    'series': manager.get('profit', {}).get('series', []),
                    'assessment_date': manager.get('profit', {}).get('jzrq')
                }
            }
            cleaned_managers.append(cleaned_manager)
        
        return cleaned_managers
    
    def clean_holder_structure(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗持有人结构数据"""
        holder_data = raw_data.get('Data_holderStructure', {})
        cleaned = {
            'categories': holder_data.get('categories', []),
            'series': []
        }
        
        for series in holder_data.get('series', []):
            cleaned_series = {
                'name': series.get('name'),
                'data': series.get('data', [])
            }
            cleaned['series'].append(cleaned_series)
        
        return cleaned
    
    def clean_same_type_funds(self, raw_data: Dict[str, Any]) -> List[List[Dict[str, Any]]]:
        """清洗同类型基金数据"""
        same_type_data = raw_data.get('swithSameType', [])
        cleaned_categories = []
        
        for category in same_type_data:
            cleaned_funds = []
            for fund_str in category:
                parts = fund_str.split('_')
                if len(parts) >= 3:
                    fund_info = {
                        'code': parts[0],
                        'name': parts[1],
                        'return_rate': self.clean_js_variable(parts[2])
                    }
                    cleaned_funds.append(fund_info)
            cleaned_categories.append(cleaned_funds)
        
        return cleaned_categories
    
    def clean_all_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗所有数据"""
        cleaned_data = {
            'basic_info': self.clean_fund_info(raw_data),
            'performance': self.clean_performance_data(raw_data),
            'portfolio': self.clean_portfolio_data(raw_data),
            # 实时估值数据（来自 fundgz 接口）
            'realtime_estimate': {
                'name': raw_data.get('name'),           # 基金名称
                'fund_code': raw_data.get('fundcode'),  # 基金代码
                'net_worth': raw_data.get('dwjz'),      # 单位净值
                'net_worth_date': raw_data.get('jzrq'), # 净值日期
                'estimate_value': raw_data.get('gsz'),  # 估算净值
                'estimate_change': raw_data.get('gszzl'), # 估算涨跌幅
                'estimate_time': raw_data.get('gztime'),  # 估值时间
            },
            'net_worth_trend': self.clean_array_data(
                raw_data.get('Data_netWorthTrend'), 'net_worth'
            ),
            'accumulated_net_worth': self.clean_array_data(
                raw_data.get('Data_ACWorthTrend'), 'position'
            ),
            'position_trend': self.clean_array_data(
                raw_data.get('Data_fundSharesPositions'), 'position'
            ),
            'total_return_trend': self.clean_array_data(
                raw_data.get('Data_grandTotal'), 'performance'
            ),
            'ranking_trend': self.clean_array_data(
                raw_data.get('Data_rateInSimilarType'), 'ranking'
            ),
            'ranking_percentage': self.clean_array_data(
                raw_data.get('Data_rateInSimilarPersent'), 'position'
            ),
            'scale_fluctuation': raw_data.get('Data_fluctuationScale', {}),
            'holder_structure': self.clean_holder_structure(raw_data),
            'asset_allocation': self.clean_asset_allocation(raw_data),
            'performance_evaluation': raw_data.get('Data_performanceEvaluation', {}),
            'fund_managers': self.clean_fund_manager(raw_data),
            'subscription_redemption': raw_data.get('Data_buySedemption', {}),
            'same_type_funds': self.clean_same_type_funds(raw_data),
            'cleaning_timestamp': datetime.now().isoformat()
        }
        
        return cleaned_data

# --- 基金 API 客户端 ---

class FundAPI:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.cleaner = FundDataCleaner()

    def get_fund_data(self, fund_code: str) -> Union[Dict[str, Any], None]:
        """
        获取单只基金的完整清洗后数据。
        包括基本信息、业绩、持仓、净值走势等。
        """
        raw_data = self._fetch_raw_data(fund_code)
        if not raw_data:
            return None
        
        # 使用 cleaner 清洗数据
        try:
            return self.cleaner.clean_all_data(raw_data)
        except Exception as e:
            print(f"Error cleaning data for {fund_code}: {e}")
            return None

    def search_funds(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索基金（返回列表）
        """
        url = "https://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx"
        params = {
            'm': 1,
            'key': keyword
        }
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'Datas' in data:
                    # 过滤只保留基金类型的条目 (CATEGORYDESC == '基金')
                    funds = [item for item in data['Datas'] if item.get('CATEGORYDESC') == '基金']
                    return funds
            return []
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def _fetch_raw_data(self, fund_code: str) -> Union[Dict[str, Any], None]:
        """
        获取原始基金数据（字典形式），包含所有JS变量。
        """
        data = {}
        
        # 1. 抓取 pingzhongdata 详细数据
        url = f"https://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                js_content = response.text
                
                # 提取所有 var xxx = ...; 也就是 JS 变量
                # 兼容值可能是数字、字符串、数组[]、对象{}
                # 正则解析：var (变量名) = (值);
                # 值可能跨多行，非贪婪匹配
                var_matches = re.findall(r'var\s+(\w+)\s*=\s*(.*?);', js_content, re.DOTALL)
                
                for var_name, var_value in var_matches:
                    var_name = var_name.strip()
                    var_value = var_value.strip()
                    
                    try:
                        # 尝试 JSON 解析 (如果是数组或对象)
                        if var_value.startswith('[') or var_value.startswith('{'):
                             data[var_name] = json.loads(var_value)
                        # 尝试去引号 (如果是字符串)
                        elif var_value.startswith('"') and var_value.endswith('"'):
                             data[var_name] = var_value[1:-1]
                        elif var_value.startswith("'") and var_value.endswith("'"):
                             data[var_name] = var_value[1:-1]
                        # 数字或其它
                        else:
                            data[var_name] = var_value
                    except:
                        # 解析失败保底保留原始字符串
                        data[var_name] = var_value
                        
        except Exception as e:
            print(f"Error fetching detail for {fund_code}: {e}")
            return None

        # 2. 抓取实时估值数据 (可选，用于补充实时信息)
        try:
            real_time_url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"
            response = requests.get(real_time_url, headers=self.headers, timeout=3)
            if response.status_code == 200:
                match = re.search(r"jsonpgz\((.*?)\);", response.text)
                if match:
                    rt_data = json.loads(match.group(1))
                    if rt_data:
                        # 这里的 key 可能和 pingzhongdata 不一样，如果需要合并，要注意 key 冲突
                        # 暂时作为一个子字段，或者直接合并
                        data.update(rt_data)
        except Exception:
            pass # 实时数据获取失败不影响整体
            
        if not data:
            return None

        # 确保 fS_code 存在
        if 'fS_code' not in data:
            data['fS_code'] = fund_code
            
        return data

if __name__ == "__main__":
    # 测试代码
    api = FundAPI()
    code = "019127" 
    print(f"Fetching data for {code}...")
    fund_data = api.get_fund_data(code)
    
    if fund_data:
        print("\n=== Data Fetch Success ===")
        print(f"Name: {fund_data['basic_info']['fund_name']}")
        print(f"Manager: {len(fund_data['fund_managers'])} managers recorded")
        print(f"Latest Net Worth: {fund_data['net_worth_trend'][-1] if fund_data['net_worth_trend'] else 'N/A'}")
        
        # 保存测试数据
        with open(f"fund_{code}_full.json", 'w', encoding='utf-8') as f:
            json.dump(fund_data, f, ensure_ascii=False, indent=2)
        print(f"Saved to fund_{code}_full.json")
    else:
        print("Failed to fetch data.")
