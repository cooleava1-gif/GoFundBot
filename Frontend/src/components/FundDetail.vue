<template>
  <div class="fund-detail">
    <!-- 基金基础信息组件 -->
    <FundBasicInfo :fundCode="currentFundCode" :fundData="fundDetail" />
    
    <!-- 主要内容区域 - Dashboard 布局 -->
    <div v-if="fundDetail" class="dashboard">
      
      <!-- 左侧主区域 -->
      <div class="main-area">
        <!-- 净值走势图 -->
        <div class="card card-chart">
          <FundChart
            :netWorthTrend="processedNetWorthTrend"
            :acWorthTrend="processedAcWorthTrend"
            :grandTotal="fundDetail.total_return_trend"
          />
        </div>
        
        <!-- 中间两列区域 -->
        <div class="grid-2">
          <div class="card card-md clickable" @click="openModal('ranking')">
            <FundRankingTrend
              :rateInSimilarType="fundDetail.ranking_trend"
              :rateInSimilarPercent="fundDetail.ranking_percentage"
            />
          </div>
          <div class="card card-md clickable" @click="openModal('asset')">
            <FundAssetAllocation
              :assetAllocation="fundDetail.asset_allocation"
            />
          </div>
        </div>

        <!-- 底部两列区域 -->
        <div class="grid-2">
          <div class="card card-md clickable" @click="openModal('holder')">
            <FundHolderStructure
              :holderStructure="fundDetail.holder_structure"
            />
          </div>
          <div class="card card-md clickable" @click="openModal('scale')">
            <FundScaleChange
              :fluctuationScale="fundDetail.scale_fluctuation"
            />
          </div>
        </div>
      </div>

      <!-- 右侧边栏 -->
      <div class="sidebar">
        <div class="card card-sidebar clickable" @click="openModal('portfolio')">
          <FundPortfolio
            :portfolio="fundDetail.portfolio"
          />
        </div>
        <div class="card card-sidebar clickable" @click="openModal('manager')">
          <FundManagerInfo
            :fundManagers="fundDetail.fund_managers"
          />
        </div>
      </div>
    </div>
    
    <!-- 放大模态框 -->
    <div v-if="modalVisible" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <button class="modal-close" @click="closeModal">×</button>
        <div class="modal-body">
          <FundRankingTrend
            v-if="modalType === 'ranking'"
            :rateInSimilarType="fundDetail.ranking_trend"
            :rateInSimilarPercent="fundDetail.ranking_percentage"
          />
          <FundAssetAllocation
            v-if="modalType === 'asset'"
            :assetAllocation="fundDetail.asset_allocation"
          />
          <FundHolderStructure
            v-if="modalType === 'holder'"
            :holderStructure="fundDetail.holder_structure"
          />
          <FundScaleChange
            v-if="modalType === 'scale'"
            :fluctuationScale="fundDetail.scale_fluctuation"
          />
          <FundPortfolio
            v-if="modalType === 'portfolio'"
            :portfolio="fundDetail.portfolio"
          />
          <FundManagerInfo
            v-if="modalType === 'manager'"
            :fundManagers="fundDetail.fund_managers"
          />
        </div>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-else-if="loading" class="loading">
      <div class="loading-spinner"></div>
      <p>正在加载基金详情...</p>
    </div>
    
    <!-- 错误状态 -->
    <div v-else-if="error" class="error">
      <div class="error-icon">⚠️</div>
      <p>{{ error }}</p>
      <button @click="retry" class="retry-btn">重试</button>
    </div>
    
    <!-- 空状态 -->
    <div v-else-if="!currentFundCode" class="empty-state">
      <div class="empty-icon">📊</div>
      <p>请输入基金代码或从搜索结果中选择基金</p>
    </div>
  </div>
</template>

