# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: login.spec.ts >> Login Flow >> should be responsive on mobile devices
- Location: tests\e2e\login.spec.ts:172:3

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
    8 × locator resolved to <h1 class="text-3xl font-bold text-white tracking-tight mb-3">Atalaia Tintas</h1>
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
  151 |     await page.keyboard.press('Tab');
  152 |     await expect(page.locator('#password')).toBeFocused();
  153 | 
  154 |     // Tab to password toggle button
  155 |     await page.keyboard.press('Tab');
  156 |     await expect(page.getByLabel('Mostrar senha')).toBeFocused();
  157 | 
  158 |     // Tab to submit button
  159 |     await page.keyboard.press('Tab');
  160 |     await expect(page.getByRole('button', { name: /entrar/i })).toBeFocused();
  161 | 
  162 |     // Enter should submit the form
  163 |     await page.getByLabel('Nome de usuário').fill('testuser');
  164 |     await page.locator('#password').fill('testpass123');
  165 |     await page.getByRole('button', { name: /entrar/i }).focus();
  166 |     await page.keyboard.press('Enter');
  167 | 
  168 |     // Form should be submitted (validation errors will show for this test case)
  169 |     await expect(page.getByText('Nome de usuário deve ter pelo menos 3 caracteres')).toBeVisible();
  170 |   });
  171 | 
  172 |   test('should be responsive on mobile devices', async ({ page }) => {
  173 |     // Set mobile viewport
  174 |     await page.setViewportSize({ width: 375, height: 667 });
  175 | 
  176 |     // Check that elements are still visible and usable
> 177 |     await expect(page.getByText('Atalaia Tintas').first()).toBeVisible();
      |                                                            ^ Error: expect(locator).toBeVisible() failed
  178 |     await expect(page.getByLabel('Nome de usuário')).toBeVisible();
  179 |     await expect(page.locator('#password')).toBeVisible();
  180 |     await expect(page.getByRole('button', { name: /entrar/i })).toBeVisible();
  181 | 
  182 |     // Form should still be functional
  183 |     await page.getByLabel('Nome de usuário').fill('mobile');
  184 |     await page.locator('#password').fill('password123');
  185 |     
  186 |     // Inputs should be filled correctly
  187 |     await expect(page.getByLabel('Nome de usuário')).toHaveValue('mobile');
  188 |     await expect(page.locator('#password')).toHaveValue('password123');
  189 |   });
  190 | });
```