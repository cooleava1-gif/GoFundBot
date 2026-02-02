<!-- src/App.vue -->
<template>
  <div id="app">
    <header class="app-header">
      <div class="header-content">
        <div class="header-left">
          <h1>GoFundBot</h1>
          <p>智能基金分析 · 实时市场追踪</p>
        </div>
        <!-- 模式切换 -->
        <div class="header-right">
          <div class="mode-switch">
            <button 
              class="mode-btn" 
              :class="{ active: viewMode === 'dashboard' }"
              @click="viewMode = 'dashboard'"
            >
              🏠 市场大盘
            </button>
            <button 
              class="mode-btn" 
              :class="{ active: viewMode === 'detail' }"
              @click="viewMode = 'detail'"
            >
              📋 基金详情
            </button>
            <button 
              class="mode-btn" 
              :class="{ active: viewMode === 'screening' }"
              @click="viewMode = 'screening'"
            >
              🔍 基金筛选
            </button>
            <button 
              class="mode-btn" 
              :class="{ active: viewMode === 'compare' }"
              @click="viewMode = 'compare'"
            >
              📈 基金对比
            </button>
            <button 
              class="mode-btn" 
              :class="{ active: viewMode === 'backtest' }"
              @click="viewMode = 'backtest'"
            >
              💰 定投回测
            </button>
          </div>
        </div>
      </div>
    </header>
    
    <main class="app-main">
      <!-- 市场大盘模式 -->
      <div v-if="viewMode === 'dashboard'" class="dashboard-layout">
        <!-- 左侧：自选列表 -->
        <aside class="dashboard-sidebar">
          <FundWatchlist 
            @view-fund="handleDashboardFundView" 
            @add-to-compare="handleAddToCompare"
            :compareMode="false"
            :compareFunds="compareFunds"
          />
        </aside>
        
        <!-- 中间：核心内容 -->
        <div class="dashboard-main">
          <!-- 市场指数 + 金价 -->
          <MarketOverview 
            :showGoldHistory="true" 
            :showSSE30Min="true"
          />
        </div>
        
        <!-- 右侧：快讯 + 板块 -->
        <aside class="dashboard-right">
          <FlashNews :count="15" :refreshInterval="60000" />
          <SectorRank :limit="50" :initialDisplay="12" />
        </aside>
      </div>

      <!-- 其他模式 -->
      <div v-else class="main-layout">
        <!-- 左侧：自选列表 (非筛选模式显示) -->
        <aside class="sidebar-left" v-if="viewMode !== 'screening'">
          <FundWatchlist 
            @view-fund="handleFundSelected" 
            @add-to-compare="handleAddToCompare"
            :compareMode="viewMode === 'compare'"
            :compareFunds="compareFunds"
          />
        </aside>
        
        <!-- 右侧：根据模式显示不同内容 -->
        <div class="content-area" :class="{ 'full-width': viewMode === 'screening' }">
          <!-- 筛选模式 -->
          <template v-if="viewMode === 'screening'">
            <FundScreening 
              @view-fund="handleScreeningFundView"
              @add-to-compare="handleAddToCompare"
            />
          </template>
          
          <!-- 对比模式 -->
          <template v-else-if="viewMode === 'compare'">
            <FundComparison 
              :compareFunds="compareFunds"
              @remove-fund="handleRemoveFromCompare"
              @clear-funds="handleClearCompare"
            />
          </template>
          
          <!-- 回测模式 -->
          <template v-else-if="viewMode === 'backtest'">
            <FundBacktest 
              :fundCode="selectedFundCode"
            />
          </template>

          <!-- 详情模式 -->
          <template v-else>
            <FundSearch @fund-selected="handleFundSelected" />
            <FundDetail v-if="selectedFundCode" :fundCode="selectedFundCode" />
            <div v-else class="welcome-container">
              <div class="welcome-icon">🔍</div>
              <h3>搜索基金开始分析</h3>
              <p>在上方搜索框输入基金代码或名称</p>
            </div>
          </template>
        </div>
      </div>
    </main>
    
    <footer class="app-footer">
      <p>数据来源：天天基金 / 东方财富 / 百度股市通 | 更新时间：{{ currentTime }}</p>
    </footer>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import FundSearch from './components/FundSearch.vue'
