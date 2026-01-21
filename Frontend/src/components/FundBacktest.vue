<template>
  <div class="fund-backtest">
    <div class="backtest-header">
      <h3>📊 定投回测</h3>
      <p class="header-desc">模拟历史定投收益，验证投资策略</p>
    </div>

    <!-- 基金选择 -->
    <div class="fund-select-section">
      <div v-if="!currentFundCode" class="search-container">
        <p class="select-hint">请先选择一只基金进行回测</p>
        <FundSearch @fund-selected="handleFundSelected" />
      </div>
      <div v-else class="selected-fund-display">
        <div class="fund-info">
          <span class="label">当前回测基金:</span>
          <span class="code">{{ currentFundCode }}</span>
          <span class="name" v-if="currentFundName">{{ currentFundName }}</span>
        </div>
        <button class="btn-change" @click="changeFund">更换基金</button>
      </div>
    </div>

    <!-- 回测参数设置 (仅在已选择基金时显示) -->
    <div v-if="currentFundCode" class="backtest-content">
      <div class="backtest-params">
        <div class="param-row">
        <div class="param-item">
          <label>投资方式</label>
          <div class="radio-group">
            <label class="radio-label">
              <input type="radio" v-model="params.investmentType" value="monthly" />
              <span>每月定投</span>
            </label>
            <label class="radio-label">
              <input type="radio" v-model="params.investmentType" value="weekly" />
              <span>每周定投</span>
            </label>
            <label class="radio-label">
              <input type="radio" v-model="params.investmentType" value="daily" />
              <span>每日定投</span>
            </label>
            <label class="radio-label">
              <input type="radio" v-model="params.investmentType" value="lump_sum" />
              <span>一次性买入</span>
            </label>
          </div>
          
          <!-- 定投具体日期选择 -->
          <div v-if="params.investmentType === 'monthly'" class="sub-param">
            <label>定投日：</label>
            <select v-model="params.investmentDay">
              <option v-for="d in 28" :key="d" :value="d">每月{{ d }}号</option>
            </select>
          </div>
          <div v-if="params.investmentType === 'weekly'" class="sub-param">
            <label>定投日：</label>
            <select v-model="params.investmentDay">
              <option :value="0">周一</option>
              <option :value="1">周二</option>
              <option :value="2">周三</option>
              <option :value="3">周四</option>
              <option :value="4">周五</option>
            </select>
          </div>
        </div>
      </div>

      <div class="param-row">
        <div class="param-item">
          <label>{{ params.investmentType === 'lump_sum' ? '投资金额' : '每期金额' }}</label>
          <div class="input-with-unit">
            <input 
              type="number" 
              v-model.number="params.amount" 
              min="0" 
              step="100"
              placeholder="1000"
            />
            <span class="unit">元</span>
          </div>
        </div>

        <div class="param-item">
          <label>初始资金</label>
          <div class="input-with-unit">
            <input 
              type="number" 
              v-model.number="params.initialAmount" 
              min="0" 
              step="1000"
              placeholder="0"
            />
            <span class="unit">元</span>
          </div>
        </div>
      </div>
      
      <div class="param-row">
        <div class="param-item">
          <label>分红方式</label>
          <div class="radio-group">
            <label class="radio-label">
              <input type="radio" v-model="params.dividendMode" value="reinvest" />
              <span>红利再投资</span>
            </label>
            <label class="radio-label">
              <input type="radio" v-model="params.dividendMode" value="cash" />
              <span>现金分红</span>
            </label>
          </div>
        </div>
        
        <div class="param-item">
          <label>止盈后资金处理</label>
          <div class="radio-group">
            <label class="radio-label">
              <input type="radio" v-model="params.takeProfitAction" value="cash" />
              <span>落袋为安 (现金)</span>
            </label>
            <label class="radio-label">
              <input type="radio" v-model="params.takeProfitAction" value="monetary" />
              <span>货币理财 (年化2%)</span>
            </label>
          </div>
        </div>
      </div>

      <div class="param-row">
        <div class="param-item">
          <label>止盈率</label>
          <div class="input-with-unit">
            <input 
              type="number" 
              v-model.number="params.takeProfitRate" 
              min="0" 
              step="1"
              placeholder="可选"
            />
            <span class="unit">%</span>
          </div>
        </div>

        <div class="param-item">
          <label>止损率</label>
          <div class="input-with-unit">
            <input 
              type="number" 
              v-model.number="params.stopLossRate" 
              min="0" 
              step="1"
              placeholder="可选"
            />
            <span class="unit">%</span>
          </div>
        </div>
      </div>

      <div class="param-row">
        <div class="param-item">
          <label>手续费率</label>
          <div class="input-with-unit">
            <input 
              type="number" 
              v-model.number="params.feeRate" 
              min="0" 
              max="2" 
              step="0.01"
              placeholder="0.15"
            />
            <span class="unit">%</span>
          </div>
        </div>
      </div>

      <div class="param-row">
        <div class="param-item">
          <label>开始日期</label>
          <input type="date" v-model="params.startDate" :min="minStartDate" :max="params.endDate" />
          <div v-if="minStartDate" class="date-hint">成立日: {{ minStartDate }}</div>
        </div>

        <div class="param-item">
          <label>结束日期</label>
          <input type="date" v-model="params.endDate" :min="params.startDate" :max="today" />
        </div>
      </div>

      <div class="param-actions">
        <button class="btn btn-primary" @click="runBacktest" :disabled="loading">
          <span v-if="loading">计算中...</span>
          <span v-else>开始回测</span>
        </button>
        <button class="btn btn-secondary" @click="resetParams" :disabled="loading">
          重置参数
        </button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <!-- 回测结果 -->
    <div v-if="result" class="backtest-result">
      <!-- 汇总指标 -->
      <div class="summary-section">
        <h4>📈 回测结果</h4>
        <div class="summary-grid">
          <div class="summary-card">
            <div class="card-label">总投入</div>
            <div class="card-value">{{ formatMoney(result.summary.total_invested) }}</div>
          </div>
          <div class="summary-card highlight">
            <div class="card-label">最终市值</div>
            <div class="card-value">{{ formatMoney(result.summary.final_value) }}</div>
          </div>
          <div class="summary-card" :class="getReturnClass(result.summary.total_return)">
            <div class="card-label">总收益</div>
            <div class="card-value">{{ formatReturn(result.summary.total_return) }}</div>
          </div>
          <div class="summary-card" :class="getReturnClass(result.summary.return_rate)">
            <div class="card-label">收益率</div>
            <div class="card-value">{{ result.summary.return_rate }}%</div>
          </div>
          <div class="summary-card">
            <div class="card-label">年化收益率</div>
            <div class="card-value" :class="getReturnClass(result.summary.annual_return)">
              {{ result.summary.annual_return }}%
            </div>
          </div>
          <div class="summary-card negative">
            <div class="card-label">最大回撤</div>
            <div class="card-value">{{ result.summary.max_drawdown }}%</div>
          </div>
          <div class="summary-card">
            <div class="card-label">夏普比率</div>
            <div class="card-value">{{ result.summary.sharpe_ratio }}</div>
          </div>
          <div class="summary-card">
            <div class="card-label">投资次数</div>
            <div class="card-value">{{ result.summary.investment_count }}次</div>
          </div>
          <div class="summary-card" v-if="result.summary.exit_reason">
            <div class="card-label">止盈止损</div>
            <div class="card-value" :class="result.summary.exit_reason === 'take_profit' ? 'red' : 'green'">
              {{ result.summary.exit_reason === 'take_profit' ? '止盈卖出' : '止损卖出' }}
            </div>
          </div>
        </div>
      </div>

      <!-- 收益曲线图 -->
      <div class="chart-section">
        <h4>💹 收益曲线</h4>
        <div class="chart-tabs">
          <div 
            class="tab-item" 
            :class="{ active: chartType === 'value' }"
            @click="chartType = 'value'"
          >
            市值变化
          </div>
          <div 
            class="tab-item" 
            :class="{ active: chartType === 'return' }"
            @click="chartType = 'return'"
          >
            收益率
          </div>
        </div>
        <div ref="chartEl" class="chart-container"></div>
      </div>

      <!-- 详细数据表格（可选展开） -->
      <div class="detail-section">
        <div class="detail-header" @click="showDetail = !showDetail">
          <h4>📋 详细记录</h4>
          <span class="toggle-icon">{{ showDetail ? '▼' : '▶' }}</span>
        </div>
        <div v-if="showDetail" class="detail-table-wrapper">
          <table class="detail-table">
            <thead>
              <tr>
                <th>日期</th>
                <th>净值</th>
                <th>累计投入</th>
                <th>持有份额</th>
                <th>市值</th>
                <th>收益</th>
                <th>收益率</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="(record, index) in paginatedTimeline" 
                :key="index"
                :class="{ 'investment-day': record.is_investment_day, 'sold-day': record.status === 'sold' }"
              >
                <td>
                  {{ record.date }}
                  <span v-if="record.is_investment_day" class="invest-badge">买入</span>
                  <span v-if="record.status === 'sold' && record.exit_reason" class="sold-badge">
                    {{ record.exit_reason === 'take_profit' ? '止盈' : '止损' }}
                  </span>
                </td>
                <td>{{ record.nav }}</td>
                <td>{{ formatMoney(record.invested) }}</td>
                <td>{{ record.shares }}</td>
                <td>{{ formatMoney(record.value) }}</td>
                <td :class="getReturnClass(record.return)">{{ formatReturn(record.return) }}</td>
                <td :class="getReturnClass(record.return_rate)">{{ record.return_rate }}%</td>
              </tr>
            </tbody>
          </table>
          <div class="pagination" v-if="totalPages > 1">
            <button @click="currentPage--" :disabled="currentPage === 1">上一页</button>
            <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
            <button @click="currentPage++" :disabled="currentPage === totalPages">下一页</button>
          </div>
        </div>
      </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { backtestAPI, fundAPI } from '../services/api'
