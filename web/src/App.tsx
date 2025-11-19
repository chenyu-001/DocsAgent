import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { authApi } from './api/client'
import LoginPage from './pages/LoginPage'
import SearchPage from './pages/SearchPage'
import DocumentPage from './pages/DocumentPage'

// ×Ý¤„ï1Äö
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  if (!authApi.isAuthenticated()) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

// {Uï1ò{Uól	
function LoginRoute({ children }: { children: React.ReactNode }) {
  if (authApi.isAuthenticated()) {
    return <Navigate to="/search" replace />
  }
  return <>{children}</>
}

function App() {
  return (
    <Router>
      <Routes>
        {/* {Uu */}
        <Route
          path="/login"
          element={
            <LoginRoute>
              <LoginPage />
            </LoginRoute>
          }
        />

        {/* "u */}
        <Route
          path="/search"
          element={
            <ProtectedRoute>
              <SearchPage />
            </ProtectedRoute>
          }
        />

        {/* ‡c
 u */}
        <Route
          path="/documents"
          element={
            <ProtectedRoute>
              <DocumentPage />
            </ProtectedRoute>
          }
        />

        {/* Ø¤ól0"u */}
        <Route path="/" element={<Navigate to="/search" replace />} />

        {/* 404 */}
        <Route path="*" element={<Navigate to="/search" replace />} />
      </Routes>
    </Router>
  )
}

export default App
