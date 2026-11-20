import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

import { NoticeProvider } from './pages/UploadPage/context/NoticeProvider'
import { UploadPage } from './pages/UploadPage'

function makeClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false }, mutations: { retry: 0 } },
  })
}

/** Providers around the single page. */
export function App() {
  const [client] = useState(makeClient)
  return (
    <QueryClientProvider client={client}>
      <NoticeProvider>
        <UploadPage />
      </NoticeProvider>
    </QueryClientProvider>
  )
}
