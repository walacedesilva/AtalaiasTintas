# QuickStart Guide: Modern Web Interface Development

**Feature**: Modern Web Interface for Paint Store Tintometric System  
**Target Audience**: Frontend and fullstack developers  
**Prerequisites**: Node.js 18+, Python 3.12+, Git  
**Estimated Setup Time**: 15-30 minutes

## Environment Setup

### 1. Repository Setup
```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd AtalaiasTintas

# Checkout the feature branch
git checkout 3-modern-web-interface

# Ensure you have the latest changes
git pull origin 3-modern-web-interface
```

### 2. Backend Setup (Django API)
```bash
# Create and activate Python virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
cd backend
python manage.py migrate

# Create superuser for testing (optional)
python manage.py createsuperuser

# Start Django development server
python manage.py runserver 8000
```

**Backend verification**: Visit http://localhost:8000/admin to confirm Django admin is accessible.

### 3. Frontend Setup (React + TypeScript)
```bash
# Navigate to frontend directory (in a new terminal)
cd frontend

# Install Node.js dependencies
npm install

# Start development server with hot reload
npm run dev
```

**Frontend verification**: Visit http://localhost:3000 to confirm React app is running.

## Development Workflow

### Project Structure Overview
```
AtalaiasTintas/
├── backend/                 # Django API server
│   ├── apps/tintometry/     # Enhanced tintometric business logic
│   ├── apps/core/           # User management and authentication  
│   └── manage.py            # Django management commands
├── frontend/                # React TypeScript application
│   ├── src/
│   │   ├── components/      # Reusable UI components  
│   │   ├── pages/           # Route-based page components
│   │   ├── services/        # API communication layer
│   │   ├── types/           # TypeScript type definitions
│   │   └── utils/           # Helper functions
│   ├── tests/               # Frontend tests (Vitest + RTL)
│   └── package.json         # Frontend dependencies
└── specs/3-modern-web-interface/  # Feature documentation
```

### Available Scripts

#### Backend Commands
```bash
# Run Django server
python manage.py runserver

# Run backend tests  
python manage.py test

# Create new Django migrations
python manage.py makemigrations

# Apply database migrations
python manage.py migrate

# Access Django shell for debugging
python manage.py shell

# Generate API documentation
python manage.py generate_schema --file schema.yml
```

#### Frontend Commands
```bash
# Start development server
npm run dev

# Build for production
npm run build

# Run tests in watch mode
npm run test

# Run tests once with coverage
npm run test:coverage

# Run ESLint for code quality
npm run lint

# Fix ESLint issues automatically  
npm run lint:fix

# Type checking
npm run type-check

# Preview production build
npm run preview

# Run Storybook for component development
npm run storybook
```

## API Integration

### Authentication Setup
The frontend uses JWT authentication with the Django backend:

```typescript
// Example API configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Token storage (handled by auth service)
localStorage.setItem('auth_token', 'your-jwt-token');
```

### Key API Endpoints
- **Authentication**: `POST /api/v1/auth/login/`
- **Pigments**: `GET /api/v1/pigments/`  
- **Formulas**: `GET /api/v1/formulas/`
- **Mixtures**: `POST /api/v1/mixtures/`
- **Labels**: `GET /api/v1/mixtures/{id}/labels/`

### API Documentation  
- **OpenAPI Spec**: `/specs/3-modern-web-interface/contracts/tintometric-api.yaml`
- **Interactive Docs**: http://localhost:8000/api/docs/ (when backend running)

## Component Development

### Atomic Design Structure
Follow the established component hierarchy:

```typescript
// Example: Creating a new component
// File: src/components/molecules/ColorPicker/ColorPicker.tsx

import React from 'react';
import { Button } from '../atoms/Button';
import { ColorSwatch } from '../atoms/ColorSwatch';

interface ColorPickerProps {
  selectedColor: string;
  onColorSelect: (color: string) => void;
  availableColors: Color[];
}

export const ColorPicker: React.FC<ColorPickerProps> = ({
  selectedColor,
  onColorSelect, 
  availableColors
}) => {
  // Component implementation
  return (
    <div className="color-picker">
      {availableColors.map(color => (
        <ColorSwatch
          key={color.id}
          color={color}
          selected={color.id === selectedColor}
          onClick={() => onColorSelect(color.id)}
        />
      ))}
    </div>
  );
};
```

