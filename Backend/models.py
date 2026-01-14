from sqlalchemy import Column, String, Float, Text, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class FundBasicInfo(Base):
    __tablename__ = 'fund_basic_info'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fund_code = Column(String(6), unique=True, nullable=False)
    fund_name = Column(String(100), nullable=False)
    fund_name_en = Column(String(200))
    fund_type = Column(String(50))
    created_time = Column(DateTime, default=datetime.now)
    updated_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class FundDetail(Base):
    __tablename__ = 'fund_detail'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fund_code = Column(String(6), nullable=False)
    data_json = Column(Text)  # 存储完整的基金数据
    net_worth_trend = Column(Text)  # 单位净值走势
    basic_info = Column(Text)  # 基础信息
    created_time = Column(DateTime, default=datetime.now)