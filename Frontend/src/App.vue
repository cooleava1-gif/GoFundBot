<!-- src/App.vue -->
<template>
  <div id="app">
    <header class="app-header">
      <h1>💰 基金分析系统</h1>
      <p>专业的基金数据分析工具</p>
    </header>
    
    <main class="app-main">
      <FundSearch @fund-selected="handleFundSelected" />
      <FundDetail v-if="selectedFundCode" :fundCode="selectedFundCode" />
      <div v-else class="welcome">
        <p>请在搜索框中输入基金代码或名称开始分析</p>
      </div>
    </main>
    
    <footer class="app-footer">
      <p>数据来源：天天基金 | 更新时间：{{ currentTime }}</p>
    </footer>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import FundSearch from './components/FundSearch.vue'
import FundDetail from './components/FundDetail.vue'

export default {
  name: 'App',
  components: {
    FundSearch,
    FundDetail
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
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  font-size: 2.2rem;
  margin-bottom: 8px;
}

.app-header p {
  opacity: 0.9;
  font-size: 1rem;
}

.app-main {
  flex: 1;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 20px;
}

.welcome {
  text-align: center;
  padding: 60px 20px;
  color: #7f8c8d;
  background: #f8f9fa;
  border-radius: 8px;
  margin-top: 20px;
  border: 2px dashed #dee2e6;
}

.welcome p {
  font-size: 1.2rem;
  margin-bottom: 20px;
}

.app-footer {
  background: #f8f9fa;
  text-align: center;
  padding: 15px;
  border-top: 1px solid #e9ecef;
  font-size: 0.9rem;
  color: #6c757d;
}
</style>