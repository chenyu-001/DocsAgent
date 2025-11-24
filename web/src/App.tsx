import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { authApi } from './api/client'
import LoginPage from './pages/LoginPage'
import SearchPage from './pages/SearchPage'
import DocumentPage from './pages/DocumentPage'
import DocumentsListPage from './pages/DocumentsListPage'
import DocumentDetailPage from './pages/DocumentDetailPage'

// Protected route - requires authentication
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  if (!authApi.isAuthenticated()) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

// Login route - redirect to home if already authenticated
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
        {/* Login page */}
        <Route
          path="/login"
          element={
            <LoginRoute>
              <LoginPage />
            </LoginRoute>
          }
        />

        {/* Search page */}
        <Route
          path="/search"
          element={
            <ProtectedRoute>
              <SearchPage />
            </ProtectedRoute>
          }
        />

        {/* Document upload page */}
        <Route
          path="/upload"
          element={
            <ProtectedRoute>
              <DocumentPage />
            </ProtectedRoute>
          }
        />

        {/* Documents list/management page */}
        <Route
          path="/documents"
          element={
            <ProtectedRoute>
              <DocumentsListPage />
            </ProtectedRoute>
          }
        />

        {/* Document detail page */}
        <Route
          path="/document/:id"
          element={
            <ProtectedRoute>
              <DocumentDetailPage />
            </ProtectedRoute>
          }
        />

        {/* Default route - redirect to search */}
        <Route path="/" element={<Navigate to="/search" replace />} />

        {/* 404 - redirect to search */}
        <Route path="*" element={<Navigate to="/search" replace />} />
      </Routes>
    </Router>
  )
}

export default App
