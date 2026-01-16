<template>
  <div v-if="fundInfo" class="fund-basic-info">
    <div class="info-header">
      <div class="header-left">
        <h2>{{ fundInfo.name || '未知基金' }}</h2>
        <span class="fund-code">{{ fundCode }}</span>
      </div>
      <div class="header-right">
        <div class="net-worth-box">
          <div class="label">单位净值</div>
          <div class="value">{{ fundInfo.dwjz || '--' }}</div>
          <div class="date">{{ formatDate(fundInfo.jzrq) }}</div>
        </div>
        <div class="estimate-box">
          <div class="label">估算净值</div>
          <div class="value" :class="getChangeClass(fundInfo.gszzl)">
            {{ fundInfo.gsz || '--' }}
          </div>
          <div class="change" :class="getChangeClass(fundInfo.gszzl)">
            {{ fundInfo.gszzl ? (fundInfo.gszzl > 0 ? '+' : '') + fundInfo.gszzl + '%' : '--' }}
          </div>
          <div class="time">{{ formatTime(fundInfo.gztime) }}</div>
        </div>
      </div>
    </div>
    
    <div class="info-metrics">
      <div class="metric-item">
        <div class="metric-label">近1月</div>
        <div class="metric-value" :class="getChangeClass(fundInfo.syl_1y)">
          {{ fundInfo.syl_1y ? (fundInfo.syl_1y > 0 ? '+' : '') + fundInfo.syl_1y + '%' : '--' }}
        </div>
      </div>
      <div class="metric-item">
        <div class="metric-label">近3月</div>
        <div class="metric-value" :class="getChangeClass(fundInfo.syl_3y)">
          {{ fundInfo.syl_3y ? (fundInfo.syl_3y > 0 ? '+' : '') + fundInfo.syl_3y + '%' : '--' }}
        </div>
      </div>
      <div class="metric-item">
        <div class="metric-label">近6月</div>
        <div class="metric-value" :class="getChangeClass(fundInfo.syl_6y)">
          {{ fundInfo.syl_6y ? (fundInfo.syl_6y > 0 ? '+' : '') + fundInfo.syl_6y + '%' : '--' }}
        </div>
      </div>
      <div class="metric-item">
        <div class="metric-label">近1年</div>
        <div class="metric-value" :class="getChangeClass(fundInfo.syl_1n)">
          {{ fundInfo.syl_1n ? (fundInfo.syl_1n > 0 ? '+' : '') + fundInfo.syl_1n + '%' : '--' }}
        </div>
      </div>
      <div class="metric-item">
        <div class="metric-label">现费率</div>
        <div class="metric-value rate">{{ formatRate(fundInfo.fund_rate) }}</div>
      </div>
      <div class="metric-item">
        <div class="metric-label">最小申购</div>
        <div class="metric-value">{{ formatMinSubscription(fundInfo.fund_minsg) }}</div>
      </div>
    </div>
    
    <div v-if="loading" class="loading">加载中...</div>
  </div>
</template>

<script>
import { fundAPI } from '../services/api'

export default {
  name: 'FundBasicInfo',
  props: {
    fundCode: {
      type: String,
      required: true
    },
    // 新增：接收父组件传递的基金数据，避免重复请求
    fundData: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      fundInfo: null,
      loading: false
    }
  },
  watch: {
    // 监听父组件传递的数据
    fundData: {
      immediate: true,
      handler(newData) {
        if (newData) {
          this.processFundData(newData)
        }
      }
    },
    fundCode: {
      immediate: true,
      handler(newCode) {
        // 只有在没有父组件传递数据时才自己请求
        if (newCode && !this.fundData) {
          this.fetchFundInfo()
        }
      }
    }
  },
  methods: {
    // 处理基金数据（可来自父组件传递或自己请求）
    processFundData(data) {
      const realtime = data.realtime_estimate || {}
      this.fundInfo = {
        ...data,
        ...data.basic_info,
        // 映射新字段名到模板使用的字段名
        name: data.basic_info?.fund_name || realtime.name,
        fund_rate: data.basic_info?.current_rate,
        fund_Rate: data.basic_info?.current_rate,
        fund_minsg: data.basic_info?.min_subscription_amount,
        fund_min_subscription: data.basic_info?.min_subscription_amount,
        // 映射业绩数据（新格式使用下划线分隔）
        syl_1y: data.performance?.['1_month_return'],
        syl_3y: data.performance?.['3_month_return'],
        syl_6y: data.performance?.['6_month_return'],
        syl_1n: data.performance?.['1_year_return'],
        // 映射实时估值数据
        dwjz: realtime.net_worth,          // 单位净值
        jzrq: realtime.net_worth_date,     // 净值日期
        gsz: realtime.estimate_value,       // 估算净值
        gszzl: realtime.estimate_change,    // 估算涨跌幅
        gztime: realtime.estimate_time      // 估值时间
      }
    },
    async fetchFundInfo() {
      this.loading = true
      try {
        const response = await fundAPI.getFundDetail(this.fundCode)
        const data = response.data
        this.processFundData(data)
      } catch (error) {
        console.error('获取基金信息失败:', error)
        this.fundInfo = null
      } finally {
        this.loading = false
      }
    },
    getChangeClass(value) {
      if (!value) return ''
      const num = parseFloat(value)
      return num > 0 ? 'positive' : num < 0 ? 'negative' : ''
    },
    formatDate(dateStr) {
      if (!dateStr) return '--'
      return dateStr
    },
    formatTime(timeStr) {
      if (!timeStr) return '--'
      return timeStr
    },
    formatRate(value) {
      // 处理费率显示：null/undefined/空值显示 '--'，数字显示带百分号
      if (value === null || value === undefined || value === '') {
        return '--'
      }
      const num = parseFloat(value)
      if (isNaN(num)) {
        return '--'
      }
      return num + '%'
    },
    formatMinSubscription(value) {
      // 处理最小申购显示
      if (value === null || value === undefined || value === '') {
        return '--'
      }
      return value + '元'
    }
  }
}
</script>

<style scoped>
.fund-basic-info {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  margin-bottom: 24px;
  color: white;
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.fund-code {
  background: rgba(255, 255, 255, 0.25);
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
}

.header-right {
  display: flex;
  gap: 24px;
}

.net-worth-box,
.estimate-box {
  text-align: right;
}

.net-worth-box .label,
.estimate-box .label {
  font-size: 12px;
  opacity: 0.9;
  margin-bottom: 4px;
}

.net-worth-box .value,
.estimate-box .value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.net-worth-box .date {
  font-size: 11px;
  opacity: 0.8;
  margin-top: 4px;
}

.estimate-box .change {
  font-size: 16px;
  font-weight: 600;
  margin-top: 2px;
}

.estimate-box .time {
  font-size: 11px;
  opacity: 0.8;
  margin-top: 4px;
}

.info-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
}

.metric-item {
  background: rgba(255, 255, 255, 0.15);
  padding: 12px;
  border-radius: 8px;
  text-align: center;
  backdrop-filter: blur(10px);
}

.metric-label {
  font-size: 12px;
  opacity: 0.9;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 20px;
  font-weight: 700;
}

.metric-value.rate {
  color: #ffd700;
}

.positive {
  color: #ff6b6b; /* 上涨显示红色 */
}

.negative {
  color: #2ed573; /* 下跌显示绿色 */
}

.loading {
  text-align: center;
  padding: 20px;
  opacity: 0.8;
}
</style>