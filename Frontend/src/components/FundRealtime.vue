<template>
  <div class="realtime-layout">
    <aside class="realtime-sidebar">
      <FundWatchlist 
        :addToRealtimeMode="true"
        @add-to-realtime="addFundToRealtime"
      />
    </aside>
    <div class="realtime-main">
      <div class="realtime-container">
    <!-- 头部 -->
    <div class="realtime-header">
      <div class="header-left">
        <h2>
          <span class="header-icon">📈</span>
          实时估值
          <span class="count-badge" v-if="funds.length">{{ funds.length }}</span>
        </h2>
        <span class="trade-status" :class="{ 'trading': isTradingTime, 'closed': !isTradingTime }">
          {{ isTradingTime ? '🟢 交易中' : '🔴 已休市' }}
        </span>
      </div>
      <div class="header-actions">
        <button class="btn btn-refresh" @click="refreshAll" :disabled="refreshing">
          <span :class="{ 'rotating': refreshing }">🔄</span>
        </button>
        <div class="refresh-interval">
          <select v-model="refreshMs" @change="saveRefreshMs" class="interval-select">
            <option :value="10000">10秒</option>
            <option :value="30000">30秒</option>
            <option :value="60000">1分钟</option>
            <option :value="120000">2分钟</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 搜索添加区域 -->
    <div class="search-section">
      <div class="search-box">
        <input
          v-model="searchTerm"
          @input="handleSearchInput"
          @focus="showDropdown = true"
          placeholder="输入基金代码或名称添加..."
          class="search-input"
        />
        <button class="btn btn-add" @click="batchAddFunds" :disabled="selectedFunds.length === 0">
          添加 {{ selectedFunds.length > 0 ? `(${selectedFunds.length})` : '' }}
        </button>
      </div>
      <!-- 搜索结果下拉 -->
      <div v-if="showDropdown && searchResults.length > 0" class="search-dropdown" ref="dropdownRef">
        <div 
          v-for="fund in searchResults" 
          :key="fund.CODE"
          class="dropdown-item"
          :class="{ 'selected': isSelected(fund.CODE) }"
          @click="toggleSelectFund(fund)"
        >
          <span class="fund-code">{{ fund.CODE }}</span>
          <span class="fund-name">{{ fund.NAME }}</span>
          <span class="check-icon" v-if="isSelected(fund.CODE)">✓</span>
        </div>
      </div>
      <!-- 已选择的基金 -->
      <div v-if="selectedFunds.length > 0" class="selected-funds">
        <span 
          v-for="fund in selectedFunds" 
          :key="fund.CODE" 
          class="selected-tag"
          @click="toggleSelectFund(fund)"
        >
          {{ fund.NAME }} <span class="remove-icon">×</span>
        </span>
      </div>
    </div>

    <!-- 汇总统计 -->
    <div v-if="hasHoldings" class="summary-card">
      <div class="summary-item">
        <div class="summary-label">总资产(估)</div>
        <div class="summary-value">¥{{ totalAsset.toFixed(2) }}</div>
      </div>
      <div class="summary-item">
        <div class="summary-label">今日收益(估)</div>
        <div class="summary-value" :class="profitTodayClass">
          {{ totalProfitToday >= 0 ? '+' : '' }}{{ totalProfitToday.toFixed(2) }}
        </div>
      </div>
      <div class="summary-item">
        <div class="summary-label">持有收益</div>
        <div class="summary-value" :class="profitTotalClass">
          {{ totalProfitTotal >= 0 ? '+' : '' }}{{ totalProfitTotal.toFixed(2) }}
        </div>
      </div>
    </div>

    <!-- 基金列表 -->
    <div v-if="funds.length === 0" class="empty-state">
      <div class="empty-icon">📊</div>
      <p>暂无监控基金</p>
      <p class="empty-hint">在上方搜索框中添加基金开始监控</p>
    </div>

    <div v-else class="fund-list">
      <div 
        v-for="fund in sortedFunds" 
        :key="fund.code" 
        class="fund-card"
        :class="{ 'collapsed': collapsedCodes.has(fund.code) }"
      >
        <!-- 基金头部 -->
        <div class="fund-header" @click="toggleCollapse(fund.code)">
          <div class="fund-main-info">
            <span class="fund-code">{{ fund.code }}</span>
            <span class="fund-name">{{ fund.name }}</span>
          </div>
          <div class="fund-estimate">
            <span class="estimate-value" :class="getChangeClass(fund.gszzl)">
              {{ formatGsz(fund) }}
            </span>
            <span class="estimate-change" :class="getChangeClass(fund.gszzl)">
              {{ formatChange(fund.gszzl) }}
            </span>
          </div>
          <!-- 今日盈亏（如果有持仓） -->
          <div v-if="holdings[fund.code]" class="fund-profit-today">
            <span class="profit-label">今日盈亏</span>
            <span class="profit-value" :class="getHoldingProfitTodayClass(fund)">
              {{ getHoldingProfitToday(fund) >= 0 ? '+' : '' }}{{ getHoldingProfitToday(fund).toFixed(2) }}
            </span>
          </div>
          <div class="fund-actions" @click.stop>
            <button class="btn-icon" @click="openHoldingModal(fund)" title="设置持仓">💰</button>
            <button class="btn-icon btn-del" @click="removeFund(fund.code)" title="删除">🗑️</button>
          </div>
        </div>

        <!-- 持仓信息（若有） -->
        <div v-if="holdings[fund.code] && !collapsedCodes.has(fund.code)" class="fund-holding">
          <div class="holding-row">
            <span class="holding-label">持有份额</span>
            <span class="holding-value">{{ holdings[fund.code].share.toFixed(2) }} 份</span>
          </div>
          <div class="holding-row">
            <span class="holding-label">成本价</span>
            <span class="holding-value">{{ holdings[fund.code].cost.toFixed(4) }}</span>
          </div>
          <div class="holding-row">
            <span class="holding-label">持有金额(估)</span>
            <span class="holding-value">¥{{ getHoldingAmount(fund).toFixed(2) }}</span>
          </div>
          <div class="holding-row">
            <span class="holding-label">今日收益(估)</span>
            <span class="holding-value" :class="getHoldingProfitTodayClass(fund)">
              {{ getHoldingProfitToday(fund) >= 0 ? '+' : '' }}{{ getHoldingProfitToday(fund).toFixed(2) }}
            </span>
          </div>
          <div class="holding-row">
            <span class="holding-label">持有收益</span>
            <span class="holding-value" :class="getHoldingProfitTotalClass(fund)">
              {{ getHoldingProfitTotal(fund) >= 0 ? '+' : '' }}{{ getHoldingProfitTotal(fund).toFixed(2) }}
            </span>
          </div>
        </div>

        <!-- 持仓详情（展开时显示） -->
        <div v-if="fund.holdings && fund.holdings.length > 0 && !collapsedCodes.has(fund.code)" class="fund-holdings-detail">
          <div class="holdings-header">
            <span>前十大持仓</span>
            <span class="update-time" v-if="fund.gztime">{{ fund.gztime }} 更新</span>
          </div>
          <div class="holdings-list">
            <div v-for="(stock, idx) in fund.holdings" :key="stock.code" class="holding-item">
              <span class="holding-index">{{ idx + 1 }}</span>
              <span class="holding-name">{{ stock.name }}</span>
              <span class="holding-weight">{{ stock.weight }}</span>
              <span class="holding-change" :class="getChangeClass(stock.change)">
                {{ stock.change !== null ? (stock.change >= 0 ? '+' : '') + stock.change.toFixed(2) + '%' : '-' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 持仓设置弹窗 -->
    <div v-if="holdingModal.open" class="modal-overlay" @click.self="closeHoldingModal">
      <div class="modal-box">
        <h3>设置持仓</h3>
        <div class="fund-modal-info">
          <span class="fund-name">{{ holdingModal.fund?.name }}</span>
          <span class="fund-code">#{{ holdingModal.fund?.code }}</span>
          <div class="fund-nav-info">
            <span>上一交易日净值：</span>
            <span class="nav-value">{{ holdingModal.fund?.dwjz || '-' }}</span>
          </div>
        </div>
        <div class="form-group">
          <label>持有金额 (元)</label>
          <input 
            v-model.number="holdingForm.amount" 
            type="number" 
            step="any"
            placeholder="请输入持有金额"
            class="modal-input"
          />
          <div class="form-hint" v-if="holdingForm.amount && holdingModal.fund?.dwjz">
            折算份额：{{ calculateShare(holdingForm.amount, holdingModal.fund.dwjz).toFixed(2) }} 份
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="closeHoldingModal">取消</button>
          <button class="btn btn-danger" @click="clearHolding" v-if="holdingModal.fund && holdings[holdingModal.fund.code]">清空</button>
          <button class="btn btn-primary" @click="saveHolding" :disabled="!holdingForm.amount">保存</button>
        </div>
      </div>
    </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import FundWatchlist from './FundWatchlist.vue'

export default {
  name: 'FundRealtime',
  components: { FundWatchlist },
  setup() {
    // ==================== 状态 ====================
    const funds = ref([])
    const holdings = ref({})  // { code: { share, cost } }
    const collapsedCodes = ref(new Set())
    const refreshing = ref(false)
    const refreshMs = ref(30000)
    const searchTerm = ref('')
    const searchResults = ref([])
    const selectedFunds = ref([])
    const showDropdown = ref(false)
    const dropdownRef = ref(null)
    const searchTimeoutRef = ref(null)
    const refreshTimer = ref(null)

    // 持仓弹窗
    const holdingModal = ref({ open: false, fund: null })
    const holdingForm = ref({ amount: '' })

    // ==================== 计算属性 ====================
    const isTradingTime = computed(() => {
      const now = new Date()
      const day = now.getDay()
      if (day === 0 || day === 6) return false
      const h = now.getHours()
      const m = now.getMinutes()
      const minutes = h * 60 + m
      // 9:30 - 11:30, 13:00 - 15:00
      return (minutes >= 570 && minutes <= 690) || (minutes >= 780 && minutes <= 900)
    })

    const sortedFunds = computed(() => {
      return [...funds.value].sort((a, b) => {
        const aChange = typeof a.gszzl === 'number' ? a.gszzl : parseFloat(a.gszzl) || 0
        const bChange = typeof b.gszzl === 'number' ? b.gszzl : parseFloat(b.gszzl) || 0
        return bChange - aChange
      })
    })

    const hasHoldings = computed(() => {
      return Object.keys(holdings.value).some(code => 
        funds.value.some(f => f.code === code)
      )
    })

    const totalAsset = computed(() => {
      let total = 0
      funds.value.forEach(fund => {
        const h = holdings.value[fund.code]
        if (h && h.share) {
          total += getHoldingAmount(fund)
        }
      })
      return total
    })

    const totalProfitToday = computed(() => {
      let total = 0
      funds.value.forEach(fund => {
        const h = holdings.value[fund.code]
        if (h && h.share) {
          total += getHoldingProfitToday(fund)
        }
      })
      return total
    })

    const totalProfitTotal = computed(() => {
      let total = 0
      funds.value.forEach(fund => {
        const h = holdings.value[fund.code]
        if (h && h.share && h.cost) {
          total += getHoldingProfitTotal(fund)
        }
      })
      return total
    })

    const profitTodayClass = computed(() => totalProfitToday.value >= 0 ? 'up' : 'down')
    const profitTotalClass = computed(() => totalProfitTotal.value >= 0 ? 'up' : 'down')

    // ==================== 方法 ====================
    const getChangeClass = (val) => {
      const num = typeof val === 'number' ? val : parseFloat(val)
      if (isNaN(num)) return ''
      return num > 0 ? 'up' : num < 0 ? 'down' : ''
    }

    const formatGsz = (fund) => {
      const gsz = fund.gsz || fund.dwjz
      return gsz ? parseFloat(gsz).toFixed(4) : '-'
    }

    const formatChange = (val) => {
      const num = typeof val === 'number' ? val : parseFloat(val)
      if (isNaN(num)) return '-'
      return (num >= 0 ? '+' : '') + num.toFixed(2) + '%'
    }

    const getHoldingAmount = (fund) => {
      const h = holdings.value[fund.code]
      if (!h || !h.share) return 0
      const nav = parseFloat(fund.gsz) || parseFloat(fund.dwjz) || 0
      return h.share * nav
    }

    const getHoldingProfitToday = (fund) => {
      const h = holdings.value[fund.code]
      if (!h || !h.share) return 0
      const amount = getHoldingAmount(fund)
      const rate = typeof fund.gszzl === 'number' ? fund.gszzl : parseFloat(fund.gszzl) || 0
      return amount - (amount / (1 + rate / 100))
    }

    const getHoldingProfitTotal = (fund) => {
      const h = holdings.value[fund.code]
      if (!h || !h.share || !h.cost) return 0
      const nav = parseFloat(fund.gsz) || parseFloat(fund.dwjz) || 0
      return (nav - h.cost) * h.share
    }

    const getHoldingProfitTodayClass = (fund) => getHoldingProfitToday(fund) >= 0 ? 'up' : 'down'
    const getHoldingProfitTotalClass = (fund) => getHoldingProfitTotal(fund) >= 0 ? 'up' : 'down'

    // 根据金额和净值计算份额
    const calculateShare = (amount, nav) => {
      const a = parseFloat(amount)
      const n = parseFloat(nav)
      if (isNaN(a) || isNaN(n) || n <= 0) return 0
      return a / n
    }

    const toggleCollapse = (code) => {
      const next = new Set(collapsedCodes.value)
      if (next.has(code)) {
        next.delete(code)
      } else {
        next.add(code)
      }
      collapsedCodes.value = next
      localStorage.setItem('realtime_collapsed', JSON.stringify([...next]))
    }

    const isSelected = (code) => selectedFunds.value.some(f => f.CODE === code)

    const toggleSelectFund = (fund) => {
      const exists = selectedFunds.value.find(f => f.CODE === fund.CODE)
      if (exists) {
        selectedFunds.value = selectedFunds.value.filter(f => f.CODE !== fund.CODE)
      } else {
        selectedFunds.value = [...selectedFunds.value, fund]
        // 选中后自动清空
        searchTerm.value = ''
        searchResults.value = []
        showDropdown.value = false
      }
    }

    // 搜索基金
    const performSearch = async (val) => {
      if (!val.trim()) {
        searchResults.value = []
        return
      }
      const callbackName = `SuggestData_${Date.now()}`
      const url = `https://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx?m=1&key=${encodeURIComponent(val)}&callback=${callbackName}&_=${Date.now()}`
      
      try {
        await new Promise((resolve, reject) => {
          window[callbackName] = (data) => {
            if (data && data.Datas) {
              const fundsOnly = data.Datas.filter(d => 
                d.CATEGORY === 700 || 
                d.CATEGORY === "700" || 
                d.CATEGORYDESC === "基金"
              )
              searchResults.value = fundsOnly
            }
            delete window[callbackName]
            resolve()
          }

          const script = document.createElement('script')
          script.src = url
          script.async = true
          script.onload = () => {
            if (document.body.contains(script)) document.body.removeChild(script)
          }
          script.onerror = () => {
            if (document.body.contains(script)) document.body.removeChild(script)
            delete window[callbackName]
            reject(new Error('搜索请求失败'))
          }
          document.body.appendChild(script)
        })
      } catch (e) {
        console.error('搜索失败', e)
      }
    }

    const handleSearchInput = () => {
      if (searchTimeoutRef.value) clearTimeout(searchTimeoutRef.value)
      searchTimeoutRef.value = setTimeout(() => performSearch(searchTerm.value), 300)
    }

    // 获取基金数据（JSONP）
    const fetchFundData = async (code) => {
      return new Promise((resolve, reject) => {
        const gzUrl = `https://fundgz.1234567.com.cn/js/${code}.js?rt=${Date.now()}`
        const scriptGz = document.createElement('script')
        scriptGz.src = gzUrl

        const originalJsonpgz = window.jsonpgz
        window.jsonpgz = (json) => {
          window.jsonpgz = originalJsonpgz
          if (!json || typeof json !== 'object') {
            reject(new Error('未获取到基金估值数据'))
            return
          }
          const gszzlNum = Number(json.gszzl)
          const gzData = {
            code: json.fundcode,
            name: json.name,
            dwjz: json.dwjz,
            gsz: json.gsz,
            gztime: json.gztime,
            jzrq: json.jzrq,
            gszzl: Number.isFinite(gszzlNum) ? gszzlNum : json.gszzl
          }

          // 获取持仓数据
          fetchHoldings(code).then(holdings => {
            resolve({ ...gzData, holdings })
          }).catch(() => {
            resolve(gzData)
          })
        }

        scriptGz.onerror = () => {
          window.jsonpgz = originalJsonpgz
          if (document.body.contains(scriptGz)) document.body.removeChild(scriptGz)
          reject(new Error('基金数据加载失败'))
        }

        document.body.appendChild(scriptGz)
        setTimeout(() => {
          if (document.body.contains(scriptGz)) document.body.removeChild(scriptGz)
        }, 5000)
      })
    }

    // 获取持仓数据
    const fetchHoldings = async (code) => {
      return new Promise((resolve) => {
        const url = `https://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code=${code}&topline=10&year=&month=&rt=${Date.now()}`
        const script = document.createElement('script')
        script.src = url
        script.onload = async () => {
          let holdings = []
          const html = window.apidata?.content || ''
          
          // 尝试先获取第一个table（最新季度的持仓）
          const tableMatch = html.match(/<table[\s\S]*?<\/table>/i)
          const tableHtml = tableMatch ? tableMatch[0] : html
          
          // 匹配所有tr行
          const rows = tableHtml.match(/<tr[\s\S]*?<\/tr>/gi) || []
          
          for (const r of rows) {
            // 跳过表头行（包含th的行）
            if (r.includes('<th') || r.includes('</th>')) continue
            
            // 提取所有td内容
            const cellMatches = r.match(/<td[\s\S]*?>([\s\S]*?)<\/td>/gi) || []
            const cells = cellMatches.map(td => td.replace(/<[^>]*>/g, '').trim())
            
            // 查找股票代码（6位数字）
            const codeIdx = cells.findIndex(txt => /^\d{6}$/.test(txt))
            // 查找占比（包含%的数字）
            const weightIdx = cells.findIndex(txt => /\d+(?:\.\d+)?\s*%/.test(txt))
            
            if (codeIdx >= 0 && weightIdx >= 0) {
              holdings.push({
                code: cells[codeIdx],
                name: cells[codeIdx + 1] || '',
                weight: cells[weightIdx],
                change: null
              })
            }
          }
          
          // 取前10个
          holdings = holdings.slice(0, 10)

          // 获取股票涨跌幅
          if (holdings.length) {
            try {
              const getTencentPrefix = (c) => {
                if (c.startsWith('6') || c.startsWith('9')) return 'sh'
                if (c.startsWith('0') || c.startsWith('3')) return 'sz'
                if (c.startsWith('4') || c.startsWith('8')) return 'bj'
                return 'sz'
              }
              const tencentCodes = holdings.map(h => `s_${getTencentPrefix(h.code)}${h.code}`).join(',')
              const quoteUrl = `https://qt.gtimg.cn/q=${tencentCodes}`

              await new Promise((res) => {
                const scriptQuote = document.createElement('script')
                scriptQuote.src = quoteUrl
                scriptQuote.onload = () => {
                  holdings.forEach(h => {
                    const varName = `v_s_${getTencentPrefix(h.code)}${h.code}`
                    const dataStr = window[varName]
                    if (dataStr) {
                      const parts = dataStr.split('~')
                      if (parts.length > 5) {
                        h.change = parseFloat(parts[5])
                      }
                    }
                  })
                  if (document.body.contains(scriptQuote)) document.body.removeChild(scriptQuote)
                  res()
                }
                scriptQuote.onerror = () => {
                  if (document.body.contains(scriptQuote)) document.body.removeChild(scriptQuote)
                  res()
                }
                document.body.appendChild(scriptQuote)
              })
            } catch (e) {
              console.error('获取股票涨跌幅失败', e)
            }
          }

          if (document.body.contains(script)) document.body.removeChild(script)
          resolve(holdings)
        }
        script.onerror = () => {
          if (document.body.contains(script)) document.body.removeChild(script)
          resolve([])
        }
        document.body.appendChild(script)
      })
    }

    // 从自选添加
    const addFundToRealtime = async (fundInfo) => {
      const code = fundInfo.fund_code || fundInfo.code || fundInfo.CODE
      if (!code) return
      
      // 已存在检查
      if (funds.value.some(f => f.code === String(code))) {
         return 
      }
      
      refreshing.value = true
      try {
        const data = await fetchFundData(String(code))
        funds.value = [data, ...funds.value]
        localStorage.setItem('realtime_funds', JSON.stringify(funds.value))
      } catch(e) {
          console.error(e)
      } finally {
          refreshing.value = false
      }
    }

    // 批量添加基金
    const batchAddFunds = async () => {
      if (selectedFunds.value.length === 0) return
      refreshing.value = true
      
      try {
        const newFunds = []
        for (const f of selectedFunds.value) {
          if (funds.value.some(existing => existing.code === f.CODE)) continue
          try {
            const data = await fetchFundData(f.CODE)
            newFunds.push(data)
          } catch (e) {
            console.error(`添加基金 ${f.CODE} 失败`, e)
          }
        }
        
        if (newFunds.length > 0) {
          const updated = [...newFunds, ...funds.value]
          funds.value = updated
          localStorage.setItem('realtime_funds', JSON.stringify(updated))
        }
        
        selectedFunds.value = []
        searchTerm.value = ''
        searchResults.value = []
        showDropdown.value = false
      } catch (e) {
        console.error('批量添加失败', e)
      } finally {
        refreshing.value = false
      }
    }

    // 刷新所有基金
    const refreshAll = async () => {
      if (refreshing.value || funds.value.length === 0) return
      refreshing.value = true
      
      try {
        const updated = []
        for (const fund of funds.value) {
          try {
            const data = await fetchFundData(fund.code)
            updated.push(data)
          } catch (e) {
            console.error(`刷新基金 ${fund.code} 失败`, e)
            updated.push(fund) // 保留旧数据
          }
        }
        
        funds.value = updated
        localStorage.setItem('realtime_funds', JSON.stringify(updated))
      } catch (e) {
        console.error('刷新失败', e)
      } finally {
        refreshing.value = false
      }
    }

    // 删除基金
    const removeFund = (code) => {
      funds.value = funds.value.filter(f => f.code !== code)
      localStorage.setItem('realtime_funds', JSON.stringify(funds.value))
    }

    // 持仓弹窗
    const openHoldingModal = (fund) => {
      holdingModal.value = { open: true, fund }
      const h = holdings.value[fund.code]
      // 如果有现有持仓，根据份额和净值计算金额
      if (h && h.share) {
        const nav = parseFloat(fund.dwjz) || 1
        holdingForm.value = {
          amount: (h.share * nav).toFixed(2)
        }
      } else {
        holdingForm.value = { amount: '' }
      }
    }

    const closeHoldingModal = () => {
      holdingModal.value = { open: false, fund: null }
    }

    const saveHolding = () => {
      const fund = holdingModal.value.fund
      if (!fund) return
      
      const amount = parseFloat(holdingForm.value.amount)
      const nav = parseFloat(fund.dwjz)
      
      if (!amount || !nav || nav <= 0) {
        closeHoldingModal()
        return
      }
      
      const share = amount / nav
      
      const newHoldings = { ...holdings.value }
      newHoldings[fund.code] = {
        share: share,
        cost: nav  // 成本价就是录入时的净值
      }
      
      holdings.value = newHoldings
      localStorage.setItem('realtime_holdings', JSON.stringify(newHoldings))
      closeHoldingModal()
    }

    const clearHolding = () => {
      const fund = holdingModal.value.fund
      if (!fund) return
      
      const newHoldings = { ...holdings.value }
      delete newHoldings[fund.code]
      holdings.value = newHoldings
      localStorage.setItem('realtime_holdings', JSON.stringify(newHoldings))
      closeHoldingModal()
    }

    const saveRefreshMs = () => {
      localStorage.setItem('realtime_refresh_ms', refreshMs.value.toString())
      // 重启定时器
      startRefreshTimer()
    }

    const startRefreshTimer = () => {
      if (refreshTimer.value) clearInterval(refreshTimer.value)
      refreshTimer.value = setInterval(() => {
        refreshAll()
      }, refreshMs.value)
    }

    // 点击外部关闭下拉框
    const handleClickOutside = (event) => {
      if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
        showDropdown.value = false
      }
    }

    // ==================== 生命周期 ====================
    onMounted(() => {
      // 加载本地数据
      try {
        const savedFunds = JSON.parse(localStorage.getItem('realtime_funds') || '[]')
        if (Array.isArray(savedFunds) && savedFunds.length) {
          funds.value = savedFunds
          refreshAll()
        }
        
        const savedHoldings = JSON.parse(localStorage.getItem('realtime_holdings') || '{}')
        if (savedHoldings && typeof savedHoldings === 'object') {
          holdings.value = savedHoldings
        }
        
        const savedMs = parseInt(localStorage.getItem('realtime_refresh_ms') || '30000', 10)
        if (Number.isFinite(savedMs) && savedMs >= 5000) {
          refreshMs.value = savedMs
        }
        
        const savedCollapsed = JSON.parse(localStorage.getItem('realtime_collapsed') || '[]')
        if (Array.isArray(savedCollapsed)) {
          collapsedCodes.value = new Set(savedCollapsed)
        }
      } catch (e) {
        console.error('加载本地数据失败', e)
      }
      
      startRefreshTimer()
      document.addEventListener('mousedown', handleClickOutside)
    })

    onUnmounted(() => {
      if (refreshTimer.value) clearInterval(refreshTimer.value)
      document.removeEventListener('mousedown', handleClickOutside)
    })

    return {
      funds,
      holdings,
      collapsedCodes,
      refreshing,
      refreshMs,
      searchTerm,
      searchResults,
      selectedFunds,
      addFundToRealtime,
      showDropdown,
      dropdownRef,
      holdingModal,
      holdingForm,
      isTradingTime,
      sortedFunds,
      hasHoldings,
      totalAsset,
      totalProfitToday,
      totalProfitTotal,
      profitTodayClass,
      profitTotalClass,
      getChangeClass,
      formatGsz,
      formatChange,
      getHoldingAmount,
      getHoldingProfitToday,
      getHoldingProfitTotal,
      getHoldingProfitTodayClass,
      getHoldingProfitTotalClass,
      toggleCollapse,
      isSelected,
      toggleSelectFund,
      handleSearchInput,
      batchAddFunds,
      refreshAll,
      removeFund,
      openHoldingModal,
      closeHoldingModal,
      saveHolding,
      clearHolding,
      saveRefreshMs,
      calculateShare
    }
  }
}
</script>

<style scoped>
.realtime-container {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-md);
  height: 100%;
  overflow-y: auto;
}

