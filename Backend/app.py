from flask import Flask, request, jsonify
from flask_cors import CORS
from database import init_db, get_db
from models import FundBasicInfo, FundTrend, FundEstimate, FundPortfolio, FundExtraData, FundWatchlist, FundWatchlistGroup
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

def _json_dumps(data):
    return json.dumps(data, ensure_ascii=False) if data is not None else None

def _json_loads(data, default):
    if not data:
        return default
    try:
        return json.loads(data)
    except Exception:
        return default

def _build_cached_response(db: Session, fund_code: str):
    basic = db.query(FundBasicInfo).filter(FundBasicInfo.fund_code == fund_code).first()
    trend = db.query(FundTrend).filter(FundTrend.fund_code == fund_code).first()
    estimate = db.query(FundEstimate).filter(FundEstimate.fund_code == fund_code).first()
    portfolio = db.query(FundPortfolio).filter(FundPortfolio.fund_code == fund_code).first()
    extra = db.query(FundExtraData).filter(FundExtraData.fund_code == fund_code).first()

    if not any([basic, trend, estimate, portfolio, extra]):
        return None

    data = {}

    if basic:
        data['basic_info'] = _json_loads(basic.basic_json, {})
        data['performance'] = _json_loads(basic.performance_json, {})

    if trend:
        data['net_worth_trend'] = _json_loads(trend.net_worth_trend_json, [])
        data['accumulated_net_worth'] = _json_loads(trend.accumulated_net_worth_json, [])
        data['position_trend'] = _json_loads(trend.position_trend_json, [])
        data['total_return_trend'] = _json_loads(trend.total_return_trend_json, [])
        data['ranking_trend'] = _json_loads(trend.ranking_trend_json, [])
        data['ranking_percentage'] = _json_loads(trend.ranking_percentage_json, [])
        data['scale_fluctuation'] = _json_loads(trend.scale_fluctuation_json, {})

    if estimate:
        data['realtime_estimate'] = {
            'name': estimate.name,
            'fund_code': fund_code,
            'net_worth': estimate.net_worth,
            'net_worth_date': estimate.net_worth_date,
            'estimate_value': estimate.estimate_value,
            'estimate_change': estimate.estimate_change,
            'estimate_time': estimate.estimate_time
        }

    if portfolio:
        data['portfolio'] = {
            'stock_codes': _json_loads(portfolio.stock_codes_json, []),
            'bond_codes': _json_loads(portfolio.bond_codes_json, []),
            'stock_codes_new': _json_loads(portfolio.stock_codes_new_json, []),
            'bond_codes_new': _json_loads(portfolio.bond_codes_new_json, [])
        }

    if extra:
        data['holder_structure'] = _json_loads(extra.holder_structure_json, {})
        data['asset_allocation'] = _json_loads(extra.asset_allocation_json, {})
        data['performance_evaluation'] = _json_loads(extra.performance_evaluation_json, {})
        data['fund_managers'] = _json_loads(extra.fund_managers_json, [])
        data['subscription_redemption'] = _json_loads(extra.subscription_redemption_json, {})
        data['same_type_funds'] = _json_loads(extra.same_type_funds_json, [])

    return data

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
        basic_info = fund_data.get('basic_info', {})
        performance = fund_data.get('performance', {})
        trend = {
            'net_worth_trend': fund_data.get('net_worth_trend', []),
            'accumulated_net_worth': fund_data.get('accumulated_net_worth', []),
            'position_trend': fund_data.get('position_trend', []),
            'total_return_trend': fund_data.get('total_return_trend', []),
            'ranking_trend': fund_data.get('ranking_trend', []),
            'ranking_percentage': fund_data.get('ranking_percentage', []),
            'scale_fluctuation': fund_data.get('scale_fluctuation', {})
        }
        estimate = fund_data.get('realtime_estimate', {})
        portfolio = fund_data.get('portfolio', {})
        extra = {
            'holder_structure': fund_data.get('holder_structure', {}),
            'asset_allocation': fund_data.get('asset_allocation', {}),
            'performance_evaluation': fund_data.get('performance_evaluation', {}),
            'fund_managers': fund_data.get('fund_managers', []),
            'subscription_redemption': fund_data.get('subscription_redemption', {}),
            'same_type_funds': fund_data.get('same_type_funds', [])
        }

        basic_record = db.query(FundBasicInfo).filter(FundBasicInfo.fund_code == fund_code).first()
        if basic_record:
            basic_record.fund_name = basic_info.get('fund_name')
            basic_record.fund_type = basic_info.get('fund_type')
            basic_record.original_rate = basic_info.get('original_rate')
            basic_record.current_rate = basic_info.get('current_rate')
            basic_record.min_subscription_amount = basic_info.get('min_subscription_amount')
            basic_record.is_hb = basic_info.get('is_hb')
            basic_record.basic_json = _json_dumps(basic_info)
            basic_record.performance_json = _json_dumps(performance)
        else:
            basic_record = FundBasicInfo(
                fund_code=fund_code,
                fund_name=basic_info.get('fund_name') or fund_code,
                fund_type=basic_info.get('fund_type'),
                original_rate=basic_info.get('original_rate'),
                current_rate=basic_info.get('current_rate'),
                min_subscription_amount=basic_info.get('min_subscription_amount'),
                is_hb=basic_info.get('is_hb'),
                basic_json=_json_dumps(basic_info),
                performance_json=_json_dumps(performance)
            )
            db.add(basic_record)

        trend_record = db.query(FundTrend).filter(FundTrend.fund_code == fund_code).first()
        if trend_record:
            trend_record.net_worth_trend_json = _json_dumps(trend['net_worth_trend'])
            trend_record.accumulated_net_worth_json = _json_dumps(trend['accumulated_net_worth'])
            trend_record.position_trend_json = _json_dumps(trend['position_trend'])
            trend_record.total_return_trend_json = _json_dumps(trend['total_return_trend'])
            trend_record.ranking_trend_json = _json_dumps(trend['ranking_trend'])
            trend_record.ranking_percentage_json = _json_dumps(trend['ranking_percentage'])
            trend_record.scale_fluctuation_json = _json_dumps(trend['scale_fluctuation'])
        else:
            trend_record = FundTrend(
                fund_code=fund_code,
                net_worth_trend_json=_json_dumps(trend['net_worth_trend']),
                accumulated_net_worth_json=_json_dumps(trend['accumulated_net_worth']),
                position_trend_json=_json_dumps(trend['position_trend']),
                total_return_trend_json=_json_dumps(trend['total_return_trend']),
                ranking_trend_json=_json_dumps(trend['ranking_trend']),
                ranking_percentage_json=_json_dumps(trend['ranking_percentage']),
                scale_fluctuation_json=_json_dumps(trend['scale_fluctuation'])
            )
            db.add(trend_record)

        estimate_record = db.query(FundEstimate).filter(FundEstimate.fund_code == fund_code).first()
        if estimate_record:
            estimate_record.name = estimate.get('name')
            estimate_record.net_worth = estimate.get('net_worth')
            estimate_record.net_worth_date = estimate.get('net_worth_date')
            estimate_record.estimate_value = estimate.get('estimate_value')
            estimate_record.estimate_change = estimate.get('estimate_change')
            estimate_record.estimate_time = estimate.get('estimate_time')
        else:
            estimate_record = FundEstimate(
                fund_code=fund_code,
                name=estimate.get('name'),
                net_worth=estimate.get('net_worth'),
                net_worth_date=estimate.get('net_worth_date'),
                estimate_value=estimate.get('estimate_value'),
                estimate_change=estimate.get('estimate_change'),
                estimate_time=estimate.get('estimate_time')
            )
            db.add(estimate_record)

        portfolio_record = db.query(FundPortfolio).filter(FundPortfolio.fund_code == fund_code).first()
        if portfolio_record:
            portfolio_record.stock_codes_json = _json_dumps(portfolio.get('stock_codes', []))
            portfolio_record.bond_codes_json = _json_dumps(portfolio.get('bond_codes', []))
            portfolio_record.stock_codes_new_json = _json_dumps(portfolio.get('stock_codes_new', []))
            portfolio_record.bond_codes_new_json = _json_dumps(portfolio.get('bond_codes_new', []))
        else:
            portfolio_record = FundPortfolio(
                fund_code=fund_code,
                stock_codes_json=_json_dumps(portfolio.get('stock_codes', [])),
                bond_codes_json=_json_dumps(portfolio.get('bond_codes', [])),
                stock_codes_new_json=_json_dumps(portfolio.get('stock_codes_new', [])),
                bond_codes_new_json=_json_dumps(portfolio.get('bond_codes_new', []))
            )
            db.add(portfolio_record)

        extra_record = db.query(FundExtraData).filter(FundExtraData.fund_code == fund_code).first()
        if extra_record:
            extra_record.holder_structure_json = _json_dumps(extra['holder_structure'])
            extra_record.asset_allocation_json = _json_dumps(extra['asset_allocation'])
            extra_record.performance_evaluation_json = _json_dumps(extra['performance_evaluation'])
            extra_record.fund_managers_json = _json_dumps(extra['fund_managers'])
            extra_record.subscription_redemption_json = _json_dumps(extra['subscription_redemption'])
            extra_record.same_type_funds_json = _json_dumps(extra['same_type_funds'])
        else:
            extra_record = FundExtraData(
                fund_code=fund_code,
                holder_structure_json=_json_dumps(extra['holder_structure']),
                asset_allocation_json=_json_dumps(extra['asset_allocation']),
                performance_evaluation_json=_json_dumps(extra['performance_evaluation']),
                fund_managers_json=_json_dumps(extra['fund_managers']),
                subscription_redemption_json=_json_dumps(extra['subscription_redemption']),
                same_type_funds_json=_json_dumps(extra['same_type_funds'])
            )
            db.add(extra_record)

        try:
            db.commit()
        except Exception as e:
            print(f"Error saving to database: {e}")
            db.rollback()

        return jsonify(fund_data)
    
    # 如果API获取失败，尝试从数据库获取缓存数据作为兜底
    cached_data = _build_cached_response(db, fund_code)
    if cached_data:
        return jsonify(cached_data)

    return jsonify({"error": "Fund not found"}), 404

