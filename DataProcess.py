import requests
import pandas as pd
import json
import re
import time
import matplotlib.pyplot as plt
import datetime
import numpy as np
from matplotlib.patches import Rectangle

def get_fund_basic_info(fund_code):
    """
    获取基金综合信息，包括实时估值、基本资料、持仓等。
    合并了原 realtmfundinfo 和 get_fund_basic_info 的功能。
    
    Args:
        fund_code (str): 基金代码
        
    Returns:
        dict: 包含基金信息的字典，包含以下字段：
            - fundcode: 基金代码
            - name: 基金名称
            - jzrq: 净值日期
            - dwjz: 单位净值
            - gsz: 估算净值
            - gszzl: 估算增长率
            - gztime: 估算时间
            - fund_rate: 现费率
            - fund_min_subscription: 最小申购金额
            - stock_codes: 前十大持仓股票代码列表
            - fund_size: 基金规模（亿元）
    """
    info = {}
    
    # 1. 获取实时估值信息 (原 realtmfundinfo)
    try:
        # 天天基金实时估值接口
        real_time_url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"
        response = requests.get(real_time_url, timeout=5)
        if response.status_code == 200:
            content = response.text
            # 提取 jsonpgz({...}) 中的 json 部分
            match = re.search(r"jsonpgz\((.*?)\);", content)
            if match:
                real_time_data = json.loads(match.group(1))
                info.update(real_time_data)
    except Exception as e:
        print(f"获取实时估值信息失败: {e}")

    # 2. 获取基本资料
    try:
        basic_url = f"https://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
        response = requests.get(basic_url, timeout=5)
        if response.status_code == 200:
            content = response.text
            
            # 基金名称 (如果实时接口没获取到，尝试在这里获取)
            if 'name' not in info:
                name_match = re.search(r'var fS_name\s*=\s*"(.*?)";', content)
                if name_match:
                    info['name'] = name_match.group(1)
            
            # 现费率
            rate_match = re.search(r'var fund_Rate\s*=\s*"(.*?)";', content)
            if rate_match:
                info['fund_rate'] = rate_match.group(1)

            # 最小申购金额
            min_match = re.search(r'var fund_minsg\s*=\s*"(.*?)";', content)
            if min_match:
                info['fund_min_subscription'] = min_match.group(1)
                
            # 前十大持仓
            stock_codes_match = re.search(r'var stockCodes\s*=\s*(\[.*?\]);', content)
            if stock_codes_match:
                try:
                    codes_raw = json.loads(stock_codes_match.group(1))
                    # 天天基金返回的code有时候带有交易所后缀（如0025580），取前6位
                    info['stock_codes'] = [code[:6] for code in codes_raw]
                except:
                    info['stock_codes'] = []

            # 基金规模
            asset_alloc_match = re.search(r'var Data_assetAllocation\s*=\s*(\{.*?\});', content, re.DOTALL)
            if asset_alloc_match:
                try:
                    asset_data = json.loads(asset_alloc_match.group(1))
                    net_asset_series = next((s for s in asset_data.get('series', []) if s.get('name') == '净资产'), None)
                    if net_asset_series and net_asset_series.get('data'):
                        info['fund_size'] = net_asset_series['data'][-1]
                except:
                    info['fund_size'] = None

    except Exception as e:
        print(f"获取基本资料失败: {e}")
        
    return info

