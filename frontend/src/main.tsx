import { createRoot } from 'react-dom/client'
// import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from './queryClient'
import './index.css'
import App from './App.tsx'

// Temporarily disable StrictMode to stop API call doubling during development
// Enable again after debugging: <StrictMode><App /></StrictMode>
createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
    <App />
  </QueryClientProvider>
)
