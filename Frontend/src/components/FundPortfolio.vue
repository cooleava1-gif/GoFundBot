<template>
  <div class="portfolio-card">
    <div class="card-header">
      <h3>📈 持仓明细</h3>
      <div class="tab-switch">
        <button 
          :class="{ active: activeTab === 'stock' }" 
          @click="activeTab = 'stock'"
        >
          股票持仓
        </button>
        <button 
          :class="{ active: activeTab === 'bond' }" 
          @click="activeTab = 'bond'"
        >
          债券持仓
        </button>
      </div>
    </div>
    <div class="card-body">
      <!-- 股票持仓 -->
      <div v-if="activeTab === 'stock'" class="portfolio-content">
        <div v-if="hasStockData" class="stock-list">
          <div class="portfolio-header">
            <span class="col-rank">排名</span>
            <span class="col-code">代码</span>
            <span class="col-name">名称</span>
            <span class="col-ratio">占比</span>
          </div>
          <div 
            v-for="(stock, index) in stockList" 
            :key="stock.code || index" 
            class="portfolio-item"
          >
            <span class="col-rank">{{ index + 1 }}</span>
            <span class="col-code">{{ stock.code }}</span>
            <span class="col-name">{{ stock.name }}</span>
            <span class="col-ratio">
              <div class="ratio-bar">
                <div class="ratio-fill" :style="{ width: getRatioWidth(stock.ratio) }"></div>
              </div>
              <span class="ratio-text">{{ formatRatio(stock.ratio) }}</span>
            </span>
          </div>
        </div>
        <div v-else class="no-data">
          <p>暂无股票持仓数据</p>
        </div>
      </div>

      <!-- 债券持仓 -->
      <div v-if="activeTab === 'bond'" class="portfolio-content">
        <div v-if="hasBondData" class="bond-list">
          <div class="portfolio-header">
            <span class="col-rank">排名</span>
            <span class="col-code">代码</span>
            <span class="col-name">名称</span>
            <span class="col-ratio">占比</span>
          </div>
          <div 
            v-for="(bond, index) in bondList" 
            :key="bond.code || index" 
            class="portfolio-item"
          >
            <span class="col-rank">{{ index + 1 }}</span>
            <span class="col-code">{{ bond.code }}</span>
            <span class="col-name">{{ bond.name }}</span>
            <span class="col-ratio">
              <div class="ratio-bar bond-bar">
                <div class="ratio-fill" :style="{ width: getRatioWidth(bond.ratio) }"></div>
              </div>
              <span class="ratio-text">{{ formatRatio(bond.ratio) }}</span>
            </span>
          </div>
        </div>
        <div v-else class="no-data">
          <p>暂无债券持仓数据</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'

export default {
  name: 'FundPortfolio',
  props: {
    portfolio: {
      type: Object,
      default: () => ({})
    }
  },
  setup(props) {
    const activeTab = ref('stock')

    // 解析持仓数据 - 格式: ["代码", "名称", "占比", ...]
    const parseHoldings = (codes) => {
      if (!codes || !Array.isArray(codes)) return []
      
      const holdings = []
      // 每3个元素为一组: [代码, 名称, 占比]
      for (let i = 0; i < codes.length; i += 3) {
        if (i + 2 < codes.length) {
          holdings.push({
            code: codes[i],
            name: codes[i + 1],
            ratio: parseFloat(codes[i + 2]) || 0
          })
        }
      }
      return holdings.sort((a, b) => b.ratio - a.ratio)
    }

    // 优先使用最新数据 (stock_codes_new)，否则使用旧数据
    const stockList = computed(() => {
      const newCodes = props.portfolio?.stock_codes_new
      const oldCodes = props.portfolio?.stock_codes
      return parseHoldings(newCodes?.length ? newCodes : oldCodes)
    })

    const bondList = computed(() => {
      const newCodes = props.portfolio?.bond_codes_new
      const oldCodes = props.portfolio?.bond_codes
      return parseHoldings(newCodes?.length ? newCodes : oldCodes)
    })

    const hasStockData = computed(() => stockList.value.length > 0)
    const hasBondData = computed(() => bondList.value.length > 0)

    const formatRatio = (ratio) => {
      if (ratio === null || ratio === undefined) return '--'
      return ratio.toFixed(2) + '%'
    }

    const getRatioWidth = (ratio) => {
      if (!ratio) return '0%'
      // 最大占比假设为20%，计算相对宽度
      const maxRatio = 20
      const width = Math.min((ratio / maxRatio) * 100, 100)
      return width + '%'
    }

    return {
      activeTab,
      stockList,
      bondList,
      hasStockData,
      hasBondData,
      formatRatio,
      getRatioWidth
    }
  }
}
</script>

<style scoped>
.portfolio-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.card-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 10px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.card-header h3 {
  margin: 0;
  color: white;
  font-size: 14px;
  font-weight: 600;
}

.tab-switch {
  display: flex;
  gap: 6px;
}

.tab-switch button {
  background: rgba(255,255,255,0.2);
  border: none;
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s;
}

.tab-switch button.active {
  background: white;
  color: #667eea;
  font-weight: 600;
}

.tab-switch button:hover:not(.active) {
  background: rgba(255,255,255,0.3);
}

.card-body {
  padding: 10px;
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.portfolio-content {
  flex: 1;
  overflow-y: auto;
}

.portfolio-header {
  display: flex;
  padding: 8px 0;
  border-bottom: 2px solid #eee;
  font-weight: 600;
  color: #666;
  font-size: 11px;
  position: sticky;
  top: 0;
  background: white;
}

.portfolio-item {
  display: flex;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  align-items: center;
  font-size: 12px;
}

.portfolio-item:hover {
  background: #f9f9f9;
}

.col-rank {
  width: 32px;
  text-align: center;
  color: #999;
  font-weight: 500;
}

.portfolio-item .col-rank {
  width: 32px;
  height: 20px;
  line-height: 20px;
  background: #f0f0f0;
  border-radius: 10px;
  font-size: 11px;
}

.portfolio-item:nth-child(2) .col-rank { background: #ffd700; color: #fff; }
.portfolio-item:nth-child(3) .col-rank { background: #c0c0c0; color: #fff; }
.portfolio-item:nth-child(4) .col-rank { background: #cd7f32; color: #fff; }

.col-code {
  width: 65px;
  color: #667eea;
  font-family: monospace;
  font-size: 11px;
}

.col-name {
  flex: 1;
  color: #333;
  font-weight: 500;
  padding-right: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.col-ratio {
  width: 90px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.ratio-bar {
  flex: 1;
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
  overflow: hidden;
}

.ratio-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 3px;
}

.bond-bar .ratio-fill {
  background: linear-gradient(90deg, #52c41a 0%, #73d13d 100%);
}

.ratio-text {
  width: 40px;
  text-align: right;
  font-weight: 600;
  color: #333;
  font-size: 11px;
}

.no-data {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  font-size: 13px;
}
</style>
