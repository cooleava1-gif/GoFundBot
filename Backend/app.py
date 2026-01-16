from flask import Flask, request, jsonify
from flask_cors import CORS
from database import init_db, get_db
from models import FundBasicInfo, FundDetail
from fund_api import FundAPI
from fund_list_cache import get_fund_list_cache
from sqlalchemy.orm import Session
import json

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 初始化数据库
init_db()
fund_api = FundAPI()
fund_list_cache = get_fund_list_cache()

@app.route('/')
def hello():
    """测试接口是否可用"""
    return jsonify({"message": "Fund Analysis API is running!"})

@app.route('/api/fund/search', methods=['GET'])
def search_funds():
    """根据关键词搜索基金列表（使用本地缓存）"""
    keyword = request.args.get('q', '')
    if not keyword:
        return jsonify({"error": "Keyword is required"}), 400
    
    # 使用本地缓存搜索
    funds = fund_list_cache.search(keyword, limit=20)
    return jsonify({"data": funds})

@app.route('/api/fund/search/status', methods=['GET'])
def get_search_status():
    """获取搜索数据库状态"""
    status = fund_list_cache.get_status()
    return jsonify(status)

@app.route('/api/fund/search/update', methods=['POST'])
def update_search_database():
    """更新本地基金搜索数据库"""
    result = fund_list_cache.update_from_api()
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@app.route('/api/fund/<fund_code>', methods=['GET'])
def get_fund_detail(fund_code):
    """获取基金详细信息"""
    if not fund_code:
        return jsonify({"error": "Fund code is required"}), 400    
    db = next(get_db()) # 获取数据库会话
    
    # 使用新的 get_fund_data 方法获取清洗后的完整数据
    fund_data = fund_api.get_fund_data(fund_code)
    
    if fund_data:
        # 检查数据库是否存在记录
        cached_fund = db.query(FundDetail).filter(FundDetail.fund_code == fund_code).first()
        # 更新或新增记录
        if cached_fund:
            cached_fund.data_json = json.dumps(fund_data, ensure_ascii=False)
            cached_fund.net_worth_trend = json.dumps(fund_data.get('net_worth_trend', []), ensure_ascii=False)
            cached_fund.basic_info = json.dumps(fund_data.get('basic_info', {}), ensure_ascii=False)
        else:
            fund_detail = FundDetail(
                fund_code=fund_code,
                data_json=json.dumps(fund_data, ensure_ascii=False),
                net_worth_trend=json.dumps(fund_data.get('net_worth_trend', []), ensure_ascii=False),
                basic_info=json.dumps(fund_data.get('basic_info', {}), ensure_ascii=False)
            )
            db.add(fund_detail)        
        try:
            db.commit() # 提交事务
        except Exception as e:
            print(f"Error saving to database: {e}")
            db.rollback()
        
        return jsonify(fund_data)
    
    # 如果API获取失败，尝试从数据库获取缓存数据作为兜底
    cached_fund = db.query(FundDetail).filter(FundDetail.fund_code == fund_code).first()
    if cached_fund:
        try:
            data = json.loads(cached_fund.data_json)
            return jsonify(data)
        except:
            pass

    return jsonify({"error": "Fund not found"}), 404

@app.route('/api/fund/<fund_code>/basic', methods=['GET'])
def get_fund_basic(fund_code):
    """获取基金基础信息 实时调用API"""
    if not fund_code:
        return jsonify({"error": "Fund code is required"}), 400
    fund_data = fund_api.get_fund_data(fund_code)
    if fund_data and fund_data.get('basic_info'):
        # 合并 basic_info 和 performance 数据
        result = {
            **fund_data.get('basic_info', {}),
            **fund_data.get('performance', {})
        }
        return jsonify(result)
    else:
        return jsonify({"error": "Fund basic info not found"}), 404

@app.route('/api/fund/<fund_code>/trend', methods=['GET'])
def get_fund_trend(fund_code):
    """获取基金走势数据 实时调用API"""
    if not fund_code:
        return jsonify({"error": "Fund code is required"}), 400
    
    fund_data = fund_api.get_fund_data(fund_code)
    if fund_data and 'net_worth_trend' in fund_data:
        return jsonify({
            "net_worth_trend": fund_data['net_worth_trend'],
            "accumulated_net_worth": fund_data.get('accumulated_net_worth', [])
        })
    else:
        return jsonify({"error": "Fund trend data not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)