import { useState, useEffect, FormEvent } from 'react'
import { api } from '../lib/api'
import type { Hall, StockBalance } from '../lib/api'
import PageHeader from '../components/PageHeader'
import Modal from '../components/Modal'

interface ReceiveForm { product_id: string; quantity: string; note: string }

export default function Stock() {
  const [halls, setHalls] = useState<Hall[]>([])
  const [selectedHall, setSelectedHall] = useState<number | null>(null)
  const [inventory, setInventory] = useState<StockBalance[]>([])
  const [loading, setLoading] = useState(false)
  const [showReceive, setShowReceive] = useState(false)
  const [receiveForm, setReceiveForm] = useState<ReceiveForm>({ product_id: '', quantity: '', note: '' })
  const [receiving, setReceiving] = useState(false)
  const [receiveError, setReceiveError] = useState('')

  async function loadHalls() {
    const { data } = await api.get<Hall[]>('/halls')
    setHalls(data)
    if (data.length > 0 && !selectedHall) setSelectedHall(data[0].id)
  }

  async function loadInventory(hallId: number) {
    setLoading(true)
    try {
      const { data } = await api.get<StockBalance[]>(`/stock/halls/${hallId}/inventory`)
      setInventory(data)
    } catch { setInventory([]) }
    finally { setLoading(false) }
  }

  useEffect(() => { loadHalls() }, [])
  useEffect(() => { if (selectedHall) loadInventory(selectedHall) }, [selectedHall])

  async function handleReceive(e: FormEvent) {
    e.preventDefault(); setReceiving(true); setReceiveError('')
    try {
      await api.post('/stock/receive', {
        hall_id: selectedHall,
        product_id: Number(receiveForm.product_id),
        quantity: Number(receiveForm.quantity),
        note: receiveForm.note || null,
      })
      setShowReceive(false)
      if (selectedHall) loadInventory(selectedHall)
    } catch (err: any) { setReceiveError(err.response?.data?.detail ?? 'Ошибка') }
    finally { setReceiving(false) }
  }

  return (
    <div>
      <PageHeader title="Склад" subtitle="Остатки товаров по залам"
        action={selectedHall ? <button className="btn-primary" onClick={() => setShowReceive(true)}>+ Приход товара</button> : undefined} />
      <div className="px-8">
        {/* Hall selector */}
        <div className="flex gap-2 mb-4 flex-wrap">
          {halls.map(h => (
            <button key={h.id} onClick={() => setSelectedHall(h.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedHall === h.id ? 'bg-brand-600 text-white' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}>
              {h.name}
            </button>
          ))}
        </div>

        {loading ? <p className="text-gray-500 text-sm">Загрузка...</p> : (
          <div className="card overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="table-header">Товар</th>
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
                {inventory.length === 0 && <tr><td colSpan={5} className="table-cell text-center text-gray-400 py-8">Склад пуст</td></tr>}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showReceive && (
        <Modal title="Приход товара" onClose={() => setShowReceive(false)}>
          <form onSubmit={handleReceive} className="space-y-4">
            <div><label className="label">ID товара</label>
              <input className="input" type="number" min="1" value={receiveForm.product_id}
                onChange={e => setReceiveForm({...receiveForm, product_id: e.target.value})}
                placeholder="Найдите ID товара в разделе Товары" required /></div>
            <div><label className="label">Количество</label>
              <input className="input" type="number" min="1" step="0.001" value={receiveForm.quantity}
                onChange={e => setReceiveForm({...receiveForm, quantity: e.target.value})} required /></div>
            <div><label className="label">Примечание</label>
              <input className="input" value={receiveForm.note}
                onChange={e => setReceiveForm({...receiveForm, note: e.target.value})}
                placeholder="Необязательно" /></div>
            {receiveError && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{receiveError}</p>}
            <div className="flex gap-3 pt-2">
              <button type="submit" className="btn-primary flex-1 justify-center" disabled={receiving}>{receiving ? 'Сохранение...' : 'Принять товар'}</button>
              <button type="button" className="btn-secondary" onClick={() => setShowReceive(false)}>Отмена</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
