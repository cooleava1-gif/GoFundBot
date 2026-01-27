# -*- coding: utf-8 -*-
"""
MyBot 配置管理模块
"""

import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv, dotenv_values
from dataclasses import dataclass, field

@dataclass
class Config:
    """系统配置类 - 单例模式"""
    
    # === AI 分析配置 ===
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-3-flash-preview"
    gemini_model_fallback: str = "gemini-2.5-flash"
    
    # OpenAI 兼容 API
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    
    # Gemini API 请求配置
    gemini_request_delay: float = 2.0
    gemini_max_retries: int = 3
    gemini_retry_delay: float = 2.0
    
    # === 搜索引擎配置 ===
    tavily_api_keys: List[str] = field(default_factory=list)
    serpapi_keys: List[str] = field(default_factory=list)
    bocha_api_keys: List[str] = field(default_factory=list)
    
    # 单例实例存储
    _instance: Optional['Config'] = None
    
    @classmethod
    def get_instance(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = cls._load_from_env()
        return cls._instance
    
    @classmethod
    def _load_from_env(cls) -> 'Config':
        # 加载项目根目录下的 .env 文件 (假设 .env 在 MyBot/Backend/ 或 MyBot/ 下)
        # 这里尝试从当前目录加载
        env_path = Path(__file__).parent / '.env'
        if not env_path.exists():
            # 尝试上级目录
            env_path = Path(__file__).parent.parent / '.env'
            
        load_dotenv(dotenv_path=env_path)
        
        # 解析搜索引擎 API Keys
        # 支持 TAVILY_API_KEYS (逗号分隔) 或 TAVILY_API_KEY (单个)
        tavily_keys_str = os.getenv('TAVILY_API_KEYS', '')
        if not tavily_keys_str:
            tavily_keys_str = os.getenv('TAVILY_API_KEY', '')
        tavily_api_keys = [k.strip() for k in tavily_keys_str.split(',') if k.strip()]
        
        # 支持 SERPAPI_API_KEYS 或 SERPAPI_API_KEY
        serpapi_keys_str = os.getenv('SERPAPI_API_KEYS', '')
        if not serpapi_keys_str:
            serpapi_keys_str = os.getenv('SERPAPI_API_KEY', '')
        serpapi_keys = [k.strip() for k in serpapi_keys_str.split(',') if k.strip()]
        
        # 支持 BOCHA_API_KEYS 或 BOCHA_API_KEY
        bocha_keys_str = os.getenv('BOCHA_API_KEYS', '')
        if not bocha_keys_str:
            bocha_keys_str = os.getenv('BOCHA_API_KEY', '')
        bocha_api_keys = [k.strip() for k in bocha_keys_str.split(',') if k.strip()]
        
        return cls(
            gemini_api_key=os.getenv('GEMINI_API_KEY'),
            gemini_model=os.getenv('GEMINI_MODEL', 'gemini-3-flash-preview'),
            gemini_model_fallback=os.getenv('GEMINI_MODEL_FALLBACK', 'gemini-2.5-flash'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            openai_base_url=os.getenv('OPENAI_BASE_URL'),
            openai_model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            gemini_request_delay=float(os.getenv('GEMINI_REQUEST_DELAY', '2.0')),
            gemini_max_retries=int(os.getenv('GEMINI_MAX_RETRIES', '3')),
            gemini_retry_delay=float(os.getenv('GEMINI_RETRY_DELAY', '2.0')),
            tavily_api_keys=tavily_api_keys,
            serpapi_keys=serpapi_keys,
            bocha_api_keys=bocha_api_keys,
        )

def get_config() -> Config:
    return Config.get_instance()