import FundSearch from './FundSearch.vue'

export default {
  name: 'FundBacktest',
  components: {
    FundSearch
  },
  props: {
    fundCode: {
      type: String,
      default: ''
    }
  },
  setup(props) {
    const chartEl = ref(null)
    const loading = ref(false)
    const error = ref('')
    const result = ref(null)
    
    // 基金相关状态
    const currentFundCode = ref(props.fundCode || '')
    const currentFundName = ref('')
    const minStartDate = ref('') // 基金成立日期（最早回测日期）
    
    watch(() => props.fundCode, (val) => {
      if (val) {
        currentFundCode.value = val
        fetchFundInfo(val)
      }
    })

    const fetchFundInfo = async (code) => {
      try {
        const response = await fundAPI.getFundTrend(code)
        if (response.data && response.data.net_worth_trend && response.data.net_worth_trend.length > 0) {
          // 获取最早的净值日期作为成立日期
          const trends = response.data.net_worth_trend
          // trends通常是按时间排序的，但为了保险起见，我们取第一个
          // 注意：API返回的数据通常是升序的（旧->新）
          const firstDate = trends[0].date // 假设格式为 "YYYY-MM-DD"
          minStartDate.value = firstDate.split(' ')[0] // 确保只有日期部分
          
          // 如果当前设置的开始日期早于成立日期，自动调整
          if (params.value.startDate < minStartDate.value) {
            params.value.startDate = minStartDate.value
          }
        }
      } catch (err) {
        console.error('获取基金信息失败:', err)
        // 如果获取失败，不强制限制最小日期，或者设为默认值
      }
    }

    const handleFundSelected = (fund) => {
      // FundSearch 返回的是 { CODE: '...', NAME: '...', ... } 或标准格式
      const code = fund.CODE || fund.fund_code || fund.code
      currentFundCode.value = code
      currentFundName.value = fund.NAME || fund.fund_name || fund.name
      // 重置结果
      result.value = null
      error.value = ''
      // 获取基金详细信息以确定成立日期
      fetchFundInfo(code)
    }

    const changeFund = () => {
      currentFundCode.value = ''
      currentFundName.value = ''
      result.value = null
      error.value = ''
    }

    const showDetail = ref(false)
    const chartType = ref('value')
    const currentPage = ref(1)
    const pageSize = 50
    
    let chartInstance = null

    // 今天的日期
    const today = new Date().toISOString().split('T')[0]
    
    // 默认参数：最近3年，每月定投1000元
    const params = ref({
      investmentType: 'monthly',
      investmentDay: 1, // 默认每月1号 / 周一
      amount: 1000,
      initialAmount: 0,
      feeRate: 0.15,
      takeProfitRate: null,
      stopLossRate: null,
      startDate: new Date(Date.now() - 3 * 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      endDate: today,
      dividendMode: 'reinvest', // 默认红利再投资
      takeProfitAction: 'cash' // 默认落袋为安
    })

    // 监听投资方式变化，重置日期
    watch(() => params.value.investmentType, (newType) => {
      if (newType === 'monthly') {
        params.value.investmentDay = 1
      } else if (newType === 'weekly') {
        params.value.investmentDay = 0 // 周一
      } else {
        params.value.investmentDay = null
      }
    })

    // 分页数据
    const paginatedTimeline = computed(() => {
      if (!result.value || !result.value.timeline) return []
      const start = (currentPage.value - 1) * pageSize
      const end = start + pageSize
      return result.value.timeline.slice(start, end)
    })

    const totalPages = computed(() => {
      if (!result.value || !result.value.timeline) return 0
      return Math.ceil(result.value.timeline.length / pageSize)
    })

    // 执行回测
    const runBacktest = async () => {
      if (!params.value.startDate || !params.value.endDate) {
        error.value = '请选择开始和结束日期'
        return
      }
      
      if (params.value.investmentType === 'lump_sum') {
        if (params.value.amount <= 0 && params.value.initialAmount <= 0) {
          error.value = '请输入投资金额或初始资金'
          return
        }
      } else if (params.value.amount < 100) {
        error.value = '每期定投金额不能小于100元'
        return
      }

      loading.value = true
      error.value = ''
      result.value = null
      currentPage.value = 1

      try {
        const response = await backtestAPI.fixedInvestment({
          fund_code: currentFundCode.value,
          start_date: params.value.startDate,
          end_date: params.value.endDate,
          investment_type: params.value.investmentType,
          investment_day: params.value.investmentDay,
          amount: params.value.amount,
          initial_amount: params.value.initialAmount,
          fee_rate: params.value.feeRate,
          take_profit_rate: params.value.takeProfitRate,
          stop_loss_rate: params.value.stopLossRate,
          dividend_mode: params.value.dividendMode,
          take_profit_action: params.value.takeProfitAction
        })

        // 后端成功时直接返回 { summary, timeline }，不包含 code 字段
        if (response.data && response.data.summary) {
          result.value = response.data
          await nextTick()
          initChart()
        } else if (response.data.error) {
          error.value = response.data.error
        } else {
          error.value = '回测失败：返回数据格式异常'
        }
      } catch (err) {
        console.error('回测错误:', err)
        error.value = err.response?.data?.error || err.response?.data?.message || '回测失败，请稍后重试'
      } finally {
        loading.value = false
      }
    }

    // 重置参数
    const resetParams = () => {
      params.value = {
        investmentType: 'monthly',
        investmentDay: 1,
        amount: 1000,
        initialAmount: 0,
        feeRate: 0.15,
        takeProfitRate: null,
        stopLossRate: null,
        startDate: new Date(Date.now() - 3 * 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        endDate: today,
        dividendMode: 'reinvest',
        takeProfitAction: 'cash'
      }
      result.value = null
      error.value = ''
      currentPage.value = 1
    }

    // 格式化金额
    const formatMoney = (value) => {
      if (value === null || value === undefined) return '0.00'
      return Number(value).toFixed(2)
    }

    // 格式化收益
    const formatReturn = (value) => {
      if (value === null || value === undefined) return '0.00'
      const num = Number(value)
      return (num >= 0 ? '+' : '') + num.toFixed(2)
    }

    // 获取收益样式类
    const getReturnClass = (value) => {
      if (value === null || value === undefined) return ''
      return Number(value) >= 0 ? 'positive' : 'negative'
    }

    // 初始化图表
    const initChart = () => {
      if (!chartEl.value || !result.value) return

      if (chartInstance) {
        chartInstance.dispose()
      }

      chartInstance = echarts.init(chartEl.value)
      updateChart()
    }

    // 更新图表
    const updateChart = () => {
      if (!chartInstance || !result.value) return

      const timeline = result.value.timeline
      const dates = timeline.map(item => item.date)
      
      let series = []
      let yAxisName = ''
      
      if (chartType.value === 'value') {
        // 市值变化图
        yAxisName = '金额（元）'
        series = [
          {
            name: '累计投入',
            type: 'line',
            data: timeline.map(item => item.invested),
            smooth: true,
            lineStyle: { color: '#909399', width: 2 },
            itemStyle: { color: '#909399' }
          },
          {
            name: '市值',
            type: 'line',
            data: timeline.map(item => item.value),
            smooth: true,
            lineStyle: { color: '#409EFF', width: 2 },
            itemStyle: { color: '#409EFF' },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
                { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
              ])
            }
          }
        ]
      } else {
        // 收益率图
        yAxisName = '收益率（%）'
        series = [
          {
            name: '收益率',
            type: 'line',
            data: timeline.map(item => item.return_rate),
            smooth: true,
            lineStyle: { color: '#F56C6C', width: 2 },
            itemStyle: { color: '#F56C6C' },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(245, 108, 108, 0.3)' },
                { offset: 1, color: 'rgba(245, 108, 108, 0.05)' }
              ])
            },
            markLine: {
              silent: true,
              symbol: 'none',
              lineStyle: { color: '#E6A23C', type: 'dashed' },
              data: [{ yAxis: 0 }],
              label: { show: false }
            }
          }
        ]
      }

      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross' },
          formatter: (params) => {
            let html = `<div style="font-weight: bold; margin-bottom: 5px;">${params[0].axisValue}</div>`
            params.forEach(param => {
              const value = chartType.value === 'value' 
                ? formatMoney(param.value)
                : param.value + '%'
              html += `<div>${param.marker} ${param.seriesName}: ${value}</div>`
            })
            return html
          }
        },
        legend: {
          data: series.map(s => s.name),
          top: 10
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: 50,
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: dates,
          axisLabel: {
            formatter: (value) => {
              return value.substring(5) // 只显示月-日
            }
          }
        },
        yAxis: {
          type: 'value',
          name: yAxisName,
          axisLabel: {
            formatter: chartType.value === 'value' 
              ? (value) => (value / 1000).toFixed(1) + 'k'
              : '{value}%'
          }
        },
        series: series,
        dataZoom: [
          {
            type: 'inside',
            start: 0,
            end: 100
          },
          {
            start: 0,
            end: 100,
            height: 20,
            bottom: 10
          }
        ]
      }

      chartInstance.setOption(option, true)
    }

    // 监听图表类型变化
    watch(chartType, () => {
      updateChart()
    })

    // 监听结果变化
    watch(result, (newVal) => {
      if (newVal) {
        showDetail.value = false
      }
    })

    // 生命周期
    onMounted(() => {
      window.addEventListener('resize', () => {
        if (chartInstance) {
          chartInstance.resize()
        }
      })
    })

    onUnmounted(() => {
      if (chartInstance) {
        chartInstance.dispose()
        chartInstance = null
      }
    })

    return {
      chartEl,
      loading,
      error,
      result,
      showDetail,
      chartType,
      currentPage,
      pageSize,
      today,
      params,
      paginatedTimeline,
      totalPages,
      runBacktest,
      resetParams,
      formatMoney,
      formatReturn,
      getReturnClass,
      currentFundCode,
      currentFundName,
      handleFundSelected,
      changeFund
    }
  }
}
</script>

