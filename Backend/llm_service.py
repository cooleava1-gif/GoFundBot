# -*- coding: utf-8 -*-
"""
MyBot AI 分析服务模块
"""

import json
import logging
import time
import re
import threading
from typing import Dict, Any, Optional
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_config
from search_service import get_search_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService:
    SYSTEM_PROMPT = """你是一位专业的公募基金分析师，擅长结合市场实时动态、基金业绩和持仓结构进行深度分析。

请根据提供的【基金数据】和【实时情报】，生成一份结构化的【决策仪表盘】分析报告。

## 输出格式 (JSON)

请严格按照以下 JSON 格式输出，不要输出 Markdown 代码块标记：

{
    "sentiment_score": 0-100整数,
    "operation_advice": "买入/加仓/持有/减仓/卖出/观望",
    "summary": "一句话核心结论（结合了最新情报）",
    "risk_factors": ["风险点1", "风险点2"],
    "highlights": ["亮点1", "亮点2"],
    "news_intel": ["【利空/利好】新闻标题 (来源)"],
    "dashboard": {
        "performance_eval": "业绩评价（优秀/良好/一般/较差）",
        "manager_ability": "基金经理能力评价",
        "position_analysis": "持仓结构分析",
        "market_outlook": "后市展望"
    }
}

## 评分标准
- >80: 强烈看多 (业绩优秀 + 市场风口 + 无重大利空)
- 60-80: 看多 (业绩良好 + 趋势向上)
- 40-60: 震荡/观望
- <40: 看空 (业绩差 + 重大利空)

## 注意事项
1. **实时情报优先**：如果【实时情报】中有重大利空（如重仓股暴雷、基金经理离职），必须在风险提示中强调，并降低评分。
2. **数据支撑**：分析结论必须有数据支撑（如“近1年收益率前10%”）。
3. **客观中立**：不吹不黑，给出理性的操作建议。
"""

    def __init__(self):
        self.config = get_config()
        self._model = None
        self._openai_client = None
        self._init_model()
        # 后台任务状态
        self._generating_market_summary = False
        self._generation_lock = threading.Lock()

    def _init_model(self):
        # 1. 优先使用 OpenAI 兼容 API（国内可直连）
        if self.config.openai_api_key:
            try:
                from openai import OpenAI
                kwargs = {"api_key": self.config.openai_api_key}
                if self.config.openai_base_url:
                    kwargs["base_url"] = self.config.openai_base_url
                self._openai_client = OpenAI(**kwargs)
                logger.info(f"OpenAI initialized (base_url: {self.config.openai_base_url or 'default'})")
                return
            except Exception as e:
                logger.error(f"OpenAI init failed: {e}")

        # 2. 备用：Gemini（需要代理/VPN）
        if self.config.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.config.gemini_api_key)
                self._model = genai.GenerativeModel(
                    model_name=self.config.gemini_model,
                    system_instruction=self.SYSTEM_PROMPT
                )
                logger.info(f"Gemini initialized: {self.config.gemini_model}")
                logger.warning("Gemini requires VPN/proxy in mainland China!")
                return
            except Exception as e:
                logger.error(f"Gemini init failed: {e}")
        
        logger.warning("No AI model initialized")

    def is_available(self) -> bool:
        return self._model is not None or self._openai_client is not None

    def _get_db_session(self):
        """获取数据库会话"""
        from database import SessionLocal
        return SessionLocal()

    def _get_cached_market_summary(self, today_str: str) -> Optional[Dict[str, Any]]:
        """从数据库获取缓存的市场摘要（含进度信息）"""
        from models import DailyMarketSummary
        db = self._get_db_session()
        try:
            record = db.query(DailyMarketSummary).filter(
                DailyMarketSummary.date == today_str
            ).first()
            
            if not record:
                return None
            
            # 返回完整状态信息，供调用方判断
            return {
                'status': record.status,
                'current_step': record.current_step or 0,
                'step_message': record.step_message or '',
                'data': self._record_to_dict(record) if record.status == 'completed' else None,
                'error': record.error_message if record.status == 'error' else None
            }
        finally:
            db.close()

    def _record_to_dict(self, record) -> Dict[str, Any]:
        """将数据库记录转换为字典"""
        return {
            'market_sentiment': record.market_sentiment or '未知',
            'summary': record.summary or '',
            'indices': json.loads(record.indices_json) if record.indices_json else [],
            'hot_sectors': json.loads(record.hot_sectors_json) if record.hot_sectors_json else [],
            'key_news': json.loads(record.key_news_json) if record.key_news_json else [],
            'outlook': record.outlook or ''
        }

    def _update_progress(self, today_str: str, step: int, message: str, status: str = 'generating'):
        """更新生成进度"""
        from models import DailyMarketSummary
        db = self._get_db_session()
        try:
            record = db.query(DailyMarketSummary).filter(
                DailyMarketSummary.date == today_str
            ).first()
            
            if not record:
                record = DailyMarketSummary(date=today_str)
                db.add(record)
            
            record.status = status
            record.current_step = step
            record.step_message = message
            record.updated_time = datetime.now()
            db.commit()
            logger.info(f"[MarketSummary] Progress: step={step}, message={message}")
        except Exception as e:
            db.rollback()
            logger.error(f"[MarketSummary] Failed to update progress: {e}")
        finally:
            db.close()

    def _save_market_summary(self, today_str: str, data: Dict[str, Any], status: str = 'completed', error: str = None):
        """保存市场摘要到数据库"""
        from models import DailyMarketSummary
        db = self._get_db_session()
        try:
            record = db.query(DailyMarketSummary).filter(
                DailyMarketSummary.date == today_str
            ).first()
            
            if not record:
                record = DailyMarketSummary(date=today_str)
                db.add(record)
            
            record.status = status
            record.updated_time = datetime.now()
            
            if status == 'completed' and data:
                record.current_step = 3
                record.step_message = '分析完成'
                record.market_sentiment = data.get('market_sentiment', '')
                record.summary = data.get('summary', '')
                record.indices_json = json.dumps(data.get('indices', []), ensure_ascii=False)
                record.hot_sectors_json = json.dumps(data.get('hot_sectors', []), ensure_ascii=False)
                record.key_news_json = json.dumps(data.get('key_news', []), ensure_ascii=False)
                record.outlook = data.get('outlook', '')
                record.error_message = None
            elif status == 'error':
                record.error_message = error
                record.step_message = f'生成失败: {error[:100] if error else "未知错误"}'
            
            db.commit()
            logger.info(f"[MarketSummary] Saved to DB: date={today_str}, status={status}")
        except Exception as e:
            db.rollback()
            logger.error(f"[MarketSummary] Failed to save to DB: {e}")
        finally:
            db.close()

    def _do_generate_market_summary(self, today_key: str, today_str: str) -> Dict[str, Any]:
        """实际执行市场摘要生成（带步骤追踪与超时控制）"""
        
        # === 步骤 1: 搜索新闻 ===
        self._update_progress(today_key, 1, '正在访问全球财经数据库...')
        
        search_service = get_search_service()
        query = f"{today_str} A股 行情复盘 热点"
        
        news_context = ""
        
        if search_service.is_available:
            try:
                # 限制搜索结果数量，加快速度
                search_resp = search_service.search(query, max_results=5)
                if search_resp.success and search_resp.results:
                    news_context = search_resp.to_context(max_results=5)
                    self._update_progress(today_key, 1, f'发现 {len(search_resp.results)} 条核心行情条目')
                else:
                    self._update_progress(today_key, 1, '实时行情较少，正在启动 AI 推理模式...')
            except Exception as e:
                logger.warning(f"[MarketSummary] Search failed: {e}")
                self._update_progress(today_key, 1, '外部搜索受阻，正在利用 AI 知识库...')
        
        # === 步骤 2: AI 分析 ===
        self._update_progress(today_key, 2, '正在根据市场动态构建分析模型...')
        
        system_prompt = "你是一位资深的金融市场分析师，擅长提炼行情，请严格输出 JSON 格式。"
        prompt = f"""
请根据以下【今日财经新闻】，生成一份【{today_str} 市场行情日报】。

【今日财经新闻】
{news_context if news_context else "（请利用你的知识库分析当日可能的 A 股走势，假定日期为 " + today_str + "）"}

请严格按照以下 JSON 格式输出，不要输出 Markdown 代码块标记：
{{
    "market_sentiment": "市场情绪（如：积极/恐慌/观望）",
    "summary": "市场行情一句话总结",
    "indices": [
        {{"name": "上证指数", "change": "跌幅/点位 (如有)", "analysis": "简评"}},
        {{"name": "创业板指", "change": "跌幅/点位 (如有)", "analysis": "简评"}}
    ],
    "hot_sectors": ["热门板块1", "热门板块2"],
    "key_news": ["关键新闻1", "关键新闻2"],
    "outlook": "后市展望"
}}
"""
        
        try:
            # 此处已在 _call_llm 中设置 60s 超时
            response_text = self._call_llm(prompt, system_prompt=system_prompt)
            self._update_progress(today_key, 2, '分析建模完成，正在解析数据...')
        except Exception as e:
            logger.error(f"[MarketSummary] AI generation failed: {e}")
            raise Exception(f"AI 调用失败: {str(e)}")
        
        fallback = {
            "market_sentiment": "未知",
            "summary": "解析失败",
            "indices": [],
            "hot_sectors": [],
            "key_news": [],
            "outlook": "请重试"
        }
        return self._parse_response(response_text, fallback)


    def _background_generate(self, today_key: str):
        """后台线程生成市场摘要"""
        today_str = datetime.now().strftime("%Y年%m月%d日")
        try:
            logger.info(f"[MarketSummary] Background generation started for {today_key}")
            result = self._do_generate_market_summary(today_key, today_str)
            
            if 'error' in result:
                self._save_market_summary(today_key, None, status='error', error=result['error'])
            else:
                self._save_market_summary(today_key, result, status='completed')
                
        except Exception as e:
            logger.error(f"[MarketSummary] Background generation failed: {e}")
            self._save_market_summary(today_key, None, status='error', error=str(e))
        finally:
            with self._generation_lock:
                self._generating_market_summary = False

    def generate_market_summary(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        生成每日市场行情摘要
        
        返回格式：
        - 完成: {data...}
        - 加载中: {loading: true, current_step: 1, step_message: "...", steps: [...]}
        - 错误: {error: "..."}
        """
        if not self.is_available():
            return {"error": "AI service not available"}
            
        today_key = datetime.now().strftime("%Y-%m-%d")
        
        # 步骤定义（前端展示用）
        steps = [
            {"step": 1, "name": "搜索新闻", "description": "获取今日财经资讯"},
            {"step": 2, "name": "AI 分析", "description": "生成市场分析报告"},
            {"step": 3, "name": "完成", "description": "分析报告已就绪"}
        ]
        
        # 1. 检查数据库缓存
        if not force_refresh:
            cached = self._get_cached_market_summary(today_key)
            if cached:
                if cached['status'] == 'completed':
                    logger.info(f"[MarketSummary] Cache hit for {today_key}")
                    return cached['data']
                elif cached['status'] == 'generating':
                    # 自愈机制：如果生成的更新时间超过 5 分钟，说明可能卡死了，允许重新开始
                    # 注意：get_cached_market_summary 尚未返回 updated_time，我们需要在下面单独处理
                    pass
                elif cached['status'] == 'error':
                    # 如果之前出错了，直接返回错误信息，不再自动重试（除非用户点击刷新）
                    logger.warning(f"[MarketSummary] Returning previous error for {today_key}: {cached['error']}")
                    return {
                        "error": cached['error'] or "今日行情分析生成失败，请点击刷新重试。",
                        "status": "error"
                    }
        
        # 2. 检查更详细的状态（包含更新时间）
        from models import DailyMarketSummary
        db = self._get_db_session()
        try:
            record = db.query(DailyMarketSummary).filter(DailyMarketSummary.date == today_key).first()
            if record and record.status == 'generating' and not force_refresh:
                # 如果状态是生成中，且更新时间在 5 分钟内，则继续等待
                if record.updated_time and (datetime.now() - record.updated_time).total_seconds() < 300:
                    return {
                        "loading": True, 
                        "current_step": record.current_step or 1,
                        "step_message": record.step_message or '正在生成...',
                        "steps": steps
                    }
                else:
                    logger.warning(f"[MarketSummary] Task for {today_key} seems stuck (updated {record.updated_time}), restarting...")
        finally:
            db.close()
        
        # 3. 开始后台生成
        with self._generation_lock:
            if self._generating_market_summary:
                cached = self._get_cached_market_summary(today_key)
                return {
                    "loading": True, 
                    "current_step": cached.get('current_step', 1) if cached else 1,
                    "step_message": cached.get('step_message', '正在生成...') if cached else '正在初始化...',
                    "steps": steps
                }
            self._generating_market_summary = True
        
        # 标记为生成中
        self._update_progress(today_key, 0, '正在初始化...')
        
        # 启动后台线程
        thread = threading.Thread(
            target=self._background_generate,
            args=(today_key,),
            daemon=True
        )
        thread.start()
        
        return {
            "loading": True, 
            "current_step": 0,
            "step_message": "正在初始化...",
            "steps": steps
        }

    def preload_market_summary(self):
        """
        预加载市场摘要（服务启动时调用）
        非阻塞，在后台执行
        """
        if not self.is_available():
            logger.warning("[MarketSummary] Preload skipped: AI service not available")
            return
        
        today_key = datetime.now().strftime("%Y-%m-%d")
        cached = self._get_cached_market_summary(today_key)
        
        if cached and cached['status'] == 'completed':
            logger.info(f"[MarketSummary] Preload skipped: already cached for {today_key}")
            return
        
        logger.info(f"[MarketSummary] Preloading market summary for {today_key}...")
        self.generate_market_summary()

    def analyze_fund(self, fund_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_available():
            return {"error": "AI service not available"}

        # 1. Search for news
        search_service = get_search_service()
        fund_name = fund_data.get('basic_info', {}).get('fund_name', '')
        fund_code = fund_data.get('basic_info', {}).get('fund_code', '')
        
        news_context = ""
        if search_service.is_available:
            logger.info(f"Searching news for {fund_name} ({fund_code})...")
            search_resp = search_service.search_fund_news(fund_name, fund_code)
            if search_resp.success:
                news_context = search_resp.to_context()
        
        # 2. Build Prompt
        prompt = self._build_prompt(fund_data, news_context)
        
        # 3. Call LLM
        try:
            response_text = self._call_llm(prompt)
            fallback = {
                "sentiment_score": 50,
                "operation_advice": "解析失败",
                "summary": "解析失败",
                "risk_factors": [],
                "highlights": [],
                "news_intel": [],
                "dashboard": {}
            }
            return self._parse_response(response_text, fallback)
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {"error": str(e)}

    def _build_prompt(self, data: Dict, news: str) -> str:
        basic = data.get('basic_info', {})
        perf = data.get('performance', {})
        
        # Format Top 10 Stocks
        portfolio = data.get('portfolio', {})
        stocks = portfolio.get('stock_codes', [])
        stock_str = ", ".join([f"{s.get('name')}({s.get('ratio',0)}%)" for s in stocks[:10]])
        
        return f"""
【基金数据】
代码: {basic.get('fund_code')}
名称: {basic.get('fund_name')}
类型: {basic.get('fund_type')}
近1年收益: {perf.get('1_year_return')}%
近3月收益: {perf.get('3_month_return')}%
前十大持仓: {stock_str}

【实时情报】
{news if news else "暂无最新重大消息"}

请开始分析：
"""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _call_llm(self, prompt: str, system_prompt: str = None) -> str:
        sys_msg = system_prompt or self.SYSTEM_PROMPT
        logger.info(f"[LLM] Calling model (System: {sys_msg[:50]}...)")
        start_time = time.time()
        
        try:
            # Use Gemini
            if self._model:
                # 注意：google-generativeai 的 system_instruction 是在初始化时设置的
                # 如果有特定的 system_prompt，我们需要创建一个临时模型或在 prompt 中包含它
                if system_prompt:
                    full_prompt = f"{system_prompt}\n\n{prompt}"
                else:
                    full_prompt = prompt
                
                # 设置 60s 超时
                response = self._model.generate_content(
                    full_prompt,
                    request_options={"timeout": 60}
                )
                duration = time.time() - start_time
                logger.info(f"[LLM] Gemini respond in {duration:.2f}s")
                return response.text
                
            # Use OpenAI
            if self._openai_client:
                resp = self._openai_client.chat.completions.create(
                    model=self.config.openai_model,
                    messages=[
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    timeout=60 # 设置 60s 超时
                )
                duration = time.time() - start_time
                logger.info(f"[LLM] OpenAI respond in {duration:.2f}s")
                return resp.choices[0].message.content
        except Exception as e:
            logger.error(f"[LLM] Call failed: {e}")
            raise # 触发重试
            
        raise Exception("No model available")

    def _parse_response(self, text: str, fallback: Dict = None) -> Dict:
        try:
            # Clean markdown code blocks
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            text = text.strip()
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("JSON parse failed, returning raw text")
            if fallback:
                fallback["raw_response"] = text
                return fallback
            return {
                "sentiment_score": 50,
                "operation_advice": "解析失败",
                "summary": text[:200] + "...",
                "raw_response": text
            }

_llm_service = None
def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
