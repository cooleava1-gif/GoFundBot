<!-- 行业板块排行组件 -->
<template>
  <div class="sector-rank-container">
    <div class="section-header">
      <h3>🏭 行业板块排行</h3>
      <div class="header-actions">
        <select v-model="sortBy" class="sort-select" @change="sortData">
          <option value="change">按涨跌幅</option>
          <option value="inflow">按主力流入</option>
        </select>
        <button class="refresh-btn" @click="fetchSectors" :disabled="loading">
          <span :class="{ 'spinning': loading }">🔄</span>
        </button>
      </div>
    </div>
    
    <div v-if="loading && !sectors.length" class="loading-state">
      <span class="loading-spinner"></span>
      <span>加载中...</span>
    </div>
    
    <div v-else-if="error" class="error-state">
      <span>{{ error }}</span>
      <button @click="fetchSectors">重试</button>
    </div>
    
    <div v-else class="sector-content">
      <!-- 涨跌分布概览 -->
      <div class="overview-bar" v-if="sectors.length">
        <div class="bar-section up" :style="{ width: upPercent + '%' }">
          <span v-if="upPercent > 15">{{ upCount }}</span>
        </div>
        <div class="bar-section flat" :style="{ width: flatPercent + '%' }">
          <span v-if="flatPercent > 10">{{ flatCount }}</span>
        </div>
        <div class="bar-section down" :style="{ width: downPercent + '%' }">
          <span v-if="downPercent > 15">{{ downCount }}</span>
        </div>
      </div>
      
      <!-- 板块列表 -->
      <div class="sector-list">
        <div 
          v-for="(sector, index) in displayedSectors" 
          :key="sector.name"
          class="sector-item"
          :class="{ 
            'up': sector.raw_change > 0,
            'down': sector.raw_change < 0
          }"
        >
          <div class="sector-rank">{{ index + 1 }}</div>
          <div class="sector-info">
            <div class="sector-name">{{ sector.name }}</div>
            <div class="sector-flow">
              <span class="label">主力:</span>
              <span :class="getFlowClass(sector.main_inflow)">{{ sector.main_inflow }}</span>
              <span class="pct">({{ sector.main_inflow_pct }})</span>
            </div>
          </div>
          <div class="sector-change" :class="{ 'up': sector.raw_change > 0, 'down': sector.raw_change < 0 }">
            {{ sector.change_pct }}
          </div>
        </div>
      </div>
      
      <!-- 展开/收起按钮 -->
      <div class="expand-toggle" v-if="sectors.length > initialDisplay">
        <button @click="expanded = !expanded">
          {{ expanded ? '收起' : `展开全部 (${sectors.length})` }}
          <span class="arrow" :class="{ 'expanded': expanded }">▼</span>
        </button>
      </div>
    </div>
    
    <div v-if="updateTime" class="update-time">
      更新于{{ updateTime }}
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { marketAPI } from '../services/api'

export default {
  name: 'SectorRank',
  props: {
    limit: {
      type: Number,
      default: 50
    },
    initialDisplay: {
      type: Number,
      default: 15
    },
    autoRefresh: {
      type: Boolean,
      default: true
    },
    refreshInterval: {
      type: Number,
      default: 300000 // 5分钟
    }
  },
  setup(props) {
    const sectors = ref([])
    const loading = ref(false)
    const error = ref(null)
    const updateTime = ref('')
    const expanded = ref(false)
    const sortBy = ref('change')
    let refreshTimer = null
    
    const fetchSectors = async () => {
      loading.value = true
      error.value = null
      
      try {
        const response = await marketAPI.getSectorRank(props.limit)
        if (response.data.success) {
          sectors.value = response.data.data
          updateTime.value = response.data.update_time
          sortData()
        } else {
          error.value = response.data.error || '获取板块数据失败'
        }
      } catch (e) {
        error.value = '网络错误，请稍后重试'
        console.error('获取板块排行失败:', e)
      } finally {
        loading.value = false
      }
    }
    
    const sortData = () => {
      if (sortBy.value === 'change') {
        sectors.value.sort((a, b) => b.raw_change - a.raw_change)
      } else {
        sectors.value.sort((a, b) => b.raw_main_inflow - a.raw_main_inflow)
      }
    }
    
    const displayedSectors = computed(() => {
      if (expanded.value) return sectors.value
      return sectors.value.slice(0, props.initialDisplay)
    })
    
    // 涨跌分布统计
    const upCount = computed(() => sectors.value.filter(s => s.raw_change > 0).length)
    const downCount = computed(() => sectors.value.filter(s => s.raw_change < 0).length)
    const flatCount = computed(() => sectors.value.filter(s => s.raw_change === 0).length)
    const total = computed(() => sectors.value.length || 1)
    
    const upPercent = computed(() => (upCount.value / total.value) * 100)
    const downPercent = computed(() => (downCount.value / total.value) * 100)
    const flatPercent = computed(() => (flatCount.value / total.value) * 100)
    
    const getFlowClass = (flow) => {
      if (!flow) return ''
      if (flow.startsWith('-')) return 'outflow'
      return 'inflow'
    }
    
    onMounted(() => {
      fetchSectors()
      if (props.autoRefresh) {
        refreshTimer = setInterval(fetchSectors, props.refreshInterval)
      }
    })
    
    onUnmounted(() => {
      if (refreshTimer) {
        clearInterval(refreshTimer)
      }
    })
    
    return {
      sectors,
      loading,
      error,
      updateTime,
      expanded,
      sortBy,
      displayedSectors,
      upCount,
      downCount,
      flatCount,
      upPercent,
      downPercent,
      flatPercent,
      fetchSectors,
      sortData,
      getFlowClass
    }
  }
}
</script>

