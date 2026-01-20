<template>
  <div class="fund-screening">
    <!-- 顶部状态栏 -->
    <div class="screening-header">
      <div class="header-title">
        <h2>🔍 基金智能筛选</h2>
        <p class="subtitle">多维度数据分析，科学筛选优质基金</p>
      </div>
      <div class="header-actions">
        <div class="db-status">
          <span class="status-label">数据库状态:</span>
          <span class="status-value" :class="{ 'has-data': dbStatus.basic_count > 0 }">
            {{ dbStatus.basic_count > 0 ? `${dbStatus.basic_count}只基金` : '暂无数据' }}
          </span>
          <span v-if="dbStatus.latest_update" class="update-time">
            更新于 {{ formatDate(dbStatus.latest_update) }}
          </span>
        </div>
        <button 
          class="btn-update" 
          @click="showUpdateModal = true"
          :disabled="updateStatus.running"
        >
          <span v-if="updateStatus.running" class="loading-spinner"></span>
          {{ updateStatus.running ? '更新中...' : '📥 更新数据' }}
        </button>
      </div>
    </div>

    <!-- 更新进度弹窗 -->
    <div v-if="showUpdateModal" class="modal-overlay" @click.self="closeUpdateModal">
      <div class="modal-content update-modal">
        <div class="modal-header">
          <h3>更新筛选数据库</h3>
          <button class="btn-close" @click="closeUpdateModal">×</button>
        </div>
        <div class="modal-body">
          <!-- 更新选项 -->
          <div v-if="!updateStatus.running" class="update-options">
            <div class="option-group">
              <label>选择基金类型:</label>
              <div class="checkbox-group">
                <label v-for="type in fundTypeOptions" :key="type.value">
                  <input type="checkbox" v-model="selectedFundTypes" :value="type.value">
                  {{ type.label }}
                </label>
              </div>
            </div>
            
            <div class="option-group">
              <label>更新数量限制 (测试用):</label>
              <input type="number" v-model.number="updateLimit" placeholder="不限制" min="1">
            </div>
            
            <button class="btn-start-update" @click="startUpdate">
              🚀 开始更新数据
            </button>
            
            <div class="secondary-actions">
              <button class="btn-recalculate" @click="recalculateRankings" :disabled="recalculating">
                {{ recalculating ? '⏳ 计算中...' : '🔄 重新计算排名' }}
              </button>
            </div>
            <p class="mode-desc">
              <strong>更新数据</strong>：直接获取基金完整数据，包括业绩、风险指标、持仓等<br>
              <strong>重新计算排名</strong>：在同类型基金中计算排名百分位和4433法则
            </p>
          </div>

          <!-- 更新进度 -->
          <div v-else class="update-progress">
            <div class="progress-info">
              <span class="current-fund">{{ updateStatus.current_fund || updateStatus.message || '准备中...' }}</span>
              <span class="progress-text">
                {{ updateStatus.progress || 0 }} / {{ updateStatus.total || '?' }} 只基金
              </span>
            </div>
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: progressPercent + '%' }"
              ></div>
            </div>
            <p class="progress-message">{{ updateStatus.message }}</p>
            <button class="btn-stop" @click="stopUpdate">停止更新</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 筛选面板 -->
    <div class="screening-panel">
      <!-- 预设策略 -->
      <div class="strategy-section">
        <h3>📊 快速筛选策略</h3>
        <div class="strategy-cards">
          <div 
            v-for="strategy in strategies" 
            :key="strategy.id"
            class="strategy-card"
            :class="{ active: selectedStrategy === strategy.id }"
            @click="selectStrategy(strategy.id)"
          >
            <div class="strategy-name">{{ strategy.name }}</div>
            <div class="strategy-desc">{{ strategy.description }}</div>
            <div class="strategy-tags">
              <span v-for="tag in strategy.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 自定义筛选条件 -->
      <div class="filter-section">
        <div class="filter-header">
          <h3>⚙️ 自定义筛选条件</h3>
          <button class="btn-reset" @click="resetFilters">重置</button>
        </div>
        
        <div class="filter-card">
          <!-- 基金类型 - 多级分类选择 -->
          <div class="filter-row type-row">
            <div class="filter-label">
              <span class="label-icon">📁</span>
              <span>基金类型</span>
              <span class="selected-count" v-if="filters.fund_types.length > 0">
                (已选 {{ filters.fund_types.length }} 项)
              </span>
            </div>
            <div class="type-categories">
              <div 
                v-for="category in fundTypeCategories" 
                :key="category.name"
                class="type-category"
              >
                <!-- 分类标题 -->
                <div 
                  class="category-header"
                  @click="toggleCategory(category.name)"
                >
                  <span class="category-toggle">
                    {{ isCategoryExpanded(category.name) ? '▼' : '▶' }}
                  </span>
                  <span class="category-icon">{{ category.icon }}</span>
                  <span class="category-name">{{ category.name }}</span>
                  <span 
                    class="category-checkbox"
                    :class="{ 
                      'checked': isCategoryAllSelected(category),
                      'partial': isCategoryPartialSelected(category)
                    }"
                    @click.stop="selectCategory(category)"
                    title="全选/取消该分类"
                  >
                    <template v-if="isCategoryAllSelected(category)">✓</template>
                    <template v-else-if="isCategoryPartialSelected(category)">-</template>
                  </span>
                </div>
                <!-- 分类下的类型标签 -->
                <div 
                  class="category-types" 
                  v-show="isCategoryExpanded(category.name)"
                >
                  <span 
                    v-for="type in category.types" 
                    :key="type.value"
                    class="type-tag"
                    :class="{ active: filters.fund_types.includes(type.value) }"
                    @click="toggleFundType(type.value)"
                  >
                    {{ type.label }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- 主要指标筛选 - 网格布局 -->
          <div class="filter-grid">
            <!-- 收益率 -->
            <div class="filter-item">
              <div class="filter-label">
                <span class="label-icon">📈</span>
                <span>近1年收益率</span>
              </div>
              <div class="range-input-group">
                <input type="number" v-model.number="filters.return_1y_min" placeholder="最小">
                <span class="range-sep">~</span>
                <input type="number" v-model.number="filters.return_1y_max" placeholder="最大">
                <span class="unit">%</span>
              </div>
            </div>

            <!-- 最大回撤 -->
            <div class="filter-item">
              <div class="filter-label">
                <span class="label-icon">📉</span>
                <span>最大回撤上限</span>
              </div>
              <div class="single-input-group">
                <input type="number" v-model.number="filters.max_drawdown_max" placeholder="如: 20">
                <span class="unit">%</span>
              </div>
            </div>

            <!-- 夏普比率 -->
            <div class="filter-item">
              <div class="filter-label">
                <span class="label-icon">⚖️</span>
                <span>夏普比率下限</span>
              </div>
              <div class="single-input-group">
                <input type="number" v-model.number="filters.sharpe_min" placeholder="如: 1" step="0.1">
              </div>
            </div>

            <!-- 波动率 -->
            <div class="filter-item">
              <div class="filter-label">
                <span class="label-icon">🌊</span>
                <span>波动率上限</span>
              </div>
              <div class="single-input-group">
                <input type="number" v-model.number="filters.volatility_max" placeholder="如: 20">
                <span class="unit">%</span>
              </div>
            </div>

            <!-- 卡玛比率 -->
            <div class="filter-item">
              <div class="filter-label">
                <span class="label-icon">🎯</span>
                <span>卡玛比率下限</span>
              </div>
              <div class="single-input-group">
                <input type="number" v-model.number="filters.calmar_min" placeholder="如: 1" step="0.1">
              </div>
            </div>

            <!-- 基金规模 -->
            <div class="filter-item">
              <div class="filter-label">
                <span class="label-icon">💰</span>
                <span>基金规模</span>
              </div>
              <div class="range-input-group">
                <input type="number" v-model.number="filters.scale_min" placeholder="最小">
                <span class="range-sep">~</span>
                <input type="number" v-model.number="filters.scale_max" placeholder="最大">
                <span class="unit">亿</span>
              </div>
            </div>

            <!-- 机构持有 -->
            <div class="filter-item">
              <div class="filter-label">
                <span class="label-icon">🏛️</span>
                <span>机构持有比例</span>
              </div>
              <div class="single-input-group">
                <input type="number" v-model.number="filters.institution_ratio_min" placeholder="如: 30">
                <span class="unit">%以上</span>
              </div>
            </div>
          </div>
        </div>

        <div class="filter-actions">
          <button class="btn-search" @click="search(true)">
            🔍 开始筛选
          </button>
        </div>
      </div>
    </div>

    <!-- 筛选结果 -->
    <div class="results-section" v-if="results.length > 0 || loading">
      <div class="results-header">
        <div class="results-title-row">
          <h3>筛选结果 <span class="result-count">(共 {{ totalCount }} 只)</span></h3>
        </div>
        
        <!-- 类型快速筛选 - 多级菜单 -->
        <div class="quick-type-filter">
          <span class="filter-label-inline">类型筛选:</span>
          <div class="quick-type-menu">
            <!-- 全部按钮 -->
            <span 
              class="quick-tag"
              :class="{ active: quickTypeFilter === '' }"
              @click="setQuickTypeFilter('')"
            >
              全部
            </span>
            
            <!-- 多级分类下拉 -->
            <div 
              v-for="category in quickTypeCategories" 
              :key="category.name"
              class="quick-type-dropdown"
              @click.stop
            >
              <span 
                class="quick-tag dropdown-trigger"
                :class="{ 
                  active: isCategoryTypeActive(category),
                  'has-active': hasCategoryActiveType(category)
                }"
                @click="toggleQuickDropdown(category.name)"
              >
                {{ category.icon }} {{ category.name }}
                <span class="dropdown-arrow">▼</span>
              </span>
              
              <!-- 下拉菜单 -->
              <div 
                class="dropdown-menu"
                v-show="activeQuickDropdown === category.name"
              >
                <div 
                  v-for="type in getFilteredCategoryTypes(category)" 
                  :key="type"
                  class="dropdown-item"
                  :class="{ active: quickTypeFilter === type }"
                  @click="setQuickTypeFilter(type)"
                >
                  {{ getShortTypeName(type) }}
                </div>
                <div v-if="getFilteredCategoryTypes(category).length === 0" class="dropdown-empty">
                  暂无此类型基金
                </div>
              </div>
            </div>
            
            <!-- 未分类的类型（如果有） -->
            <span 
              v-for="type in uncategorizedTypes" 
              :key="type"
              class="quick-tag"
              :class="{ active: quickTypeFilter === type }"
              @click="setQuickTypeFilter(type)"
            >
              {{ getShortTypeName(type) }}
            </span>
          </div>
        </div>
        
        <div class="sort-options">
          <label>排序:</label>
          <select v-model="sortBy" @change="search">
            <option value="sharpe_ratio_1y">夏普比率(1年)</option>
            <option value="return_1y">收益率(1年)</option>
            <option value="calmar_ratio_1y">卡玛比率(1年)</option>
            <option value="max_drawdown_1y">最大回撤(1年)</option>
            <option value="volatility_1y">波动率(1年)</option>
            <option value="fund_scale">基金规模</option>
          </select>
          <select v-model="sortOrder" @change="search">
            <option value="desc">降序</option>
            <option value="asc">升序</option>
          </select>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner large"></div>
        <p>正在筛选...</p>
      </div>

      <!-- 结果表格 -->
      <div v-else class="results-table-wrapper">
        <table class="results-table">
          <thead>
            <tr>
              <th class="sticky-col">基金代码</th>
              <th class="sticky-col-2">基金名称</th>
              <th>类型</th>
              <th>近1月</th>
              <th>近3月</th>
              <th>近1年</th>
              <th>最大回撤</th>
              <th>波动率</th>
              <th>夏普比率</th>
              <th>卡玛比率</th>
              <th>4433</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="fund in results" 
              :key="fund.fund_code"
              @click="viewFundDetail(fund)"
              class="clickable-row"
            >
              <td class="sticky-col fund-code">{{ fund.fund_code }}</td>
              <td class="sticky-col-2 fund-name" :title="fund.fund_name">
                {{ truncateName(fund.fund_name) }}
              </td>
              <td>{{ fund.fund_type }}</td>
              <td :class="getReturnClass(fund.return_1m)">
                {{ formatPercent(fund.return_1m) }}
              </td>
              <td :class="getReturnClass(fund.return_3m)">
                {{ formatPercent(fund.return_3m) }}
              </td>
              <td :class="getReturnClass(fund.return_1y)">
                {{ formatPercent(fund.return_1y) }}
              </td>
              <td class="negative">{{ formatPercent(fund.max_drawdown_1y, true) }}</td>
              <td>{{ formatPercent(fund.volatility_1y) }}</td>
              <td :class="getSharpeClass(fund.sharpe_ratio_1y)">
                {{ formatNumber(fund.sharpe_ratio_1y) }}
              </td>
              <td :class="getCalmarClass(fund.calmar_ratio_1y)">
                {{ formatNumber(fund.calmar_ratio_1y) }}
              </td>
              <td>
                <span v-if="fund.pass_4433" class="pass-badge">✓</span>
                <span v-else class="fail-badge">-</span>
              </td>
              <td class="actions" @click.stop>
                <button class="btn-action" @click="addToWatchlist(fund)" title="加入自选">
                  ⭐
                </button>
                <button class="btn-action" @click="addToCompare(fund)" title="加入对比">
                  📊
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div class="pagination" v-if="totalPages > 1">
        <button 
          class="page-btn" 
          :disabled="currentPage === 1"
          @click="changePage(currentPage - 1)"
        >
          上一页
        </button>
        <span class="page-info">
          第 {{ currentPage }} / {{ totalPages }} 页
        </span>
        <button 
          class="page-btn" 
          :disabled="currentPage === totalPages"
          @click="changePage(currentPage + 1)"
        >
          下一页
        </button>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="searched && !loading" class="empty-state">
      <div class="empty-icon">📭</div>
      <p>未找到符合条件的基金</p>
      <p class="hint">请尝试调整筛选条件</p>
    </div>

    <!-- 初始状态 -->
    <div v-else class="initial-state">
      <div class="initial-icon">🎯</div>
      <p>选择筛选策略或设置筛选条件</p>
      <p class="hint">支持4433法则（同类排名）、夏普比率、卡玛比率等多维度筛选</p>
      <p class="hint sub-hint">注：4433法则的排名是在同类型基金中计算的</p>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { screeningAPI, watchlistAPI } from '../services/api'

