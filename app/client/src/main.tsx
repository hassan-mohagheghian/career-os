import React from 'react'
import ReactDOM from 'react-dom/client'
import AppWithTheme from './App.jsx'
import { TooltipProvider } from '@/shared/ui/tooltip'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <TooltipProvider>
      <AppWithTheme />
    </TooltipProvider>
  </React.StrictMode>,
)
