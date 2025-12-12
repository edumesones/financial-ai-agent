import { useState, useEffect } from 'react'
import Login from './components/Login'
import Dashboard from './components/Dashboard'

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'))
  
  const handleLogin = (newToken) => {
    localStorage.setItem('token', newToken)
    setToken(newToken)
  }
  
  const handleLogout = () => {
    localStorage.removeItem('token')
    setToken(null)
  }
  
  if (!token) {
    return <Login onLogin={handleLogin} />
  }
  
  return <Dashboard token={token} onLogout={handleLogout} />
}

export default App
