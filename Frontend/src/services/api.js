import axios from 'axios'

// 使用相对路径，以便在开发环境中使用 Vite 代理，生产环境中使用 Nginx 代理
// 也可以通过环境变量 import.meta.env.VITE_API_BASE_URL 来配置
const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000
})

export const fundAPI = {
  // 搜索基金
  searchFunds(keyword) {
    return api.get(`/fund/search?q=${encodeURIComponent(keyword)}`)
  },
  
  // 获取基金详细信息
  getFundDetail(fundCode) {
    return api.get(`/fund/${fundCode}`)
  },
  
  // 获取基金基础信息
  getFundBasicInfo(fundCode) {
    return api.get(`/fund/${fundCode}/basic`)
  },
  
  // 获取基金走势数据
  getFundTrend(fundCode) {
    return api.get(`/fund/${fundCode}/trend`)
  }
}

export default api