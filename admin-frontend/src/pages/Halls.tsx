import { useState, useEffect, FormEvent } from 'react'
import { api } from '../lib/api'
import type { Hall } from '../lib/api'
import PageHeader from '../components/PageHeader'
import Modal from '../components/Modal'

interface HallForm {
  name: string
  capacity: string
  price_per_hour: string
  is_active: boolean
}

const emptyForm = (): HallForm => ({ name: '', capacity: '', price_per_hour: '', is_active: true })

export default function Halls() {
  const [halls, setHalls] = useState<Hall[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editHall, setEditHall] = useState<Hall | null>(null)
  const [form, setForm] = useState<HallForm>(emptyForm())
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState('')

  async function load() {
    setLoading(true)
    try {
      const { data } = await api.get<Hall[]>('/halls')
      setHalls(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  function openCreate() {
    setEditHall(null)
    setForm(emptyForm())
    setFormError('')
    setShowModal(true)
  }

  function openEdit(h: Hall) {
    setEditHall(h)
    setForm({
      name: h.name,
      capacity: String(h.capacity),
      price_per_hour: String(h.price_per_hour),
      is_active: h.is_active,
    })
    setFormError('')
    setShowModal(true)
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    setFormError('')
    const body = {
      name: form.name,
      capacity: Number(form.capacity),
      price_per_hour: Number(form.price_per_hour),
      is_active: form.is_active,
    }
    try {
      if (editHall) {
        await api.patch(`/halls/${editHall.id}`, body)
      } else {
        await api.post('/halls', body)
      }
      setShowModal(false)
      await load()
    } catch (err: any) {
      setFormError(err.response?.data?.detail ?? 'Ошибка')
    } finally {
      setSaving(false)
    }
  }

  async function deleteHall(h: Hall) {
    if (!confirm(`Удалить зал «${h.name}»?`)) return
    try {
      await api.delete(`/halls/${h.id}`)
      await load()
    } catch (err: any) {
      alert(err.response?.data?.detail ?? 'Ошибка')
    }
  }

  return (
    <div>
      <PageHeader
        title="Залы"
        subtitle="Управление кинозалами"
        action={<button className="btn-primary" onClick={openCreate}>+ Новый зал</button>}
      />
      <div className="px-8">
        {loading ? (
          <p className="text-gray-500 text-sm">Загрузка...</p>
        ) : (
          <div className="card overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="table-header">Название</th>
                  <th className="table-header">Вместимость</th>
                  <th className="table-header">₸/час</th>
                  <th className="table-header">Статус</th>
                  <th className="table-header">Действия</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {halls.map((h) => (
                  <tr key={h.id} className="hover:bg-gray-50">
                    <td className="table-cell font-medium">{h.name}</td>
                    <td className="table-cell">{h.capacity}</td>
                    <td className="table-cell">{Number(h.price_per_hour).toLocaleString()}</td>
                    <td className="table-cell">
                      <span className={`badge ${h.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {h.is_active ? 'Активен' : 'Скрыт'}
                      </span>
                    </td>
                    <td className="table-cell">
                      <div className="flex gap-2">
                        <button className="btn-ghost py-1 px-2 text-xs" onClick={() => openEdit(h)}>Изменить</button>
                        <button className="btn-ghost py-1 px-2 text-xs text-red-500" onClick={() => deleteHall(h)}>Удалить</button>
                      </div>
                    </td>
                  </tr>
                ))}
                {halls.length === 0 && (
                  <tr><td colSpan={5} className="table-cell text-center text-gray-400 py-8">Нет залов</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showModal && (
        <Modal title={editHall ? `Изменить: ${editHall.name}` : 'Новый зал'} onClose={() => setShowModal(false)}>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="label">Название</label>
              <input className="input" value={form.name} onChange={e => setForm({...form, name: e.target.value})} required />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Вместимость (чел.)</label>
                <input className="input" type="number" min="1" value={form.capacity} onChange={e => setForm({...form, capacity: e.target.value})} required />
              </div>
              <div>
                <label className="label">Цена (₸/час)</label>
                <input className="input" type="number" min="0" step="0.01" value={form.price_per_hour} onChange={e => setForm({...form, price_per_hour: e.target.value})} required />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" id="hall_active" checked={form.is_active} onChange={e => setForm({...form, is_active: e.target.checked})} className="rounded" />
              <label htmlFor="hall_active" className="text-sm text-gray-700">Зал активен (виден в мини-аппе)</label>
            </div>
            {formError && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{formError}</p>}
            <div className="flex gap-3 pt-2">
              <button type="submit" className="btn-primary flex-1 justify-center" disabled={saving}>{saving ? 'Сохранение...' : 'Сохранить'}</button>
              <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>Отмена</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