export default {
  name: 'FundScreening',
  emits: ['view-fund', 'add-to-compare'],
  
  setup(props, { emit }) {
    // 数据库状态
    const dbStatus = ref({
      basic_count: 0,
      latest_update: null,
      type_counts: {}
    })
    
    // 更新状态
    const updateStatus = ref({
      running: false,
      progress: 0,
      total: 0,
      current_fund: '',
      success_count: 0,
      fail_count: 0,
      message: ''
    })
    
    const showUpdateModal = ref(false)
    const selectedFundTypes = ref(['混合型-偏股', '混合型-灵活', '股票型'])
    const updateLimit = ref(null)
    const recalculating = ref(false)  // 重新计算排名状态
    
    // 策略
    const strategies = ref([])
    const selectedStrategy = ref(null)
    
    // 筛选条件
    const filters = reactive({
      fund_types: [],
      return_1y_min: null,
      return_1y_max: null,
      max_drawdown_max: null,
      sharpe_min: null,
      volatility_max: null,
      calmar_min: null,
      scale_min: null,
      scale_max: null,
      institution_ratio_min: null
    })
    
    // 多级基金类型选项
    const fundTypeCategories = [
      {
        name: '偏股型',
        icon: '📈',
        expanded: true,
        types: [
          { value: '混合型-偏股', label: '偏股混合' },
          { value: '混合型-灵活', label: '灵活配置' },
          { value: '混合型-平衡', label: '平衡混合' },
          { value: '股票型', label: '股票型' },
          { value: '股票指数', label: '股票指数' },
          { value: '联接基金', label: '联接基金' }
        ]
      },
      {
        name: '偏债型',
        icon: '📊',
        expanded: false,
        types: [
          { value: '混合型-偏债', label: '偏债混合' },
          { value: '债券型-长债', label: '长期纯债' },
          { value: '债券型-中短债', label: '中短债' },
          { value: '债券型', label: '债券型(全部)' },
          { value: '债券指数', label: '债券指数' }
        ]
      },
      {
        name: '货币/其他',
        icon: '💰',
        expanded: false,
        types: [
          { value: '货币型', label: '货币型' },
          { value: 'FOF', label: 'FOF' },
          { value: 'QDII', label: 'QDII' },
          { value: 'QDII-指数', label: 'QDII指数' },
          { value: 'REITs', label: 'REITs' }
        ]
      }
    ]
    
    // 控制分类展开状态
    const expandedCategories = ref(['偏股型'])
    
    // 切换分类展开/折叠
    const toggleCategory = (categoryName) => {
      const index = expandedCategories.value.indexOf(categoryName)
      if (index > -1) {
        expandedCategories.value.splice(index, 1)
      } else {
        expandedCategories.value.push(categoryName)
      }
    }
    
    // 检查分类是否展开
    const isCategoryExpanded = (categoryName) => {
      return expandedCategories.value.includes(categoryName)
    }
    
    // 选择整个分类下的所有类型
    const selectCategory = (category) => {
      const categoryTypes = category.types.map(t => t.value)
      const allSelected = categoryTypes.every(t => filters.fund_types.includes(t))
      
      if (allSelected) {
        // 全部取消
        categoryTypes.forEach(t => {
          const idx = filters.fund_types.indexOf(t)
          if (idx > -1) filters.fund_types.splice(idx, 1)
        })
      } else {
        // 全部选中
        categoryTypes.forEach(t => {
          if (!filters.fund_types.includes(t)) {
            filters.fund_types.push(t)
          }
        })
      }
    }
    
    // 检查分类是否全选
    const isCategoryAllSelected = (category) => {
      return category.types.every(t => filters.fund_types.includes(t))
    }
    
    // 检查分类是否部分选中
    const isCategoryPartialSelected = (category) => {
      const selected = category.types.filter(t => filters.fund_types.includes(t))
      return selected.length > 0 && selected.length < category.types.length
    }
    
    // 兼容旧的 fundTypeOptions (用于更新弹窗)
    const fundTypeOptions = computed(() => {
      const allTypes = []
      fundTypeCategories.forEach(cat => {
        cat.types.forEach(t => allTypes.push(t))
      })
      return allTypes
    })
    
    // 排序
    const sortBy = ref('return_1y')
    const sortOrder = ref('desc')
    
    // 快速类型筛选（后端筛选）
    const quickTypeFilter = ref('')
    const availableTypes = ref([])  // 从后端获取可选类型
    const activeQuickDropdown = ref(null)  // 当前打开的下拉菜单
    
    // 快速筛选的多级分类配置
    const quickTypeCategories = [
      {
        name: '偏股型',
        icon: '📈',
        patterns: ['混合型-偏股', '混合型-灵活', '混合型-平衡', '股票型', '股票指数', '指数型-股票', '联接基金', '增强指数', '被动指数', '指数-股票']
      },
      {
        name: '偏债型',
        icon: '📊',
        patterns: ['混合型-偏债', '债券型', '债券指数', '指数型-固收', '短债', '中短债', '长债', '纯债', '可转债', '指数-债券']
      },
      {
        name: 'FOF',
        icon: '🎯',
        patterns: ['FOF']
      },
      {
        name: 'QDII',
        icon: '🌍',
        patterns: ['QDII', '海外指数', '指数型-海外']
      },
      {
        name: '货币/其他',
        icon: '💰',
        patterns: ['货币', 'REITs', '商品', '指数-其他', '指数型-其他', '其他']
      }
    ]
    
    // 辅助函数：确定类型的归属分类（按顺序优先匹配，避免重复）
    const getTypeCategoryName = (type) => {
      for (const cat of quickTypeCategories) {
        if (cat.patterns.some(p => type.includes(p))) {
          return cat.name
        }
      }
      return null
    }

    // 切换下拉菜单
    const toggleQuickDropdown = (categoryName) => {
      if (activeQuickDropdown.value === categoryName) {
        activeQuickDropdown.value = null
      } else {
        activeQuickDropdown.value = categoryName
      }
    }
    
    // 打开下拉菜单 (不再使用)
    const openQuickDropdown = (categoryName) => {
      // no-op
    }
    
    // 关闭下拉菜单
    const closeQuickDropdown = () => {
      activeQuickDropdown.value = null
    }
    
    // 获取分类下在可用类型中的类型
    const getFilteredCategoryTypes = (category) => {
      return availableTypes.value.filter(type => getTypeCategoryName(type) === category.name)
    }
    
    // 检查分类下是否有当前选中的类型
    const isCategoryTypeActive = (category) => {
      if (!quickTypeFilter.value) return false
      // 如果当前选中的类型属于该分类
      return getTypeCategoryName(quickTypeFilter.value) === category.name
    }
    
    // 检查分类下是否有可用类型
    const hasCategoryActiveType = (category) => {
      return getFilteredCategoryTypes(category).length > 0
    }
    
    // 获取未分类的类型
    const uncategorizedTypes = computed(() => {
      return availableTypes.value.filter(type => getTypeCategoryName(type) === null)
    })
    
    // 分页
    const currentPage = ref(1)
    const pageSize = ref(20)
    const totalCount = ref(0)  // 后端返回的总数
    const totalPages = computed(() => Math.ceil(totalCount.value / pageSize.value))
    
    // 结果
    const results = ref([])
    const loading = ref(false)
    const searched = ref(false)
    
    // 进度百分比
    const progressPercent = computed(() => {
      const status = updateStatus.value
      if (!status.total || status.total === 0) {
        // 使用 success_count 作为进度指示
        return status.success_count > 0 ? Math.min((status.success_count / 5000) * 100, 99) : 0
      }
      return Math.round((status.progress / status.total) * 100)
    })
    
    // 状态轮询定时器
    let statusPollTimer = null
    
    // 获取数据库状态
    const fetchDbStatus = async () => {
      try {
        const res = await screeningAPI.getStatus()
        dbStatus.value = res.data
        if (res.data.update_status) {
          updateStatus.value = res.data.update_status
        }
      } catch (err) {
        console.error('获取状态失败:', err)
      }
    }
    
    // 获取策略列表
    const fetchStrategies = async () => {
      try {
        const res = await screeningAPI.getStrategies()
        strategies.value = res.data.strategies || []
      } catch (err) {
        console.error('获取策略失败:', err)
      }
    }
    
    // 开始更新
    const startUpdate = async () => {
      try {
        await screeningAPI.startUpdate({
          fund_types: selectedFundTypes.value,
          limit: updateLimit.value || null
        })
        // 开始轮询状态
        startStatusPoll()
      } catch (err) {
        if (err.response?.status === 409) {
          alert('更新任务已在进行中')
        } else {
          console.error('启动更新失败:', err)
          alert('启动更新失败')
        }
      }
    }
    
    // 停止更新
    const stopUpdate = async () => {
      try {
        await screeningAPI.stopUpdate()
      } catch (err) {
        console.error('停止更新失败:', err)
      }
    }
    
    // 重新计算同类型排名
    const recalculateRankings = async () => {
      if (recalculating.value) return
      
      recalculating.value = true
      try {
        const response = await screeningAPI.recalculateRankings()
        if (response.data.success) {
          alert(`排名计算完成！\n\n各类型4433通过率:\n${
            Object.entries(response.data.stats || {})
              .map(([type, stat]) => `${type}: ${stat.pass_4433}/${stat.total} (${stat.pass_rate}%)`)
              .join('\n')
          }`)
          // 刷新数据
          await fetchDbStatus()
          if (results.value.length > 0) {
            await search()
          }
        } else {
          alert('计算失败: ' + response.data.error)
        }
      } catch (err) {
        console.error('重新计算排名失败:', err)
        alert('重新计算排名失败')
      } finally {
        recalculating.value = false
      }
    }
    
    // 开始轮询状态
    const startStatusPoll = () => {
      if (statusPollTimer) return
      statusPollTimer = setInterval(async () => {
        await fetchDbStatus()
        if (!updateStatus.value.running) {
          stopStatusPoll()
        }
      }, 2000)
    }
    
    // 停止轮询
    const stopStatusPoll = () => {
      if (statusPollTimer) {
        clearInterval(statusPollTimer)
        statusPollTimer = null
      }
    }
    
    // 关闭更新弹窗
    const closeUpdateModal = () => {
      if (!updateStatus.value.running) {
        showUpdateModal.value = false
      }
    }
    
    // 选择策略
    const selectStrategy = async (strategyId) => {
      if (selectedStrategy.value === strategyId) {
        selectedStrategy.value = null
      } else {
        selectedStrategy.value = strategyId
      }
      quickTypeFilter.value = ''  // 重置快速类型筛选
      availableTypes.value = []   // 重置可用类型
      
      // 先查询可用的基金类型
      if (selectedStrategy.value) {
        try {
          const cleanFilters = {}
          for (const [key, value] of Object.entries(filters)) {
            if (value !== null && value !== '' && !(Array.isArray(value) && value.length === 0)) {
              cleanFilters[key] = value
            }
          }
          const res = await screeningAPI.getAvailableTypes({
            strategy: selectedStrategy.value,
            filters: cleanFilters
          })
          availableTypes.value = res.data.types || []
        } catch (err) {
          console.error('获取类型失败:', err)
        }
      }
      
      search(true)  // 重置页码
    }
    
    // 重置筛选条件
    const resetFilters = () => {
      filters.fund_types = []
      filters.return_1y_min = null
      filters.return_1y_max = null
      filters.max_drawdown_max = null
      filters.sharpe_min = null
      filters.volatility_max = null
      filters.calmar_min = null
      filters.scale_min = null
      filters.scale_max = null
      filters.institution_ratio_min = null
      selectedStrategy.value = null
    }
    
    // 搜索
    const search = async (resetPage = false) => {
      loading.value = true
      searched.value = true
      
      // 重置页码（新搜索时）
      if (resetPage) {
        currentPage.value = 1
      }
      
      try {
        // 清理空值
        const cleanFilters = {}
        for (const [key, value] of Object.entries(filters)) {
          if (value !== null && value !== '' && !(Array.isArray(value) && value.length === 0)) {
            cleanFilters[key] = value
          }
        }
        
        // 如果有快速类型筛选，添加到过滤条件
        if (quickTypeFilter.value) {
          cleanFilters.quick_fund_type = quickTypeFilter.value
        }
        
        const res = await screeningAPI.query({
          filters: cleanFilters,
          strategy: selectedStrategy.value,
          sort_by: sortBy.value,
          sort_order: sortOrder.value,
          page: currentPage.value,
          page_size: pageSize.value
        })
        
        results.value = res.data.data || []
        totalCount.value = res.data.total || 0
        
        // 从返回数据中提取当前页的类型（用于显示有哪些类型）
        // 注意：这只是当前页的类型，不是全部类型
        if (!quickTypeFilter.value) {
          const types = new Set()
          results.value.forEach(f => {
            if (f.fund_type) types.add(f.fund_type)
          })
          // 保留已有类型，并添加新类型
          const existingTypes = new Set(availableTypes.value)
          types.forEach(t => existingTypes.add(t))
          availableTypes.value = Array.from(existingTypes).sort()
        }
      } catch (err) {
        console.error('筛选失败:', err)
        results.value = []
        totalCount.value = 0
      } finally {
        loading.value = false
      }
    }
    
    // 切换基金类型选择
    const toggleFundType = (typeValue) => {
      const index = filters.fund_types.indexOf(typeValue)
      if (index > -1) {
        filters.fund_types.splice(index, 1)
      } else {
        filters.fund_types.push(typeValue)
      }
    }
    
    // 快速类型筛选（触发后端重新查询）
    const setQuickTypeFilter = (type) => {
      quickTypeFilter.value = type
      activeQuickDropdown.value = null // 关闭下拉菜单
      currentPage.value = 1  // 重置到第一页
      search()  // 重新查询后端
    }
    
    // 获取简短类型名称
    const getShortTypeName = (type) => {
      if (!type) return '未知'
      // 简化显示名称
      const shortNames = {
        '混合型-偏股': '偏股混合',
        '混合型-灵活': '灵活配置',
        '混合型-偏债': '偏债混合',
        '混合型-平衡': '平衡混合',
        '指数型-股票': '股票指数',
        '指数型-固收': '债券指数',
        '指数型-海外股票': '海外指数',
        '债券型-长债': '长期债券',
        '债券型-中短债': '中短债',
        '债券型-混合一级': '一级债基',
        '债券型-混合二级': '二级债基',
        '货币型-普通货币': '货币基金',
        'FOF-稳健型': 'FOF稳健',
        'FOF-均衡型': 'FOF均衡',
        'FOF-进取型': 'FOF进取',
      }
      return shortNames[type] || type.replace('型-', '-').replace('型', '')
    }
    
    // 换页
    const changePage = (page) => {
      currentPage.value = page
      search()
    }
    
    // 查看基金详情
    const viewFundDetail = (fund) => {
      emit('view-fund', fund.fund_code)
    }
    
    // 加入自选
    const addToWatchlist = async (fund) => {
      try {
        await watchlistAPI.addToWatchlist(fund.fund_code, fund.fund_name, fund.fund_type)
        alert(`已将 ${fund.fund_name} 加入自选`)
      } catch (err) {
        if (err.response?.status === 409) {
          alert('该基金已在自选列表中')
        } else {
          alert('加入自选失败')
        }
      }
    }
    
    // 加入对比
    const addToCompare = (fund) => {
      emit('add-to-compare', {
        code: fund.fund_code,
        name: fund.fund_name
      })
    }
    
    // 格式化函数
    const formatPercent = (value, isNegative = false) => {
      if (value === null || value === undefined) return '--'
      const prefix = isNegative ? '-' : (value > 0 ? '+' : '')
      return `${prefix}${Math.abs(value).toFixed(2)}%`
    }
    
    const formatNumber = (value) => {
      if (value === null || value === undefined) return '--'
      return value.toFixed(2)
    }
    
    const formatDate = (dateStr) => {
      if (!dateStr) return '--'
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN')
    }
    
    const truncateName = (name) => {
      if (!name) return '--'
      return name.length > 12 ? name.slice(0, 12) + '...' : name
    }
    
    // 样式判断函数
    const getReturnClass = (value) => {
      if (value === null || value === undefined) return ''
      return value > 0 ? 'positive' : value < 0 ? 'negative' : ''
    }
    
    const getSharpeClass = (value) => {
      if (value === null || value === undefined) return ''
      if (value >= 1.5) return 'excellent'
      if (value >= 1) return 'good'
      if (value >= 0.5) return 'normal'
      return 'poor'
    }
    
    const getCalmarClass = (value) => {
      if (value === null || value === undefined) return ''
      if (value >= 2) return 'excellent'
      if (value >= 1) return 'good'
      if (value >= 0.5) return 'normal'
      return 'poor'
    }
    
    const getStyleClass = (style) => {
      if (!style) return ''
      if (style.includes('股票')) return 'style-stock'
      if (style.includes('债券')) return 'style-bond'
      if (style.includes('均衡')) return 'style-balanced'
      return 'style-mixed'
    }
    
    // 生命周期
    onMounted(async () => {
      await fetchDbStatus()
      fetchStrategies()
      
      // 如果正在更新，开始轮询
      if (updateStatus.value.running) {
        startStatusPoll()
      }

      // 点击外部关闭下拉菜单
      document.addEventListener('click', closeQuickDropdown)
    })
    
    onUnmounted(() => {
      stopStatusPoll()
      document.removeEventListener('click', closeQuickDropdown)
    })
    
    return {
      // 状态
      dbStatus,
      updateStatus,
      showUpdateModal,
      selectedFundTypes,
      updateLimit,
      recalculating,
      strategies,
      selectedStrategy,
      filters,
      fundTypeOptions,
      fundTypeCategories,
      expandedCategories,
      sortBy,
      sortOrder,
      currentPage,
      totalCount,
      totalPages,
      results,
      loading,
      searched,
      progressPercent,
      quickTypeFilter,
      availableTypes,
      activeQuickDropdown,
      quickTypeCategories,
      uncategorizedTypes,
      
      // 方法
      fetchDbStatus,
      startUpdate,
      stopUpdate,
      recalculateRankings,
      closeUpdateModal,
      selectStrategy,
      resetFilters,
      search,
      changePage,
      viewFundDetail,
      addToWatchlist,
      addToCompare,
      formatPercent,
      formatNumber,
      formatDate,
      truncateName,
      getReturnClass,
      getSharpeClass,
      getCalmarClass,
      getStyleClass,
      toggleFundType,
      setQuickTypeFilter,
      getShortTypeName,
      toggleCategory,
      isCategoryExpanded,
      selectCategory,
      isCategoryAllSelected,
      isCategoryPartialSelected,
      openQuickDropdown,
      closeQuickDropdown,
      toggleQuickDropdown,
      getFilteredCategoryTypes,
      isCategoryTypeActive,
      hasCategoryActiveType
    }
      isCategoryPartialSelected,
      openQuickDropdown,
      closeQuickDropdown,
      getFilteredCategoryTypes,
      isCategoryTypeActive,
      hasCategoryActiveType
    }
  }