### Testing Components
```typescript
// Example test: ColorPicker.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ColorPicker } from './ColorPicker';

describe('ColorPicker', () => {
  const mockColors = [
    { id: '1', name: 'Red', rgb: { r: 255, g: 0, b: 0 } },
    { id: '2', name: 'Blue', rgb: { r: 0, g: 0, b: 255 } }
  ];

  it('calls onColorSelect when color is clicked', () => {
    const onColorSelect = vi.fn();
    
    render(
      <ColorPicker
        selectedColor="1"
        onColorSelect={onColorSelect}
        availableColors={mockColors}
      />
    );
    
    fireEvent.click(screen.getByText('Blue'));
    expect(onColorSelect).toHaveBeenCalledWith('2');
  });
});
```

## State Management

### React Query for Server State
```typescript
// Example: Custom hook for pigments data
// File: src/services/hooks/usePigments.ts

import { useQuery } from '@tanstack/react-query';
import { pigmentsApi } from '../api/pigments';

export const usePigments = (filters?: PigmentFilters) => {
  return useQuery({
    queryKey: ['pigments', filters],
    queryFn: () => pigmentsApi.list(filters),
    staleTime: 1000 * 60 * 5, // 5 minutes
    cacheTime: 1000 * 60 * 30, // 30 minutes
  });
};

// Usage in component
const PigmentsPage = () => {
  const { data: pigments, isLoading, error } = usePigments();
  
  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  
  return <PigmentsList pigments={pigments} />;
};
```

### Zustand for Client State
```typescript
// Example: UI state store
// File: src/services/stores/uiStore.ts

import { create } from 'zustand';

interface UiState {
  sidebarOpen: boolean;
  currentTheme: 'light' | 'dark';
  notifications: Notification[];
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  addNotification: (notification: Notification) => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: true,
  currentTheme: 'light',
  notifications: [],
  
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setTheme: (theme) => set({ currentTheme: theme }),
  addNotification: (notification) => 
    set((state) => ({ 
      notifications: [...state.notifications, notification] 
    })),
}));
```

## Styling Guidelines

### Tailwind CSS Configuration
The project uses Tailwind CSS with custom paint industry color palette:

```typescript
// tailwind.config.js excerpt
module.exports = {
  theme: {
    extend: {
      colors: {
        // Paint industry specific colors
        pigment: {
          titanium: '#FFFFFF',
          ultramarine: '#120A8F',
          cadmium: '#ED872D',
          chrome: '#FDE047'
        },
        paint: {
          base: '#F8F9FA',
          primary: '#3B82F6', 
          secondary: '#6B7280',
          danger: '#EF4444'
        }
      }
    }
  }
};
```

### Component Styling Best Practices
```typescript
// Example: Using Tailwind with component variants
const Button = ({ variant = 'primary', size = 'md', children, ...props }) => {
  const baseClasses = 'font-medium rounded-md focus:outline-none focus:ring-2';
  
  const variants = {
    primary: 'bg-paint-primary text-white hover:bg-paint-primary/90',
    secondary: 'bg-paint-secondary text-white hover:bg-paint-secondary/90',
    danger: 'bg-paint-danger text-white hover:bg-paint-danger/90'
  };
  
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  };
  
  const classes = `${baseClasses} ${variants[variant]} ${sizes[size]}`;
  
  return (
    <button className={classes} {...props}>
      {children}
    </button>
  );
};
```

## Error Handling

### API Error Boundaries
```typescript
// Global error boundary for unhandled errors
// File: src/components/ErrorBoundary.tsx

class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to monitoring service
    console.error('Error caught by boundary:', error, errorInfo);
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="error-fallback">
          <h2>Something went wrong</h2>
          <details>
            {this.state.error && this.state.error.toString()}
          </details>
          <button onClick={() => window.location.reload()}>
            Reload Page
          </button>
        </div>
      );
    }
    
    return this.props.children;
  }
}
```

