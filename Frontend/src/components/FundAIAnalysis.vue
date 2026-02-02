<template>
  <div class="fund-ai-analysis card">
    <div class="header">
      <div class="title-area">
        <span class="icon">🤖</span>
        <h3>AI 智能分析</h3>
        <span class="badge" v-if="data">已分析</span>
      </div>
      <div class="header-actions">
        <button v-if="!loading" @click="analyze" class="analyze-btn" :class="{ 'has-data': data }">
          <span class="btn-icon">{{ data ? '🔄' : '✨' }}</span>
          {{ data ? '重新分析' : '开始分析' }}
        </button>
        <button class="close-btn" @click="$emit('close')" title="关闭">×</button>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="loading-animation">
        <div class="spinner"></div>
        <div class="loading-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
      <p class="loading-text">AI 正在深度分析基金表现(可能需要2-3分钟)...</p>
      <p class="loading-sub">结合市场数据、基金业绩、持仓结构进行综合评估</p>
    </div>

    <div v-else-if="error" class="error">
      <span class="error-icon">⚠️</span>
      <p>{{ error }}</p>
      <button @click="analyze" class="retry-btn">重试</button>
    </div>

    <div v-else-if="data" class="analysis-content">
      <!-- 核心评分卡 -->
      <div class="score-section">
        <div class="score-card" :class="scoreColorClass">
          <div class="score-ring">
            <svg viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="45" fill="none" stroke="#e8e8e8" stroke-width="8"/>
              <circle cx="50" cy="50" r="45" fill="none" :stroke="scoreColor" stroke-width="8"
                      :stroke-dasharray="scoreProgress" stroke-linecap="round"
                      transform="rotate(-90 50 50)"/>
            </svg>
            <div class="score-value">{{ data.sentiment_score }}</div>
          </div>
          <div class="score-label">综合评分</div>
        </div>
        <div class="advice-card" :class="adviceClass">
          <div class="advice-icon">{{ adviceIcon }}</div>
          <div class="advice-text">{{ data.operation_advice }}</div>
        </div>
      </div>

      <!-- 分析摘要 -->
      <div class="summary-section">
        <p>{{ data.summary }}</p>
      </div>

      <!-- 仪表盘 -->
      <div class="dashboard-grid">
        <div class="dash-item" v-for="(item, key) in dashboardItems" :key="key">
          <div class="dash-icon">{{ item.icon }}</div>
          <div class="dash-content">
            <label>{{ item.label }}</label>
            <span :class="getEvalClass(data.dashboard[key])">{{ data.dashboard[key] }}</span>
          </div>
        </div>
      </div>

      <!-- 亮点与风险 -->
      <div class="details-grid">
        <div class="detail-col highlights">
          <h4><span class="col-icon">✅</span> 投资亮点</h4>
          <ul>
            <li v-for="(item, i) in data.highlights" :key="i">
              <span class="bullet">•</span>{{ item }}
            </li>
          </ul>
        </div>
        <div class="detail-col risks">
          <h4><span class="col-icon">⚠️</span> 风险提示</h4>
          <ul>
            <li v-for="(item, i) in data.risk_factors" :key="i">
              <span class="bullet">•</span>{{ item }}
            </li>
          </ul>
        </div>
      </div>
      
      <!-- 实时情报 -->
      <div class="news-section" v-if="data.news_intel && data.news_intel.length">
        <h4><span class="col-icon">📰</span> 实时情报</h4>
        <ul>
          <li v-for="(news, i) in data.news_intel" :key="i">{{ news }}</li>
        </ul>
      </div>

      <!-- 深度分析报告 -->
      <div class="detailed-report" v-if="data.detailed_report">
        <div class="report-header">
          <span class="report-icon">📑</span>
          <h4>深度分析报告</h4>
        </div>
        <div class="markdown-content" v-html="parsedReport"></div>
      </div>

      <!-- 免责声明 -->
      <div class="disclaimer">
        💡 以上分析由 AI 生成，仅供参考，不构成投资建议。投资有风险，入市需谨慎。
      </div>
    </div>
    
    <div v-else class="empty-state">
      <div class="empty-icon">🔮</div>
      <p class="empty-title">点击上方按钮，获取 AI 对该基金的实时深度分析报告</p>
      <p class="empty-sub">分析内容包括：业绩评价、经理能力、持仓分析、后市展望等</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { fundAPI } from '../services/api'