<style scoped>
.fund-backtest {
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

.date-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.backtest-header {
  margin-bottom: 20px;
  text-align: center;
}

.backtest-header h3 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #303133;
}

.header-desc {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

/* 基金选择区域 */
.fund-select-section {
  margin-bottom: 20px;
}

.search-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px 0;
}

.select-hint {
  color: #606266;
  margin-bottom: 15px;
  text-align: center;
}

.selected-fund-display {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: #ecf5ff;
  border: 1px solid #d9ecff;
  border-radius: 8px;
}

.fund-info {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
}

.fund-info .label {
  color: #606266;
}

.fund-info .code {
  font-weight: bold;
  color: #409eff;
  font-family: 'SF Mono', Monaco, monospace;
}

.fund-info .name {
  color: #303133;
}

.btn-change {
  padding: 6px 16px;
  border: 1px solid #409eff;
  color: #409eff;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-change:hover {
  background: #409eff;
  color: #fff;
}

/* 参数设置 */
.backtest-params {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.param-row {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
}

.param-row:last-child {
  margin-bottom: 0;
}

.param-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
}

.param-item label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
  font-weight: 500;
}

.input-with-unit {
  position: relative;
  display: flex;
  align-items: center;
}

.param-item input[type="number"],
.param-item input[type="date"] {
  flex: 1;
  padding: 8px 12px;
  padding-right: 40px; /* 为右侧单位文字预留空间 */
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.3s;
  font-family: inherit;
  box-sizing: border-box;
  height: 40px; /* 固定高度确保对齐 */
}