/* 头部 */
.realtime-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.header-icon {
  font-size: 1.2em;
}

.count-badge {
  background: var(--primary-color);
  color: white;
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 10px;
}

.trade-status {
  font-size: 0.75rem;
  padding: 4px 10px;
  border-radius: 12px;
}

.trade-status.trading {
  background: rgba(82, 196, 26, 0.1);
  color: var(--success-color);
}

.trade-status.closed {
  background: rgba(255, 77, 79, 0.1);
  color: var(--danger-color);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.interval-select {
  padding: 6px 10px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 0.8rem;
  background: var(--bg-card);
  cursor: pointer;
}

/* 搜索区域 */
.search-section {
  position: relative;
  margin-bottom: 16px;
}

.search-box {
  display: flex;
  gap: 8px;
}

.search-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.1);
}

.search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  max-height: 240px;
  overflow-y: auto;
  z-index: 1000;
  margin-top: 4px;
  box-shadow: var(--shadow-lg);
}

.dropdown-item {
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: all 0.15s;
}

.dropdown-item:hover {
  background: var(--bg-primary);
}

.dropdown-item.selected {
  background: rgba(22, 119, 255, 0.1);
}

.dropdown-item .fund-code {
  font-weight: 600;
  color: var(--primary-color);
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 13px;
  min-width: 60px;
}

