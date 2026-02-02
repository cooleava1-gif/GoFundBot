<template>
  <div class="daily-market-summary">
    <div class="summary-header">
      <div class="header-left">
        <h3>📅 每日市场行情</h3>
        <span class="date">{{ today }}</span>
      </div>
      <div class="header-actions">
        <button v-if="data && !loading" @click="refresh" class="refresh-btn" title="刷新数据">
          <span class="refresh-icon">🔄</span>
          <span class="refresh-text">刷新</span>
        </button>
      </div>
    </div>

    <!-- 加载中状态 - 步骤可视化 -->
    <div v-if="loading" class="loading-container">
      <div class="progress-card">
        <div class="progress-header">
          <div class="pulse-dot"></div>
          <span>正在生成今日市场分析</span>
        </div>
        
        <!-- 步骤列表 -->
        <div class="steps-container">
          <div 
            v-for="step in steps" 
            :key="step.step" 
            class="step-item"
            :class="getStepClass(step.step)"
          >
            <div class="step-indicator">
              <div class="step-circle">
                <span v-if="currentStep > step.step" class="check-icon">✓</span>
                <span v-else-if="currentStep === step.step" class="loading-spinner"></span>
                <span v-else class="step-number">{{ step.step }}</span>
              </div>
              <div v-if="step.step < 3" class="step-line" :class="{ active: currentStep > step.step }"></div>
            </div>
            <div class="step-content">
              <div class="step-name">{{ step.name }}</div>
              <div class="step-description">{{ step.description }}</div>
            </div>
          </div>
        </div>

        <!-- 当前状态消息 -->
        <div class="current-status">
          <div class="status-message">{{ stepMessage }}</div>
          <div class="status-hint">首次生成可能需要30-60秒，请耐心等待...</div>
        </div>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-container">
      <div class="error-card">
        <div class="error-icon">⚠️</div>
        <div class="error-message">{{ error }}</div>
        <button @click="() => fetchData(false)" class="retry-btn">
          <span>🔄</span> 重新生成
        </button>
      </div>
    </div>

    <!-- 数据展示 -->
    <div v-else-if="data" class="summary-content">
      <div class="market-sentiment" :class="sentimentClass">
        <span class="sentiment-icon">{{ sentimentIcon }}</span>
        <span class="sentiment-label">市场情绪：</span>
        <span class="sentiment-value">{{ data.market_sentiment }}</span>
      </div>

      <div class="summary-text">
        <div class="summary-icon">💡</div>
        <div class="summary-body">{{ data.summary }}</div>
      </div>

      <div class="indices-grid">
        <div v-for="(idx, index) in data.indices" :key="index" class="index-card">
          <div class="index-header">
            <span class="index-icon">📊</span>
            <span class="index-name">{{ idx.name }}</span>
          </div>
          <div class="index-change" :class="getChangeClass(idx.change)">{{ idx.change }}</div>
          <div class="index-analysis">{{ idx.analysis }}</div>
        </div>
      </div>

      <div class="sections">
        <div class="section hot-sectors">
          <h4><span class="section-icon">🔥</span> 热门板块</h4>
          <div class="tags">
            <span v-for="(sector, i) in data.hot_sectors" :key="i" class="tag">{{ sector }}</span>
          </div>
        </div>

        <div class="section key-news">
          <h4><span class="section-icon">📰</span> 关键新闻</h4>
          <ul class="news-list">
            <li v-for="(news, i) in data.key_news" :key="i">
              <span class="news-bullet">•</span>
              {{ news }}
            </li>
          </ul>
        </div>
        
        <div class="section outlook">
          <h4><span class="section-icon">🔭</span> 后市展望</h4>
          <p class="outlook-text">{{ data.outlook }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { fundAPI } from '../services/api'

const data = ref(null)
const loading = ref(false)
const error = ref(null)
const currentStep = ref(0)
const stepMessage = ref('正在初始化...')
const steps = ref([
  { step: 1, name: '搜索新闻', description: '获取今日财经资讯' },
  { step: 2, name: 'AI 分析', description: '生成市场分析报告' },
  { step: 3, name: '完成', description: '分析报告已就绪' }
])

const today = new Date().toLocaleDateString('zh-CN', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  weekday: 'long'
})

// 轮询相关
let pollTimer = null
const POLL_INTERVAL = 2500  // 2.5秒轮询一次
const MAX_POLL_COUNT = 120  // 最多轮询120次（5分钟）
let pollCount = 0

const sentimentClass = computed(() => {
  if (!data.value) return ''
  const s = data.value.market_sentiment || ''
  if (s.includes('积极') || s.includes('乐观') || s.includes('看多')) return 'sentiment-positive'
  if (s.includes('恐慌') || s.includes('悲观') || s.includes('看空')) return 'sentiment-negative'
  return 'sentiment-neutral'
})

