# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: login.spec.ts >> Login Flow >> should show validation errors for short inputs
- Location: tests\e2e\login.spec.ts:43:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('Nome de usuário deve ter pelo menos 3 caracteres')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for getByText('Nome de usuário deve ter pelo menos 3 caracteres')

```

# Page snapshot

```yaml
- generic [ref=e2]:
  - generic [ref=e3]:
    - generic [ref=e7]:
      - img [ref=e9]
      - heading [level=1] [ref=e13]: Atalaia Tintas
      - paragraph [ref=e14]: Gestão inteligente para a sua tintaria. Controle misturas, etiquetas e estoque em um único sistema.
      - generic [ref=e15]:
        - generic [ref=e16]:
          - generic [ref=e17]: 🎨
          - generic [ref=e18]: Catálogo completo de cores e fórmulas
        - generic [ref=e19]:
          - generic [ref=e20]: 🧪
          - generic [ref=e21]: Controle de misturas em tempo real
        - generic [ref=e22]:
          - generic [ref=e23]: 🏷️
          - generic [ref=e24]: Geração automática de etiquetas
        - generic [ref=e25]:
          - generic [ref=e26]: 📦
          - generic [ref=e27]: Alertas de estoque inteligentes
      - paragraph [ref=e28]: Atalaia Tintas © 2026
    - generic [ref=e30]:
      - heading "Bem-vindo de volta!" [level=2] [ref=e31]
      - paragraph [ref=e32]: Entre com suas credenciais para acessar o sistema.
      - form "Login" [ref=e33]:
        - generic [ref=e34]:
          - generic [ref=e35]: Nome de usuário
          - generic [ref=e36]:
            - img
            - textbox "Nome de usuário" [active] [ref=e37]:
              - /placeholder: Digite seu usuário
              - text: ab
          - alert [ref=e38]: Mínimo 3 caracteres
        - generic [ref=e39]:
          - generic [ref=e40]: Senha
          - generic [ref=e41]:
            - img
            - textbox "Senha" [ref=e42]:
              - /placeholder: Digite sua senha
              - text: "123"
            - button "Mostrar senha" [ref=e43]:
              - img [ref=e44]
          - button "Esqueceu sua senha?" [ref=e48]
          - alert [ref=e49]: Mínimo 6 caracteres
        - button "Entrar" [ref=e50]
      - paragraph [ref=e51]:
        - text: Não tem uma conta?
        - button "Cadastre-se" [ref=e52]
  - generic [ref=e53]:
    - img [ref=e55]
    - button "Open Tanstack query devtools" [ref=e104] [cursor=pointer]:
      - img [ref=e105]
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
  19  |     await expect(page.getByText('Atalaia Tintas').first()).toBeVisible();
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
> 50  |     await expect(page.getByText('Nome de usuário deve ter pelo menos 3 caracteres')).toBeVisible();
      |                                                                                      ^ Error: expect(locator).toBeVisible() failed
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
  120 |         contentType: 'application/json',
  121 |         body: JSON.stringify({
  122 |           id: 1,
  123 |           username: 'testuser',
  124 |           email: 'test@example.com',
  125 |           first_name: 'Test',
  126 |           last_name: 'User'
  127 |         })
  128 |       });
  129 |     });
  130 | 
  131 |     // Fill and submit login form
  132 |     await page.getByLabel('Nome de usuário').fill('admin');
  133 |     await page.locator('#password').fill('admin123');
  134 |     await page.getByRole('button', { name: /entrar/i }).click();
  135 | 
  136 |     // Should show success message
  137 |     await expect(page.getByText('Login realizado com sucesso!')).toBeVisible();
  138 | 
  139 |     // Should redirect to dashboard
  140 |     await expect(page).toHaveURL('/dashboard');
  141 |     
  142 |     // Should show dashboard content
  143 |     await expect(page.getByText('Bom dia, Test!')).toBeVisible();
  144 |   });
  145 | 
  146 |   test('should handle keyboard navigation', async ({ page }) => {
  147 |     // Username field should be focused initially
  148 |     await expect(page.getByLabel('Nome de usuário')).toBeFocused();
  149 | 
  150 |     // Tab to password field
```