.param-item input:focus {
  outline: none;
  border-color: #409eff;
}

.param-item .unit {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #909399;
  font-size: 14px;
  pointer-events: none;
  background: white;
  padding: 0 4px;
  height: 20px;
  line-height: 20px;
}

.radio-group {
  display: flex;
  gap: 15px;
  margin-top: 4px;
  flex-wrap: wrap; /* 允许换行以适应更多选项 */
}

.sub-param {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #606266;
}

.sub-param select {
  padding: 4px 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
}

.radio-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 14px;
  color: #606266;
}

.radio-label input[type="radio"] {
  margin-right: 6px;
  cursor: pointer;
}

.param-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 20px;
}

.btn {
  padding: 10px 24px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  font-family: inherit;
  min-width: 100px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #409eff;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #66b1ff;
}

.btn-secondary {
  background: #fff;
  color: #606266;
  border: 1px solid #dcdfe6;
}

.btn-secondary:hover:not(:disabled) {
  color: #409eff;
  border-color: #409eff;
}

/* 错误提示 */
.error-message {
  padding: 12px 16px;
  background: #fef0f0;
  border: 1px solid #fde2e2;
  border-radius: 4px;
  color: #f56c6c;
  margin-bottom: 20px;
  font-size: 14px;
}

/* 回测结果 */
.backtest-result {
  margin-top: 20px;
}

