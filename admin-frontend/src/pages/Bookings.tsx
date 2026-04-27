import { useState, useEffect, useRef } from 'react'
import { api } from '../lib/api'
import type { Booking, Hall, Order, Product } from '../lib/api'
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
const PREP_WINDOW_MINUTES = 20

function fmt(dt: string | null) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString('ru-RU', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit' })
}

function minutesUntil(dt: string) {
  return Math.round((new Date(dt).getTime() - Date.now()) / 60000)
}

function sameLocalDay(a: Date, b: Date) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
}

function timeContext(booking: Booking) {
  if (booking.status === 'active') return { label: 'Идет сейчас', tone: 'bg-red-50 text-red-700 border-red-200', rank: 0 }
  const startIn = minutesUntil(booking.start_time)
  const endIn = booking.end_time ? minutesUntil(booking.end_time) : null
  if (booking.status === 'pending' && startIn <= 0 && (booking.is_open_ended || endIn === null || endIn >= 0)) {
    return { label: 'Пора начинать', tone: 'bg-red-50 text-red-700 border-red-200', rank: 1 }
  }
  if (booking.status === 'pending' && startIn > 0 && startIn <= 30) {
    return { label: `Начинается через ${startIn} мин`, tone: 'bg-yellow-50 text-yellow-700 border-yellow-200', rank: 2 }
  }
  if (booking.status === 'pending' && startIn > 30) {
    return { label: `Через ${startIn} мин`, tone: 'bg-gray-50 text-gray-600 border-gray-200', rank: 3 }
  }
  if (booking.status === 'completed') return { label: 'Завершен', tone: 'bg-blue-50 text-blue-700 border-blue-200', rank: 4 }
  if (booking.status === 'cancelled') return { label: 'Отменен', tone: 'bg-gray-50 text-gray-500 border-gray-200', rank: 5 }
  return { label: STATUS_LABELS[booking.status] ?? booking.status, tone: 'bg-gray-50 text-gray-600 border-gray-200', rank: 6 }
}

function orderTotal(order: Order) {
  if (order.total != null) return Number(order.total)
  return (order.items ?? []).reduce((sum, item) => sum + Number(item.price_at_order) * Number(item.quantity), 0)
}

function isOrderWaiting(order: Order) {
  return ['pending', 'pending_ready', 'created', 'confirmed'].includes(order.status)
}

function isOrderReady(order: Order) {
  return ['completed', 'ready'].includes(order.status)
}