.dropdown-item .fund-name {
  flex: 1;
  color: var(--text-primary);
  font-size: 14px;
}

.check-icon {
  color: var(--success-color);
  font-weight: bold;
}

.selected-funds {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.selected-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(22, 119, 255, 0.1);
  color: var(--primary-color);
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  cursor: pointer;
}

.selected-tag:hover {
  background: rgba(22, 119, 255, 0.2);
}

.remove-icon {
  font-size: 14px;
  opacity: 0.7;
}

/* 汇总卡片 */
.summary-card {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(22, 119, 255, 0.05) 0%, rgba(9, 88, 217, 0.05) 100%);
  border-radius: var(--radius-md);
  margin-bottom: 16px;
}

.summary-item {
  text-align: center;
}

.summary-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.summary-value {
  font-size: 18px;
  font-weight: 700;
  font-family: 'SF Mono', Menlo, monospace;
}

.summary-value.up {
  color: var(--danger-color);
}

.summary-value.down {
  color: var(--success-color);
}

/* 基金列表 */
.fund-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.fund-card {
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--border-color);
  transition: all 0.2s;
}

.fund-card:hover {
  box-shadow: var(--shadow-sm);
}

.fund-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  cursor: pointer;
}

.fund-main-info {
  flex: 1;
  min-width: 0;
}