.summary-section,
.chart-section,
.detail-section {
  margin-bottom: 30px;
  padding: 0 5px;
}

.summary-section h4,
.chart-section h4,
.detail-section h4 {
  margin: 0 0 15px 0;
  font-size: 18px;
  color: #303133;
  padding-left: 5px;
}

/* 汇总指标卡片 */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.summary-card {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  text-align: center;
  transition: transform 0.3s, box-shadow 0.3s;
  min-height: 80px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.summary-card.highlight {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.summary-card.positive {
  background: #f0f9ff;
  border: 1px solid #c6f6d5;
}

.summary-card.negative {
  background: #fff5f5;
  border: 1px solid #fed7d7;
}

.card-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
  line-height: 1.2;
}

.summary-card.highlight .card-label {
  color: rgba(255, 255, 255, 0.9);
}

.card-value {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
  word-break: break-all;
}

.summary-card.highlight .card-value {
  color: #fff;
}

.card-value.positive {
  color: #f56c6c;
}

.card-value.negative {
  color: #67c23a;
}

/* 图表 */
.chart-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
  padding-left: 5px;
}

.tab-item {
  padding: 8px 16px;
  background: #f5f7fa;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  color: #606266;
  transition: all 0.3s;
  border: 1px solid transparent;
}

.tab-item:hover {
  background: #e4e7ed;
  border-color: #dcdfe6;
}

