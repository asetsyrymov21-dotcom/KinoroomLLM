import { useState, useEffect, FormEvent } from 'react'
import { api } from '../../lib/api'
import type { Tenant } from '../../lib/api'
import PageHeader from '../../components/PageHeader'
import Modal from '../../components/Modal'

interface TenantFormData {
  name: string
  slug: string
  address: string
  phone: string
  logo_url: string
}

interface AdminFormData {
  username: string
  password: string
}

interface StaffMember {
  id: number
  username: string
  role: string
}

export default function Tenants() {
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Create/Edit tenant modal
  const [showModal, setShowModal] = useState(false)
  const [editTenant, setEditTenant] = useState<Tenant | null>(null)
  const [form, setForm] = useState<TenantFormData>({ name: '', slug: '', address: '', phone: '', logo_url: '' })
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState('')

  // Create admin modal
  const [adminModalTenant, setAdminModalTenant] = useState<Tenant | null>(null)
  const [adminForm, setAdminForm] = useState<AdminFormData>({ username: '', password: '' })
  const [adminSaving, setAdminSaving] = useState(false)
  const [adminResult, setAdminResult] = useState('')
  const [adminError, setAdminError] = useState('')

  // Staff list modal
  const [staffModalTenant, setStaffModalTenant] = useState<Tenant | null>(null)
  const [staffList, setStaffList] = useState<StaffMember[]>([])
  const [staffLoading, setStaffLoading] = useState(false)

  async function load() {
    setLoading(true)
    try {
      const { data } = await api.get<Tenant[]>('/tenants')
      setTenants(data)
    } catch {
      setError('Не удалось загрузить кинорумы')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  function openCreate() {
    setEditTenant(null)
    setForm({ name: '', slug: '', address: '', phone: '', logo_url: '' })
    setFormError('')
    setShowModal(true)
  }

  function openEdit(t: Tenant) {
    setEditTenant(t)
    setForm({ name: t.name, slug: t.slug, address: t.address ?? '', phone: t.phone ?? '', logo_url: t.logo_url ?? '' })
    setFormError('')
    setShowModal(true)
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    setFormError('')
    try {
      const body = {
        name: form.name, slug: form.slug,
        address: form.address || null,
        phone: form.phone || null,
        logo_url: form.logo_url || null,
      }
      if (editTenant) {
        await api.patch(`/tenants/${editTenant.id}`, body)
      } else {
        await api.post('/tenants', body)
      }
      setShowModal(false)
      await load()
    } catch (err: any) {
      setFormError(err.response?.data?.detail ?? 'Ошибка')
    } finally {
      setSaving(false)
    }
  }

  async function toggleActive(t: Tenant) {
    try {
      await api.patch(`/tenants/${t.id}`, { is_active: !t.is_active })
      await load()
    } catch (err: any) {
      alert(err.response?.data?.detail ?? 'Ошибка')
    }
  }

  async function deleteTenant(t: Tenant) {
    if (!confirm(`Удалить кинорум «${t.name}»? Это удалит все связанные данные.`)) return
    try {
      await api.delete(`/tenants/${t.id}`)
      await load()
    } catch (err: any) {
      alert(err.response?.data?.detail ?? 'Ошибка')
    }
  }

  function openAdminModal(t: Tenant) {
    setAdminModalTenant(t)
    setAdminForm({ username: '', password: '' })
    setAdminResult('')
    setAdminError('')
  }

  async function handleCreateAdmin(e: FormEvent) {
    e.preventDefault()
    if (!adminModalTenant) return
    setAdminSaving(true)
    setAdminError('')
    setAdminResult('')
    try {
      const { data } = await api.post(`/tenants/${adminModalTenant.id}/staff`, adminForm)
      setAdminResult(`✅ Администратор создан. Логин: ${data.username}`)
    } catch (err: any) {
      setAdminError(err.response?.data?.detail ?? 'Ошибка')
    } finally {
      setAdminSaving(false)
    }
  }

  async function openStaffModal(t: Tenant) {
    setStaffModalTenant(t)
    setStaffList([])
    setStaffLoading(true)
    try {
      const { data } = await api.get<StaffMember[]>(`/tenants/${t.id}/staff`)
      setStaffList(data)
    } finally {
      setStaffLoading(false)
    }
  }

  const ROLE_LABELS: Record<string, string> = {
    admin: 'Администратор',
    operator: 'Оператор',
  }

  return (
    <div>
      <PageHeader
        title="Кинорумы"
        subtitle="Управление тенантами платформы"
        action={
          <button className="btn-primary" onClick={openCreate}>
            + Новый кинорум
          </button>
        }
      />

      <div className="px-8">
        {loading && <p className="text-gray-500 text-sm">Загрузка...</p>}
        {error && <p className="text-red-600 text-sm">{error}</p>}

        {!loading && tenants.length === 0 && (
          <div className="card px-4 py-8 text-center text-sm text-gray-400">
            Нет кинорумов. Создайте первый.
          </div>
        )}

        {!loading && tenants.length > 0 && (
          <>
          <div className="mobile-records">
            {tenants.map((t) => (
              <div key={t.id} className="card p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="font-semibold text-gray-900 leading-5">{t.name}</p>
                    <p className="mt-1 font-mono text-xs text-gray-500">{t.slug}</p>
                  </div>
                  <span
                    className={`badge shrink-0 ${
                      t.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                    }`}
                  >
                    {t.is_active ? 'Активен' : 'Отключён'}
                  </span>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-2">
                  <button className="btn-secondary justify-center py-2 text-xs" onClick={() => openEdit(t)}>
                    Изменить
                  </button>
                  <button className="btn-secondary justify-center py-2 text-xs" onClick={() => toggleActive(t)}>
                    {t.is_active ? 'Отключить' : 'Включить'}
                  </button>
                  <button
                    className="btn-secondary justify-center py-2 text-xs text-gray-600"
                    onClick={() => openStaffModal(t)}
                  >
                    Сотрудники
                  </button>
                  <button
                    className="btn-secondary justify-center py-2 text-xs text-brand-600"
                    onClick={() => openAdminModal(t)}
                  >
                    Администратор
                  </button>
                  <button
                    className="btn-ghost col-span-2 justify-center py-2 text-xs text-red-500"
                    onClick={() => deleteTenant(t)}
                  >
                    Удалить
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="card desktop-table">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="table-header">Название</th>
                  <th className="table-header">Slug</th>
                  <th className="table-header">Статус</th>
                  <th className="table-header">Действия</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {tenants.map((t) => (
                  <tr key={t.id} className="hover:bg-gray-50 transition-colors">
                    <td className="table-cell font-medium">{t.name}</td>
                    <td className="table-cell text-gray-500 font-mono text-xs">{t.slug}</td>
                    <td className="table-cell">
                      <span
                        className={`badge ${
                          t.is_active
                            ? 'bg-green-100 text-green-700'
                            : 'bg-gray-100 text-gray-500'
                        }`}
                      >
                        {t.is_active ? 'Активен' : 'Отключён'}
                      </span>
                    </td>
                    <td className="table-cell">
                      <div className="flex items-center gap-2 flex-wrap">
                        <button className="btn-ghost py-1 px-2 text-xs" onClick={() => openEdit(t)}>
                          Изменить
                        </button>
                        <button className="btn-ghost py-1 px-2 text-xs" onClick={() => toggleActive(t)}>
                          {t.is_active ? 'Отключить' : 'Включить'}
                        </button>
                        <button
                          className="btn-ghost py-1 px-2 text-xs text-gray-600"
                          onClick={() => openStaffModal(t)}
                        >
                          Сотрудники
                        </button>
                        <button
                          className="btn-ghost py-1 px-2 text-xs text-brand-600"
                          onClick={() => openAdminModal(t)}
                        >
                          + Администратор
                        </button>
                        <button
                          className="btn-ghost py-1 px-2 text-xs text-red-500"
                          onClick={() => deleteTenant(t)}
                        >
                          Удалить
                        </button>
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

      {/* Create/Edit Tenant Modal */}
      {showModal && (
        <Modal
          title={editTenant ? `Изменить: ${editTenant.name}` : 'Новый кинорум'}
          onClose={() => setShowModal(false)}
        >
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="label">Название</label>
              <input
                className="input"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Кинорум «Иллюзион»"
                required
              />
            </div>
            <div>
              <label className="label">Slug (латиница)</label>
              <input
                className="input font-mono"
                value={form.slug}
                onChange={(e) => setForm({ ...form, slug: e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, '') })}
                placeholder="illyuzion"
                required
              />
              <p className="text-xs text-gray-400 mt-1">Только строчные латинские буквы, цифры, `-` и `_`</p>
            </div>
            <div>
              <label className="label">Адрес <span className="text-gray-400 font-normal">— необязательно</span></label>
              <input
                className="input"
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
                placeholder="ул. Абая 10, Алматы"
              />
            </div>
            <div>
              <label className="label">Телефон <span className="text-gray-400 font-normal">— необязательно</span></label>
              <input
                className="input"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                placeholder="+7 (777) 000-00-00"
              />
            </div>
            <div>
              <label className="label">URL логотипа/фото <span className="text-gray-400 font-normal">— необязательно</span></label>
              <input
                className="input"
                value={form.logo_url}
                onChange={(e) => setForm({ ...form, logo_url: e.target.value })}
                placeholder="https://..."
              />
            </div>
            {formError && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{formError}</p>}
            <div className="flex gap-3 pt-2">
              <button type="submit" className="btn-primary flex-1 justify-center" disabled={saving}>
                {saving ? 'Сохранение...' : 'Сохранить'}
              </button>
              <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>
                Отмена
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Staff List Modal */}
      {staffModalTenant && (
        <Modal
          title={`Сотрудники «${staffModalTenant.name}»`}
          onClose={() => setStaffModalTenant(null)}
        >
          {staffLoading ? (
            <p className="text-sm text-gray-500 py-4 text-center">Загрузка...</p>
          ) : staffList.length === 0 ? (
            <p className="text-sm text-gray-400 py-4 text-center">Нет сотрудников. Создайте администратора.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2 px-3 text-xs font-medium text-gray-500">Логин</th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-gray-500">Роль</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {staffList.map((s) => (
                  <tr key={s.id}>
                    <td className="py-2 px-3 font-medium text-gray-800">{s.username}</td>
                    <td className="py-2 px-3 text-gray-500">{ROLE_LABELS[s.role] ?? s.role}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <div className="pt-4">
            <button className="btn-secondary w-full justify-center" onClick={() => setStaffModalTenant(null)}>
              Закрыть
            </button>
          </div>
        </Modal>
      )}

      {/* Create Admin Modal */}
      {adminModalTenant && (
        <Modal
          title={`Администратор для «${adminModalTenant.name}»`}
          onClose={() => setAdminModalTenant(null)}
        >
          <form onSubmit={handleCreateAdmin} className="space-y-4">
            <p className="text-sm text-gray-600">
              Создайте администратора для этого кинорума. Он сможет войти в панель и управлять залами, товарами и сотрудниками.
            </p>
            <div>
              <label className="label">Логин</label>
              <input
                className="input"
                value={adminForm.username}
                onChange={(e) => setAdminForm({ ...adminForm, username: e.target.value })}
                placeholder="admin"
                required
              />
            </div>
            <div>
              <label className="label">Пароль</label>
              <input
                className="input"
                type="password"
                value={adminForm.password}
                onChange={(e) => setAdminForm({ ...adminForm, password: e.target.value })}
                placeholder="минимум 6 символов"
                minLength={6}
                maxLength={72}
                required
              />
            </div>
            {adminError && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{adminError}</p>}
            {adminResult && <p className="text-sm text-green-700 bg-green-50 px-3 py-2 rounded-lg">{adminResult}</p>}
            <div className="flex gap-3 pt-2">
              <button type="submit" className="btn-primary flex-1 justify-center" disabled={adminSaving || !!adminResult}>
                {adminSaving ? 'Создание...' : 'Создать администратора'}
              </button>
              <button type="button" className="btn-secondary" onClick={() => setAdminModalTenant(null)}>
                {adminResult ? 'Закрыть' : 'Отмена'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
