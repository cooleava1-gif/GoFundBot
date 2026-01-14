<template>
  <div class="fund-chart">
    <div class="chart-container">
      <div ref="chartEl" style="width: 100%; height: 400px;"></div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

export default {
  name: 'FundChart',
  props: {
    netWorthTrend: {
      type: Array,
      default: () => []
    },
    acWorthTrend: {
      type: Array,
      default: () => []
    }
  },
  setup(props) {
    const chartEl = ref(null)
    let chartInstance = null

    const initChart = () => {
      if (!chartEl.value) return
      
      chartInstance = echarts.init(chartEl.value)
      updateChart()
    }

    const updateChart = () => {
      if (!chartInstance) return

      const option = {
        title: {
          text: '基金净值走势',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          formatter: function(params) {
            let result = ''
            params.forEach(param => {
              const date = new Date(param.value[0])
              const dateStr = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`
              result += `${dateStr}<br/>`
              result += `${param.seriesName}: ${param.value[1].toFixed(4)}<br/>`
            })
            return result
          }
        },
        legend: {
          data: ['单位净值', '累计净值'],
          top: 30
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'time',
          boundaryGap: false
        },
        yAxis: {
          type: 'value',
          scale: true
        },
        series: [
          {
            name: '单位净值',
            type: 'line',
            data: props.netWorthTrend.map(item => [item.x, item.y]),
            smooth: true,
            lineStyle: {
              width: 2
            }
          },
          {
            name: '累计净值',
            type: 'line',
            data: props.acWorthTrend.map(item => [item[0], item[1]]),
            smooth: true,
            lineStyle: {
              width: 2
            }
          }
        ]
      }

      chartInstance.setOption(option)
    }

    onMounted(() => {
      initChart()
    })

    onUnmounted(() => {
      if (chartInstance) {
        chartInstance.dispose()
      }
    })

    watch(() => [props.netWorthTrend, props.acWorthTrend], () => {
      updateChart()
    }, { deep: true })

    return {
      chartEl
    }
  }
}
</script>

<style scoped>
.chart-container {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>