.tab-item.active {
  background: #409eff;
  color: #fff;
  border-color: #409eff;
}

.chart-container {
  width: 100%;
  height: 400px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

/* 详细记录 */
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  padding: 12px 15px;
  background: #f5f7fa;
  border-radius: 4px;
  transition: background 0.3s;
  border: 1px solid transparent;
}

.detail-header:hover {
  background: #e4e7ed;
  border-color: #dcdfe6;
}

.toggle-icon {
  font-size: 12px;
  color: #909399;
}

.detail-table-wrapper {
  margin-top: 15px;
  overflow-x: auto;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.detail-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  min-width: 800px;
}

.detail-table th,
.detail-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #ebeef5;
  line-height: 1.4;
}

.detail-table th {
  background: #f5f7fa;
  color: #606266;
  font-weight: 600;
  white-space: nowrap;
}

.detail-table tbody tr:hover {
  background: #f5f7fa;
}

.detail-table tbody tr.investment-day {
  background: #ecf5ff;
}

.detail-table tbody tr.sold-day {
  background: #fff5f5;
}

.invest-badge {
  display: inline-block;
  padding: 2px 6px;
  background: #409eff;
  color: #fff;
  font-size: 12px;
  border-radius: 3px;
  margin-left: 8px;
  line-height: 1;
}

