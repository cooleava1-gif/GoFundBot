<template>
  <div class="fund-search">
    <div class="search-box">
      <input
        v-model="searchKeyword"
        @input="handleSearch"
        @keyup.enter="performSearch"
        placeholder="输入基金代码或名称搜索..."
        class="search-input"
      />
      <button @click="performSearch" class="search-btn">搜索</button>
    </div>
    
    <div v-if="searchResults.length > 0" class="search-results">
      <div
        v-for="fund in searchResults"
        :key="fund.CODE"
        class="fund-item"
        @click="selectFund(fund)"
      >
        <div class="fund-code">{{ fund.CODE }}</div>
        <div class="fund-name">{{ fund.NAME }}</div>
        <div class="fund-type">{{ fund.FundBaseInfo ? fund.FundBaseInfo.FTYPE : '基金' }}</div>
      </div>
    </div>
    
    <div v-if="loading" class="loading">搜索中...</div>
  </div>
</template>

<script>
import { fundAPI } from '../services/api'

export default {
  name: 'FundSearch',
  emits: ['fund-selected'],
  data() {
    return {
      searchKeyword: '',
      searchResults: [],
      loading: false,
      searchTimer: null
    }
  },
  methods: {
    handleSearch() {
      clearTimeout(this.searchTimer)
      if (this.searchKeyword.length >= 2) {
        this.searchTimer = setTimeout(this.performSearch, 300)
      } else {
        this.searchResults = []
      }
    },
    
    async performSearch() {
      if (!this.searchKeyword.trim()) return
      
      this.loading = true
      try {
        const response = await fundAPI.searchFunds(this.searchKeyword)
        this.searchResults = response.data.data || []
      } catch (error) {
        console.error('搜索失败:', error)
        this.searchResults = []
      } finally {
        this.loading = false
      }
    },
    
    selectFund(fund) {
      this.$emit('fund-selected', fund.CODE)
      this.searchResults = []
      this.searchKeyword = ''
    }
  }
}
</script>

<style scoped>
.fund-search {
  margin-bottom: 20px;
}

.search-box {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.search-input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

.search-btn {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.search-btn:hover {
  background: #0056b3;
}

.search-results {
  border: 1px solid #ddd;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
}

.fund-item {
  padding: 10px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
}

.fund-item:hover {
  background: #f5f5f5;
}

.fund-code {
  font-weight: bold;
  color: #007bff;
}

.fund-name {
  margin: 5px 0;
}

.fund-type {
  font-size: 12px;
  color: #666;
}

.loading {
  text-align: center;
  padding: 10px;
  color: #666;
}
</style>