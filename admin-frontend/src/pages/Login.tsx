import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import type { AuthInfo } from '../lib/api'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { setAuth } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await api.post<AuthInfo>('/staff/login', { username, password })
      setAuth(data)
      // Перенаправить на первую доступную страницу
      if (data.role === 'superadmin') {
        navigate('/tenants')
      } else {
        navigate('/bookings')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Ошибка входа')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-brand-50">
      <div className="w-full max-w-sm">
        {/* Card */}
        <div className="card p-8 shadow-md">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="text-5xl mb-3">🎬</div>
            <h1 className="text-xl font-semibold text-gray-900">KinoRoom</h1>
            <p className="text-sm text-gray-500 mt-1">Панель управления</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Логин</label>
              <input
                className="input"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="username"
                required
                autoFocus
              />
            </div>
            <div>
              <label className="label">Пароль</label>
              <input
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••"
                required
              />
            </div>

            {error && (
              <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center py-2.5"
            >
              {loading ? 'Вход...' : 'Войти'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
