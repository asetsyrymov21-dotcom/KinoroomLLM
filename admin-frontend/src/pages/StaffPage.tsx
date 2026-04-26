import { useState, useEffect, FormEvent } from 'react'
import { api } from '../lib/api'
import type { StaffMember } from '../lib/api'
import PageHeader from '../components/PageHeader'
import Modal from '../components/Modal'

interface StaffForm { username: string; password: string; role: 'admin' | 'operator' }
const emptyForm = (): StaffForm => ({ username: '', password: '', role: 'operator' })

export default function StaffPage() {
  const [staff, setStaff] = useState<StaffMember[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editStaff, setEditStaff] = useState<StaffMember | null>(null)
  const [form, setForm] = useState<StaffForm>(emptyForm())
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState('')

  async function load() {
    setLoading(true)
    try {
      const { data } = await api.get<StaffMember[]>('/staff')
      setStaff(data)
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  function openCreate() { setEditStaff(null); setForm(emptyForm()); setFormError(''); setShowModal(true) }
  function openEdit(s: StaffMember) {
    setEditStaff(s)
    setForm({ username: s.username, password: '', role: s.role })
    setFormError(''); setShowModal(true)
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault(); setSaving(true); setFormError('')
    try {
      if (editStaff) {
        const body: any = { role: form.role }
        if (form.password) body.password = form.password
        await api.patch(`/staff/${editStaff.id}`, body)
      } else {
        await api.post('/staff', { username: form.username, password: form.password, role: form.role })
      }
      setShowModal(false); await load()
    } catch (err: any) { setFormError(err.response?.data?.detail ?? 'Ошибка') }
    finally { setSaving(false) }
  }

  async function deleteStaff(s: StaffMember) {
    if (!confirm(`Удалить сотрудника «${s.username}»?`)) return
    try { await api.delete(`/staff/${s.id}`); await load() }
    catch (err: any) { alert(err.response?.data?.detail ?? 'Ошибка') }
  }

  return (
    <div>
      <PageHeader title="Сотрудники" subtitle="Администраторы и операторы"
        action={<button className="btn-primary" onClick={openCreate}>+ Добавить сотрудника</button>} />
      <div className="px-8">
        {loading ? <p className="text-gray-500 text-sm">Загрузка...</p> : (
          <div className="card overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="table-header">Логин</th>
                  <th className="table-header">Роль</th>
                  <th className="table-header">Действия</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {staff.map(s => (
                  <tr key={s.id} className="hover:bg-gray-50">
                    <td className="table-cell font-medium">{s.username}</td>
                    <td className="table-cell">
                      <span className={`badge ${s.role === 'admin' ? 'bg-brand-100 text-brand-700' : 'bg-gray-100 text-gray-600'}`}>
                        {s.role === 'admin' ? 'Администратор' : 'Оператор'}
                      </span>
                    </td>
                    <td className="table-cell">
                      <div className="flex gap-2">
                        <button className="btn-ghost py-1 px-2 text-xs" onClick={() => openEdit(s)}>Изменить</button>
                        <button className="btn-ghost py-1 px-2 text-xs text-red-500" onClick={() => deleteStaff(s)}>Удалить</button>
                      </div>
                    </td>
                  </tr>
                ))}
                {staff.length === 0 && <tr><td colSpan={3} className="table-cell text-center text-gray-400 py-8">Нет сотрудников</td></tr>}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showModal && (
        <Modal title={editStaff ? `Изменить: ${editStaff.username}` : 'Новый сотрудник'} onClose={() => setShowModal(false)}>
          <form onSubmit={handleSave} className="space-y-4">
            {!editStaff && (
              <div><label className="label">Логин</label>
                <input className="input" value={form.username} onChange={e => setForm({...form, username: e.target.value})} required /></div>
            )}
            <div><label className="label">{editStaff ? 'Новый пароль (оставьте пустым чтобы не менять)' : 'Пароль'}</label>
              <input className="input" type="password" value={form.password}
                onChange={e => setForm({...form, password: e.target.value})}
                minLength={editStaff ? 0 : 6} required={!editStaff} placeholder="••••••" /></div>
            <div><label className="label">Роль</label>
              <select className="input" value={form.role} onChange={e => setForm({...form, role: e.target.value as any})}>
                <option value="operator">Оператор — видит брони, заказы, склад</option>
                <option value="admin">Администратор — полный доступ</option>
              </select>
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