<script>
import { ref, watch, computed } from 'vue'
import FundBasicInfo from './FundBasicInfo.vue'
import FundChart from './FundChart.vue'
import FundRankingTrend from './FundRankingTrend.vue'
import FundAssetAllocation from './FundAssetAllocation.vue'
import FundScaleChange from './FundScaleChange.vue'
import FundManagerInfo from './FundManagerInfo.vue'
import FundHolderStructure from './FundHolderStructure.vue'
import FundPortfolio from './FundPortfolio.vue'
import { fundAPI } from '../services/api'

export default {
  name: 'FundDetail',
  components: {
    FundBasicInfo,
    FundChart,
    FundRankingTrend,
    FundAssetAllocation,
    FundScaleChange,
    FundManagerInfo,
    FundHolderStructure,
    FundPortfolio
  },
  props: {
    fundCode: {
      type: String,
      default: ''
    }
  },
  setup(props) {
    const currentFundCode = ref(props.fundCode)
    const fundDetail = ref(null)
    const loading = ref(false)
    const error = ref('')
    const modalVisible = ref(false)
    const modalType = ref('')

    // 打开模态框
    const openModal = (type) => {
      modalType.value = type
      modalVisible.value = true
      document.body.style.overflow = 'hidden'
    }

    // 关闭模态框
    const closeModal = () => {
      modalVisible.value = false
      modalType.value = ''
      document.body.style.overflow = ''
    }

    // 处理净值走势数据格式
    const processedNetWorthTrend = computed(() => {
      if (!fundDetail.value?.net_worth_trend) return []
      
      try {
        // 处理不同的数据格式
        const trend = fundDetail.value.net_worth_trend
        if (Array.isArray(trend) && trend.length > 0) {
          // 新格式: [{date: '2024-01-01', net_worth: 1.23}]
          if (trend[0].date && trend[0].net_worth !== undefined) {
            return trend.map(item => ({
              x: new Date(item.date).getTime(),
              y: parseFloat(item.net_worth) || 0
            }))
          }
          // 旧格式1: [{x: timestamp, y: value}]
          if (trend[0].x && trend[0].y) {
            return trend.map(item => ({
              x: item.x,
              y: parseFloat(item.y) || 0
            }))
          }
          // 旧格式2: [timestamp, value]
          else if (Array.isArray(trend[0]) && trend[0].length >= 2) {
            return trend.map(item => ({
              x: item[0],
              y: parseFloat(item[1]) || 0
            }))
          }
        }
        return []
      } catch (e) {
        console.error('处理净值走势数据错误:', e)
        return []
      }
    })

    // 处理累计净值走势数据
    const processedAcWorthTrend = computed(() => {
      if (!fundDetail.value?.accumulated_net_worth) return []
      
      try {
        const trend = fundDetail.value.accumulated_net_worth
        if (Array.isArray(trend) && trend.length > 0) {
          // 新格式: [{date: '2024-01-01', position_percentage: 1.23}]
          if (trend[0].date !== undefined) {
            return trend.map(item => [
              new Date(item.date).getTime(),
              parseFloat(item.position_percentage) || 0
            ])
          }
          // 旧格式: [[timestamp, value]]
          return trend.map(item => {
            if (Array.isArray(item) && item.length >= 2) {
              return [item[0], parseFloat(item[1]) || 0]
            }
            return [0, 0]
          })
        }
        return []
      } catch (e) {
        console.error('处理累计净值数据错误:', e)
        return []
      }
    })

    // 获取基金详情
    const fetchFundDetail = async (fundCode) => {
      if (!fundCode) {
        fundDetail.value = null
        return
      }

      loading.value = true
      error.value = ''
      try {
        const response = await fundAPI.getFundDetail(fundCode)
        fundDetail.value = response.data
        console.log('基金详情数据:', response.data)
      } catch (err) {
        console.error('获取基金详情失败:', err)
        error.value = err.response?.data?.error || '获取基金详情失败，请检查基金代码是否正确'
        fundDetail.value = null
      } finally {
        loading.value = false
      }
    }

    // 重试函数
    const retry = () => {
      if (currentFundCode.value) {
        fetchFundDetail(currentFundCode.value)
      }
    }

    // 监听基金代码变化
    watch(() => props.fundCode, (newCode) => {
      currentFundCode.value = newCode
      if (newCode) {
        fetchFundDetail(newCode)
      } else {
        fundDetail.value = null
        loading.value = false
        error.value = ''
      }
    }, { immediate: true })

    return {
      currentFundCode,
      fundDetail,
      loading,
      error,
      processedNetWorthTrend,
      processedAcWorthTrend,
      retry,
      modalVisible,
      modalType,
      openModal,
      closeModal
    }
  }
}
</script>

