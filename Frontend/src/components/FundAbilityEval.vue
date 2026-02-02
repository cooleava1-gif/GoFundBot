<template>
  <div class="ability-card">
    <div class="card-header">
      <h3>📊 本基金历史表现</h3>
      <div class="avg-score" v-if="avgScore">
        <span class="score-label">综合</span>
        <span class="score-value" :class="getScoreClass(avgScore)">{{ avgScore }}</span>
      </div>
    </div>
    <div class="card-body">
      <div v-if="hasEvalData" class="eval-content">
        <div ref="radarChartEl" class="radar-chart"></div>
        <div class="eval-details">
          <div 
            v-for="(item, index) in evalItems" 
            :key="index" 
            class="eval-item"
          >
            <div class="eval-item-header">
              <span class="eval-name">{{ item.name }}</span>
              <span class="eval-score" :class="getScoreClass(item.score)">{{ item.score }}</span>
            </div>
            <div class="eval-bar">
              <div class="eval-bar-fill" :style="{ width: item.score + '%', background: getBarColor(item.score) }"></div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="no-data">
        <p>暂无评价数据</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

export default {
  name: 'FundAbilityEval',
  props: {
    performanceEvaluation: {
      type: Object,
      default: () => ({})
    }
  },
  setup(props) {
    const radarChartEl = ref(null)
    let radarChart = null

    const hasEvalData = computed(() => {
      const data = props.performanceEvaluation?.data
      return data && Array.isArray(data) && data.some(v => v !== null)
    })

    const avgScore = computed(() => props.performanceEvaluation?.avr || null)

    const evalItems = computed(() => {
      const categories = props.performanceEvaluation?.categories || []
      const data = props.performanceEvaluation?.data || []
      
      return categories.map((name, index) => ({
        name,
        score: data[index] ?? 0
      }))
    })

    const getScoreClass = (score) => {
      if (score >= 80) return 'excellent'
      if (score >= 60) return 'good'
      if (score >= 40) return 'normal'
      return 'poor'
    }

    const getBarColor = (score) => {
      if (score >= 80) return 'linear-gradient(90deg, #52c41a 0%, #73d13d 100%)'
      if (score >= 60) return 'linear-gradient(90deg, #1890ff 0%, #69c0ff 100%)'
      if (score >= 40) return 'linear-gradient(90deg, #faad14 0%, #ffc53d 100%)'
      return 'linear-gradient(90deg, #ff4d4f 0%, #ff7875 100%)'
    }

    const initRadarChart = () => {
      if (!radarChartEl.value || !hasEvalData.value) return

      if (radarChart) radarChart.dispose()
      radarChart = echarts.init(radarChartEl.value)

      const categories = props.performanceEvaluation?.categories || []
      const data = props.performanceEvaluation?.data || []

      const option = {
        tooltip: {
          trigger: 'item'
        },
        radar: {
          indicator: categories.map(name => ({
            name,
            max: 100
          })),
          radius: '70%',
          axisName: {
            color: '#666',
            fontSize: 10
          },
          splitArea: {
            areaStyle: {
              color: ['rgba(22, 119, 255, 0.05)', 'rgba(22, 119, 255, 0.1)']
            }
          },
          axisLine: {
            lineStyle: {
              color: 'rgba(22, 119, 255, 0.3)'
            }
          },
          splitLine: {
            lineStyle: {
              color: 'rgba(22, 119, 255, 0.3)'
            }
          }
        },
        series: [{
          type: 'radar',
          data: [{
            value: data,
            name: '能力评分',
            areaStyle: {
              color: 'rgba(22, 119, 255, 0.3)'
            },
            lineStyle: {
              color: '#1677ff',
              width: 2
            },
            itemStyle: {
              color: '#1677ff'
            }
          }]
        }]
      }

      radarChart.setOption(option)
    }

    onMounted(() => {
      nextTick(() => {
        initRadarChart()
      })
    })

    watch(() => props.performanceEvaluation, () => {
      nextTick(() => {
        initRadarChart()
      })
    }, { deep: true })

    return {
      radarChartEl,
      hasEvalData,
      avgScore,
      evalItems,
      getScoreClass,
      getBarColor
    }
  }
}
</script>

<style scoped>
.ability-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.card-header {
  background: linear-gradient(135deg, #1677ff 0%, #0958d9 100%);
  padding: 10px 14px;
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  color: white;
  font-size: 14px;
  font-weight: 600;
}

.avg-score {
  display: flex;
  align-items: center;
  gap: 6px;
}

.score-label {
  font-size: 11px;
  color: rgba(255,255,255,0.8);
}

.score-value {
  font-size: 16px;
  font-weight: bold;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(255,255,255,0.2);
}

.score-value.excellent { color: #52c41a; }
.score-value.good { color: #69c0ff; }
.score-value.normal { color: #faad14; }
.score-value.poor { color: #ff4d4f; }

.card-body {
  padding: 10px;
  flex: 1;
  overflow-y: auto;
}

.eval-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.radar-chart {
  width: 100%;
  height: 180px;
  flex-shrink: 0;
}

.eval-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.eval-item {
  padding: 6px 8px;
  background: #fafafa;
  border-radius: 6px;
}

.eval-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.eval-name {
  font-size: 11px;
  font-weight: 500;
  color: #333;
}

.eval-score {
  font-size: 12px;
  font-weight: bold;
}

.eval-score.excellent { color: #52c41a; }
.eval-score.good { color: #1890ff; }
.eval-score.normal { color: #faad14; }
.eval-score.poor { color: #ff4d4f; }

.eval-bar {
  height: 4px;
  background: #e8e8e8;
  border-radius: 2px;
  overflow: hidden;
}

.eval-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
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