### API Error Handling
```typescript
// Centralized API error handling
// File: src/services/api/client.ts

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Request interceptor for auth
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    
    // Format error for UI consumption
    const formattedError = {
      message: error.response?.data?.message || 'An unexpected error occurred',
      details: error.response?.data?.details || {},
      status: error.response?.status
    };
    
    return Promise.reject(formattedError);
  }
);
```

## Testing Strategy

### Running Tests
```bash
# Frontend tests
cd frontend
npm run test              # Watch mode
npm run test:coverage     # With coverage report
npm run test:ci           # CI mode (run once)

# Backend tests  
cd backend
python manage.py test     # Django tests
pytest                    # Alternative test runner
```

### Test Structure
```
frontend/tests/
├── components/           # Component unit tests
├── pages/               # Page integration tests  
├── services/            # API service tests
├── utils/               # Utility function tests
├── __mocks__/           # Mock implementations
└── fixtures/            # Test data and fixtures
```

## Accessibility Testing

### Manual Testing Checklist
- [ ] Keyboard navigation works for all interactive elements
- [ ] Screen reader announces content correctly
- [ ] Color information is conveyed through text/patterns
- [ ] Focus indicators are visible (2px minimum)
- [ ] Form errors are announced to screen readers
- [ ] Skip links work for main navigation

### Automated Testing
```bash
# Run accessibility tests
npm run test:a11y

# Check individual components with axe
npx @axe-core/cli http://localhost:3000
```

## Performance Guidelines

### Bundle Optimization
```bash
# Analyze bundle size
npm run build
npm run analyze

# Target metrics:
# - Initial bundle: <500KB
# - Time to Interactive: <3s  
# - First Contentful Paint: <1.5s
```

### Code Splitting Example
```typescript
// Route-based code splitting
const PigmentsPage = lazy(() => import('../pages/PigmentsPage'));
const MixingPage = lazy(() => import('../pages/MixingPage'));

// Component-based code splitting  
const ColorCalculator = lazy(() => import('../components/ColorCalculator'));
```

## Debugging

### Browser DevTools Setup
1. Install React DevTools extension
2. Install Redux DevTools (for Zustand integration)
3. Enable source maps in development build

### Common Debug Commands
```bash
# Backend debugging
python manage.py shell_plus  # Enhanced Django shell
python manage.py debug_toolbar  # Debug toolbar

# Frontend debugging  
console.log('API Response:', data);  # Basic logging
debugger; // Breakpoint for DevTools
```

## Deployment

### Production Build
```bash
# Build frontend for production
cd frontend
npm run build

# Collect Django static files
cd ../backend
python manage.py collectstatic --noinput

# Test production build locally
cd ../frontend  
npm run preview
```

### Environment Variables
```bash
# Frontend (.env)
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_ENVIRONMENT=development

# Backend (environment or .env)
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost/db_name
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

## Troubleshooting

### Common Issues

**Issue**: CORS errors when calling API  
**Solution**: Ensure `CORS_ALLOWED_ORIGINS` includes frontend URL in Django settings

**Issue**: JWT token expired  
**Solution**: Implement token refresh logic in API client interceptors  

**Issue**: Component not updating with new data  
**Solution**: Check React Query cache keys and invalidation logic

**Issue**: TypeScript compilation errors  
**Solution**: Run `npm run type-check` to identify type issues

**Issue**: Tests failing with API mocks  
**Solution**: Verify Mock Service Worker (MSW) handlers match API contracts

### Getting Help

- **Documentation**: Check `/specs/3-modern-web-interface/` for detailed specs
- **API Reference**: `/contracts/tintometric-api.yaml` for endpoint documentation  
- **Component Library**: Run `npm run storybook` for component examples
- **Code Issues**: Use ESLint and TypeScript compiler for code quality checks

## Next Steps

1. **Read the specification**: Review `/specs/3-modern-web-interface/spec.md`
2. **Explore the data model**: Study `/specs/3-modern-web-interface/data-model.md`  
3. **Check API contracts**: Examine `/specs/3-modern-web-interface/contracts/`
4. **Start development**: Begin with atomic components and build up
5. **Follow TDD**: Write tests before implementing features
6. **Test accessibility**: Ensure WCAG 2.1 AA compliance throughout development

**Happy coding!** 🎨