<template>
  <div class="asset-allocation-card">
    <div class="card-header">
      <h3>📊 资产配置</h3>
    </div>
    <div class="card-body">
      <div v-if="hasData" class="allocation-content">
        <div ref="chartEl" class="allocation-chart"></div>
        <div class="legend-info">
          <div v-for="(serie, index) in displaySeries" :key="index" class="legend-item">
            <span class="legend-dot" :style="{ background: getColor(index) }"></span>
            <span class="legend-name">{{ serie.name }}</span>
            <span class="legend-value">{{ formatValue(serie.data[serie.data.length - 1], serie.name) }}</span>
          </div>
        </div>
      </div>
      <div v-else class="no-data">
        <p>暂无资产配置数据</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

export default {
  name: 'FundAssetAllocation',
  props: {
    assetAllocation: {
      type: Object,
      default: () => ({})
    }
  },
  setup(props) {
    const chartEl = ref(null)
    let chartInstance = null

    const categories = computed(() => props.assetAllocation?.categories || [])
    const series = computed(() => props.assetAllocation?.series || [])
    const hasData = computed(() => categories.value.length > 0 && series.value.length > 0)

    const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc']

    const getColor = (index) => colors[index % colors.length]

    const formatValue = (value, name) => {
      if (value === null || value === undefined) return '--'
      if (name === '净资产') {
        return value + '亿'
      }
      return value + '%'
    }

    const initChart = () => {
      if (!chartEl.value || !hasData.value) return

      if (chartInstance) {
        chartInstance.dispose()
      }

      chartInstance = echarts.init(chartEl.value)

      // 准备柱状图数据（排除净资产，它用折线图）
      const barSeries = series.value
        .filter(s => s.name !== '净资产')
        .map((serie, index) => ({
          name: serie.name,
          type: 'bar',
          stack: 'total',
          data: serie.data,
          itemStyle: {
            color: getColor(index)
          },
          label: {
            show: true,
            position: 'inside', 
            formatter: (p) => p.value > 5 ? p.value + '%' : '' // Show label if wide enough
          }
        }))

      // 净资产用折线图
      const netAssetSerie = series.value.find(s => s.name === '净资产')
      const lineSeries = netAssetSerie ? [{
        name: '净资产',
        type: 'line',
        yAxisIndex: 1, // 使用右侧Y轴
        data: netAssetSerie.data,
        itemStyle: {
          color: '#ee6666'
        },
        lineStyle: {
            width: 3
        },
        symbol: 'circle',
        symbolSize: 8
      }] : []

      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          },
          formatter: (params) => {
            let result = `<div style="font-weight: bold; margin-bottom: 8px;">${params[0].axisValue}</div>`
            params.forEach(param => {
              const unit = param.seriesName === '净资产' ? '亿' : '%'
              result += `<div style="margin: 4px 0;">
                <span style="display:inline-block;margin-right:5px;border-radius:50%;width:10px;height:10px;background-color:${param.color};"></span>
                ${param.seriesName}: <strong>${param.value}${unit}</strong>
              </div>`
            })
            return result
          }
        },
        legend: {
          data: series.value.map(s => s.name),
          bottom: 0,
          type: 'scroll'
        },
        grid: {
          left: '3%',
          right: '5%',
          bottom: '10%',
          top: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: categories.value,
          boundaryGap: true
        },
        yAxis: [
            {
                type: 'value',
                axisLabel: { formatter: '{value}%' },
                splitLine: { show: true }
            },
            {
                type: 'value',
                name: '净资产(亿)',
                position: 'right',
                axisLabel: { formatter: '{value}' },
                splitLine: { show: false }
            }
        ],
        series: [...barSeries, ...lineSeries]
      }

      chartInstance.setOption(option)
    }

    onMounted(() => {
      nextTick(() => {
        initChart()
      })
    })

    watch(() => props.assetAllocation, () => {
      nextTick(() => {
        initChart()
      })
    }, { deep: true })

    // 用于显示的系列（排除净资产）
    const displaySeries = computed(() => series.value.filter(s => s.name !== '净资产'))

    return {
      chartEl,
      categories,
      series,
      displaySeries,
      hasData,
      getColor,
      formatValue
    }
  }
}
</script>

<style scoped>
.asset-allocation-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.card-header {
  background: linear-gradient(135deg, #9CADBD 0%, #7B8D9E 100%);
  color: white;
  padding: 12px 16px;
  flex-shrink: 0;
}

.card-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}

.card-body {
  padding: 12px;
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.allocation-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
}

.allocation-chart {
  width: 100%;
  flex: 1;
  min-height: 200px;
}

.legend-info {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  padding: 8px 0;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-name {
  color: #666;
}

.legend-value {
  font-weight: 600;
  color: #333;
}

.no-data {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
}
</style>
