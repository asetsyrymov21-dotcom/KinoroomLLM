import { useState, useEffect, FormEvent } from 'react'
import { api } from '../lib/api'
import type { Hall, StockBalance } from '../lib/api'
import PageHeader from '../components/PageHeader'
import Modal from '../components/Modal'

interface ReceiveForm { hall_id: string; product_id: string; quantity: string; note: string }

export default function Stock() {
  const [halls, setHalls] = useState<Hall[]>([])
  const [inventory, setInventory] = useState<(StockBalance & { hall_name: string })[]>([])
  const [loading, setLoading] = useState(false)
  const [showReceive, setShowReceive] = useState(false)
  const [receiveForm, setReceiveForm] = useState<ReceiveForm>({ hall_id: '', product_id: '', quantity: '', note: '' })
  const [receiving, setReceiving] = useState(false)
  const [receiveError, setReceiveError] = useState('')

  async function loadAll() {
    setLoading(true)
    try {
      const { data: hallList } = await api.get<Hall[]>('/halls')
      setHalls(hallList)
      if (receiveForm.hall_id === '' && hallList.length > 0) {
        setReceiveForm(f => ({ ...f, hall_id: String(hallList[0].id) }))
      }
      const results = await Promise.all(
        hallList.map(h =>
          api.get<StockBalance[]>(`/stock/halls/${h.id}/inventory`)
            .then(r => r.data.map(item => ({ ...item, hall_name: h.name })))
            .catch(() => [])
        )
      )
      setInventory(results.flat())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadAll() }, [])

  async function handleReceive(e: FormEvent) {
    e.preventDefault(); setReceiving(true); setReceiveError('')
    try {
      await api.post('/stock/receive', {
        hall_id: Number(receiveForm.hall_id),
        product_id: Number(receiveForm.product_id),
        quantity: Number(receiveForm.quantity),
        note: receiveForm.note || null,
      })
      setShowReceive(false)
      loadAll()
    } catch (err: any) { setReceiveError(err.response?.data?.detail ?? 'Ошибка') }
    finally { setReceiving(false) }
  }

  return (
    <div>
      <PageHeader title="Склад" subtitle="Остатки товаров"
        action={<button className="btn-primary" onClick={() => setShowReceive(true)}>+ Приход товара</button>} />
      <div className="px-8">
        {loading ? <p className="text-gray-500 text-sm">Загрузка...</p> : (
          <div className="card overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="table-header">Товар</th>
                  <th className="table-header">Зал</th>
                  <th className="table-header">Остаток</th>
                  <th className="table-header">В резерве</th>
                  <th className="table-header">Свободно</th>
                  <th className="table-header">Ед.</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {inventory.map(item => (
                  <tr key={`${item.hall_id}-${item.product_id}`} className="hover:bg-gray-50">
                    <td className="table-cell font-medium">{item.product_name}</td>
                    <td className="table-cell text-gray-500">{item.hall_name}</td>
                    <td className="table-cell">{item.quantity}</td>
                    <td className="table-cell text-orange-600">{item.reserved_quantity}</td>
                    <td className="table-cell">
                      <span className={`font-medium ${item.quantity - item.reserved_quantity <= 0 ? 'text-red-600' : 'text-green-700'}`}>
                        {item.quantity - item.reserved_quantity}
                      </span>
                    </td>
                    <td className="table-cell text-gray-500">{item.unit}</td>
                  </tr>
                ))}
                {inventory.length === 0 && (
                  <tr><td colSpan={6} className="table-cell text-center text-gray-400 py-8">Склад пуст</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showReceive && (
        <Modal title="Приход товара" onClose={() => setShowReceive(false)}>
          <form onSubmit={handleReceive} className="space-y-4">
            <div><label className="label">Зал</label>
              <select className="input" value={receiveForm.hall_id}
                onChange={e => setReceiveForm({ ...receiveForm, hall_id: e.target.value })} required>
                {halls.map(h => <option key={h.id} value={h.id}>{h.name}</option>)}
              </select>
            </div>
            <div><label className="label">ID товара</label>
              <input className="input" type="number" min="1" value={receiveForm.product_id}
                onChange={e => setReceiveForm({ ...receiveForm, product_id: e.target.value })}
                placeholder="Найдите ID товара в разделе Товары" required /></div>
            <div><label className="label">Количество</label>
              <input className="input" type="number" min="1" step="0.001" value={receiveForm.quantity}
                onChange={e => setReceiveForm({ ...receiveForm, quantity: e.target.value })} required /></div>
            <div><label className="label">Примечание</label>
              <input className="input" value={receiveForm.note}
                onChange={e => setReceiveForm({ ...receiveForm, note: e.target.value })}
                placeholder="Необязательно" /></div>
            {receiveError && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{receiveError}</p>}
            <div className="flex gap-3 pt-2">
              <button type="submit" className="btn-primary flex-1 justify-center" disabled={receiving}>
                {receiving ? 'Сохранение...' : 'Принять товар'}
              </button>
              <button type="button" className="btn-secondary" onClick={() => setShowReceive(false)}>Отмена</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