const props = defineProps({
  fundCode: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['close', 'analysis-complete'])

const data = ref(null)
const loading = ref(false)
const error = ref(null)

// 监听数据变化，分析完成后通知父组件
watch(data, (newVal) => {
  if (newVal) {
    emit('analysis-complete', newVal)
  }
})

// 仪表盘配置
const dashboardItems = {
  performance_eval: { label: '业绩评价', icon: '📈' },
  manager_ability: { label: '经理能力', icon: '👨‍💼' },
  position_analysis: { label: '持仓结构', icon: '📊' },
  market_outlook: { label: '后市展望', icon: '🔮' }
}

// 评分颜色类
const scoreColorClass = computed(() => {
  if (!data.value) return ''
  const s = data.value.sentiment_score
  if (s >= 80) return 'score-excellent'
  if (s >= 60) return 'score-good'
  if (s >= 40) return 'score-normal'
  return 'score-poor'
})

// 评分颜色
const scoreColor = computed(() => {
  if (!data.value) return '#1677ff'
  const s = data.value.sentiment_score
  if (s >= 80) return '#52c41a'
  if (s >= 60) return '#1677ff'
  if (s >= 40) return '#faad14'
  return '#f5222d'
})

// 评分进度（SVG 圆环）
const scoreProgress = computed(() => {
  if (!data.value) return '0 283'
  const progress = (data.value.sentiment_score / 100) * 283
  return `${progress} 283`
})

// 解析 Markdown
const parsedReport = computed(() => {
  if (!data.value || !data.value.detailed_report) return ''
  const lines = data.value.detailed_report.split('\n')
  let html = ''
  let inList = false
  
  lines.forEach(line => {
    line = line.trim()
    if (!line) return
    
    // Header 3
    if (line.startsWith('### ')) {
      if (inList) { html += '</ul>'; inList = false; }
      html += `<h4>${line.substring(4)}</h4>`
    }
    // Header 2
    else if (line.startsWith('## ')) {
      if (inList) { html += '</ul>'; inList = false; }
      html += `<h3>${line.substring(3)}</h3>`
    }
    // List item
    else if (line.startsWith('- ') || line.startsWith('* ')) {
      if (!inList) { html += '<ul>'; inList = true; }
      let content = line.substring(2)
      // Bold
      content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      html += `<li>${content}</li>`
    }
    // Paragraph
    else {
      if (inList) { html += '</ul>'; inList = false; }
      let content = line
      content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      html += `<p>${content}</p>`
    }
  })
  
  if (inList) html += '</ul>'
  
  return html
})

// 建议样式类
const adviceClass = computed(() => {
  if (!data.value) return ''
  const advice = data.value.operation_advice
  if (advice.includes('推荐') || advice.includes('买入')) return 'advice-buy'
  if (advice.includes('减仓') || advice.includes('卖出')) return 'advice-sell'
  return 'advice-hold'
})

// 建议图标
const adviceIcon = computed(() => {
  if (!data.value) return '📊'
  const advice = data.value.operation_advice
  if (advice.includes('推荐') || advice.includes('买入')) return '🚀'
  if (advice.includes('减仓') || advice.includes('卖出')) return '📉'
  return '⏳'
})

// 获取评价类名
const getEvalClass = (eval_text) => {
  if (!eval_text) return ''
  if (eval_text === '优秀' || eval_text === '乐观') return 'eval-excellent'
  if (eval_text === '良好') return 'eval-good'
  if (eval_text === '较差' || eval_text === '谨慎' || eval_text === '悲观') return 'eval-poor'
  return 'eval-normal'
}

const analyze = async () => {
  if (!props.fundCode) return
  loading.value = true
  error.value = null
  try {
    const response = await fundAPI.analyzeFund(props.fundCode)
    if (response.data.error) {
      error.value = response.data.error
    } else {
      data.value = response.data
    }
  } catch (err) {
    error.value = '分析失败: ' + (err.response?.data?.error || err.message)
  } finally {
    loading.value = false
  }
}

watch(() => props.fundCode, () => {
  data.value = null
  error.value = null
})

defineExpose({
  analyze
})
</script>

<style scoped>
.fund-ai-analysis {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  border: 1px solid #f0f0f0;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.title-area {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-area .icon {
  font-size: 1.5em;
}

.title-area h3 {
  margin: 0;
  font-size: 1.2em;
  font-weight: 600;
}

.badge {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
  color: white;
  font-size: 0.7em;
  padding: 2px 8px;
  border-radius: 10px;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.analyze-btn {
  background: linear-gradient(135deg, #1677ff 0%, #0958d9 100%);
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.9em;
  transition: all 0.3s ease;
}

.analyze-btn.mini {
  background: #f0f0f0;
  color: #666;
  box-shadow: none;
}

.analyze-btn.mini:hover {
  background: #e0e0e0;
  color: #333;
  transform: none;
}

.close-btn {
  background: transparent;
  border: none;
  color: #999;
  font-size: 1.2em;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: #f5f5f5;
  color: #666;
}

/* 评分区域 */
.score-section {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 24px;
  align-items: center;
  justify-content: center;
}

.score-card {
  text-align: center;
}

.score-ring {
  position: relative;
  width: 100px;
  height: 100px;
}

.score-ring svg {
  width: 100%;
  height: 100%;
}

.score-ring circle:last-child {
  transition: stroke-dasharray 0.8s ease;
}

.score-value {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 2em;
  font-weight: bold;
}

.score-excellent .score-value { color: #52c41a; }
.score-good .score-value { color: #1677ff; }
.score-normal .score-value { color: #faad14; }
.score-poor .score-value { color: #f5222d; }

.score-label {
  margin-top: 8px;
  color: #666;
  font-size: 0.9em;
}

.advice-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  border-radius: 12px;
  background: #f5f5f5;
}

.advice-buy {
  background: linear-gradient(135deg, #f6ffed 0%, #d9f7be 100%);
}

.advice-sell {
  background: linear-gradient(135deg, #fff1f0 0%, #ffa39e 100%);
}

.advice-hold {
  background: linear-gradient(135deg, #e6f7ff 0%, #91d5ff 100%);
}

.advice-icon {
  font-size: 2em;
}

.advice-text {
  font-size: 1.3em;
  font-weight: 600;
}

/* 摘要区域 */
.summary-section {
  background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
  padding: 16px 20px;
  border-radius: 10px;
  margin-bottom: 20px;
  border-left: 4px solid #1677ff;
}

/* 深度分析报告 */
.detailed-report {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #eee;
}

.report-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.report-icon {
  font-size: 1.4em;
}

.detailed-report h4 {
  margin: 0;
  font-size: 1.1em;
  color: #333;
}

.markdown-content {
  color: #444;
  line-height: 1.6;
}

.markdown-content :deep(h3) {
  font-size: 1.1em;
  color: #1890ff;
  margin: 16px 0 12px;
  font-weight: 600;
}

.markdown-content :deep(h4) {
  font-size: 1em;
  color: #555;
  margin: 12px 0 8px;
  font-weight: 600;
}

.markdown-content :deep(p) {
  margin-bottom: 12px;
  text-align: justify;
}

.markdown-content :deep(ul) {
  padding-left: 20px;
  margin-bottom: 12px;
}

.markdown-content :deep(li) {
  margin-bottom: 6px;
}

.summary-section p {
  margin: 0;
  line-height: 1.8;
  color: #333;
}

/* 仪表盘 */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.dash-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #fafafa;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.dash-item:hover {
  background: #f0f0f0;
  transform: translateY(-2px);
}

.dash-icon {
  font-size: 1.5em;
}

.dash-content {
  display: flex;
  flex-direction: column;
}

.dash-content label {
  font-size: 0.8em;
  color: #999;
  margin-bottom: 4px;
}

.dash-content span {
  font-weight: 600;
  font-size: 1em;
}

.eval-excellent { color: #52c41a; }
.eval-good { color: #1890ff; }
.eval-normal { color: #666; }
.eval-poor { color: #f5222d; }

/* 详情网格 */
.details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.detail-col {
  padding: 16px;
  border-radius: 10px;
}

.detail-col.highlights {
  background: linear-gradient(135deg, #f6ffed 0%, #d9f7be 50%);
}

.detail-col.risks {
  background: linear-gradient(135deg, #fff7e6 0%, #ffe7ba 50%);
}

.detail-col h4 {
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1em;
}

.col-icon {
  font-size: 1.1em;
}

.detail-col ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.detail-col li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
  color: #333;
  line-height: 1.5;
}

.bullet {
  color: #999;
}

/* 新闻区域 */
.news-section {
  background: #f9f9f9;
  padding: 16px;
  border-radius: 10px;
  margin-bottom: 16px;
}

.news-section h4 {
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.news-section ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.news-section li {
  padding: 8px 0;
  border-bottom: 1px dashed #e8e8e8;
  color: #666;
  font-size: 0.9em;
}

.news-section li:last-child {
  border-bottom: none;
}

/* 免责声明 */
.disclaimer {
  text-align: center;
  color: #999;
  font-size: 0.8em;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
}

/* 加载状态 */
.loading {
  text-align: center;
  padding: 60px 20px;
}

.loading-animation {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #1677ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-dots {
  display: flex;
  gap: 6px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: #1677ff;
  border-radius: 50%;
  animation: bounce 1.4s ease-in-out infinite;
}

.loading-dots span:nth-child(1) { animation-delay: 0s; }
.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.loading-text {
  font-size: 1.1em;
  color: #333;
  margin: 0;
}

.loading-sub {
  font-size: 0.9em;
  color: #999;
  margin: 8px 0 0;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 50px 20px;
  background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
  border-radius: 10px;
}

.empty-icon {
  font-size: 3em;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 1em;
  color: #666;
  margin: 0 0 8px;
}

.empty-sub {
  font-size: 0.85em;
  color: #999;
  margin: 0;
}

/* 错误状态 */
.error {
  text-align: center;
  padding: 40px 20px;
  background: #fff1f0;
  border-radius: 10px;
}

.error-icon {
  font-size: 2em;
}

.error p {
  color: #f5222d;
  margin: 12px 0;
}

.retry-btn {
  background: #f5222d;
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: 6px;
  cursor: pointer;
}

.retry-btn:hover {
  background: #cf1322;
}

/* 响应式 */
@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .details-grid {
    grid-template-columns: 1fr;
  }
  
  .score-section {
    flex-direction: column;
  }
}
</style>