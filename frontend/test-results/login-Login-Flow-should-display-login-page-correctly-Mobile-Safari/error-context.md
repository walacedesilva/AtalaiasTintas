# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: login.spec.ts >> Login Flow >> should display login page correctly
- Location: tests\e2e\login.spec.ts:14:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator:  getByText('Atalaia Tintas').first()
Expected: visible
Received: hidden
Timeout:  5000ms

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for getByText('Atalaia Tintas').first()
    9 × locator resolved to <h1 class="text-3xl font-bold text-white tracking-tight mb-3">Atalaia Tintas</h1>
      - unexpected value "hidden"

```

# Page snapshot

```yaml
- generic [ref=e2]:
  - generic [ref=e5]:
    - generic [ref=e6]:
      - img [ref=e8]
      - generic [ref=e12]: Atalaia Tintas
    - heading "Bem-vindo de volta!" [level=2] [ref=e13]
    - paragraph [ref=e14]: Entre com suas credenciais para acessar o sistema.
    - form "Login" [ref=e15]:
      - generic [ref=e16]:
        - generic [ref=e17]: Nome de usuário
        - generic [ref=e18]:
          - img
          - textbox "Nome de usuário" [active] [ref=e19]:
            - /placeholder: Digite seu usuário
      - generic [ref=e20]:
        - generic [ref=e21]: Senha
        - generic [ref=e22]:
          - img
          - textbox "Senha" [ref=e23]:
            - /placeholder: Digite sua senha
          - button "Mostrar senha" [ref=e24]:
            - img [ref=e25]
        - button "Esqueceu sua senha?" [ref=e29]
      - button "Entrar" [ref=e30]
    - paragraph [ref=e31]:
      - text: Não tem uma conta?
      - button "Cadastre-se" [ref=e32]
  - generic [ref=e33]:
    - img [ref=e35]
    - button "Open Tanstack query devtools" [ref=e103] [cursor=pointer]:
      - img [ref=e104]
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | /**
  4   |  * End-to-End Login Flow Tests
  5   |  * Tests the complete authentication user journey
  6   |  */
  7   | 
  8   | test.describe('Login Flow', () => {
  9   |   test.beforeEach(async ({ page }) => {
  10  |     // Navigate to login page before each test
  11  |     await page.goto('/login');
  12  |   });
  13  | 
  14  |   test('should display login page correctly', async ({ page }) => {
  15  |     // Check page title
  16  |     await expect(page).toHaveTitle(/Atalaia Tintas/);
  17  | 
  18  |     // Check main elements are visible
> 19  |     await expect(page.getByText('Atalaia Tintas').first()).toBeVisible();
      |                                                            ^ Error: expect(locator).toBeVisible() failed
  20  |     await expect(page.getByText('Gestão inteligente para a sua tintaria')).toBeVisible();
  21  |     await expect(page.getByText('Bem-vindo de volta!')).toBeVisible();
  22  | 
  23  |     // Check form fields
  24  |     await expect(page.getByLabel('Nome de usuário')).toBeVisible();
  25  |     await expect(page.locator('#password')).toBeVisible();
  26  |     await expect(page.getByRole('button', { name: /entrar/i })).toBeVisible();
  27  |   });
  28  | 
  29  |   test('should focus on username field when page loads', async ({ page }) => {
  30  |     // Username field should be focused
  31  |     await expect(page.getByLabel('Nome de usuário')).toBeFocused();
  32  |   });
  33  | 
  34  |   test('should show validation errors for empty form submission', async ({ page }) => {
  35  |     // Click submit without filling form
  36  |     await page.getByRole('button', { name: /entrar/i }).click();
  37  | 
  38  |     // Should show validation errors
  39  |     await expect(page.getByText('Nome de usuário é obrigatório')).toBeVisible();
  40  |     await expect(page.getByText('Senha é obrigatória')).toBeVisible();
  41  |   });
  42  | 
  43  |   test('should show validation errors for short inputs', async ({ page }) => {
  44  |     // Fill with short inputs
  45  |     await page.getByLabel('Nome de usuário').fill('ab');
  46  |     await page.locator('#password').fill('123');
  47  |     await page.getByRole('button', { name: /entrar/i }).click();
  48  | 
  49  |     // Should show specific validation errors
  50  |     await expect(page.getByText('Nome de usuário deve ter pelo menos 3 caracteres')).toBeVisible();
  51  |     await expect(page.getByText('Senha deve ter pelo menos 6 caracteres')).toBeVisible();
  52  |   });
  53  | 
  54  |   test('should toggle password visibility', async ({ page }) => {
  55  |     const passwordField = page.locator('#password');
  56  |     const toggleButton = page.getByRole('button', { name: 'Mostrar senha' });
  57  | 
  58  |     // Initially password should be hidden
  59  |     await expect(passwordField).toHaveAttribute('type', 'password');
  60  | 
  61  |     // Click to show password
  62  |     await toggleButton.click();
  63  |     await expect(passwordField).toHaveAttribute('type', 'text');
  64  |     await expect(page.getByRole('button', { name: 'Ocultar senha' })).toBeVisible();
  65  | 
  66  |     // Click to hide password again
  67  |     await page.getByRole('button', { name: 'Ocultar senha' }).click();
  68  |     await expect(passwordField).toHaveAttribute('type', 'password');
  69  |     await expect(page.getByRole('button', { name: 'Mostrar senha' })).toBeVisible();
  70  |   });
  71  | 
  72  |   test('should handle failed login attempt', async ({ page }) => {
  73  |     // Mock failed login response
  74  |     await page.route('/api/auth/login/', async route => {
  75  |       await route.fulfill({
  76  |         status: 401,
  77  |         contentType: 'application/json',
  78  |         body: JSON.stringify({
  79  |           detail: 'Credenciais inválidas'
  80  |         })
  81  |       });
  82  |     });
  83  | 
  84  |     // Fill form with credentials
  85  |     await page.getByLabel('Nome de usuário').fill('wronguser');
  86  |     await page.locator('#password').fill('wrongpassword123');
  87  |     await page.getByRole('button', { name: /entrar/i }).click();
  88  | 
  89  |     // Should show error message
  90  |     await expect(page.getByText('Credenciais inválidas')).toBeVisible();
  91  |     
  92  |     // Should remain on login page
  93  |     await expect(page).toHaveURL('/login');
  94  |   });
  95  | 
  96  |   test('should successfully login and redirect to dashboard', async ({ page }) => {
  97  |     // Mock successful login response
  98  |     await page.route('/api/auth/login/', async route => {
  99  |       await route.fulfill({
  100 |         status: 200,
  101 |         contentType: 'application/json',
  102 |         body: JSON.stringify({
  103 |           access: 'mock-token',
  104 |           refresh: 'mock-refresh',
  105 |           user: {
  106 |             id: 1,
  107 |             username: 'testuser',
  108 |             email: 'test@example.com',
  109 |             first_name: 'Test',
  110 |             last_name: 'User'
  111 |           }
  112 |         })
  113 |       });
  114 |     });
  115 | 
  116 |     // Mock user profile endpoint for auth verification
  117 |     await page.route('/api/auth/user/', async route => {
  118 |       await route.fulfill({
  119 |         status: 200,
```