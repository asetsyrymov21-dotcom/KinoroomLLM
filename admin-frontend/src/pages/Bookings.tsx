import { useState, useEffect } from 'react'
import { api } from '../lib/api'
import type { Booking, Hall } from '../lib/api'
import PageHeader from '../components/PageHeader'

const STATUS_LABELS: Record<string, string> = {
  pending: 'Ожидает', active: 'Активна', completed: 'Завершена', cancelled: 'Отменена'
}
const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-700',
  active: 'bg-green-100 text-green-700',
  completed: 'bg-blue-100 text-blue-700',
  cancelled: 'bg-gray-100 text-gray-500',
}

function fmt(dt: string | null) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString('ru-RU', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit' })
}

export default function Bookings() {
  const [bookings, setBookings] = useState<Booking[]>([])
  const [halls, setHalls] = useState<Hall[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')
  const [actioning, setActioning] = useState<number | null>(null)

  async function load() {
    setLoading(true)
    try {
      const [b, h] = await Promise.all([api.get<Booking[]>('/bookings'), api.get<Hall[]>('/halls')])
      setBookings(b.data); setHalls(h.data)
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  async function action(id: number, act: 'activate' | 'complete' | 'cancel') {
    setActioning(id)
    try { await api.post(`/bookings/${id}/${act}`); await load() }
    catch (err: any) { alert(err.response?.data?.detail ?? 'Ошибка') }
    finally { setActioning(null) }
  }

  const hallMap = Object.fromEntries(halls.map(h => [h.id, h]))
  const filtered = filter === 'all' ? bookings : bookings.filter(b => b.status === filter)

  return (
    <div>
      <PageHeader title="Бронирования" subtitle="Управление сессиями" />
      <div className="px-8">
        {/* Filter tabs */}
        <div className="flex gap-1 mb-4">
          {['all', 'pending', 'active', 'completed', 'cancelled'].map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                filter === f ? 'bg-brand-600 text-white' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}>
              {f === 'all' ? 'Все' : STATUS_LABELS[f]}
            </button>
          ))}
        </div>

        {loading ? <p className="text-gray-500 text-sm">Загрузка...</p> : (
          <div className="card overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="table-header">#</th>
                  <th className="table-header">Зал</th>
                  <th className="table-header">Начало</th>
                  <th className="table-header">Конец</th>
                  <th className="table-header">Сумма</th>
                  <th className="table-header">Статус</th>
                  <th className="table-header">Действия</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map(b => (
                  <tr key={b.id} className="hover:bg-gray-50">
                    <td className="table-cell text-gray-400">#{b.id}</td>
                    <td className="table-cell font-medium">{hallMap[b.hall_id]?.name ?? `#${b.hall_id}`}</td>
                    <td className="table-cell">{fmt(b.start_time)}</td>
                    <td className="table-cell text-gray-500">{b.is_open_ended ? 'Открытая' : fmt(b.end_time)}</td>
                    <td className="table-cell">{b.total_price != null ? `${Number(b.total_price).toLocaleString()} ₸` : '—'}</td>
                    <td className="table-cell">
                      <span className={`badge ${STATUS_COLORS[b.status] ?? 'bg-gray-100 text-gray-500'}`}>
                        {STATUS_LABELS[b.status] ?? b.status}
                      </span>
                    </td>
                    <td className="table-cell">
                      <div className="flex gap-1 flex-wrap">
                        {b.status === 'pending' && (
                          <>
                            <button className="btn-ghost py-1 px-2 text-xs text-green-600" disabled={actioning === b.id} onClick={() => action(b.id, 'activate')}>Активировать</button>
                            <button className="btn-ghost py-1 px-2 text-xs text-red-500" disabled={actioning === b.id} onClick={() => action(b.id, 'cancel')}>Отменить</button>
                          </>
                        )}
                        {b.status === 'active' && (
                          <>
                            <button className="btn-ghost py-1 px-2 text-xs text-blue-600" disabled={actioning === b.id} onClick={() => action(b.id, 'complete')}>Завершить</button>
                            <button className="btn-ghost py-1 px-2 text-xs text-red-500" disabled={actioning === b.id} onClick={() => action(b.id, 'cancel')}>Отменить</button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && <tr><td colSpan={7} className="table-cell text-center text-gray-400 py-8">Нет бронирований</td></tr>}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
