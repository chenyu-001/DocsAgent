import { useNavigate } from 'react-router-dom'
import LoginForm from '../components/LoginForm'

export default function LoginPage() {
  const navigate = useNavigate()

  const handleSuccess = () => {
    navigate('/search')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4">
      <LoginForm onSuccess={handleSuccess} />
    </div>
  )
}
