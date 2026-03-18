import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './context/AuthContext'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <AuthProvider>
      <App />
      <Toaster position="bottom-right" toastOptions={{
        style: { background: '#fff', color: '#1c1c28', border: '1px solid #e2e4ea', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }
      }} />
    </AuthProvider>
  </BrowserRouter>
)
