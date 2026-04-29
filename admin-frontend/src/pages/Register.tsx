import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import type { AuthInfo } from '../lib/api'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const { setAuth } = useAuth()
  const navigate = useNavigate()
  const [tenantName, setTenantName] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await api.post<AuthInfo>('/staff/register', {
        tenant_name: tenantName.trim(),
        phone: phone.trim() || null,
        email: email.trim(),
        password,
      })
      setAuth(data)
      navigate('/bookings')
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Не удалось создать аккаунт')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 via-white to-brand-50 px-4 py-10">
      <div className="w-full max-w-md">
        <div className="card p-8 shadow-md">
          <div className="text-center mb-8">
            <div className="text-5xl mb-3">🎬</div>
            <h1 className="text-xl font-semibold text-gray-900">Создать Kinorum</h1>
            <p className="text-sm text-gray-500 mt-1">Новый кинорум и первый администратор</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Название кинорума</label>
              <input
                className="input"
                type="text"
                value={tenantName}
                onChange={(e) => setTenantName(e.target.value)}
                placeholder="Например, KinoRoom Qyzylorda"
                required
                autoFocus
              />
            </div>

            <div>
              <label className="label">Телефон организации</label>
              <input
                className="input"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+7 700 000 00 00"
              />
            </div>

            <div>
              <label className="label">Email администратора</label>
              <input
                className="input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@example.com"
                autoComplete="email"
                required
              />
            </div>

            <div>
              <label className="label">Пароль</label>
              <input
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Минимум 6 символов"
                autoComplete="new-password"
                required
                minLength={6}
                maxLength={72}
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
              {loading ? 'Создаём...' : 'Зарегистрироваться'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500">
            Уже есть аккаунт?{' '}
            <Link to="/login" className="font-medium text-brand-600 hover:text-brand-700">
              Войти
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