const sentimentIcon = computed(() => {
  if (!data.value) return '📈'
  const s = data.value.market_sentiment || ''
  if (s.includes('积极') || s.includes('乐观') || s.includes('看多')) return '🚀'
  if (s.includes('恐慌') || s.includes('悲观') || s.includes('看空')) return '📉'
  return '📊'
})

const getStepClass = (step) => {
  if (currentStep.value > step) return 'completed'
  if (currentStep.value === step) return 'active'
  return 'pending'
}

const getChangeClass = (change) => {
  if (!change) return ''
  if (change.includes('+') || change.includes('涨')) return 'change-up'
  if (change.includes('-') || change.includes('跌')) return 'change-down'
  return ''
}

const stopPolling = () => {
  if (pollTimer) {
    clearTimeout(pollTimer)
    pollTimer = null
  }
  pollCount = 0
}

const fetchData = async (forceRefresh = false) => {
  // 如果当前是手动重试且已经失败，重置 error 状态
  if (error.value) {
    error.value = null
  }
  loading.value = true
  
  try {
    const response = await fundAPI.getDailyMarket(forceRefresh)
    
    // 如果返回 200 成功，且不是 loading
    if (response.status === 200 && !response.data.loading) {
      stopPolling()
      data.value = response.data
      loading.value = false
      return
    }

    // 处理加载中状态 (202 或 data 中带 loading)
    if (response.status === 202 || response.data.loading) {
      currentStep.value = response.data.current_step || 1
      stepMessage.value = response.data.step_message || '正在生成...'
      
      pollCount++
      if (pollCount < MAX_POLL_COUNT) {
        // 使用动态间隔：前10次快一些，后面慢一些以减少服务器压力
        const nextInterval = pollCount < 10 ? 2000 : POLL_INTERVAL
        pollTimer = setTimeout(() => fetchData(false), nextInterval)
      } else {
        stopPolling()
        error.value = '行情生成时间较长，请稍后刷新页面查看。'
        loading.value = false
      }
      return
    }

    // 处理后端明确返回的错误
    if (response.data.error) {
      stopPolling()
      error.value = response.data.error
      loading.value = false
      return
    }
    
  } catch (err) {
    // 处理 Axios 错误响应
    const status = err.response?.status
    const responseData = err.response?.data

    if (status === 202 || responseData?.loading) {
      currentStep.value = responseData?.current_step || 1
      stepMessage.value = responseData?.step_message || '正在生成...'
      pollCount++
      if (pollCount < MAX_POLL_COUNT) {
        pollTimer = setTimeout(() => fetchData(false), POLL_INTERVAL)
      } else {
        stopPolling()
        error.value = '请求排队中，请稍后重试'
        loading.value = false
      }
      return
    }

    stopPolling()
    // 这种情况下通常是网络中断或 500 错误
    error.value = '服务器连接异常，请检查网络或后端状态'
    loading.value = false
  }
}

const refresh = () => {
  stopPolling()
  data.value = null
  currentStep.value = 0
  stepMessage.value = '正在初始化...'
  fetchData(true)
}

onMounted(() => {
  fetchData()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.daily-market-summary {
  background: linear-gradient(135deg, #1677ff 0%, #0958d9 100%);
  border-radius: 16px;
  padding: 4px;
  margin: 20px 0;
}

.daily-market-summary > * {
  background: white;
  border-radius: 14px;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px;
  border-bottom: 1px solid #f0f0f0;
  border-radius: 14px 14px 0 0;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 16px;
}

.summary-header h3 {
  margin: 0;
  color: #1a1a2e;
  font-size: 1.5em;
  font-weight: 600;
}

.date {
  color: #666;
  font-size: 0.95em;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, #1677ff 0%, #0958d9 100%);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 0.9em;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(22, 119, 255, 0.3);
}

.refresh-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(22, 119, 255, 0.4);
}

/* ============ 加载状态样式 ============ */
.loading-container {
  padding: 40px 28px;
  border-radius: 0 0 14px 14px;
}

.progress-card {
  max-width: 500px;
  margin: 0 auto;
}

.progress-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 32px;
  font-size: 1.2em;
  font-weight: 500;
  color: #333;
}

.pulse-dot {
  width: 12px;
  height: 12px;
  background: linear-gradient(135deg, #1677ff 0%, #0958d9 100%);
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.7; }
}

.steps-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 32px;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 12px 16px;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.step-item.active {
  background: linear-gradient(135deg, rgba(22, 119, 255, 0.1) 0%, rgba(9, 88, 217, 0.1) 100%);
}

.step-item.completed {
  opacity: 0.7;
}

.step-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.step-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.9em;
  transition: all 0.3s ease;
}

.step-item.pending .step-circle {
  background: #f0f0f0;
  color: #999;
}

