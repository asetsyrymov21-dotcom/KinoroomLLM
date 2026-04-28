import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Tenants from './pages/superadmin/Tenants'
import Halls from './pages/Halls'
import Categories from './pages/Categories'
import Products from './pages/Products'
import StaffPage from './pages/StaffPage'
import Bookings from './pages/Bookings'
import Orders from './pages/Orders'
import Stock from './pages/Stock'

function DefaultRedirect() {
  const { auth } = useAuth()
  if (!auth) return <Navigate to="/login" replace />
  if (auth.role === 'superadmin') return <Navigate to="/tenants" replace />
  return <Navigate to="/bookings" replace />
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { auth } = useAuth()
  if (!auth) return <Navigate to="/login" replace />
  return <>{children}</>
}

function RequireRole({ children, roles }: { children: React.ReactNode; roles: string[] }) {
  const { auth } = useAuth()
  if (!auth || !roles.includes(auth.role)) return <Navigate to="/" replace />
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        {/* Superadmin */}
        <Route path="/tenants" element={
          <RequireRole roles={['superadmin']}><Tenants /></RequireRole>
        } />

        {/* Admin only */}
        <Route path="/halls" element={
          <RequireRole roles={['admin']}><Halls /></RequireRole>
        } />
        <Route path="/categories" element={
          <RequireRole roles={['admin']}><Categories /></RequireRole>
        } />
        <Route path="/products" element={
          <RequireRole roles={['admin']}><Products /></RequireRole>
        } />
        <Route path="/staff" element={
          <RequireRole roles={['admin']}><StaffPage /></RequireRole>
        } />

        {/* Admin + Operator */}
        <Route path="/bookings" element={
          <RequireRole roles={['admin', 'operator']}><Bookings /></RequireRole>
        } />
        <Route path="/orders" element={
          <RequireRole roles={['admin', 'operator']}><Orders /></RequireRole>
        } />
        <Route path="/stock" element={
          <RequireRole roles={['admin', 'operator']}><Stock /></RequireRole>
        } />
      </Route>

      <Route path="*" element={<DefaultRedirect />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
