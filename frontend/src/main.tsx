import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import toast, { Toaster, ToastBar } from 'react-hot-toast'
import { X } from 'lucide-react'
import { LanguageProvider } from './contexts/LanguageContext'
import App from './App'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30000,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <LanguageProvider>
          <App />
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 5000,
              style: {
                fontSize: '16px',
                padding: '12px 16px',
                borderRadius: '12px',
                maxWidth: '400px',
              },
              success: {
                style: {
                  background: '#059669',
                  color: 'white',
                },
              },
              error: {
                style: {
                  background: '#DC2626',
                  color: 'white',
                },
                duration: 6000,
              },
            }}
          >
            {(t) => (
              <ToastBar toast={t}>
                {({ icon, message }) => (
                  <div className="flex items-center gap-2">
                    {icon}
                    <div className="flex-1">{message}</div>
                    {t.type !== 'loading' && (
                      <button
                        onClick={() => toast.dismiss(t.id)}
                        className="p-1 rounded-full hover:bg-white/20 transition-colors flex-shrink-0"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                )}
              </ToastBar>
            )}
          </Toaster>
        </LanguageProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)
