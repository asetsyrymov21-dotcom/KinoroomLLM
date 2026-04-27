import { useState, useEffect, FormEvent } from 'react'
import { api } from '../lib/api'
import type { Category } from '../lib/api'
import PageHeader from '../components/PageHeader'
import Modal from '../components/Modal'

interface CatForm {
  name: string
  is_active: boolean
  parent_id: string  // '' = нет родителя
}

const emptyForm = (): CatForm => ({
  name: '', is_active: true, parent_id: ''
})

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
    setForm({
      name: c.name,
      is_active: c.is_active,
      parent_id: c.parent_id ? String(c.parent_id) : '',
    })
    setFormError(''); setShowModal(true)
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault(); setSaving(true); setFormError('')
    const body = {
      name: form.name,
      emoji: null,
      is_active: form.is_active,
      parent_id: form.parent_id ? Number(form.parent_id) : null,
    }
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

  // Только корневые категории доступны как родители (без вложенности 3+ уровней)
  const rootCats = cats.filter(c => c.parent_id === null)
  const catMap = Object.fromEntries(cats.map(c => [c.id, c]))

  const byName = (a: Category, b: Category) => a.name.localeCompare(b.name, 'ru')

  // Сортировка: сначала корневые, потом подкатегории, внутри — по алфавиту
  const sorted = [
    ...rootCats.sort(byName),
    ...cats.filter(c => c.parent_id !== null).sort(byName),
  ]

  return (
    <div>
      <PageHeader title="Категории меню" subtitle="Группировка товаров"
        action={<button className="btn-primary" onClick={openCreate}>+ Новая категория</button>} />

      <div className="px-8">
        {loading ? <p className="text-gray-500 text-sm">Загрузка...</p> : cats.length === 0 ? (
          <div className="card px-4 py-8 text-center text-sm text-gray-400">Нет категорий</div>
        ) : (
          <>
          <div className="mobile-records">
            {sorted.map(c => (
              <div key={c.id} className="card p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="font-semibold text-gray-900 leading-5">{c.name}</p>
                    <p className="mt-1 text-sm text-gray-500">
                      {c.parent_id ? `Родитель: ${catMap[c.parent_id]?.name ?? '—'}` : 'Корневая категория'}
                    </p>
                  </div>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-2">
                  <button className="btn-secondary justify-center py-2 text-xs" onClick={() => openEdit(c)}>Изменить</button>
                  <button className="btn-ghost justify-center py-2 text-xs text-red-500" onClick={() => deleteCat(c)}>Удалить</button>
                </div>
              </div>
            ))}
          </div>

          <div className="card desktop-table">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="table-header">Название</th>
                  <th className="table-header">Родитель</th>
                  <th className="table-header">Действия</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {sorted.map(c => (
                  <tr key={c.id} className="hover:bg-gray-50">
                    <td className="table-cell font-medium">
                      {c.parent_id && <span className="text-gray-400 mr-1">↳</span>}
                      {c.name}
                    </td>
                    <td className="table-cell text-gray-500 text-sm">
                      {c.parent_id ? (catMap[c.parent_id]?.name ?? '—') : <span className="text-gray-300">—</span>}
                    </td>
                    <td className="table-cell">
                      <div className="flex gap-2">
                        <button className="btn-ghost py-1 px-2 text-xs" onClick={() => openEdit(c)}>Изменить</button>
                        <button className="btn-ghost py-1 px-2 text-xs text-red-500" onClick={() => deleteCat(c)}>Удалить</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          </>
        )}
      </div>

      {showModal && (
        <Modal title={editCat ? `Изменить: ${editCat.name}` : 'Новая категория'} onClose={() => setShowModal(false)}>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="label">Название</label>
              <input className="input" value={form.name}
                onChange={e => setForm({...form, name: e.target.value})} required />
            </div>

            <div>
              <label className="label">
                Родительская категория <span className="text-gray-400 font-normal">— необязательно</span>
              </label>
              <select className="input" value={form.parent_id}
                onChange={e => setForm({...form, parent_id: e.target.value})}>
                <option value="">— корневая категория —</option>
                {rootCats
                  .filter(c => c.id !== editCat?.id)  // нельзя выбрать себя
                  .map(c => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))
                }
              </select>
            </div>

            <div className="flex items-center gap-2">
              <input type="checkbox" id="cat_active" checked={form.is_active}
                onChange={e => setForm({...form, is_active: e.target.checked})} className="rounded" />
              <label htmlFor="cat_active" className="text-sm text-gray-700">Категория активна</label>
            </div>

            {formError && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{formError}</p>}
            <div className="flex gap-3 pt-2">
              <button type="submit" className="btn-primary flex-1 justify-center" disabled={saving}>
                {saving ? 'Сохранение...' : 'Сохранить'}
              </button>
              <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>Отмена</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