<style scoped>
.sector-rank-container {
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

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.sort-select {
  padding: 4px 8px;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 4px;
  font-size: 12px;
  background: var(--card-bg, #fff);
  color: var(--text-secondary, #666);
  cursor: pointer;
}

.refresh-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 16px;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.refresh-btn:hover {
  background: var(--hover-bg, #f5f5f5);
}

.spinning {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 涨跌分布�?*/
.overview-bar {
  display: flex;
  height: 24px;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 16px;
}

.bar-section {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 500;
  color: #fff;
  transition: width 0.3s;
}

.bar-section.up {
  background: linear-gradient(90deg, #e74c3c, #c0392b);
}

.bar-section.flat {
  background: #95a5a6;
}

.bar-section.down {
  background: linear-gradient(90deg, #27ae60, #1e8449);
}

/* 板块列表 */
.sector-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 500px;
  overflow-y: auto;
}

.sector-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  background: var(--item-bg, #f9f9f9);
  border-radius: 8px;
  transition: all 0.2s;
  border-left: 3px solid transparent;
}

.sector-item:hover {
  background: var(--item-hover-bg, #f0f0f0);
}

.sector-item.up {
  border-left-color: #e74c3c;
}

.sector-item.down {
  border-left-color: #27ae60;
}

.sector-rank {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--rank-bg, #e8e8e8);
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary, #666);
  margin-right: 12px;
}

.sector-item:nth-child(1) .sector-rank {
  background: #ffd700;
  color: #fff;
}

.sector-item:nth-child(2) .sector-rank {
  background: #c0c0c0;
  color: #fff;
}

.sector-item:nth-child(3) .sector-rank {
  background: #cd7f32;
  color: #fff;
}

.sector-info {
  flex: 1;
}

.sector-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #333);
  margin-bottom: 2px;
}

.sector-flow {
  font-size: 12px;
  color: var(--text-secondary, #999);
}

.sector-flow .label {
  margin-right: 4px;
}

.sector-flow .inflow {
  color: #e74c3c;
}

.sector-flow .outflow {
  color: #27ae60;
}

.sector-flow .pct {
  margin-left: 4px;
  color: var(--text-tertiary, #bbb);
}

.sector-change {
  font-size: 16px;
  font-weight: 600;
  min-width: 70px;
  text-align: right;
}

.sector-change.up {
  color: #e74c3c;
}

.sector-change.down {
  color: #27ae60;
}

/* 展开按钮 */
.expand-toggle {
  margin-top: 12px;
  text-align: center;
}

.expand-toggle button {
  background: transparent;
  border: 1px solid var(--border-color, #ddd);
  padding: 8px 20px;
  border-radius: 20px;
  font-size: 13px;
  color: var(--text-secondary, #666);
  cursor: pointer;
  transition: all 0.2s;
}

.expand-toggle button:hover {
  background: var(--hover-bg, #f5f5f5);
  border-color: var(--primary-color, #81D8CF);
  color: var(--primary-color, #81D8CF);
}

.arrow {
  display: inline-block;
  margin-left: 4px;
  transition: transform 0.2s;
}

.arrow.expanded {
  transform: rotate(180deg);
}

/* 状�?*/
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--text-secondary, #999);
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border-color, #eee);
  border-top-color: var(--primary-color, #81D8CF);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 8px;
}

.error-state button {
  margin-top: 12px;
  padding: 6px 16px;
  background: var(--primary-color, #81D8CF);
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.update-time {
  margin-top: 12px;
  text-align: right;
  font-size: 11px;
  color: var(--text-tertiary, #bbb);
}
</style>
