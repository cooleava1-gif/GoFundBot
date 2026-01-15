<template>
  <div class="fund-performance-card">
    <div class="card-header">
      <h3>📉 收益率对比分析</h3>
    </div>
    <div class="card-body">
      <div v-if="hasGrandTotalData" class="performance-content">
        <div ref="performanceChartEl" class="performance-chart"></div>
      </div>
      <div v-else class="no-data">
        <p>暂无收益率对比数据</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

export default {
  name: 'FundPerformanceComparison',
  props: {
    grandTotal: {
      type: Array,
      default: () => []
    }
  },
  setup(props) {
    const performanceChartEl = ref(null)
    let performanceChartInstance = null

    const hasGrandTotalData = computed(() => 
      props.grandTotal && props.grandTotal.length > 0
    )

    const initPerformanceChart = () => {
      if (!performanceChartEl.value || !hasGrandTotalData.value) return

      if (performanceChartInstance) {
        performanceChartInstance.dispose()
      }

      performanceChartInstance = echarts.init(performanceChartEl.value)

      const series = props.grandTotal.map((item, index) => {
        const colors = ['#667eea', '#91cc75', '#fac858']
        return {
          name: item.name,
          type: 'line',
          data: item.data,
          smooth: true,
          symbol: 'none',
          lineStyle: {
            width: 2,
            color: colors[index % colors.length]
          }
        }
      })

      const option = {
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            let result = `<div style="font-weight: bold; margin-bottom: 8px;">${new Date(params[0].axisValue).toLocaleDateString()}</div>`
            params.forEach(param => {
              result += `<div style="margin: 4px 0;">
                <span style="display:inline-block;margin-right:5px;border-radius:50%;width:10px;height:10px;background-color:${param.color};"></span>
                ${param.seriesName}: <strong>${param.value[1]}%</strong>
              </div>`
            })
            return result
          }
        },
        legend: {
          data: props.grandTotal.map(item => item.name),
          bottom: 10,
          icon: 'circle'
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          top: '5%',
          containLabel: true
        },
        xAxis: {
          type: 'time',
          boundaryGap: false
        },
        yAxis: {
          type: 'value',
          name: '累计收益率(%)',
          axisLabel: {
            formatter: '{value}%'
          }
        },
        series: series
      }

      performanceChartInstance.setOption(option)
    }

    onMounted(() => {
      nextTick(() => {
        initPerformanceChart()
      })
    })

    watch(() => props.grandTotal, () => {
      nextTick(() => {
        initPerformanceChart()
      })
    }, { deep: true })

    return {
      performanceChartEl,
      hasGrandTotalData
    }
  }
}
</script>

<style scoped>
.fund-performance-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-bottom: 24px;
}

.card-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px 20px;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.card-body {
  padding: 24px;
}

.performance-content {
  width: 100%;
}

.performance-chart {
  width: 100%;
  height: 400px;
}

.no-data {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.no-data p {
  font-size: 16px;
}
</style>