.fund-main-info .fund-code {
  font-weight: 600;
  color: var(--primary-color);
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 13px;
  margin-right: 8px;
}

.fund-main-info .fund-name {
  color: var(--text-primary);
  font-size: 14px;
}

.fund-estimate {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.estimate-value {
  font-size: 16px;
  font-weight: 700;
  font-family: 'SF Mono', Menlo, monospace;
}

.estimate-change {
  font-size: 13px;
  font-weight: 600;
}

.estimate-value.up, .estimate-change.up {
  color: var(--danger-color);
}

.estimate-value.down, .estimate-change.down {
  color: var(--success-color);
}

/* 今日盈亏 */
.fund-profit-today {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  min-width: 80px;
  padding: 0 12px;
  border-left: 1px solid var(--border-color);
}

.fund-profit-today .profit-label {
  font-size: 11px;
  color: var(--text-tertiary);
}

.fund-profit-today .profit-value {
  font-size: 15px;
  font-weight: 700;
  font-family: 'SF Mono', Menlo, monospace;
}

.fund-profit-today .profit-value.up {
  color: var(--danger-color);
}

.fund-profit-today .profit-value.down {
  color: var(--success-color);
}

.fund-actions {
  display: flex;
  gap: 6px;
}

/* 持仓信息 */
.fund-holding {
  padding: 12px 16px;
  background: rgba(22, 119, 255, 0.03);
  border-top: 1px solid var(--border-color);
}

.holding-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 13px;
}

