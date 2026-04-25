import { useState, useEffect, FormEvent } from 'react'
import { api } from '../lib/api'
import type { Category } from '../lib/api'
import PageHeader from '../components/PageHeader'
import Modal from '../components/Modal'

interface CatForm { name: string; emoji: string; position: string; is_active: boolean }
const emptyForm = (): CatForm => ({ name: '', emoji: '', position: '0', is_active: true })

export default function Categories() {
  const [cats, setCats] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editCat, setEditCat] = useState<Category | null>(null)
  const [form, setForm] = useState<CatForm>(emptyForm())
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState('')

  async function load() {
    setLoading(true)
    try {
      const { data } = await api.get<Category[]>('/categories')
      setCats(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  function openCreate() {
    setEditCat(null); setForm(emptyForm()); setFormError(''); setShowModal(true)
  }
  function openEdit(c: Category) {
    setEditCat(c)
    setForm({ name: c.name, emoji: c.emoji ?? '', position: String(c.position), is_active: c.is_active })
    setFormError(''); setShowModal(true)
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault(); setSaving(true); setFormError('')
    const body = { name: form.name, emoji: form.emoji || null, position: Number(form.position), is_active: form.is_active }
    try {
      if (editCat) await api.patch(`/categories/${editCat.id}`, body)
      else await api.post('/categories', body)
      setShowModal(false); await load()
    } catch (err: any) {
      setFormError(err.response?.data?.detail ?? 'Ошибка')
    } finally { setSaving(false) }
  }

  async function deleteCat(c: Category) {
    if (!confirm(`Удалить категорию «${c.name}»?`)) return
    try { await api.delete(`/categories/${c.id}`); await load() }
    catch (err: any) { alert(err.response?.data?.detail ?? 'Ошибка') }
  }

  return (
    <div>
      <PageHeader title="Категории меню" subtitle="Группировка товаров"
        action={<button className="btn-primary" onClick={openCreate}>+ Новая категория</button>} />
      <div className="px-8">
        {loading ? <p className="text-gray-500 text-sm">Загрузка...</p> : (
          <div className="card overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="table-header">Название</th>
                  <th className="table-header">Эмодзи</th>
                  <th className="table-header">Позиция</th>
                  <th className="table-header">Статус</th>
                  <th className="table-header">Действия</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {cats.map(c => (
                  <tr key={c.id} className="hover:bg-gray-50">
                    <td className="table-cell font-medium">{c.name}</td>
                    <td className="table-cell text-xl">{c.emoji ?? '—'}</td>
                    <td className="table-cell text-gray-500">{c.position}</td>
                    <td className="table-cell">
                      <span className={`badge ${c.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {c.is_active ? 'Активна' : 'Скрыта'}
                      </span>
                    </td>
                    <td className="table-cell">
                      <div className="flex gap-2">
                        <button className="btn-ghost py-1 px-2 text-xs" onClick={() => openEdit(c)}>Изменить</button>
                        <button className="btn-ghost py-1 px-2 text-xs text-red-500" onClick={() => deleteCat(c)}>Удалить</button>
                      </div>
                    </td>
                  </tr>
                ))}
                {cats.length === 0 && <tr><td colSpan={5} className="table-cell text-center text-gray-400 py-8">Нет категорий</td></tr>}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showModal && (
        <Modal title={editCat ? `Изменить: ${editCat.name}` : 'Новая категория'} onClose={() => setShowModal(false)}>
          <form onSubmit={handleSave} className="space-y-4">
            <div><label className="label">Название</label>
              <input className="input" value={form.name} onChange={e => setForm({...form, name: e.target.value})} required /></div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="label">Эмодзи</label>
                <input className="input text-2xl" value={form.emoji} onChange={e => setForm({...form, emoji: e.target.value})} placeholder="🍿" /></div>
              <div><label className="label">Позиция</label>
                <input className="input" type="number" value={form.position} onChange={e => setForm({...form, position: e.target.value})} /></div>
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" id="cat_active" checked={form.is_active} onChange={e => setForm({...form, is_active: e.target.checked})} className="rounded" />
              <label htmlFor="cat_active" className="text-sm text-gray-700">Категория активна</label>
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