export default function Bookings() {
  const [bookings, setBookings] = useState<Booking[]>([])
  const [halls, setHalls] = useState<Hall[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('today')
  const [selectedHallId, setSelectedHallId] = useState<number | null>(null)
  const [actioning, setActioning] = useState<number | null>(null)
  const autoActivating = useRef<Set<number>>(new Set())

  async function load(silent = false) {
    if (!silent) setLoading(true)
    try {
      const [b, h, o, p] = await Promise.all([
        api.get<Booking[]>('/bookings'),
        api.get<Hall[]>('/halls'),
        api.get<Order[]>('/orders'),
        api.get<Product[]>('/products'),
      ])
      setBookings(b.data); setHalls(h.data)
      setSelectedHallId(current => current ?? h.data[0]?.id ?? null)
      setOrders(Array.isArray(o.data) ? o.data : [])
      setProducts(Array.isArray(p.data) ? p.data : [])
    } finally { if (!silent) setLoading(false) }
  }

  useEffect(() => {
    load()
    const timer = window.setInterval(() => load(true), 30000)
    return () => window.clearInterval(timer)
  }, [])

  async function action(id: number, act: 'activate' | 'complete' | 'cancel') {
    setActioning(id)
    try { await api.post(`/bookings/${id}/${act}`); await load() }
    catch (err: any) { alert(err.response?.data?.detail ?? 'Ошибка') }
    finally { setActioning(null) }
  }

  async function orderAction(id: number, act: 'complete' | 'cancel') {
    setActioning(id)
    try { await api.post(`/orders/${id}/${act}`); await load() }
    catch (err: any) { alert(err.response?.data?.detail ?? 'Ошибка') }
    finally { setActioning(null) }
  }

  useEffect(() => {
    const dueBookings = bookings.filter(b => {
      if (b.status !== 'pending' || autoActivating.current.has(b.id)) return false
      const startIn = minutesUntil(b.start_time)
      const endIn = b.end_time ? minutesUntil(b.end_time) : null
      return startIn <= 0 && (b.is_open_ended || endIn === null || endIn >= 0)
    })
    dueBookings.forEach(b => {
      autoActivating.current.add(b.id)
      api.post(`/bookings/${b.id}/activate`).then(() => load(true)).catch(() => autoActivating.current.delete(b.id))
    })
  }, [bookings])

  const hallMap = Object.fromEntries(halls.map(h => [h.id, h]))
  const productMap = Object.fromEntries(products.map(p => [p.id, p]))
  const ordersByBooking = orders.reduce<Record<number, Order[]>>((acc, order) => {
    acc[order.booking_id] = [...(acc[order.booking_id] ?? []), order]
    return acc
  }, {})
  const prepTasks = bookings
    .flatMap(booking => {
      const bookingOrders = (ordersByBooking[booking.id] ?? []).filter(isOrderWaiting)
      if (bookingOrders.length === 0 || booking.status === 'cancelled' || booking.status === 'completed') return []
      const startIn = minutesUntil(booking.start_time)
      if (startIn > PREP_WINDOW_MINUTES) return []
      return bookingOrders.map(order => ({ booking, order, startIn }))
    })
    .sort((a, b) => a.startIn - b.startIn || new Date(a.booking.start_time).getTime() - new Date(b.booking.start_time).getTime())
  const selectedHall = selectedHallId === null ? null : hallMap[selectedHallId]
  const selectedHallBookings = selectedHallId === null ? [] : bookings.filter(b => b.hall_id === selectedHallId)
  const now = new Date()
  const filtered = selectedHallBookings
    .filter(b => {
      const start = new Date(b.start_time)
      const end = b.end_time ? new Date(b.end_time) : null
      if (filter === 'now') return b.status === 'active' || (b.status === 'pending' && start <= now && (!end || end >= now))
      if (filter === 'future') return b.status === 'pending' && start > now
      return sameLocalDay(start, now)
    })
    .sort((a, b) => {
      const ac = timeContext(a)
      const bc = timeContext(b)
      return ac.rank - bc.rank || new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
    })
  const activeBooking = selectedHallBookings.find(b => b.status === 'active')
  const pendingBookings = selectedHallBookings
    .filter(b => b.status === 'pending')
    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
  const nextPendingBooking = pendingBookings[0]

  return (
    <div>
      <PageHeader title="Бронирования" subtitle="Управление залами и сессиями" />
      <div className="px-8">
        {!loading && (
          <>
            {prepTasks.length > 0 && (
              <div className="mb-5 space-y-3">
                {prepTasks.map(({ booking, order, startIn }) => {
                  const lines = order.items ?? []
                  const total = orderTotal(order)
                  return (
                    <div key={`${booking.id}-${order.id}`} className="border border-orange-200 bg-orange-50 rounded-lg p-4">
                      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-wide text-orange-700">Нужно подготовить</p>
                          <h2 className="mt-1 text-lg font-semibold text-gray-900">{hallMap[booking.hall_id]?.name ?? `Зал #${booking.hall_id}`}</h2>
                          <p className="mt-1 text-sm text-gray-700">
                            Сеанс: {new Date(booking.start_time).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                            {'-'}
                            {booking.end_time ? new Date(booking.end_time).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }) : 'открытая'}
                          </p>
                          <p className="mt-2 text-sm font-medium text-orange-800">
                            {startIn > 0 ? `Через ${startIn} минут начинается сеанс. ` : 'Сеанс уже должен начаться. '}
                            Есть предзаказ на {total.toLocaleString()} ₸.
                          </p>
                          <div className="mt-3">
                            <p className="text-sm font-semibold text-gray-900">Предзаказ:</p>
                            {lines.length > 0 ? (
                              <ul className="mt-1 space-y-1 text-sm text-gray-700">
                                {lines.map(item => (
                                  <li key={item.id}>
                                    {productMap[item.product_id]?.name ?? `Товар #${item.product_id}`} x {item.quantity}
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <p className="mt-1 text-sm text-gray-500">Состав заказа не указан</p>
                            )}
                          </div>
                          <p className="mt-3 text-sm text-gray-700">
                            Нужно подготовить к {new Date(booking.start_time).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </div>
                        <button className="btn-primary" disabled={actioning === order.id} onClick={() => orderAction(order.id, 'complete')}>
                          Готово
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            <div className="grid gap-3 mb-5 sm:grid-cols-2 xl:grid-cols-4">
              {halls.map(hall => {
                const hallBookings = bookings.filter(b => b.hall_id === hall.id)
                const hasActive = hallBookings.some(b => b.status === 'active')
                const pendingCount = hallBookings.filter(b => b.status === 'pending').length
                return (
                  <button
                    key={hall.id}
                    onClick={() => setSelectedHallId(hall.id)}
                    className={`text-left border rounded-lg p-4 transition-colors ${
                      selectedHallId === hall.id
                        ? 'border-brand-500 bg-brand-50'
                        : 'border-gray-200 bg-white hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-semibold text-gray-900">{hall.name}</p>
                      <span className={`badge ${hasActive ? STATUS_COLORS.active : 'bg-gray-100 text-gray-500'}`}>
                        {hasActive ? 'Идет сеанс' : 'Свободен'}
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-gray-500">
                      Ожидают: {pendingCount} · Всего: {hallBookings.length}
                    </p>
                  </button>
                )
              })}
            </div>

            {selectedHall && (
              <div className="mb-5 border border-gray-200 bg-white rounded-lg p-4">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <p className="text-sm text-gray-500">Пульт зала</p>
                    <h2 className="text-lg font-semibold text-gray-900">{selectedHall.name}</h2>
                    <p className="mt-1 text-sm text-gray-600">
                      {activeBooking
                        ? `Активный сеанс #${activeBooking.id}: ${fmt(activeBooking.start_time)} - ${activeBooking.is_open_ended ? 'открытая' : fmt(activeBooking.end_time)}`
                        : nextPendingBooking
                          ? `Ближайшая бронь #${nextPendingBooking.id}: ${fmt(nextPendingBooking.start_time)} - ${nextPendingBooking.is_open_ended ? 'открытая' : fmt(nextPendingBooking.end_time)}`
                          : 'Нет активных или ожидающих броней'}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {activeBooking && (
                      <>
                        <button className="btn-primary" disabled={actioning === activeBooking.id} onClick={() => action(activeBooking.id, 'complete')}>Завершить сеанс</button>
                        <button className="btn-secondary text-red-600" disabled={actioning === activeBooking.id} onClick={() => action(activeBooking.id, 'cancel')}>Отменить</button>
                      </>
                    )}
                    {!activeBooking && nextPendingBooking && (
                      <>
                        <button className="btn-primary" disabled={actioning === nextPendingBooking.id} onClick={() => action(nextPendingBooking.id, 'activate')}>Запустить сеанс</button>
                        <button className="btn-secondary text-red-600" disabled={actioning === nextPendingBooking.id} onClick={() => action(nextPendingBooking.id, 'cancel')}>Отменить бронь</button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        <div className="flex gap-1 mb-4">
          {[
            ['today', 'Сегодня'],
            ['now', 'Сейчас'],
            ['future', 'Будущие'],
          ].map(([f, label]) => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                filter === f ? 'bg-brand-600 text-white' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}>
              {label}
            </button>
          ))}
        </div>

        {loading ? <p className="text-gray-500 text-sm">Загрузка...</p> : (
          <div className="space-y-3">
            {filtered.map(b => {
              const context = timeContext(b)
              const bookingOrders = ordersByBooking[b.id] ?? []
              const pendingOrder = bookingOrders.find(isOrderWaiting)
              const preorderTotal = bookingOrders.reduce((sum, order) => sum + orderTotal(order), 0)
              const preorderItemsCount = bookingOrders.reduce((sum, order) => sum + (order.items ?? []).reduce((items, item) => items + Number(item.quantity), 0), 0)
              return (
                <div key={b.id} className={`border rounded-lg bg-white p-4 ${context.tone}`}>
                  <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-base font-semibold text-gray-900">{hallMap[b.hall_id]?.name ?? `Зал #${b.hall_id}`}</h3>
                        <span className="text-xs text-gray-400">#{b.id}</span>
                        <span className={`badge ${STATUS_COLORS[b.status] ?? 'bg-gray-100 text-gray-500'}`}>{STATUS_LABELS[b.status] ?? b.status}</span>
                      </div>
                      <p className="mt-2 text-sm font-medium">{context.label}</p>
                      <p className="mt-1 text-xs text-gray-500">
                        {fmt(b.start_time)} - {b.is_open_ended ? 'открытая' : fmt(b.end_time)}
                      </p>
                    </div>

                    <div className="min-w-[180px]">
                      <p className="text-xs text-gray-500">Предзаказ</p>
                      {bookingOrders.length > 0 ? (
                        <p className="mt-1 text-sm font-semibold text-gray-900">
                          🍿 {preorderTotal.toLocaleString()} ₸
                          {preorderItemsCount > 0 && <span className="ml-2 text-xs font-normal text-gray-500">позиций: {preorderItemsCount}</span>}
                          {bookingOrders.every(isOrderReady) && <span className="ml-2 text-xs font-normal text-green-700">готово</span>}
                        </p>
                      ) : (
                        <p className="mt-1 text-sm text-gray-400">Нет</p>
                      )}
                    </div>

                    <div className="flex flex-wrap gap-2 xl:justify-end">
                      {pendingOrder && (
                        <button className="btn-secondary text-orange-700" disabled={actioning === pendingOrder.id} onClick={() => orderAction(pendingOrder.id, 'complete')}>Готово</button>
                      )}
                      {b.status === 'pending' && (
                        <>
                          <button className="btn-primary" disabled={actioning === b.id} onClick={() => action(b.id, 'activate')}>Начать сеанс</button>
                          <button className="btn-secondary text-red-600" disabled={actioning === b.id} onClick={() => action(b.id, 'cancel')}>Отмена</button>
                        </>
                      )}
                      {b.status === 'active' && (
                        <>
                          <button className="btn-primary" disabled={actioning === b.id} onClick={() => action(b.id, 'complete')}>Завершить</button>
                          <button className="btn-secondary text-red-600" disabled={actioning === b.id} onClick={() => action(b.id, 'cancel')}>Отмена</button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
            {filtered.length === 0 && <div className="border border-gray-200 rounded-lg bg-white p-8 text-center text-sm text-gray-400">Нет бронирований</div>}
          </div>
        )}
      </div>
    </div>
  )
}
