"""
基金列表本地缓存服务
从天天基金获取全部基金列表并存储到本地，支持快速本地搜索
"""
import requests
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any

# 获取项目根目录下的 Data 文件夹路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'Data')

class FundListCache:
    """基金列表本地缓存"""
    
    def __init__(self, cache_file: str = None):
        # 默认存储到 Data 目录
        if cache_file is None:
            cache_file = os.path.join(DATA_DIR, "fund_list_cache.json")
        self.cache_file = cache_file
        self.fund_list: List[Dict[str, Any]] = []
        self.last_update: str = ""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://fund.eastmoney.com/'
        }
        self._load_cache()
    
    def _load_cache(self):
        """从本地文件加载缓存"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.fund_list = data.get('funds', [])
                    self.last_update = data.get('last_update', '')
                    print(f"[FundListCache] 已加载本地缓存: {len(self.fund_list)} 只基金, 更新时间: {self.last_update}")
            except Exception as e:
                print(f"[FundListCache] 加载缓存失败: {e}")
                self.fund_list = []
                self.last_update = ""
        else:
            print("[FundListCache] 本地缓存文件不存在")
    
    def _save_cache(self):
        """保存缓存到本地文件"""
        try:
            data = {
                'funds': self.fund_list,
                'last_update': self.last_update
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[FundListCache] 缓存已保存: {len(self.fund_list)} 只基金")
        except Exception as e:
            print(f"[FundListCache] 保存缓存失败: {e}")
    
    def update_from_api(self) -> Dict[str, Any]:
        """
        从天天基金API获取全部基金列表并更新本地缓存
        返回更新结果信息
        """
        print("[FundListCache] 开始从API获取基金列表...")
        
        try:
            # 天天基金全部基金列表API
            url = "http://fund.eastmoney.com/js/fundcode_search.js"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                return {"success": False, "error": f"API请求失败: {response.status_code}"}
            
            content = response.text
            
            # 解析 JS 格式: var r = [["000001","HXCZHH","华夏成长混合","混合型-偏股","HUAXIACHENGZHANGHUNHE"],...]
            match = re.search(r'var\s+r\s*=\s*(\[[\s\S]*?\]);', content)
            if not match:
                return {"success": False, "error": "无法解析API返回数据"}
            
            raw_list = json.loads(match.group(1))
            
            # 转换为标准格式
            self.fund_list = []
            for item in raw_list:
                if len(item) >= 5:
                    fund = {
                        'CODE': item[0],           # 基金代码
                        'SHORTNAME': item[1],      # 基金简称拼音
                        'NAME': item[2],           # 基金名称
                        'TYPE': item[3],           # 基金类型
                        'PINYIN': item[4]          # 全拼
                    }
                    self.fund_list.append(fund)
            
            self.last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._save_cache()
            
            return {
                "success": True,
                "count": len(self.fund_list),
                "last_update": self.last_update
            }
            
        except Exception as e:
            print(f"[FundListCache] 更新失败: {e}")
            return {"success": False, "error": str(e)}
    
    def search(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        在本地缓存中搜索基金
        支持按代码、名称、拼音搜索
        """
        if not keyword or not self.fund_list:
            return []
        
        keyword_lower = keyword.lower()
        results = []
        
        for fund in self.fund_list:
            # 优先匹配代码（精确匹配开头）
            if fund['CODE'].startswith(keyword):
                results.append({**fund, '_score': 100})
                continue
            
            # 匹配名称
            if keyword in fund['NAME']:
                results.append({**fund, '_score': 80})
                continue
            
            # 匹配拼音缩写
            if keyword_lower in fund.get('SHORTNAME', '').lower():
                results.append({**fund, '_score': 60})
                continue
            
            # 匹配全拼
            if keyword_lower in fund.get('PINYIN', '').lower():
                results.append({**fund, '_score': 40})
                continue
        
        # 按匹配分数排序
        results.sort(key=lambda x: (-x['_score'], x['CODE']))
        
        # 移除评分字段并限制数量
        return [{k: v for k, v in item.items() if k != '_score'} for item in results[:limit]]
    
    def get_status(self) -> Dict[str, Any]:
        """获取缓存状态"""
        return {
            "count": len(self.fund_list),
            "last_update": self.last_update,
            "has_cache": len(self.fund_list) > 0
        }


# 单例模式
_fund_list_cache = None

def get_fund_list_cache() -> FundListCache:
    """获取基金列表缓存单例"""
    global _fund_list_cache
    if _fund_list_cache is None:
        _fund_list_cache = FundListCache()
    return _fund_list_cache


if __name__ == "__main__":
    # 测试代码
    cache = get_fund_list_cache()
    
    # 更新缓存
    result = cache.update_from_api()
    print(f"更新结果: {result}")
    
    # 测试搜索
    print("\n搜索 '华夏':")
    for fund in cache.search("华夏", limit=5):
        print(f"  {fund['CODE']} - {fund['NAME']} ({fund['TYPE']})")
    
    print("\n搜索 '000001':")
    for fund in cache.search("000001", limit=5):
        print(f"  {fund['CODE']} - {fund['NAME']} ({fund['TYPE']})")
