from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from pathlib import Path

# 获取当前文件所在目录（Backend/）
BACKEND_DIR = Path(__file__).parent.resolve()
# 项目根目录 = BACKEND_DIR 的父目录
PROJECT_ROOT = BACKEND_DIR.parent
# 数据库路径：PROJECT_ROOT / Data / funds.db
DATABASE_PATH = PROJECT_ROOT / "Data" / "funds.db"

# 构造 SQLite URL（注意：Windows 和 Linux/macOS 都兼容）
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # 确保 Data 目录存在
    (PROJECT_ROOT / "Data").mkdir(exist_ok=True)
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()