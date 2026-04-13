import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Enable React strict mode in development
const StrictModeWrapper = ({ children }: { children: React.ReactNode }): React.ReactElement => {
  return import.meta.env.DEV ? (
    <React.StrictMode>{children}</React.StrictMode>
  ) : (
    <>{children}</>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <StrictModeWrapper>
    <App />
  </StrictModeWrapper>,
)