.sold-badge {
  display: inline-block;
  padding: 2px 6px;
  background: #f56c6c;
  color: #fff;
  font-size: 12px;
  border-radius: 3px;
  margin-left: 8px;
  line-height: 1;
}

.detail-table .positive {
  color: #f56c6c;
  font-weight: 500;
}

.detail-table .negative {
  color: #67c23a;
  font-weight: 500;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  margin-top: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-top: 1px solid #ebeef5;
}

.pagination button {
  padding: 6px 12px;
  border: 1px solid #dcdfe6;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
  min-width: 80px;
}

.pagination button:hover:not(:disabled) {
  color: #409eff;
  border-color: #409eff;
  background: #ecf5ff;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination span {
  font-size: 14px;
  color: #606266;
  min-width: 100px;
  text-align: center;
}

/* 响应式 */
@media (max-width: 768px) {
  .param-row {
    flex-direction: column;
    gap: 15px;
  }
  
  .param-item {
    width: 100%;
  }
  
  .summary-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .chart-container {
    height: 300px;
  }
  
  .param-actions {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .fund-backtest {
    padding: 15px;
  }
  
  .summary-grid {
    grid-template-columns: 1fr;
  }
  
  .selected-fund-display {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .btn-change {
    align-self: flex-end;
  }
}
</style>