</script>

<style scoped>
.fund-screening {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

/* 顶部状态栏 */
.screening-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.header-title h2 {
  margin: 0 0 4px 0;
  font-size: 1.4rem;
}

.subtitle {
  margin: 0;
  opacity: 0.9;
  font-size: 0.9rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.db-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  background: rgba(255, 255, 255, 0.15);
  padding: 8px 12px;
  border-radius: 8px;
}

.status-value {
  font-weight: 600;
}

.status-value.has-data {
  color: #a5f3a5;
}

.update-time {
  opacity: 0.8;
  font-size: 0.85rem;
}

.btn-update {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: white;
  color: #667eea;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-update:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.btn-update:disabled {
  opacity: 0.7;
  cursor: not-allowed;
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

.modal-content {
  background: white;
  border-radius: 16px;
  width: 90%;
  max-width: 500px;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.1rem;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.modal-body {
  padding: 20px;
}

.update-options .option-group {
  margin-bottom: 16px;
}

.update-options label {
  display: block;
  font-weight: 500;
  margin-bottom: 8px;
}

.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: normal;
  padding: 6px 12px;
  background: #f5f7fa;
  border-radius: 6px;
  cursor: pointer;
}

.checkbox-group label:hover {
  background: #e9ecef;
}

.update-options input[type="number"] {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
}

/* 更新模式选择 */
.update-mode-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.mode-tab {
  flex: 1;
  padding: 12px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.mode-tab:hover {
  border-color: #667eea;
}

.mode-tab.active {
  border-color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  color: #667eea;
}

.mode-desc {
  font-size: 12px;
  color: #666;
  margin: 0 0 16px 0;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 6px;
}

.btn-start-update {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 8px;
}

.btn-start-update:hover {
  opacity: 0.9;
}

.secondary-actions {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}

.secondary-actions button {
  flex: 1;
}

.btn-supplement,
.btn-recalculate {
  padding: 10px;
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
}

.btn-supplement:hover:not(:disabled),
.btn-recalculate:hover:not(:disabled) {
  background: #e5e7eb;
}

.btn-supplement:disabled,
.btn-recalculate:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.supplement-progress {
  margin-top: 16px;
  padding: 12px;
  background: #f0f9ff;
  border-radius: 8px;
  border: 1px solid #bae6fd;
}

.supplement-progress h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #0369a1;
}

/* 进度 */
.update-progress {
  text-align: center;
}

.progress-mode {
  font-size: 14px;
  color: #667eea;
  font-weight: 500;
  margin-bottom: 12px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.current-fund {
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 70%;
}

.progress-bar {
  height: 12px;
  background: #e9ecef;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s;
}

.progress-stats {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-bottom: 12px;
}

.progress-stats .success {
  color: #10b981;
}

.progress-stats .fail {
  color: #ef4444;
}

.progress-message {
  color: #666;
  font-size: 14px;
  margin-bottom: 16px;
}

.btn-stop {
  padding: 10px 24px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

/* 筛选面板 */
.screening-panel {
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
}

.strategy-section h3,
.filter-section h3 {
  margin: 0 0 16px 0;
  font-size: 1rem;
  color: #333;
}

.strategy-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

.strategy-card {
  padding: 16px;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.strategy-card:hover {
  border-color: #667eea;
  transform: translateY(-2px);
}

.strategy-card.active {
  border-color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
}

.strategy-name {
  font-weight: 600;
  margin-bottom: 6px;
}

.strategy-desc {
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 8px;
}

.strategy-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag {
  padding: 2px 8px;
  background: #f0f0f0;
  border-radius: 4px;
  font-size: 0.75rem;
  color: #666;
}

/* 筛选条件 - 新设计 */
.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.btn-reset {
  padding: 6px 16px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  cursor: pointer;
  font-size: 13px;
  color: #6b7280;
  transition: all 0.2s;
}

.btn-reset:hover {
  background: #f9fafb;
  border-color: #d1d5db;
  color: #374151;
}

.filter-card {
  background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid #e2e8f0;
}

/* 基金类型标签选择 */
.filter-row {
  margin-bottom: 20px;
}

.filter-row .filter-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 12px;
}

.label-icon {
  font-size: 16px;
}

.selected-count {
  font-size: 12px;
  color: #667eea;
  font-weight: normal;
  margin-left: 6px;
}

/* 多级类型分类容器 */
.type-categories {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.type-category {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
  background: white;
}

.category-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #f9fafb;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.category-header:hover {
  background: #f3f4f6;
}

.category-toggle {
  font-size: 10px;
  color: #9ca3af;
  width: 12px;
}

.category-icon {
  font-size: 14px;
}

.category-name {
  flex: 1;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.category-checkbox {
  width: 18px;
  height: 18px;
  border: 2px solid #d1d5db;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.category-checkbox:hover {
  border-color: #667eea;
}

.category-checkbox.checked {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: transparent;
}

.category-checkbox.partial {
  background: #a5b4fc;
  border-color: transparent;
  color: white;
}

.category-types {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 14px;
  background: white;
  border-top: 1px solid #f3f4f6;
}

/* 保留旧的type-tags样式用于更新弹窗 */
.type-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.type-tag {
  padding: 6px 14px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  font-size: 13px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.type-tag:hover {
  border-color: #a5b4fc;
  color: #4f46e5;
  background: #eef2ff;
}

.type-tag.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: transparent;
  color: white;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

/* 筛选指标网格 */
.filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.filter-item {
  background: white;
  border-radius: 12px;
  padding: 14px 16px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
}

.filter-item:hover {
  border-color: #c7d2fe;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.08);
}

.filter-item .filter-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #4b5563;
  margin-bottom: 10px;
}

.filter-item .label-icon {
  font-size: 14px;
}

/* 输入框组 */
.range-input-group,
.single-input-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.range-input-group input,
.single-input-group input {
  flex: 1;
  min-width: 0;
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  background: #f9fafb;
  transition: all 0.2s;
}

.range-input-group input:focus,
.single-input-group input:focus {
  outline: none;
  border-color: #818cf8;
  background: white;
  box-shadow: 0 0 0 3px rgba(129, 140, 248, 0.1);
}

.range-sep {
  color: #9ca3af;
  font-size: 14px;
}

.unit {
  color: #9ca3af;
  font-size: 13px;
  white-space: nowrap;
}

.filter-actions {
  text-align: center;
  margin-top: 20px;
}

.btn-search {
  padding: 12px 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 25px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.35);
}

.btn-search:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.45);
}

.btn-search:active {
  transform: translateY(0);
}

/* 结果区域 */
.results-section {
  padding: 20px 24px;
}

.results-header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
  position: relative;
  z-index: 50;
  overflow: visible;
}

.results-title-row {
  flex-shrink: 0;
}

.results-header h3 {
  margin: 0;
  font-size: 1rem;
}

.result-count {
  font-weight: normal;
  color: #666;
  font-size: 0.9rem;
}

/* 快速类型筛选 */
.quick-type-filter {
  flex: 1;
  min-width: 300px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 10px;
  overflow: visible;
  position: relative;
  z-index: 50;
}

.filter-label-inline {
  font-size: 13px;
  color: #6b7280;
  white-space: nowrap;
}

.quick-type-menu {
  display: flex;
  gap: 6px;
  flex-wrap: nowrap;
  align-items: center;
}

.quick-type-tags {
  display: flex;
  gap: 6px;
  flex-wrap: nowrap;
}

.quick-tag {
  padding: 4px 12px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 15px;
  font-size: 12px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.quick-tag:hover {
  border-color: #a5b4fc;
  color: #4f46e5;
}

.quick-tag.active {
  background: #667eea;
  border-color: #667eea;
  color: rgb(50, 53, 218);
}

.quick-tag.has-active {
  border-color: #a5b4fc;
  background: #eef2ff;
}

/* 下拉菜单容器 */
.quick-type-dropdown {
  position: relative;
  z-index: 100;
}

.dropdown-trigger {
  display: flex;
  align-items: center;
  gap: 4px;
}

.dropdown-arrow {
  font-size: 8px;
  margin-left: 2px;
  transition: transform 0.2s;
}

.quick-type-dropdown:hover .dropdown-arrow {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  min-width: 140px;
  max-height: 280px;
  overflow-y: auto;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  margin-top: 4px;
  padding: 4px 0;
}

.dropdown-item {
  padding: 8px 14px;
  font-size: 12px;
  color: #374151;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.dropdown-item:hover {
  background: #f3f4f6;
  color: #4f46e5;
}

.dropdown-item.active {
  background: #eef2ff;
  color: #667eea;
  font-weight: 500;
}

.dropdown-empty {
  padding: 12px 14px;
  font-size: 12px;
  color: #9ca3af;
  text-align: center;
}

.sort-options {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.sort-options label {
  color: #666;
  font-size: 0.9rem;
}

.sort-options select {
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  background: white;
}

/* 表格 */
.results-table-wrapper {
  overflow-x: auto;
}

.results-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.results-table th,
.results-table td {
  padding: 12px 10px;
  text-align: left;
  border-bottom: 1px solid #eee;
  white-space: nowrap;
}

.results-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #666;
  position: sticky;
  top: 0;
}

.results-table .sticky-col {
  position: sticky;
  left: 0;
  background: white;
  z-index: 1;
}

.results-table .sticky-col-2 {
  position: sticky;
  left: 70px;
  background: white;
  z-index: 1;
}

.results-table th.sticky-col,
.results-table th.sticky-col-2 {
  background: #f8f9fa;
  z-index: 2;
}

.clickable-row {
  cursor: pointer;
  transition: background 0.2s;
}

.clickable-row:hover {
  background: #f8f9fa;
}

.fund-code {
  font-family: monospace;
  color: #667eea;
  font-weight: 600;
}

.fund-name {
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.positive {
  color: #ef4444;
}

.negative {
  color: #10b981;
}

.excellent {
  color: #10b981;
  font-weight: 600;
}

.good {
  color: #3b82f6;
}

.normal {
  color: #666;
}

.poor {
  color: #9ca3af;
}

.style-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.pass-badge {
  color: #059669;
  font-weight: bold;
}

.fail-badge {
  color: #9ca3af;
}

.style-stock {
  background: #fef3c7;
  color: #92400e;
}

.style-bond {
  background: #dbeafe;
  color: #1e40af;
}

.style-balanced {
  background: #d1fae5;
  color: #065f46;
}

.style-mixed {
  background: #f3e8ff;
  color: #6b21a8;
}

.actions {
  display: flex;
  gap: 8px;
}

.btn-action {
  padding: 4px 8px;
  background: #f5f7fa;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-action:hover {
  background: #e9ecef;
  transform: scale(1.1);
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.page-btn {
  padding: 8px 16px;
  background: #f5f7fa;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
}

.page-btn:hover:not(:disabled) {
  background: #e9ecef;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #666;
  font-size: 14px;
}

/* 状态显示 */
.loading-state,
.empty-state,
.initial-state {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid #fff;
  border-radius: 50%;
  border-top-color: transparent;
  animation: spin 0.8s linear infinite;
}

.loading-spinner.large {
  width: 40px;
  height: 40px;
  border-width: 3px;
  border-color: #667eea;
  border-top-color: transparent;
  margin-bottom: 16px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-icon,
.initial-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.hint {
  font-size: 0.9rem;
  color: #9ca3af;
  margin-top: 8px;
}

.sub-hint {
  font-size: 0.8rem;
  color: #6b7280;
}
</style>
