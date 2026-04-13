import React from 'react';
import { QueryProvider } from '@/providers/QueryProvider';
import { RouterProvider } from '@/providers/RouterProvider';

/**
 * Main App component
 * Provides all necessary providers and initializes the application
 */
function App(): React.ReactElement {
  return (
    <QueryProvider>
      <RouterProvider />
    </QueryProvider>
  );
}

export default App;