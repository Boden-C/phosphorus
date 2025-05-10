import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

// MAIN
import { runTests } from './main.test.ts'

try {
  // runTests()
}
catch (error) {
  // Print traceback
  console.error(error)
  console.trace()
}