.step-item.active .step-circle {
  background: linear-gradient(135deg, #1677ff 0%, #0958d9 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(22, 119, 255, 0.4);
}

.step-item.completed .step-circle {
  background: #52c41a;
  color: white;
}

.check-icon {
  font-size: 1.1em;
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.step-line {
  width: 2px;
  height: 24px;
  background: #e0e0e0;
  margin-top: 4px;
  transition: background 0.3s ease;
}

.step-line.active {
  background: #52c41a;
}

.step-content {
  flex: 1;
  padding-top: 6px;
}

.step-name {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.step-item.pending .step-name {
  color: #999;
}

.step-description {
  font-size: 0.85em;
  color: #888;
}

.current-status {
  text-align: center;
  padding: 20px;
  background: #fafafa;
  border-radius: 12px;
}

.status-message {
  color: #1677ff;
  font-weight: 500;
  margin-bottom: 8px;
}

.status-hint {
  font-size: 0.85em;
  color: #999;
}

/* ============ 错误状态样式 ============ */
.error-container {
  padding: 40px 28px;
  border-radius: 0 0 14px 14px;
}

.error-card {
  max-width: 400px;
  margin: 0 auto;
  text-align: center;
  padding: 32px;
  background: #fff5f5;
  border-radius: 12px;
  border: 1px solid #ffccc7;
}

.error-icon {
  font-size: 3em;
  margin-bottom: 16px;
}

.error-message {
  color: #cf1322;
  margin-bottom: 20px;
  line-height: 1.6;
}

.retry-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #ff4d4f;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 10px 24px;
  cursor: pointer;
  font-size: 1em;
  transition: all 0.3s ease;
}

.retry-btn:hover {
  background: #ff7875;
  transform: translateY(-2px);
}

/* ============ 数据展示样式 ============ */
.summary-content {
  padding: 28px;
  border-radius: 0 0 14px 14px;
}

.market-sentiment {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 24px;
  margin-bottom: 24px;
  font-weight: 600;
  font-size: 1.1em;
}

.sentiment-icon {
  font-size: 1.2em;
}

.sentiment-positive { 
  background: linear-gradient(135deg, #f6ffed 0%, #d9f7be 100%);
  color: #389e0d;
  border: 1px solid #b7eb8f;
}

.sentiment-negative { 
  background: linear-gradient(135deg, #fff1f0 0%, #ffccc7 100%);
  color: #cf1322;
  border: 1px solid #ffa39e;
}

.sentiment-neutral { 
  background: linear-gradient(135deg, #f0f5ff 0%, #d6e4ff 100%);
  color: #1890ff;
  border: 1px solid #91d5ff;
}

.summary-text {
  display: flex;
  gap: 16px;
  padding: 20px 24px;
  background: linear-gradient(135deg, #f8f9ff 0%, #f0f5ff 100%);
  border-radius: 12px;
  margin-bottom: 28px;
  border-left: 4px solid #1677ff;
}

.summary-icon {
  font-size: 1.5em;
  flex-shrink: 0;
}

.summary-body {
  font-size: 1.15em;
  line-height: 1.8;
  color: #333;
}

.indices-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 28px;
}

.index-card {
  background: #fafafa;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  border: 1px solid #f0f0f0;
  transition: all 0.3s ease;
}

.index-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}

.index-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 12px;
}

.index-icon {
  font-size: 1.2em;
}

.index-name { 
  font-weight: 600;
  font-size: 1.1em;
  color: #333;
}

.index-change { 
  font-weight: 700;
  font-size: 1.3em;
  margin-bottom: 12px;
  color: #666;
}

.index-change.change-up {
  color: #cf1322;
}

.index-change.change-down {
  color: #389e0d;
}

.index-analysis { 
  font-size: 0.9em;
  color: #666;
  line-height: 1.5;
}

.sections {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

.section {
  background: #fafafa;
  padding: 20px 24px;
  border-radius: 12px;
}

.section h4 {
  margin: 0 0 16px 0;
  color: #333;
  font-size: 1.15em;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-icon {
  font-size: 1.1em;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag {
  background: linear-gradient(135deg, #1677ff 0%, #0958d9 100%);
  color: white;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.95em;
  font-weight: 500;
}

.news-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.news-list li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 12px;
  line-height: 1.6;
  color: #555;
}

.news-bullet {
  color: #1677ff;
  font-weight: bold;
  flex-shrink: 0;
}

.outlook-text {
  margin: 0;
  line-height: 1.8;
  color: #555;
}

/* 响应式 */
@media (max-width: 768px) {
  .summary-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .header-left {
    flex-direction: column;
    gap: 8px;
  }
  
  .indices-grid {
    grid-template-columns: 1fr;
  }
  
  .sections {
    grid-template-columns: 1fr;
  }
}
</style>