def get_fund_net_worth_history(fund_code, years=None):
    """
    获取基金历史净值数据
    
    Args:
        fund_code (str): 基金代码
        years (int, optional): 显示最近多少年的数据，None表示显示全部数据
        
    Returns:
        pd.DataFrame: 包含日期和净值的DataFrame
    """
    url = f"https://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.text
        
        # 使用正则表达式提取 Data_netWorthTrend
        match = re.search(r'var Data_netWorthTrend\s*=\s*(\[.*?\]);', content, re.DOTALL)
        
        if not match:
            print(f"无法在响应中找到 Data_netWorthTrend 数据 (基金代码: {fund_code})")
            return None
            
        json_str = match.group(1)
        data = json.loads(json_str)
        
        # 转换为DataFrame
        df = pd.DataFrame(data)
        
        # 处理数据
        df['date'] = pd.to_datetime(df['x'], unit='ms')
        df['net_worth'] = df['y']
        
        # 只保留需要的列
        result_df = df[['date', 'net_worth']].copy()
        result_df.set_index('date', inplace=True)
        result_df.sort_index(inplace=True)
        
        # 如果指定了年份，筛选最近的数据
        if years is not None:
            cutoff_date = result_df.index[-1] - pd.DateOffset(years=years)
            result_df = result_df[result_df.index >= cutoff_date]
        
        return result_df
        
    except requests.RequestException as e:
        print(f"网络请求错误: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return None
    except Exception as e:
        print(f"发生未知错误: {e}")
        return None

def calculate_max_drawdown(net_worth_series):
    """
    计算最大回撤
    
    Args:
        net_worth_series: 净值序列
        
    Returns:
        dict: 包含最大回撤信息的字典
    """
    if len(net_worth_series) < 2:
        return {
            'max_drawdown': 0,
            'drawdown_period': 0,
            'drawdown_start': None,
            'drawdown_end': None,
            'drawdown_start_value': 0,
            'drawdown_end_value': 0
        }
    
    # 计算累积最大值
    cumulative_max = net_worth_series.expanding().max()
    
    # 计算回撤
    drawdown = (net_worth_series - cumulative_max) / cumulative_max * 100
    drawdown_abs = (cumulative_max - net_worth_series) / cumulative_max * 100
    
    # 最大回撤值（负值表示回撤）
    max_dd_value = drawdown.min()
    max_dd_idx = drawdown.idxmin()
    
    if pd.isna(max_dd_value) or max_dd_value == 0:
        return {
            'max_drawdown': 0,
            'drawdown_period': 0,
            'drawdown_start': None,
            'drawdown_end': None,
            'drawdown_start_value': 0,
            'drawdown_end_value': 0
        }
    
    # 找到最大回撤开始点（最高点）
    max_dd_end = max_dd_idx
    temp_series = net_worth_series[:max_dd_end]
    
    if len(temp_series) > 0:
        max_dd_start = temp_series.idxmax()
        max_dd_start_value = net_worth_series.loc[max_dd_start]
        max_dd_end_value = net_worth_series.loc[max_dd_end]
        max_dd_period = (max_dd_end - max_dd_start).days
    else:
        max_dd_start = None
        max_dd_start_value = 0
        max_dd_end_value = 0
        max_dd_period = 0
    
    return {
        'max_drawdown': -max_dd_value,  # 转为正数
        'drawdown_period': max_dd_period,
        'drawdown_start': max_dd_start,
        'drawdown_end': max_dd_end,
        'drawdown_start_value': max_dd_start_value,
        'drawdown_end_value': max_dd_end_value
    }

def calculate_technical_indicators(df, window=20):
    """
    计算技术指标
    
    Args:
        df: 包含net_worth的DataFrame
        window: 移动平均窗口
        
    Returns:
        DataFrame: 包含技术指标的DataFrame
    """
    result_df = df.copy()
    
    # 计算移动平均线
    if len(result_df) >= window:
        result_df[f'MA{window}'] = result_df['net_worth'].rolling(window=window, min_periods=1).mean()
    else:
        result_df[f'MA{window}'] = result_df['net_worth']
    
    # 计算收益率
    if len(result_df) > 1:
        result_df['daily_return'] = result_df['net_worth'].pct_change() * 100
    
    return result_df

def plot_fund_vector_graph(fund_code, years=None, save_path=None):
    """
    绘制基金历史表现矢量图
    
    Args:
        fund_code (str): 基金代码
        years (int, optional): 显示最近多少年的数据，None表示显示全部数据，1表示最近1年的数据，依此类推.
        save_path (str, optional): 保存路径，例如 'fund_plot.svg'. 默认为 None (显示图表).
    """
    # 首先获取基金的基本信息用于标题
    try:
        fund_info = get_fund_basic_info(fund_code)
        fund_name = fund_info.get('name', f'基金{fund_code}')
    except:
        fund_name = f'基金{fund_code}'
    
    # 获取数据
    df = get_fund_net_worth_history(fund_code, years)
    
    if df is None or df.empty:
        print("没有数据可供绘图")
        return
    
    if len(df) < 20:
        print(f"数据不足，至少需要20个交易日的数据，当前只有{len(df)}个")
        return
    
    # 计算技术指标
    df = calculate_technical_indicators(df, window=20)
    
    # 计算最大回撤
    max_dd_info = calculate_max_drawdown(df['net_worth'])
    
    # 计算收益和风险指标
    if 'daily_return' in df.columns:
        returns = df['daily_return'].dropna()
        if len(returns) > 0:
            mean_return = returns.mean()
            std_return = returns.std()
            total_return = (df['net_worth'].iloc[-1] / df['net_worth'].iloc[0] - 1) * 100
            positive_days = (returns > 0).sum()
            total_days = len(returns)
            positive_ratio = positive_days / total_days * 100
            
            # 年化收益率（假设一年252个交易日）
            if len(df) > 252:
                annual_return = ((1 + total_return/100) ** (252/len(df)) - 1) * 100
            else:
                annual_return = total_return
        else:
            mean_return = 0
            std_return = 0
            total_return = 0
            positive_days = 0
            total_days = 0
            positive_ratio = 0
            annual_return = 0
    else:
        mean_return = 0
        std_return = 0
        total_return = 0
        positive_days = 0
        total_days = 0
        positive_ratio = 0
        annual_return = 0
    
    # 设置绘图风格
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # 支持中文显示
    try:
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    except:
        pass

    # 创建图形
    fig = plt.figure(figsize=(14, 10))
    
    # 创建子图网格
    gs = fig.add_gridspec(3, 2, height_ratios=[2, 1, 0.8], width_ratios=[3, 1])
    
    # 主图 - 净值走势
    ax1 = fig.add_subplot(gs[0, :])
    
    # 绘制单位净值走势
    ax1.plot(df.index, df['net_worth'], 
             linewidth=2, 
             color='#1f77b4',
             label='单位净值', 
             alpha=0.8)
    
    # 绘制20日移动平均线
    ax1.plot(df.index, df['MA20'], 
             'orange', 
             linewidth=1.5, 
             alpha=0.7, 
             label='20日均线')
    
    # 标记最大回撤区间
    if (max_dd_info['drawdown_start'] is not None and 
        max_dd_info['drawdown_end'] is not None):
        
        # 找到最大回撤区间内的数据
        mask = (df.index >= max_dd_info['drawdown_start']) & (df.index <= max_dd_info['drawdown_end'])
        if mask.any():
            # 填充最大回撤区间
            ax1.fill_between(df.index[mask], 
                             df.loc[mask, 'net_worth'].min(),
                             df.loc[mask, 'net_worth'].max(),
                             color='red', alpha=0.2, label='最大回撤区间')
            
            # 标注最大回撤
            ax1.annotate(f"最大回撤: {max_dd_info['max_drawdown']:.2f}%\n"
                         f"持续: {max_dd_info['drawdown_period']}天", 
                         xy=(max_dd_info['drawdown_end'], 
                             max_dd_info['drawdown_end_value']),
                         xytext=(10, -30), textcoords='offset points',
                         bbox=dict(boxstyle="round,pad=0.3", facecolor="red", alpha=0.7),
                         fontsize=9,
                         arrowprops=dict(arrowstyle="->", color='red', alpha=0.7))
    
    # 标记当前点
    last_date = df.index[-1]
    last_value = df['net_worth'].iloc[-1]
    ax1.scatter([last_date], [last_value], color='green', s=100, zorder=5)
    ax1.annotate(f'当前: {last_value:.3f}', 
                 xy=(last_date, last_value),
                 xytext=(10, 10), textcoords='offset points',
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="green", alpha=0.7))
    
    # 设置主图属性
    year_text = f' ({years}年)' if years else ' (全部数据)'
    ax1.set_title(f'{fund_name} {year_text}', fontsize=16, fontweight='bold', pad=20)
    ax1.set_ylabel('单位净值 (元)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left', fontsize=11)
    
    # 收益率子图
    ax2 = fig.add_subplot(gs[1, :], sharex=ax1)
    
    if 'daily_return' in df.columns:
        returns = df['daily_return'].dropna()
        if len(returns) > 0:
            # 绘制收益率柱状图
            colors = ['red' if r >= 0 else 'green' for r in returns]
            ax2.bar(returns.index, returns, color=colors, alpha=0.7, width=1.0)
            
            # 添加零线
            ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.5)
            
            ax2.set_ylabel('日收益率 (%)', fontsize=12)
            ax2.grid(True, alpha=0.3)
    
    # 统计信息子图
    ax3 = fig.add_subplot(gs[2, 0])
    ax3.axis('off')
    
    # 创建统计信息表格
    stats_data = [
        ['总收益率', f'{total_return:+.2f}%'],
        ['年化收益率', f'{annual_return:+.2f}%'],
        ['平均日收益率', f'{mean_return:+.2f}%'],
        ['波动率(日)', f'{std_return:.2f}%'],
        ['最大回撤', f'{max_dd_info["max_drawdown"]:.2f}%'],
        ['回撤天数', f'{max_dd_info["drawdown_period"]}天'],
        ['上涨天数', f'{positive_days}/{total_days} ({positive_ratio:.1f}%)'],
        ['数据点数', f'{len(df)}']
    ]
    
    # 绘制表格
    table = ax3.table(cellText=stats_data,
                      colLabels=['指标', '数值'],
                      cellLoc='center',
                      loc='center',
                      colWidths=[0.3, 0.3])
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    # 基本信息子图
    ax4 = fig.add_subplot(gs[2, 1])
    ax4.axis('off')
    
    info_text = (f'基金代码: {fund_code}\n'
                 f'数据范围:\n{df.index[0].strftime("%Y-%m-%d")}\n至\n{df.index[-1].strftime("%Y-%m-%d")}\n'
                 f'净值范围:\n{df["net_worth"].min():.3f} - {df["net_worth"].max():.3f}')
    
    ax4.text(0.5, 0.5, info_text, 
             transform=ax4.transAxes,
             fontsize=9,
             verticalalignment='center',
             horizontalalignment='center',
             bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.7))
    
    # 旋转日期标签
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    
    if save_path:
        if not save_path.lower().endswith('.svg'):
            save_path += '.svg'
        plt.savefig(save_path, format='svg', dpi=300, bbox_inches='tight')
        print(f"图表已保存至: {save_path}")
        plt.close()
    else:
        plt.show()

    