import FundDetail from './components/FundDetail.vue'
import FundWatchlist from './components/FundWatchlist.vue'
import FundComparison from './components/FundComparison.vue'
import FundScreening from './components/FundScreening.vue'
import FundBacktest from './components/FundBacktest.vue'
import MarketOverview from './components/MarketOverview.vue'
import FlashNews from './components/FlashNews.vue'
import SectorRank from './components/SectorRank.vue'

export default {
  name: 'App',
  components: {
    FundSearch,
    FundDetail,
    FundWatchlist,
    FundComparison,
    FundScreening,
    FundBacktest,
    MarketOverview,
    FlashNews,
    SectorRank
  },
  setup() {
    const selectedFundCode = ref('')
    const currentTime = ref('')
    const viewMode = ref('dashboard') // 默认显示市场大盘
    const compareFunds = ref([]) // 用于对比的基金列表
    
    const handleFundSelected = (fundOrCode) => {
      if (fundOrCode && typeof fundOrCode === 'object') {
        selectedFundCode.value = fundOrCode.CODE || fundOrCode.fund_code || fundOrCode.code
      } else {
        selectedFundCode.value = fundOrCode
      }
    }
    
    // 从仪表盘点击基金，切换到详情模式
    const handleDashboardFundView = (fundOrCode) => {
      handleFundSelected(fundOrCode)
      viewMode.value = 'detail'
    }
    
    // 从筛选页面查看基金详情
    const handleScreeningFundView = (fundCode) => {
      selectedFundCode.value = fundCode
      viewMode.value = 'detail'
    }
    
    // 添加基金到对比列表
    const handleAddToCompare = (fund) => {
      // 最多5只基金
      if (compareFunds.value.length >= 5) {
        alert('最多只能对比5只基金')
        return
      }
      // 检查是否已存在
      if (compareFunds.value.some(f => f.code === fund.code)) {
        // 如果已存在则移除
        compareFunds.value = compareFunds.value.filter(f => f.code !== fund.code)
        return
      }
      compareFunds.value.push({
        code: fund.code,
        name: fund.name
      })
    }
    
    // 从对比列表移除基金
    const handleRemoveFromCompare = (fundCode) => {
      compareFunds.value = compareFunds.value.filter(f => f.code !== fundCode)
    }
    
    // 清空对比列表
    const handleClearCompare = () => {
      compareFunds.value = []
    }
    
    // 更新时间
    const updateTime = () => {
      const now = new Date()
      currentTime.value = now.toLocaleString('zh-CN')
    }
    
    onMounted(() => {
      updateTime()
      // 每分钟更新时间
      setInterval(updateTime, 60000)
    })
    
    return {
      selectedFundCode,
      currentTime,
      viewMode,
      compareFunds,
      handleFundSelected,
      handleDashboardFundView,
      handleScreeningFundView,
      handleAddToCompare,
      handleRemoveFromCompare,
      handleClearCompare
    }
  }
}
</script>

