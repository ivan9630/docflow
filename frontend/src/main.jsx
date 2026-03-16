import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <App />
    <Toaster position="bottom-right" toastOptions={{
      style: { background: '#1a1a24', color: '#e8e8f0', border: '1px solid #2a2a38' }
    }} />
  </BrowserRouter>
)
