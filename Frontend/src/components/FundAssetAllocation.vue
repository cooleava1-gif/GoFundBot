<template>
  <div class="asset-allocation-card">
    <div class="card-header">
      <h3>📊 资产配置</h3>
    </div>
    <div class="card-body">
      <div v-if="hasData" class="allocation-content">
        <div ref="chartEl" class="allocation-chart"></div>
        <div class="allocation-table">
          <table>
            <thead>
              <tr>
                <th>资产类型</th>
                <th v-for="(date, index) in categories" :key="index">{{ date }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(serie, index) in series" :key="index">
                <td class="type-cell">
                  <span class="type-dot" :style="{ background: getColor(index) }"></span>
                  {{ serie.name }}
                </td>
                <td v-for="(value, idx) in serie.data" :key="idx" class="value-cell">
                  {{ formatValue(value, serie.name) }}
                </td>
              </tr>
            </tbody>
          </table>
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
          }
        }))

      // 净资产用折线图
      const netAssetSerie = series.value.find(s => s.name === '净资产')
      const lineSeries = netAssetSerie ? [{
        name: '净资产',
        type: 'line',
        yAxisIndex: 1,
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
          bottom: 0
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          top: '10%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: categories.value
        },
        yAxis: [
          {
            type: 'value',
            name: '占净值比(%)',
            axisLabel: {
              formatter: '{value}%'
            }
          },
          {
            type: 'value',
            name: '净资产(亿)',
            axisLabel: {
              formatter: '{value}亿'
            }
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

    return {
      chartEl,
      categories,
      series,
      hasData,
      getColor,
      formatValue
    }
  }
}
</script>

<style scoped>
.asset-allocation-card {
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
  border-bottom: 1px solid #e8e8e8;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.card-body {
  padding: 24px;
}

.allocation-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.allocation-chart {
  width: 100%;
  height: 300px;
}

.allocation-table {
  overflow-x: auto;
}

.allocation-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.allocation-table th,
.allocation-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e8e8e8;
}

.allocation-table th {
  background: #f5f5f5;
  font-weight: 600;
  color: #333;
}

.type-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.value-cell {
  font-weight: 500;
  text-align: center;
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