<style>
:root {
  --primary-color: #1677ff;
  --primary-gradient: linear-gradient(135deg, #1677ff 0%, #0958d9 100%);
  --success-color: #52c41a;
  --danger-color: #ff4d4f;
  --warning-color: #faad14;
  --text-primary: #1f2937;
  --text-secondary: #6b7280;
  --text-tertiary: #9ca3af;
  --bg-primary: #f8fafc;
  --bg-card: #ffffff;
  --border-color: #e5e7eb;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--text-primary);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

.app-header {
  background: var(--primary-gradient);
  color: white;
  padding: 12px 24px;
  box-shadow: var(--shadow-md);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1920px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left h1 {
  font-size: 1.6rem;
  font-weight: 700;
  margin-bottom: 2px;
  letter-spacing: -0.5px;
}

.header-left p {
  opacity: 0.85;
  font-size: 0.85rem;
}

.header-right {
  display: flex;
  align-items: center;
}

.mode-switch {
  display: flex;
  gap: 6px;
  background: rgba(255, 255, 255, 0.12);
  padding: 4px;
  border-radius: var(--radius-md);
}

.mode-btn {
  padding: 8px 14px;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  background: transparent;
  color: rgba(255, 255, 255, 0.75);
  transition: all 0.2s ease;
  white-space: nowrap;
}

.mode-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.mode-btn.active {
  background: white;
  color: var(--primary-color);
  box-shadow: var(--shadow-sm);
}

.app-main {
  flex: 1;
  max-width: 1920px;
  width: 100%;
  margin: 0 auto;
  padding: 20px;
}

/* ==================== 仪表盘布局 ==================== */
.dashboard-layout {
  display: grid;
  grid-template-columns: 320px 1fr 380px;
  gap: 20px;
  min-height: calc(100vh - 140px);
}

.dashboard-sidebar {
  position: sticky;
  top: 80px;
  height: fit-content;
  max-height: calc(100vh - 100px);
  overflow-y: auto;
}

.dashboard-main {
  min-width: 0;
}

.dashboard-right {
  display: flex;
  flex-direction: column;
  gap: 20px;
  position: sticky;
  top: 80px;
  height: fit-content;
  max-height: calc(100vh - 100px);
  overflow-y: auto;
}

/* ==================== 原有布局 ==================== */
.main-layout {
  display: flex;
  gap: 20px;
  min-height: calc(100vh - 160px);
}

.sidebar-left {
  width: 360px;
  flex-shrink: 0;
}

.content-area {
  flex: 1;
  min-width: 0;
}

.content-area.full-width {
  width: 100%;
}

/* ==================== 欢迎页面 ==================== */
.welcome-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 40px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  margin-top: 20px;
  box-shadow: var(--shadow-md);
  text-align: center;
}

.welcome-icon {
  font-size: 48px;
  margin-bottom: 16px;
  background: linear-gradient(135deg, #1677ff20 0%, #0958d920 100%);
  width: 80px;
  height: 80px;
  line-height: 80px;
  border-radius: 50%;
}

.welcome-container h3 {
  font-size: 1.4rem;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.welcome-container p {
  color: var(--text-secondary);
  font-size: 0.95rem;
}

/* ==================== 页脚 ==================== */
.app-footer {
  background: var(--bg-card);
  text-align: center;
  padding: 12px;
  border-top: 1px solid var(--border-color);
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

/* ==================== 响应式设计 ==================== */
@media (max-width: 1400px) {
  .dashboard-layout {
    grid-template-columns: 280px 1fr 340px;
  }
}

@media (max-width: 1200px) {
  .dashboard-layout {
    grid-template-columns: 1fr 340px;
  }
  
  .dashboard-sidebar {
    display: none;
  }
}

@media (max-width: 1024px) {
  .main-layout {
    flex-direction: column;
  }
  
  .sidebar-left {
    width: 100%;
  }
  
  .dashboard-layout {
    grid-template-columns: 1fr;
  }
  
  .dashboard-right {
    position: static;
    max-height: none;
  }
  
  .mode-switch {
    flex-wrap: wrap;
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .app-header {
    padding: 10px 16px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 12px;
  }
  
  .header-left {
    text-align: center;
  }
  
  .mode-btn {
    padding: 6px 10px;
    font-size: 12px;
  }
  
  .app-main {
    padding: 12px;
  }
}

/* ==================== 滚动条美化 ==================== */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>