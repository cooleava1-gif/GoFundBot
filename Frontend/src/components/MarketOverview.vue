<!-- 市场概览组件：指数、金价、成交量、上证分�?-->
<template>
  <div class="market-overview-container">
    <!-- 全球市场指数 -->
    <div class="market-section">
      <div class="section-header">
        <h3>🌍 全球市场指数</h3>
        <button class="refresh-btn" @click="fetchAll" :disabled="loading">
          <span :class="{ 'spinning': loading }">🔄</span>
        </button>
      </div>
      <div class="index-grid" v-if="marketIndex.length">
        <div 
          v-for="item in marketIndex" 
          :key="item.name" 
          class="index-card"
          :class="{ 
            'up': !item.change_pct.startsWith('-'),
            'down': item.change_pct.startsWith('-')
          }"
        >
          <div class="index-name">{{ item.name }}</div>
          <div class="index-price">{{ item.price }}</div>
          <div class="index-change">{{ item.change_pct }}</div>
        </div>
      </div>
      <div v-else class="empty-state">暂无数据</div>
    </div>
    
    <!-- 实时贵金属 -->
    <div class="market-section">
      <div class="section-header">
        <h3>🥇 实时贵金属</h3>
      </div>
      <div class="gold-grid" v-if="goldRealtime.length">
        <div 
          v-for="item in goldRealtime" 
          :key="item.name" 
          class="gold-card"
          :class="{ 
            'up': item.change >= 0,
            'down': item.change < 0
          }"
        >
          <div class="gold-name">{{ item.name }}</div>
          <div class="gold-price">{{ item.price }} <span class="unit">{{ item.unit }}</span></div>
          <div class="gold-change">
            <span>{{ item.change >= 0 ? '+' : '' }}{{ item.change }}</span>
            <span class="pct">{{ item.change_pct }}</span>
          </div>
          <div class="gold-detail">
            <span>高 {{ item.high }}</span>
            <span>低 {{ item.low }}</span>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">暂无数据</div>
    </div>
    
    <!-- 黄金历史价格 -->
    <div class="market-section" v-if="showGoldHistory">
      <div class="section-header">
        <h3>📊 黄金历史价格</h3>
        <button class="toggle-btn" @click="goldHistoryExpanded = !goldHistoryExpanded">
          {{ goldHistoryExpanded ? '收起' : '展开' }}
        </button>
      </div>
      <div v-if="goldHistoryExpanded && goldHistory.length" class="history-table">
        <table>
          <thead>
            <tr>
              <th>日期</th>
              <th>中国黄金基础金价</th>
              <th>涨跌</th>
              <th>周大福金价</th>
              <th>涨跌</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in goldHistory" :key="item.date">
              <td>{{ item.date }}</td>
              <td>{{ item.china_gold_price }}</td>
              <td :class="getChangeClass(item.china_gold_change)">{{ item.china_gold_change }}</td>
              <td>{{ item.zhoudafu_price }}</td>
              <td :class="getChangeClass(item.zhoudafu_change)">{{ item.zhoudafu_change }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <!-- 近7日A股成交量 -->
    <div class="market-section">
      <div class="section-header">
        <h3>📈 近7日A股成交量</h3>
      </div>
      <div v-if="aVolume.length" class="volume-chart">
        <div class="volume-bars">
          <div 
            v-for="item in aVolume" 
            :key="item.date" 
            class="volume-bar-wrapper"
          >
            <div 
              class="volume-bar" 
              :style="{ height: getBarHeight(item.total) + '%' }"
            >
              <span class="bar-value">{{ item.total }}</span>
            </div>
            <span class="bar-date">{{ formatDate(item.date) }}</span>
          </div>
        </div>
        <div class="volume-detail">
          <table>
            <thead>
              <tr>
                <th>日期</th>
                <th>总成交额</th>
                <th>上交所</th>
                <th>深交所</th>
                <th>北交所</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in aVolume.slice(0, 5)" :key="item.date">
                <td>{{ item.date }}</td>
                <td class="highlight">{{ item.total }}</td>
                <td>{{ item.shanghai }}</td>
                <td>{{ item.shenzhen }}</td>
                <td>{{ item.beijing }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div v-else class="empty-state">暂无数据</div>
    </div>
    
    <!-- 近30分钟上证指数 -->
    <div class="market-section" v-if="showSSE30Min">
      <div class="section-header">
        <h3>📉 近30分钟上证指数</h3>
        <button class="toggle-btn" @click="sse30MinExpanded = !sse30MinExpanded">
          {{ sse30MinExpanded ? '收起' : '展开' }}
        </button>
      </div>
      <div v-if="sse30MinExpanded && sse30Min.length" class="sse-chart">
        <div class="sse-mini-chart">
          <svg viewBox="0 0 300 60" class="price-line">
            <polyline
              :points="getChartPoints()"
              fill="none"
              :stroke="getChartColor()"
              stroke-width="1.5"
            />
          </svg>
        </div>
        <div class="sse-table">
          <table>
            <thead>
              <tr>
                <th>时间</th>
                <th>指数</th>
                <th>涨跌</th>
                <th>涨跌</th>
                <th>成交量</th>
                <th>成交额</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in sse30Min.slice(-10)" :key="item.time">
                <td>{{ item.time }}</td>
                <td class="price">{{ item.price }}</td>
                <td :class="getChangeClass(item.change)">{{ item.change }}</td>
                <td :class="getChangeClass(item.change)">{{ item.change_pct }}</td>
                <td>{{ item.volume }}</td>
                <td>{{ item.amount }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    
    <div v-if="updateTime" class="update-time">
      更新于 {{ updateTime }}
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { marketAPI } from '../services/api'

export default {
  name: 'MarketOverview',
  props: {
    showGoldHistory: {
      type: Boolean,
      default: true
    },
    showSSE30Min: {
      type: Boolean,
      default: true
    },
    autoRefresh: {
      type: Boolean,
      default: true
    },
    refreshInterval: {
      type: Number,
      default: 60000
    }
  },
  setup(props) {
    const loading = ref(false)
    const marketIndex = ref([])
    const goldRealtime = ref([])
    const goldHistory = ref([])
    const aVolume = ref([])
    const sse30Min = ref([])
    const updateTime = ref('')
    const goldHistoryExpanded = ref(false)
    const sse30MinExpanded = ref(false)
    let refreshTimer = null
    
    const fetchAll = async () => {
      loading.value = true
      try {
        const response = await marketAPI.getOverview()
        if (response.data.success) {
          const data = response.data
          
          if (data.market_index?.success) {
            marketIndex.value = data.market_index.data
          }
          if (data.gold_realtime?.success) {
            goldRealtime.value = data.gold_realtime.data
          }
          if (data.sector_rank?.success) {
            // 板块数据�?SectorRank 组件单独处理
          }
          if (data.a_volume_7days?.success) {
            aVolume.value = data.a_volume_7days.data
          }
          if (data.sse_30min?.success) {
            sse30Min.value = data.sse_30min.data
          }
          
          updateTime.value = data.update_time
        }
        
        // 单独获取黄金历史（不在overview 中）
        if (props.showGoldHistory) {
          const historyRes = await marketAPI.getGoldHistory(10)
          if (historyRes.data.success) {
            goldHistory.value = historyRes.data.data
          }
        }
      } catch (e) {
        console.error('获取市场数据失败:', e)
      } finally {
        loading.value = false
      }
    }
    
    const getChangeClass = (change) => {
      if (!change) return ''
      const str = String(change)
      if (str.startsWith('-')) return 'down'
      if (str !== '0' && str !== '0%') return 'up'
      return ''
    }
    
    const formatDate = (dateStr) => {
      if (!dateStr) return ''
      const parts = dateStr.split('-')
      return parts.length >= 3 ? `${parts[1]}/${parts[2]}` : dateStr
    }
    
    const getBarHeight = (total) => {
      if (!total) return 0
      const num = parseFloat(total.replace('亿', ''))
      const max = Math.max(...aVolume.value.map(v => parseFloat(v.total.replace('亿', ''))))
      return max > 0 ? (num / max) * 80 : 0
    }
    
    const getChartPoints = () => {
      if (!sse30Min.value.length) return ''
      const prices = sse30Min.value.map(d => parseFloat(d.price))
      const min = Math.min(...prices)
      const max = Math.max(...prices)
      const range = max - min || 1
      
      return sse30Min.value.map((d, i) => {
        const x = (i / (sse30Min.value.length - 1)) * 300
        const y = 55 - ((parseFloat(d.price) - min) / range) * 50
        return `${x},${y}`
      }).join(' ')
    }
    
    const getChartColor = () => {
      if (!sse30Min.value.length) return '#999'
      const first = sse30Min.value[0]
      return first.change && first.change.startsWith('-') ? '#27ae60' : '#e74c3c'
    }
    
    onMounted(() => {
      fetchAll()
      if (props.autoRefresh) {
        refreshTimer = setInterval(fetchAll, props.refreshInterval)
      }
    })
    
    onUnmounted(() => {
      if (refreshTimer) {
        clearInterval(refreshTimer)
      }
    })
    
    return {
      loading,
      marketIndex,
      goldRealtime,
      goldHistory,
      aVolume,
      sse30Min,
      updateTime,
      goldHistoryExpanded,
      sse30MinExpanded,
      fetchAll,
      getChangeClass,
      formatDate,
      getBarHeight,
      getChartPoints,
      getChartColor
    }
  }
}
</script>

<style scoped>
.market-overview-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.market-section {
  background: var(--card-bg, #fff);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color, #eee);
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #333);
}

.refresh-btn, .toggle-btn {
  background: transparent;
  border: 1px solid var(--border-color, #ddd);
  cursor: pointer;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 4px;
  transition: all 0.2s;
  color: var(--text-secondary, #666);
}

.refresh-btn:hover, .toggle-btn:hover {
  background: var(--hover-bg, #f5f5f5);
  border-color: var(--primary-color, #81D8CF);
  color: var(--primary-color, #81D8CF);
}

.spinning {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 指数网格 */
.index-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.index-card {
  background: var(--item-bg, #f9f9f9);
  border-radius: 8px;
  padding: 12px;
  text-align: center;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.index-card.up {
  border-color: rgba(231, 76, 60, 0.3);
  background: rgba(231, 76, 60, 0.05);
}

.index-card.down {
  border-color: rgba(39, 174, 96, 0.3);
  background: rgba(39, 174, 96, 0.05);
}

.index-name {
  font-size: 12px;
  color: var(--text-secondary, #666);
  margin-bottom: 4px;
}

.index-price {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #333);
}

.index-change {
  font-size: 14px;
  font-weight: 500;
  margin-top: 4px;
}

.index-card.up .index-change { color: #e74c3c; }
.index-card.down .index-change { color: #27ae60; }

/* 贵金属网�?*/
.gold-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.gold-card {
  background: var(--item-bg, #f9f9f9);
  border-radius: 8px;
  padding: 14px;
  border-left: 3px solid transparent;
}

.gold-card.up { border-left-color: #e74c3c; }
.gold-card.down { border-left-color: #27ae60; }

.gold-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #333);
  margin-bottom: 6px;
}

.gold-price {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary, #333);
}

.gold-price .unit {
  font-size: 12px;
  font-weight: 400;
  color: var(--text-secondary, #999);
}

.gold-change {
  margin-top: 6px;
  font-size: 14px;
  font-weight: 500;
}

.gold-card.up .gold-change { color: #e74c3c; }
.gold-card.down .gold-change { color: #27ae60; }

.gold-change .pct {
  margin-left: 8px;
}

.gold-detail {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-secondary, #999);
  display: flex;
  gap: 12px;
}

/* 表格样式 */
.history-table, .volume-detail, .sse-table {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

th, td {
  padding: 8px 12px;
  text-align: right;
  border-bottom: 1px solid var(--border-color, #eee);
}

th {
  background: var(--table-header-bg, #f5f5f5);
  font-weight: 600;
  color: var(--text-secondary, #666);
}

th:first-child, td:first-child {
  text-align: left;
}

.highlight {
  font-weight: 600;
  color: var(--primary-color, #81D8CF);
}

.up { color: #e74c3c; }
.down { color: #27ae60; }

/* 成交量柱状图 */
.volume-chart {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.volume-bars {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  height: 100px;
  padding: 10px 0;
  background: var(--item-bg, #f9f9f9);
  border-radius: 8px;
}

.volume-bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.volume-bar {
  width: 30px;
  background: linear-gradient(180deg, #81D8CF 0%, #9FE5DE 100%);
  border-radius: 4px 4px 0 0;
  min-height: 4px;
  display: flex;
  justify-content: center;
  position: relative;
}

.bar-value {
  position: absolute;
  top: -18px;
  font-size: 10px;
  color: var(--text-secondary, #666);
  white-space: nowrap;
}

.bar-date {
  margin-top: 6px;
  font-size: 10px;
  color: var(--text-secondary, #999);
}

/* 上证分时�?*/
.sse-mini-chart {
  height: 60px;
  background: var(--item-bg, #f9f9f9);
  border-radius: 8px;
  padding: 5px;
  margin-bottom: 12px;
}

.price-line {
  width: 100%;
  height: 100%;
}

.empty-state {
  text-align: center;
  padding: 30px;
  color: var(--text-tertiary, #bbb);
}

.update-time {
  text-align: right;
  font-size: 11px;
  color: var(--text-tertiary, #bbb);
}
</style>
