import React from 'react';
import { createBrowserRouter, RouterProvider as ReactRouterProvider, Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

// Pages - We'll create these components
import RootLayout from '@/components/layout/RootLayout';
import LoginPage from '@/pages/auth/LoginPage';
import Dashboard from '@/pages/Dashboard';
import PigmentosPage from '@/pages/pigments/PigmentosPage';
import CoresPage from '@/pages/colors/CoresPage';
import FormulasPage from '@/pages/formulas/FormulasPage';
import MisturasPage from '@/pages/mixtures/MisturasPage';
import EstoquePage from '@/pages/inventory/EstoquePage';
import EtiquetasPage from '@/pages/labels/EtiquetasPage';
import ProfilePage from '@/pages/profile/ProfilePage';
import NotFoundPage from '@/pages/NotFoundPage';
import VendasPage from '@/pages/sales/VendasPage';
import PedidosPage from '@/pages/sales/PedidosPage';
import RecebiveisPage from '@/pages/sales/RecebiveisPage';
import ClientesPage from '@/pages/customers/ClientesPage';
import TintometryPage from '@/pages/TintometryPage';
import PigmentStockPage from '@/pages/PigmentStockPage';
import PDVPage from '@/pages/pdv/PDVPage';
import NotaFiscalPage from '@/pages/fiscal/NotaFiscalPage';
import ReportsPage from '@/pages/reports/ReportsPage';
import MonitoringPage from '@/pages/monitoring/MonitoringPage';
import SettingsPage from '@/pages/settings/SettingsPage';
import HelpPage from '@/pages/help/HelpPage';

/**
 * Protected route component
 * Redirects to login if user is not authenticated
 */
interface ProtectedRouteProps {
  children: React.ReactNode;
}

function ProtectedRoute({ children }: ProtectedRouteProps): React.ReactElement {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

/**
 * Public route component
 * Redirects to dashboard if user is already authenticated
 */
interface PublicRouteProps {
  children: React.ReactNode;
}

function PublicRoute({ children }: PublicRouteProps): React.ReactElement {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}

// Router configuration
const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/dashboard" replace />
  },
  {
    path: '/login',
    element: (
      <PublicRoute>
        <LoginPage />
      </PublicRoute>
    )
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <RootLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        path: 'dashboard',
        element: <Dashboard />
      },
      {
        path: 'pigments',
        element: <PigmentosPage />
      },
      {
        path: 'colors',
        element: <CoresPage />
      },
      {
        path: 'formulas',
        element: <FormulasPage />
      },
      {
        path: 'mixtures',
        element: <MisturasPage />
      },
      {
        path: 'inventory',
        element: <EstoquePage />
      },
      {
        path: 'labels',
        element: <EtiquetasPage />
      },
      {
        path: 'profile',
        element: <ProfilePage />
      },
      {
        path: 'sales',
        element: <VendasPage />
      },
      {
        path: 'sales/orders',
        element: <PedidosPage />
      },
      {
        path: 'customers',
        element: <ClientesPage />
      },
      {
        path: 'pdv',
        element: <PDVPage />
      },
      {
        path: 'recebiveis',
        element: <RecebiveisPage />
      },
      {
        path: 'tintometry',
        element: <TintometryPage />
      },
      {
        path: 'tintometry/stock',
        element: <PigmentStockPage />
      },
      {
        path: 'fiscal',
        element: <NotaFiscalPage />
      },
      {
        path: 'reports',
        element: <ReportsPage />
      },
      {
        path: 'monitoring',
        element: <MonitoringPage />
      },
      {
        path: 'orders',
        element: <Navigate to="/sales/orders" replace />
      },
      {
        path: 'settings',
        element: <SettingsPage />
      },
      {
        path: 'help',
        element: <HelpPage />
      }
    ]
  },
  {
    path: '*',
    element: <NotFoundPage />
  }
], {
  future: {
    v7_relativeSplatPath: true,
  } as Record<string, boolean>
});

interface RouterProviderProps {
  children?: never; // This provider doesn't accept children
}

/**
 * Router provider component
 * Sets up React Router with authentication-aware routing
 */
export function RouterProvider(_props: RouterProviderProps): React.ReactElement {
  return <ReactRouterProvider router={router} />;
}