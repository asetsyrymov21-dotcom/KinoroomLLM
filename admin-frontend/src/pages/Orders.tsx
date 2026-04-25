import { useState, useEffect } from 'react'
import { api } from '../lib/api'
import type { Order } from '../lib/api'
import PageHeader from '../components/PageHeader'

const STATUS_LABELS: Record<string, string> = {
  open: 'Открыт', completed: 'Выполнен', cancelled: 'Отменён'
}
const STATUS_COLORS: Record<string, string> = {
  open: 'bg-yellow-100 text-yellow-700',
  completed: 'bg-blue-100 text-blue-700',
  cancelled: 'bg-gray-100 text-gray-500',
}

export default function Orders() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [actioning, setActioning] = useState<number | null>(null)

  async function load() {
    setLoading(true)
    try {
      const { data } = await api.get<Order[]>('/orders')
      setOrders(Array.isArray(data) ? data : [])
    } catch {
      setOrders([])
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  async function action(id: number, act: 'complete' | 'cancel') {
    setActioning(id)
    try { await api.post(`/orders/${id}/${act}`); await load() }
    catch (err: any) { alert(err.response?.data?.detail ?? 'Ошибка') }
    finally { setActioning(null) }
  }

  return (
    <div>
      <PageHeader title="Заказы" subtitle="Заказы товаров в рамках бронирований" />
      <div className="px-8">
        {loading ? <p className="text-gray-500 text-sm">Загрузка...</p> : (
          <div className="card overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="table-header">#</th>
                  <th className="table-header">Бронь #</th>
                  <th className="table-header">Сумма</th>
                  <th className="table-header">Статус</th>
                  <th className="table-header">Действия</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {orders.map(o => (
                  <tr key={o.id} className="hover:bg-gray-50">
                    <td className="table-cell text-gray-400">#{o.id}</td>
                    <td className="table-cell text-gray-500">#{o.booking_id}</td>
                    <td className="table-cell">{o.total != null ? `${Number(o.total).toLocaleString()} ₸` : '—'}</td>
                    <td className="table-cell">
                      <span className={`badge ${STATUS_COLORS[o.status] ?? 'bg-gray-100 text-gray-500'}`}>
                        {STATUS_LABELS[o.status] ?? o.status}
                      </span>
                    </td>
                    <td className="table-cell">
                      {o.status === 'open' && (
                        <div className="flex gap-1">
                          <button className="btn-ghost py-1 px-2 text-xs text-blue-600" disabled={actioning === o.id} onClick={() => action(o.id, 'complete')}>Выполнить</button>
                          <button className="btn-ghost py-1 px-2 text-xs text-red-500" disabled={actioning === o.id} onClick={() => action(o.id, 'cancel')}>Отменить</button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
                {orders.length === 0 && <tr><td colSpan={5} className="table-cell text-center text-gray-400 py-8">Нет заказов</td></tr>}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