.holding-label {
  color: var(--text-secondary);
}

.holding-value {
  font-weight: 500;
  font-family: 'SF Mono', Menlo, monospace;
}

.holding-value.up {
  color: var(--danger-color);
}

.holding-value.down {
  color: var(--success-color);
}

/* 持仓详情 */
.fund-holdings-detail {
  padding: 12px 16px;
  border-top: 1px solid var(--border-color);
}

.holdings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 13px;
  color: var(--text-secondary);
}

.update-time {
  font-size: 11px;
}

.holdings-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.holding-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
  font-size: 13px;
}

.holding-index {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--border-color);
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.holding-name {
  flex: 1;
  color: var(--text-primary);
}

.holding-weight {
  color: var(--text-secondary);
  font-family: 'SF Mono', Menlo, monospace;
}

.holding-change {
  min-width: 60px;
  text-align: right;
  font-family: 'SF Mono', Menlo, monospace;
  font-weight: 500;
}

.holding-change.up {
  color: var(--danger-color);
}

.holding-change.down {
  color: var(--success-color);
}

/* 按钮样式 */
.btn {
  padding: 8px 14px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-add {
  background: var(--primary-color);
  color: white;
}

.btn-add:hover:not(:disabled) {
  background: #0958d9;
}

.btn-add:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-refresh {
  padding: 6px 10px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
}

.btn-refresh:hover:not(:disabled) {
  background: var(--bg-primary);
}

.btn-icon {
  padding: 4px 8px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 14px;
  opacity: 0.7;
  transition: all 0.2s;
}

.btn-icon:hover {
  opacity: 1;
  transform: scale(1.1);
}

.btn-icon.btn-del:hover {
  color: var(--danger-color);
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-secondary {
  background: var(--bg-primary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-danger {
  background: var(--danger-color);
  color: white;
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-hint {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-top: 8px;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-box {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  min-width: 360px;
  max-width: 90vw;
  box-shadow: var(--shadow-lg);
}

.modal-box h3 {
  margin: 0 0 16px 0;
  font-size: 1.1rem;
}

.fund-modal-info {
  margin-bottom: 16px;
  padding: 12px;
  background: var(--bg-primary);
  border-radius: 8px;
}

.fund-modal-info .fund-name {
  font-weight: 600;
  display: block;
  margin-bottom: 4px;
}

.fund-modal-info .fund-code {
  font-size: 12px;
  color: var(--text-secondary);
}

.fund-modal-info .fund-nav-info {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--border-color);
  font-size: 12px;
  color: var(--text-secondary);
}

.fund-modal-info .nav-value {
  font-weight: 600;
  color: var(--primary-color);
  font-family: 'SF Mono', Menlo, monospace;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.form-hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  background: rgba(22, 119, 255, 0.05);
  padding: 6px 10px;
  border-radius: 6px;
}

.modal-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 14px;
}

.modal-input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

/* New Layout Styles */
.realtime-layout {
  display: flex;
  height: calc(100vh - 80px); /* Adjust for app header */
  gap: 16px;
  padding: 16px;
  box-sizing: border-box;
}

.realtime-sidebar {
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  overflow: hidden;
}

.realtime-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  /* Reset container styles if needed */
}

/* Adjust original container to fit inside main */
.realtime-main .realtime-container {
  max-width: none;
  margin: 0;
  padding: 0;
  height: auto;
}
</style>
