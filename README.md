# GoFundBot

GoFundBot 是一个基于 Python (Flask) 和 Vue 3 构建的基金分析与可视化工具。它通过获取天天基金网的公开数据，为用户提供便捷的基金搜索、详细信息查询、业绩评估及多维度的图表分析功能。

## 🚀 功能特性

*   **基金搜索**：支持通过关键词快速搜索基金（基于本地缓存优化），快速定位目标基金。
*   **基本信息概览**：展示基金的单位净值、日涨幅、基金规模、费率结构等核心数据。
*   **深度数据分析**：
    *   **能力评估**：通过雷达图直观展示基金的盈利能力、抗风险能力等。
    *   **资产配置**：分析股票、债券、现金的资产占比。
    *   **持仓分析**：查看前十大重仓股及其持仓占比变化。
    *   **排名趋势**：展示基金在同类产品中的排名走势。
    *   **经理信息**：展示现任基金经理的从业年限及管理业绩。
*   **交互式图表**：集成 ECharts，提供流畅的数据可视化体验。

## 🛠 技术栈

### 后端 (Backend)
*   **语言**: Python 3
*   **框架**: Flask
*   **数据库/ORM**: SQLAlchemy (默认使用 SQLite), `database.py`
*   **网络请求**: Requests
*   **数据处理**: Pandas (如果用到), JSON

### 前端 (Frontend)
*   **框架**: Vue 3 (Composition API)
*   **构建工具**: Vite
*   **可视化**: ECharts, Vue-Echarts
*   **HTTP 客户端**: Axios
*   **样式**: CSS / Scss

## 📋 环境准备

在运行项目之前，请确保您的本地环境已安装以下软件：

*   **Node.js** (推荐 LTS 版本) 和 `npm`
*   **Python 3.8+** 或 **Anaconda/Miniconda**

## ⚡ 快速开始

### 方式一：一键启动 (Windows)

如果您的环境满足以下条件，可以直接使用脚本启动：
1. 已安装 Conda。
2. Conda 中已创建名为 `fundbot` 的虚拟环境（或者您可以修改 `.bat` 文件适配您的环境名）。

双击运行根目录下的：
```bash
一键启动.bat
```

### 方式二：手动安装与启动

#### 1. 后端服务 (Backend)

```bash
# 1. 进入后端目录
cd Backend

# 2. 创建/激活虚拟环境 (可选，但在 bat 脚本中默认名为 fundbot)
# conda create -n fundbot python=3.9
# conda activate fundbot

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动 Flask 应用
python app.py
```
后端服务启动后，默认监听 `http://localhost:5000`。

#### 2. 前端界面 (Frontend)

```bash
# 1. 进入前端目录
cd Frontend

# 2. 安装 Node 依赖
npm install

# 3. 启动开发服务器
npm run dev
```
启动成功后，控制台会显示访问地址（通常为 `http://localhost:5173`）。在浏览器中打开该地址即可使用。

## 📂 项目结构

```text
MyBot/
├── Backend/                 # 后端源码
│   ├── app.py               # 后端入口文件
│   ├── models.py            # 数据模型定义
│   ├── fund_api.py          # 基金数据获取接口
│   └── ...
├── Frontend/                # 前端源码
│   ├── src/
│   │   ├── components/      # Vue 组件 (FundDetail, FundChart 等)
│   │   ├── services/        # API 请求封装
│   │   ├── App.vue          # 主组件
│   │   └── main.js          # 入口文件
│   └── ...
├── Data/                    # 本地数据缓存 (如 fund_list_cache.json)
├── 开发笔记.md              # 项目开发过程中的笔记与接口文档
├── 一键启动.bat             # Windows 启动脚本
└── requirements.txt         # 后端依赖列表
```

## 📝 数据来源与免责声明

*   **数据来源**：本项目数据来源于 [天天基金网](https://fund.eastmoney.com/) 的公开接口。
*   **免责声明**：本项目仅供学习与技术交流使用，不构成任何投资建议。数据可能存在延迟或误差，投资有风险，理财需谨慎。

## 🤝 贡献

欢迎提交 Issue 或 Pull Request 来完善这个项目！