@app.route('/api/fund/<fund_code>/basic', methods=['GET'])
def get_fund_basic(fund_code):
    """获取基金基础信息 实时调用API"""
    if not fund_code:
        return jsonify({"error": "Fund code is required"}), 400
    fund_data = fund_api.get_fund_data(fund_code)
    if fund_data and fund_data.get('basic_info'):
        result = {
            **fund_data.get('basic_info', {}),
            **fund_data.get('performance', {})
        }
        return jsonify(result)

    db = next(get_db())
    basic = db.query(FundBasicInfo).filter(FundBasicInfo.fund_code == fund_code).first()
    if basic:
        basic_info = _json_loads(basic.basic_json, {})
        performance = _json_loads(basic.performance_json, {})
        return jsonify({**basic_info, **performance})

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

    db = next(get_db())
    trend = db.query(FundTrend).filter(FundTrend.fund_code == fund_code).first()
    if trend:
        return jsonify({
            "net_worth_trend": _json_loads(trend.net_worth_trend_json, []),
            "accumulated_net_worth": _json_loads(trend.accumulated_net_worth_json, [])
        })

    return jsonify({"error": "Fund trend data not found"}), 404


# ==================== 自选基金 API ====================

@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    """获取自选基金列表（按分组和排序顺序）"""
    db = next(get_db())
    
    # 获取所有分组
    groups = db.query(FundWatchlistGroup).order_by(FundWatchlistGroup.sort_order).all()
    
    # 获取所有基金
    watchlist = db.query(FundWatchlist).order_by(FundWatchlist.sort_order).all()
    
    # 构建分组数据
    groups_data = []
    for group in groups:
        groups_data.append({
            'id': group.id,
            'name': group.name,
            'sort_order': group.sort_order
        })
    
    # 构建基金数据
    funds_data = []
    for item in watchlist:
        estimate = db.query(FundEstimate).filter(FundEstimate.fund_code == item.fund_code).first()
        
        fund_data = {
            'fund_code': item.fund_code,
            'fund_name': item.fund_name,
            'fund_type': item.fund_type,
            'group_id': item.group_id,
            'sort_order': item.sort_order,
            'created_time': item.created_time.isoformat() if item.created_time else None,
            'net_worth': estimate.net_worth if estimate else None,
            'net_worth_date': estimate.net_worth_date if estimate else None,
            'estimate_value': estimate.estimate_value if estimate else None,
            'estimate_change': estimate.estimate_change if estimate else None,
            'estimate_time': estimate.estimate_time if estimate else None
        }
        funds_data.append(fund_data)
    
    return jsonify({
        'groups': groups_data,
        'data': funds_data
    })