<style scoped>
.fund-detail {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 16px;
  background: #f0f2f5;
  min-height: 100vh;
}

/* Dashboard 主布局 */
.dashboard {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 16px;
  padding: 16px 0;
}

/* 左侧主区域 */
.main-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

/* 右侧边栏 */
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 两列网格 */
.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

/* 卡片基础样式 */
.card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  overflow: hidden;
}

/* 图表卡片 - 固定高度 */
.card-chart {
  height: 500px;
  display: flex;
  flex-direction: column;
}

/* 中等高度卡片 - 增加高度 */
.card-md {
  height: 450px;
  display: flex;
  flex-direction: column;
}

/* 侧边栏卡片 */
.card-sidebar {
  flex: 1;
  min-height: 300px;
  max-height: 480px;
  display: flex;
  flex-direction: column;
}

/* 加载状态 */
.loading {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading p {
  font-size: 16px;
  margin-top: 16px;
}

/* 错误状态 */
.error {
  text-align: center;
  padding: 60px 40px;
  color: #d32f2f;
  background: #ffebee;
  border-radius: 12px;
  margin: 20px 0;
}

.error-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.error p {
  font-size: 16px;
  margin-bottom: 20px;
}

.retry-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 12px 32px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.retry-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.retry-btn:active {
  transform: translateY(0);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: #666;
  background: white;
  border-radius: 12px;
  margin: 20px 0;
}

.empty-icon {
  font-size: 80px;
  margin-bottom: 24px;
  opacity: 0.6;
}

.empty-state p {
  font-size: 18px;
  color: #999;
}

/* 响应式设计 */
@media (max-width: 1400px) {
  .dashboard {
    grid-template-columns: 1fr 340px;
  }
}

@media (max-width: 1200px) {
  .dashboard {
    grid-template-columns: 1fr;
  }
  
  .sidebar {
    flex-direction: row;
  }
  
  .card-sidebar {
    flex: 1;
    max-height: 400px;
  }
}

@media (max-width: 900px) {
  .grid-2 {
    grid-template-columns: 1fr;
  }
  
  .card-md {
    height: auto;
    min-height: 320px;
  }
  
  .sidebar {
    flex-direction: column;
  }
  
  .card-sidebar {
    max-height: none;
  }
}

@media (max-width: 768px) {
  .fund-detail {
    padding: 0 8px;
  }
  
  .dashboard {
    gap: 12px;
    padding: 12px 0;
  }
  
  .main-area, .sidebar {
    gap: 12px;
  }
  
  .grid-2 {
    gap: 12px;
  }
}

/* 可点击卡片样式 */
.clickable {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 16px;
  width: 90vw;
  max-width: 900px;
  height: 80vh;
  max-height: 700px;
  position: relative;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  animation: modalIn 0.3s ease;
}

@keyframes modalIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.modal-close {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 36px;
  height: 36px;
  border: none;
  background: #f0f0f0;
  border-radius: 50%;
  font-size: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  transition: background 0.2s;
}

.modal-close:hover {
  background: #e0e0e0;
}

.modal-body {
  flex: 1;
  overflow: hidden;
  border-radius: 16px;
}

.modal-body > * {
  height: 100%;
}
</style>