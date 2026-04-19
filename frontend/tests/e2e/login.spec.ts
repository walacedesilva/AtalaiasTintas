import { test, expect } from '@playwright/test';

/**
 * End-to-End Login Flow Tests
 * Tests the complete authentication user journey
 */

test.describe('Login Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page before each test
    await page.goto('/login');
  });

  test('should display login page correctly', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/Atalaia Tintas/);

    // Check main elements are visible
    await expect(page.getByText('Atalaia Tintas').first()).toBeVisible();
    await expect(page.getByText('Gestão inteligente para a sua tintaria')).toBeVisible();
    await expect(page.getByText('Bem-vindo de volta!')).toBeVisible();

    // Check form fields
    await expect(page.getByLabel('Nome de usuário')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();
    await expect(page.getByRole('button', { name: /entrar/i })).toBeVisible();
  });

  test('should focus on username field when page loads', async ({ page }) => {
    // Username field should be focused
    await expect(page.getByLabel('Nome de usuário')).toBeFocused();
  });

  test('should show validation errors for empty form submission', async ({ page }) => {
    // Click submit without filling form
    await page.getByRole('button', { name: /entrar/i }).click();

    // Should show validation errors
    await expect(page.getByText('Nome de usuário é obrigatório')).toBeVisible();
    await expect(page.getByText('Senha é obrigatória')).toBeVisible();
  });

  test('should show validation errors for short inputs', async ({ page }) => {
    // Fill with short inputs
    await page.getByLabel('Nome de usuário').fill('ab');
    await page.locator('#password').fill('123');
    await page.getByRole('button', { name: /entrar/i }).click();

    // Should show specific validation errors
    await expect(page.getByText('Nome de usuário deve ter pelo menos 3 caracteres')).toBeVisible();
    await expect(page.getByText('Senha deve ter pelo menos 6 caracteres')).toBeVisible();
  });

  test('should toggle password visibility', async ({ page }) => {
    const passwordField = page.locator('#password');
    const toggleButton = page.getByRole('button', { name: 'Mostrar senha' });

    // Initially password should be hidden
    await expect(passwordField).toHaveAttribute('type', 'password');

    // Click to show password
    await toggleButton.click();
    await expect(passwordField).toHaveAttribute('type', 'text');
    await expect(page.getByRole('button', { name: 'Ocultar senha' })).toBeVisible();

    // Click to hide password again
    await page.getByRole('button', { name: 'Ocultar senha' }).click();
    await expect(passwordField).toHaveAttribute('type', 'password');
    await expect(page.getByRole('button', { name: 'Mostrar senha' })).toBeVisible();
  });

  test('should handle failed login attempt', async ({ page }) => {
    // Mock failed login response
    await page.route('/api/auth/login/', async route => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Credenciais inválidas'
        })
      });
    });

    // Fill form with credentials
    await page.getByLabel('Nome de usuário').fill('wronguser');
    await page.locator('#password').fill('wrongpassword123');
    await page.getByRole('button', { name: /entrar/i }).click();

    // Should show error message
    await expect(page.getByText('Credenciais inválidas')).toBeVisible();
    
    // Should remain on login page
    await expect(page).toHaveURL('/login');
  });

  test('should successfully login and redirect to dashboard', async ({ page }) => {
    // Mock successful login response
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
            email: 'test@example.com',
            first_name: 'Test',
            last_name: 'User'
          }
        })
      });
    });

    // Mock user profile endpoint for auth verification
    await page.route('/api/auth/user/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          first_name: 'Test',
          last_name: 'User'
        })
      });
    });

    // Fill and submit login form
    await page.getByLabel('Nome de usuário').fill('admin');
    await page.locator('#password').fill('admin123');
    await page.getByRole('button', { name: /entrar/i }).click();

    // Should show success message
    await expect(page.getByText('Login realizado com sucesso!')).toBeVisible();

    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
    
    // Should show dashboard content
    await expect(page.getByText('Bom dia, Test!')).toBeVisible();
  });

  test('should handle keyboard navigation', async ({ page }) => {
    // Username field should be focused initially
    await expect(page.getByLabel('Nome de usuário')).toBeFocused();

    // Tab to password field
    await page.keyboard.press('Tab');
    await expect(page.locator('#password')).toBeFocused();

    // Tab to password toggle button
    await page.keyboard.press('Tab');
    await expect(page.getByLabel('Mostrar senha')).toBeFocused();

    // Tab to submit button
    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', { name: /entrar/i })).toBeFocused();

    // Enter should submit the form
    await page.getByLabel('Nome de usuário').fill('testuser');
    await page.locator('#password').fill('testpass123');
    await page.getByRole('button', { name: /entrar/i }).focus();
    await page.keyboard.press('Enter');

    // Form should be submitted (validation errors will show for this test case)
    await expect(page.getByText('Nome de usuário deve ter pelo menos 3 caracteres')).toBeVisible();
  });

  test('should be responsive on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Check that elements are still visible and usable
    await expect(page.getByText('Atalaia Tintas').first()).toBeVisible();
    await expect(page.getByLabel('Nome de usuário')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();
    await expect(page.getByRole('button', { name: /entrar/i })).toBeVisible();

    // Form should still be functional
    await page.getByLabel('Nome de usuário').fill('mobile');
    await page.locator('#password').fill('password123');
    
    // Inputs should be filled correctly
    await expect(page.getByLabel('Nome de usuário')).toHaveValue('mobile');
    await expect(page.locator('#password')).toHaveValue('password123');
  });
});