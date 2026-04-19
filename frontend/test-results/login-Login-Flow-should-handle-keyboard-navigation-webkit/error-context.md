# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: login.spec.ts >> Login Flow >> should handle keyboard navigation
- Location: tests\e2e\login.spec.ts:146:3

# Error details

```
Error: expect(locator).toBeFocused() failed

Locator:  getByRole('button', { name: /entrar/i })
Expected: focused
Received: inactive
Timeout:  5000ms

Call log:
  - Expect "toBeFocused" with timeout 5000ms
  - waiting for getByRole('button', { name: /entrar/i })
    9 × locator resolved to <button type="submit" class="btn-primary w-full py-2.5">Entrar</button>
      - unexpected value "inactive"

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
            - textbox "Nome de usuário" [ref=e37]:
              - /placeholder: Digite seu usuário
        - generic [ref=e38]:
          - generic [ref=e39]: Senha
          - generic [ref=e40]:
            - img
            - textbox "Senha" [ref=e41]:
              - /placeholder: Digite sua senha
            - button "Mostrar senha" [ref=e42]:
              - img [ref=e43]
          - button "Esqueceu sua senha?" [active] [ref=e47]
        - button "Entrar" [ref=e48]
      - paragraph [ref=e49]:
        - text: Não tem uma conta?
        - button "Cadastre-se" [ref=e50]
  - generic [ref=e51]:
    - img [ref=e53]
    - button "Open Tanstack query devtools" [ref=e121] [cursor=pointer]:
      - img [ref=e122]
```

# Test source

```ts
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
  151 |     await page.keyboard.press('Tab');
  152 |     await expect(page.locator('#password')).toBeFocused();
  153 | 
  154 |     // Tab to password toggle button
  155 |     await page.keyboard.press('Tab');
  156 |     await expect(page.getByLabel('Mostrar senha')).toBeFocused();
  157 | 
  158 |     // Tab to submit button
  159 |     await page.keyboard.press('Tab');
> 160 |     await expect(page.getByRole('button', { name: /entrar/i })).toBeFocused();
      |                                                                 ^ Error: expect(locator).toBeFocused() failed
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
  177 |     await expect(page.getByText('Atalaia Tintas').first()).toBeVisible();
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