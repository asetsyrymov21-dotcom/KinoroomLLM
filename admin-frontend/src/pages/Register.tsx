import { FormEvent, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import type { AuthInfo } from '../lib/api'
import { useAuth } from '../context/AuthContext'

function makeSlug(value: string) {
  const map: Record<string, string> = {
    а: 'a',
    б: 'b',
    в: 'v',
    г: 'g',
    д: 'd',
    е: 'e',
    ё: 'e',
    ж: 'zh',
    з: 'z',
    и: 'i',
    й: 'y',
    к: 'k',
    л: 'l',
    м: 'm',
    н: 'n',
    о: 'o',
    п: 'p',
    р: 'r',
    с: 's',
    т: 't',
    у: 'u',
    ф: 'f',
    х: 'h',
    ц: 'c',
    ч: 'ch',
    ш: 'sh',
    щ: 'sch',
    ы: 'y',
    э: 'e',
    ю: 'yu',
    я: 'ya',
  }

  return value
    .trim()
    .toLowerCase()
    .split('')
    .map((char) => map[char] ?? char)
    .join('')
    .replace(/[^a-z0-9_-]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 100)
}

export default function Register() {
  const { setAuth } = useAuth()
  const navigate = useNavigate()
  const [tenantName, setTenantName] = useState('')
  const [tenantSlug, setTenantSlug] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const suggestedSlug = useMemo(() => makeSlug(tenantName), [tenantName])
  const slug = tenantSlug || suggestedSlug

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await api.post<AuthInfo>('/staff/register', {
        tenant_name: tenantName,
        tenant_slug: slug,
        username,
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
              <label className="label">Адрес в системе</label>
              <input
                className="input"
                type="text"
                value={slug}
                onChange={(e) => setTenantSlug(makeSlug(e.target.value))}
                placeholder="kinoroom-qyzylorda"
                required
              />
            </div>

            <div>
              <label className="label">Логин администратора</label>
              <input
                className="input"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin"
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
              disabled={loading || !slug}
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
