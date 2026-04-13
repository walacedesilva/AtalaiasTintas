import React from 'react';
import { Outlet } from 'react-router-dom';
import Navigation from './Navigation';
import Header from './Header';
import { Toaster } from 'react-hot-toast';

/**
 * Root layout component
 * Provides the main application shell with navigation, header, and content area
 */
export default function RootLayout(): React.ReactElement {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Skip links for accessibility */}
      <a 
        href="#main-content" 
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-600 text-white px-4 py-2 rounded-md z-50"
      >
        Pular para conteúdo principal
      </a>
      <a 
        href="#navigation" 
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-32 bg-blue-600 text-white px-4 py-2 rounded-md z-50"
      >
        Pular para navegação
      </a>

      {/* Header */}
      <Header />

      <div className="flex">
        {/* Sidebar Navigation */}
        <Navigation />

        {/* Main Content */}
        <main 
          id="main-content"
          className="flex-1 p-6 ml-64"
          role="main"
          aria-label="Conteúdo principal"
        >
          <Outlet />
        </main>
      </div>

      {/* Toast notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            style: {
              background: '#22c55e',
            },
          },
          error: {
            duration: 5000,
            style: {
              background: '#ef4444',
            },
          },
        }}
        containerStyle={{
          top: 80, // Below the header
        }}
      />
    </div>
  );
}