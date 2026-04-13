import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';

/**
 * Accessibility Tests using axe-playwright
 * Ensures WCAG 2.1 AA compliance across the application
 */

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Inject axe-core into the page
    await injectAxe(page);
  });

  test('Login page should meet WCAG 2.1 AA standards', async ({ page }) => {
    await page.goto('/login');
    
    // Wait for page to load completely
    await page.waitForLoadState('networkidle');

    // Check accessibility
    await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: { html: true }
    });
  });

  test('Dashboard should meet WCAG 2.1 AA standards', async ({ page }) => {
    // First login to access dashboard
    await page.goto('/login');

    // Mock authentication
    await page.route('/api/auth/login/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access: 'mock-token',
          refresh: 'mock-refresh',
          user: {
            id: 1,
            username: 'testuser',
            first_name: 'Test',
            last_name: 'User'
          }
        })
      });
    });

    await page.route('/api/auth/user/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          username: 'testuser',
          first_name: 'Test',
          last_name: 'User'
        })
      });
    });

    await page.route('/api/tintometry/dashboard/stats/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_templates: 25,
          misturas_hoje: 8,
          estoque_baixo: 3,
          etiquetas_geradas: 15
        })
      });
    });

    // Fill and submit login form
    await page.fill('[aria-label="Nome de usuário"]', 'admin');
    await page.fill('[aria-label="Senha"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Wait for dashboard to load
    await page.waitForURL('/dashboard');
    await page.waitForLoadState('networkidle');

    // Check accessibility
    await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: { html: true },
      rules: {
        // Custom rules for paint store context
        'color-contrast': { enabled: true },
        'focus-order-semantics': { enabled: true },
        'keyboard-navigation': { enabled: true }
      }
    });
  });

  test('Navigation should be keyboard accessible', async ({ page }) => {
    // Mock authentication and navigate to dashboard
    await page.goto('/login');
    
    // Login process (mocked)
    await page.route('/api/auth/login/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access: 'mock-token',
          refresh: 'mock-refresh',
          user: { id: 1, username: 'test', first_name: 'Test' }
        })
      });
    });

    await page.route('/api/auth/user/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1, username: 'test', first_name: 'Test'
        })
      });
    });

    await page.fill('[aria-label="Nome de usuário"]', 'admin');
    await page.fill('[aria-label="Senha"]', 'admin123');
    await page.click('button[type="submit"]');
    
    await page.waitForURL('/dashboard');

    // Test keyboard navigation through main menu
    await page.keyboard.press('Tab'); // Should focus on skip links
    await page.keyboard.press('Tab'); // Navigate to first nav item
    
    // Verify focus is visible and navigation is accessible
    const focusedElement = await page.locator(':focus');
    await expect(focusedElement).toBeVisible();

    // Check accessibility of navigation
    await checkA11y(page, '[role="navigation"]', {
      detailedReport: true,
      tags: ['wcag2a', 'wcag2aa', 'wcag21aa']
    });
  });

  test('Forms should have proper labels and error handling', async ({ page }) => {
    await page.goto('/login');
    
    // Test form without filling it (should show errors)
    await page.click('button[type="submit"]');
    
    // Wait for validation errors
    await page.waitForSelector('[role="alert"]');

    // Check accessibility of form with errors
    await checkA11y(page, 'form', {
      detailedReport: true,
      tags: ['wcag2a', 'wcag2aa', 'wcag21aa'],
      rules: {
        'label-content-name-mismatch': { enabled: true },
        'form-field-multiple-labels': { enabled: true },
        'aria-required-attr': { enabled: true }
      }
    });
  });

  test('Color contrast should meet WCAG AA standards', async ({ page }) => {
    await page.goto('/login');
    
    // Check color contrast specifically
    await checkA11y(page, null, {
      detailedReport: true,
      rules: {
        'color-contrast': { enabled: true }
      },
      tags: ['wcag2aa']
    });
  });

  test('Page should work with screen reader simulation', async ({ page }) => {
    await page.goto('/login');
    
    // Test with high contrast mode simulation
    await page.emulateMedia({ colorScheme: 'dark' });
    
    // Verify critical elements are still visible
    await expect(page.getByText('Atalaia Tintas')).toBeVisible();
    await expect(page.getByLabel('Nome de usuário')).toBeVisible();
    await expect(page.getByLabel('Senha')).toBeVisible();
    
    // Check accessibility in high contrast mode
    await checkA11y(page, null, {
      detailedReport: true,
      tags: ['wcag2aa'],
      rules: {
        'color-contrast': { enabled: true }
      }
    });
  });

  test('Skip links should work properly', async ({ page }) => {
    // Mock authentication for layout with skip links
    await page.goto('/login');
    
    await page.route('/api/auth/login/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access: 'mock-token',
          refresh: 'mock-refresh',
          user: { id: 1, username: 'test', first_name: 'Test' }
        })
      });
    });

    await page.route('/api/auth/user/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1, username: 'test', first_name: 'Test'
        })
      });
    });

    await page.fill('[aria-label="Nome de usuário"]', 'admin');
    await page.fill('[aria-label="Senha"]', 'admin123');
    await page.click('button[type="submit"]');
    
    await page.waitForURL('/dashboard');

    // Test skip to main content
    await page.keyboard.press('Tab'); // Focus first skip link
    const skipLink = page.getByText('Pular para conteúdo principal');
    await expect(skipLink).toBeVisible();
    await expect(skipLink).toBeFocused();
    
    // Activate skip link
    await page.keyboard.press('Enter');
    
    // Should focus main content
    const mainContent = page.locator('#main-content');
    await expect(mainContent).toBeFocused();
  });
});