# -*- coding: UTF-8 -*-
"""
Fund-Master API 路由模块
提供市场数据相关的 REST API
"""

from flask import Blueprint, jsonify, request
from fund_master_service import get_fund_master_service

# 创建 Blueprint
fund_master_bp = Blueprint('fund_master', __name__, url_prefix='/api/market')


@fund_master_bp.route('/overview', methods=['GET'])
def get_market_overview():
    """
    获取市场概览（汇总所有关键数据）
    GET /api/market/overview
    """
    service = get_fund_master_service()
    return jsonify(service.get_market_overview())


@fund_master_bp.route('/news', methods=['GET'])
def get_flash_news():
    """
    获取7x24快讯
    GET /api/market/news?count=20
    """
    count = request.args.get('count', 20, type=int)
    service = get_fund_master_service()
    return jsonify(service.get_flash_news(count=count))


@fund_master_bp.route('/sectors', methods=['GET'])
def get_sector_rank():
    """
    获取行业板块排行
    GET /api/market/sectors?limit=50
    """
    limit = request.args.get('limit', 50, type=int)
    service = get_fund_master_service()
    return jsonify(service.get_sector_rank(limit=limit))


@fund_master_bp.route('/index', methods=['GET'])
def get_market_index():
    """
    获取市场指数汇总
    GET /api/market/index
    """
    service = get_fund_master_service()
    return jsonify(service.get_market_index())


@fund_master_bp.route('/gold/realtime', methods=['GET'])
def get_gold_realtime():
    """
    获取实时贵金属价格
    GET /api/market/gold/realtime
    """
    service = get_fund_master_service()
    return jsonify(service.get_gold_realtime())


@fund_master_bp.route('/gold/history', methods=['GET'])
def get_gold_history():
    """
    获取黄金历史价格
    GET /api/market/gold/history?days=10
    """
    days = request.args.get('days', 10, type=int)
    service = get_fund_master_service()
    return jsonify(service.get_gold_history(days=days))


@fund_master_bp.route('/volume', methods=['GET'])
def get_a_volume_7days():
    """
    获取近7日A股成交量
    GET /api/market/volume
    """
    service = get_fund_master_service()
    return jsonify(service.get_a_volume_7days())


@fund_master_bp.route('/indices/intraday', methods=['GET'])
def get_indices_intraday():
    """
    获取多指数分时数据（上证、深证、沪深300）
    GET /api/market/indices/intraday
    """
    service = get_fund_master_service()
    return jsonify(service.get_indices_intraday())


@fund_master_bp.route('/sse', methods=['GET'])
def get_sse_30min():
    """
    获取近30分钟上证指数
    GET /api/market/sse
    """
    service = get_fund_master_service()
    return jsonify(service.get_sse_30min())
