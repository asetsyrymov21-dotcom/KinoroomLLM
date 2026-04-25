import axios from 'axios'

export const api = axios.create({
  baseURL: '/api/v1',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('kinorum_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('kinorum_token')
      localStorage.removeItem('kinorum_auth')
      window.location.href = '/admin/'
    }
    return Promise.reject(err)
  },
)

export type Role = 'superadmin' | 'admin' | 'operator'

export interface AuthInfo {
  token: string
  role: Role
  username: string
  tenant_id: number | null
}

export interface Tenant {
  id: number
  name: string
  slug: string
  is_active: boolean
}

export interface Hall {
  id: number
  name: string
  capacity: number
  price_per_hour: number
  is_active: boolean
  tenant_id: number
}

export interface Category {
  id: number
  name: string
  emoji: string | null
  position: number
  is_active: boolean
}

export interface Product {
  id: number
  name: string
  sku: string
  price: number
  cost_price: number | null
  unit: string
  is_active: boolean
  category_id: number | null
}

export interface StaffMember {
  id: number
  username: string
  role: 'admin' | 'operator'
  tenant_id: number
}

export interface Booking {
  id: number
  hall_id: number
  user_id: number
  start_time: string
  end_time: string | null
  status: string
  total_price: number | null
  discount_pct: number | null
  extra_charge: number | null
  is_open_ended: boolean
}

export interface Order {
  id: number
  booking_id: number
  status: string
  total: number | null
}

export interface StockBalance {
  hall_id: number
  product_id: number
  product_name: string
  quantity: number
  reserved_quantity: number
  unit: string
}
