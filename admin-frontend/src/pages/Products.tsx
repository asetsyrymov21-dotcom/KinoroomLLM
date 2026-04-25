import { useState, useEffect, FormEvent } from 'react'
import { api } from '../lib/api'
import type { Product, Category } from '../lib/api'
import PageHeader from '../components/PageHeader'
import Modal from '../components/Modal'

interface ProdForm {
  name: string; sku: string; price: string; cost_price: string
  unit: string; is_active: boolean; category_id: string
}
const emptyForm = (): ProdForm => ({
  name: '', sku: '', price: '', cost_price: '', unit: 'шт', is_active: true, category_id: ''
})

export default function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editProd, setEditProd] = useState<Product | null>(null)
  const [form, setForm] = useState<ProdForm>(emptyForm())
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState('')

  async function load() {
    setLoading(true)
    try {
      const [p, c] = await Promise.all([
        api.get<Product[]>('/products'),
        api.get<Category[]>('/categories'),
      ])
      setProducts(p.data); setCategories(c.data)
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  function openCreate() { setEditProd(null); setForm(emptyForm()); setFormError(''); setShowModal(true) }
  function openEdit(p: Product) {
    setEditProd(p)
    setForm({
      name: p.name, sku: p.sku ?? '', price: String(p.price),
      cost_price: p.cost_price != null ? String(p.cost_price) : '',
      unit: p.unit, is_active: p.is_active, category_id: p.category_id ? String(p.category_id) : ''
    })
    setFormError(''); setShowModal(true)
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault(); setSaving(true); setFormError('')
    const body = {
      name: form.name, sku: form.sku.trim() || null, price: Number(form.price),
      cost_price: form.cost_price ? Number(form.cost_price) : null,
      unit: form.unit, is_active: form.is_active,
      category_id: form.category_id ? Number(form.category_id) : null,
    }
    try {
      if (editProd) await api.patch(`/products/${editProd.id}`, body)
      else await api.post('/products', body)
      setShowModal(false); await load()
    } catch (err: any) { setFormError(err.response?.data?.detail ?? 'Ошибка') }
    finally { setSaving(false) }
  }

  const catMap = Object.fromEntries(categories.map(c => [c.id, c]))

  return (
    <div>
      <PageHeader title="Товары" subtitle="Меню и позиции для заказов"
        action={<button className="btn-primary" onClick={openCreate}>+ Новый товар</button>} />
      <div className="px-8">
        {loading ? <p className="text-gray-500 text-sm">Загрузка...</p> : (
          <div className="card overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="table-header">Название</th>
                  <th className="table-header">SKU</th>
                  <th className="table-header">Категория</th>
                  <th className="table-header">Цена</th>
                  <th className="table-header">Ед.</th>
                  <th className="table-header">Статус</th>
                  <th className="table-header">Действия</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {products.map(p => (
                  <tr key={p.id} className="hover:bg-gray-50">
                    <td className="table-cell font-medium">{p.name}</td>
                    <td className="table-cell font-mono text-xs text-gray-500">{p.sku}</td>
                    <td className="table-cell text-gray-500">{p.category_id ? (catMap[p.category_id]?.name ?? '—') : '—'}</td>
                    <td className="table-cell">{Number(p.price).toLocaleString()} ₸</td>
                    <td className="table-cell text-gray-500">{p.unit}</td>
                    <td className="table-cell">
                      <span className={`badge ${p.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {p.is_active ? 'Активен' : 'Скрыт'}
                      </span>
                    </td>
                    <td className="table-cell">
                      <button className="btn-ghost py-1 px-2 text-xs" onClick={() => openEdit(p)}>Изменить</button>
                    </td>
                  </tr>
                ))}
                {products.length === 0 && <tr><td colSpan={7} className="table-cell text-center text-gray-400 py-8">Нет товаров</td></tr>}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showModal && (
        <Modal title={editProd ? `Изменить: ${editProd.name}` : 'Новый товар'} onClose={() => setShowModal(false)} size="lg">
          <form onSubmit={handleSave} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div><label className="label">Название</label>
                <input className="input" value={form.name} onChange={e => setForm({...form, name: e.target.value})} required /></div>
              <div><label className="label">SKU (артикул) <span className="text-gray-400 font-normal">— необязательно</span></label>
                <input className="input font-mono" value={form.sku} onChange={e => setForm({...form, sku: e.target.value})} placeholder="A-001" /></div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div><label className="label">Цена (₸)</label>
                <input className="input" type="number" min="0" step="0.01" value={form.price} onChange={e => setForm({...form, price: e.target.value})} required /></div>
              <div><label className="label">Себестоимость</label>
                <input className="input" type="number" min="0" step="0.01" value={form.cost_price} onChange={e => setForm({...form, cost_price: e.target.value})} /></div>
              <div><label className="label">Единица</label>
                <input className="input" value={form.unit} onChange={e => setForm({...form, unit: e.target.value})} placeholder="шт" /></div>
            </div>
            <div><label className="label">Категория</label>
              <select className="input" value={form.category_id} onChange={e => setForm({...form, category_id: e.target.value})}>
                <option value="">— без категории —</option>
                {categories.map(c => <option key={c.id} value={c.id}>{c.emoji ? `${c.emoji} ` : ''}{c.name}</option>)}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" id="prod_active" checked={form.is_active} onChange={e => setForm({...form, is_active: e.target.checked})} className="rounded" />
              <label htmlFor="prod_active" className="text-sm text-gray-700">Товар активен</label>
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
