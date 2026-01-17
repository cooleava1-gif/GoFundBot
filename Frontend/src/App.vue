<!-- src/App.vue -->
<template>
  <div id="app">
    <header class="app-header">
      <div class="header-content">
        <div class="header-left">
          <h1>GoFundBot</h1>
          <p>一个有趣的基金分析机器人</p>
        </div>
      </div>
    </header>
    
    <main class="app-main">
      <div class="main-layout">
        <!-- 左侧：自选列表 -->
        <aside class="sidebar-left">
          <FundWatchlist @view-fund="handleFundSelected" />
        </aside>
        
        <!-- 右侧：搜索和详情 -->
        <div class="content-area">
          <FundSearch @fund-selected="handleFundSelected" />
          <FundDetail v-if="selectedFundCode" :fundCode="selectedFundCode" />
          <div v-else class="welcome">
            <div class="welcome-icon">📊</div>
            <p>请在搜索框中输入基金代码或名称</p>
            <p class="welcome-hint">或从左侧自选列表中选择基金开始分析</p>
          </div>
        </div>
      </div>
    </main>
    
    <footer class="app-footer">
      <p>数据来源：天天基金 | 更新时间：{{ currentTime }}</p>
    </footer>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import FundSearch from './components/FundSearch.vue'
import FundDetail from './components/FundDetail.vue'
import FundWatchlist from './components/FundWatchlist.vue'

export default {
  name: 'App',
  components: {
    FundSearch,
    FundDetail,
    FundWatchlist
  },
  setup() {
    const selectedFundCode = ref('')
    const currentTime = ref('')
    
    const handleFundSelected = (fundCode) => {
      selectedFundCode.value = fundCode
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
      handleFundSelected
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 15px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-content {
  max-width: 1600px;
  margin: 0 auto;
}

.header-left h1 {
  font-size: 1.8rem;
  margin-bottom: 2px;
}

.header-left p {
  opacity: 0.9;
  font-size: 0.9rem;
}

.app-main {
  flex: 1;
  max-width: 1600px;
  width: 100%;
  margin: 0 auto;
  padding: 20px;
}

/* 主布局：左侧自选 + 右侧内容 */
.main-layout {
  display: flex;
  gap: 20px;
  min-height: calc(100vh - 160px);
}

/* 左侧边栏 */
.sidebar-left {
  width: 360px;
  flex-shrink: 0;
}

/* 右侧内容区 */
.content-area {
  flex: 1;
  min-width: 0;
}

.welcome {
  text-align: center;
  padding: 80px 20px;
  color: #7f8c8d;
  background: white;
  border-radius: 12px;
  margin-top: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.welcome-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.welcome p {
  font-size: 1.1rem;
  margin-bottom: 8px;
}

.welcome-hint {
  font-size: 0.9rem !important;
  color: #9ca3af;
}

.app-footer {
  background: white;
  text-align: center;
  padding: 12px;
  border-top: 1px solid #e9ecef;
  font-size: 0.85rem;
  color: #6c757d;
}

/* 响应式：小屏幕时自选列表折叠或在上方 */
@media (max-width: 1024px) {
  .main-layout {
    flex-direction: column;
  }
  
  .sidebar-left {
    width: 100%;
  }
}
</style>