@app.route('/api/watchlist/<fund_code>', methods=['GET'])
def check_watchlist(fund_code):
    """检查基金是否在自选列表中"""
    db = next(get_db())
    exists = db.query(FundWatchlist).filter(FundWatchlist.fund_code == fund_code).first() is not None
    return jsonify({'in_watchlist': exists})


@app.route('/api/watchlist', methods=['POST'])
def add_to_watchlist():
    """添加基金到自选列表"""
    data = request.get_json()
    fund_code = data.get('fund_code')
    fund_name = data.get('fund_name', '')
    fund_type = data.get('fund_type', '')
    group_id = data.get('group_id')  # 可选的分组ID
    
    if not fund_code:
        return jsonify({'error': 'Fund code is required'}), 400
    
    db = next(get_db())
    
    # 检查是否已存在
    existing = db.query(FundWatchlist).filter(FundWatchlist.fund_code == fund_code).first()
    if existing:
        return jsonify({'error': 'Fund already in watchlist', 'fund_code': fund_code}), 409
    
    # 获取当前最大排序值（在同一分组内）
    query = db.query(FundWatchlist)
    if group_id:
        query = query.filter(FundWatchlist.group_id == group_id)
    max_order = query.order_by(FundWatchlist.sort_order.desc()).first()
    new_order = (max_order.sort_order + 1) if max_order else 0
    
    # 创建新记录
    new_item = FundWatchlist(
        fund_code=fund_code,
        fund_name=fund_name,
        fund_type=fund_type,
        group_id=group_id,
        sort_order=new_order
    )
    
    try:
        db.add(new_item)
        db.commit()
        return jsonify({
            'message': 'Fund added to watchlist',
            'fund_code': fund_code,
            'sort_order': new_order
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/watchlist/<fund_code>', methods=['DELETE'])
def remove_from_watchlist(fund_code):
    """从自选列表移除基金"""
    db = next(get_db())
    
    item = db.query(FundWatchlist).filter(FundWatchlist.fund_code == fund_code).first()
    if not item:
        return jsonify({'error': 'Fund not in watchlist'}), 404
    
    try:
        db.delete(item)
        db.commit()
        return jsonify({'message': 'Fund removed from watchlist', 'fund_code': fund_code})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/watchlist/batch-delete', methods=['POST'])
def batch_delete_from_watchlist():
    """批量删除自选基金"""
    data = request.get_json()
    fund_codes = data.get('fund_codes', [])
    
    if not fund_codes:
        return jsonify({'error': 'Fund codes are required'}), 400
    
    db = next(get_db())
    
    try:
        deleted_count = db.query(FundWatchlist).filter(
            FundWatchlist.fund_code.in_(fund_codes)
        ).delete(synchronize_session=False)
        db.commit()
        return jsonify({
            'message': f'Deleted {deleted_count} funds from watchlist',
            'deleted_count': deleted_count
        })
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/watchlist/reorder', methods=['PUT'])
def reorder_watchlist():
    """
    更新自选基金排序
    请求体格式: { "order": ["000001", "000002", "000003"], "group_id": 1 }
    数组顺序即为排序顺序，索引值作为 sort_order
    group_id 可选，用于同时更新基金的分组
    """
    data = request.get_json()
    order = data.get('order', [])
    group_id = data.get('group_id')  # 可选，移动到某个分组
    
    if not order:
        return jsonify({'error': 'Order array is required'}), 400
    
    db = next(get_db())
    
    try:
        for index, fund_code in enumerate(order):
            update_data = {'sort_order': index}
            if group_id is not None:
                update_data['group_id'] = group_id if group_id > 0 else None
            db.query(FundWatchlist).filter(
                FundWatchlist.fund_code == fund_code
            ).update(update_data)
        db.commit()
        return jsonify({'message': 'Watchlist reordered successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== 分组管理 API ====================

@app.route('/api/watchlist/groups', methods=['GET'])
def get_groups():
    """获取所有分组"""
    db = next(get_db())
    groups = db.query(FundWatchlistGroup).order_by(FundWatchlistGroup.sort_order).all()
    
    result = [{
        'id': g.id,
        'name': g.name,
        'sort_order': g.sort_order
    } for g in groups]
    
    return jsonify({'data': result})


@app.route('/api/watchlist/groups', methods=['POST'])
def create_group():
    """创建新分组"""
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'error': 'Group name is required'}), 400
    
    db = next(get_db())
    
    # 获取最大排序值
    max_order = db.query(FundWatchlistGroup).order_by(FundWatchlistGroup.sort_order.desc()).first()
    new_order = (max_order.sort_order + 1) if max_order else 0
    
    new_group = FundWatchlistGroup(name=name, sort_order=new_order)
    
    try:
        db.add(new_group)
        db.commit()
        return jsonify({
            'message': 'Group created',
            'group': {
                'id': new_group.id,
                'name': new_group.name,
                'sort_order': new_group.sort_order
            }
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/watchlist/groups/<int:group_id>', methods=['PUT'])
def update_group(group_id):
    """更新分组（重命名）"""
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'error': 'Group name is required'}), 400
    
    db = next(get_db())
    group = db.query(FundWatchlistGroup).filter(FundWatchlistGroup.id == group_id).first()
    
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    
    try:
        group.name = name
        db.commit()
        return jsonify({'message': 'Group updated', 'group': {'id': group.id, 'name': group.name}})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/watchlist/groups/<int:group_id>', methods=['DELETE'])
def delete_group(group_id):
    """删除分组（分组内的基金会变为未分组）"""
    db = next(get_db())
    group = db.query(FundWatchlistGroup).filter(FundWatchlistGroup.id == group_id).first()
    
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    
    try:
        # 将该分组的基金设为未分组
        db.query(FundWatchlist).filter(FundWatchlist.group_id == group_id).update({'group_id': None})
        db.delete(group)
        db.commit()
        return jsonify({'message': 'Group deleted'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/watchlist/groups/reorder', methods=['PUT'])
def reorder_groups():
    """更新分组排序"""
    data = request.get_json()
    order = data.get('order', [])  # [group_id1, group_id2, ...]
    
    if not order:
        return jsonify({'error': 'Order array is required'}), 400
    
    db = next(get_db())
    
    try:
        for index, group_id in enumerate(order):
            db.query(FundWatchlistGroup).filter(
                FundWatchlistGroup.id == group_id
            ).update({'sort_order': index})
        db.commit()
        return jsonify({'message': 'Groups reordered successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/watchlist/move', methods=['PUT'])
def move_fund_to_group():
    """移动基金到指定分组"""
    data = request.get_json()
    fund_code = data.get('fund_code')
    group_id = data.get('group_id')  # None 或 0 表示移到未分组
    
    if not fund_code:
        return jsonify({'error': 'Fund code is required'}), 400
    
    db = next(get_db())
    fund = db.query(FundWatchlist).filter(FundWatchlist.fund_code == fund_code).first()
    
    if not fund:
        return jsonify({'error': 'Fund not in watchlist'}), 404
    
    try:
        fund.group_id = group_id if group_id and group_id > 0 else None
        db.commit()
        return jsonify({'message': 'Fund moved successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)