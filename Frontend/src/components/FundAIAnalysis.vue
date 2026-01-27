<template>
  <div class="fund-ai-analysis card">
    <div class="header">
      <h3>🤖 AI 智能分析</h3>
      <button v-if="!loading" @click="analyze" class="analyze-btn">
        {{ data ? '重新分析' : '开始分析' }}
      </button>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>AI 正在深度分析基金表现与市场情报...</p>
    </div>

    <div v-else-if="error" class="error">
      {{ error }}
    </div>

    <div v-else-if="data" class="analysis-content">
      <div class="overview">
        <div class="score-card">
          <div class="score" :class="scoreClass">{{ data.sentiment_score }}</div>
          <div class="advice">{{ data.operation_advice }}</div>
        </div>
        <div class="summary">
          {{ data.summary }}
        </div>
      </div>

      <div class="dashboard-grid">
        <div class="dash-item">
          <label>业绩评价</label>
          <span>{{ data.dashboard.performance_eval }}</span>
        </div>
        <div class="dash-item">
          <label>经理能力</label>
          <span>{{ data.dashboard.manager_ability }}</span>
        </div>
        <div class="dash-item">
          <label>持仓结构</label>
          <span>{{ data.dashboard.position_analysis }}</span>
        </div>
        <div class="dash-item">
          <label>后市展望</label>
          <span>{{ data.dashboard.market_outlook }}</span>
        </div>
      </div>

      <div class="details-grid">
        <div class="detail-col">
          <h4>✅ 亮点</h4>
          <ul>
            <li v-for="(item, i) in data.highlights" :key="i">{{ item }}</li>
          </ul>
        </div>
        <div class="detail-col">
          <h4>⚠️ 风险提示</h4>
          <ul>
            <li v-for="(item, i) in data.risk_factors" :key="i">{{ item }}</li>
          </ul>
        </div>
      </div>
      
      <div class="news-section" v-if="data.news_intel && data.news_intel.length">
        <h4>📰 实时情报</h4>
        <ul>
          <li v-for="(news, i) in data.news_intel" :key="i">{{ news }}</li>
        </ul>
      </div>
    </div>
    
    <div v-else class="empty-state">
      <p>点击上方按钮，获取 AI 对该基金的实时深度分析报告</p>
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

const data = ref(null)
const loading = ref(false)
const error = ref(null)

const scoreClass = computed(() => {
  if (!data.value) return ''
  const s = data.value.sentiment_score
  if (s >= 80) return 'score-high'
  if (s >= 60) return 'score-mid'
  return 'score-low'
})

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
</script>

<style scoped>
.fund-ai-analysis {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.header h3 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.analyze-btn {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: opacity 0.3s;
}

.analyze-btn:hover {
  opacity: 0.9;
}

.overview {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  align-items: center;
}

.score-card {
  text-align: center;
  min-width: 100px;
}

.score {
  font-size: 2.5em;
  font-weight: bold;
  line-height: 1;
}

.score-high { color: #f5222d; }
.score-mid { color: #fa8c16; }
.score-low { color: #52c41a; }

.advice {
  margin-top: 5px;
  font-weight: bold;
  color: #333;
}

.summary {
  flex: 1;
  font-size: 1.1em;
  line-height: 1.5;
  color: #333;
  background: #f9f9f9;
  padding: 15px;
  border-radius: 6px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  margin-bottom: 20px;
  background: #f0f7ff;
  padding: 15px;
  border-radius: 6px;
}

.dash-item {
  text-align: center;
}

.dash-item label {
  display: block;
  font-size: 0.85em;
  color: #666;
  margin-bottom: 5px;
}

.dash-item span {
  font-weight: bold;
  color: #1890ff;
}

.details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.detail-col h4 {
  margin: 0 0 10px 0;
  border-bottom: 2px solid #eee;
  padding-bottom: 5px;
}

.detail-col ul {
  padding-left: 20px;
  margin: 0;
}

.detail-col li {
  margin-bottom: 5px;
  color: #555;
}

.news-section h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.news-section ul {
  padding-left: 20px;
  margin: 0;
}

.news-section li {
  margin-bottom: 5px;
  color: #666;
  font-size: 0.9em;
}

.loading {
  text-align: center;
  padding: 40px;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 30px;
  color: #999;
  background: #fafafa;
  border-radius: 6px;
}

.error {
  color: #f5222d;
  padding: 20px;
  text-align: center;
  background: #fff1f0;
  border-radius: 6px;
}
</style>