import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'  // 修正导入路径，添加.tsx扩展名
import './index.css'

ReactDOM.createRoot(document.getElementById('app') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)