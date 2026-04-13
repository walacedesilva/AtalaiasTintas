import React from 'react';
import { Outlet } from 'react-router-dom';
import Navigation from './Navigation';
import Header from './Header';
import { Toaster } from 'react-hot-toast';

export default function RootLayout(): React.ReactElement {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Skip links for accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:rounded-lg focus:bg-teal-600 focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white focus:shadow-lg"
      >
        Pular para conteúdo principal
      </a>

      {/* Header */}
      <Header />

      <div className="flex pt-16">
        {/* Sidebar Navigation */}
        <Navigation />

        {/* Main Content */}
        <main
          id="main-content"
          className="flex-1 ml-64 min-h-[calc(100vh-4rem)] p-6"
          role="main"
          aria-label="Conteúdo principal"
        >
          <div className="animate-fade-in">
            <Outlet />
          </div>
        </main>
      </div>

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          className: '!rounded-xl !shadow-lg !text-sm !font-medium',
          success: {
            duration: 3000,
            iconTheme: { primary: '#0d9488', secondary: '#fff' },
          },
          error: { duration: 5000 },
        }}
        containerStyle={{ top: 72 }}
      />
    </div>
  );
}