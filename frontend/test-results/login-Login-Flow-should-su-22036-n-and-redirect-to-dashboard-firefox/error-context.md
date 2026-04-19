# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: login.spec.ts >> Login Flow >> should successfully login and redirect to dashboard
- Location: tests\e2e\login.spec.ts:96:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('Bom dia, Test!')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for getByText('Bom dia, Test!')

```

# Page snapshot

```yaml
- generic [ref=e2]:
  - generic [ref=e3]:
    - link "Pular para conteúdo principal" [ref=e4] [cursor=pointer]:
      - /url: "#main-content"
    - banner [ref=e5]:
      - link "Ir para dashboard" [ref=e6] [cursor=pointer]:
        - /url: /dashboard
        - img [ref=e8]
        - generic [ref=e12]: Atalaia Tintas
      - generic [ref=e14]: Painel
      - navigation "Ações rápidas" [ref=e15]:
        - link "Vendas" [ref=e16] [cursor=pointer]:
          - /url: /sales
        - link "Nova Mistura" [ref=e17] [cursor=pointer]:
          - /url: /mixtures?action=new
        - link "Gerar Etiqueta" [ref=e18] [cursor=pointer]:
          - /url: /labels?action=generate
      - button "Abrir instruções de uso" [ref=e19]:
        - img [ref=e20]
      - button "Menu do usuário" [ref=e25]:
        - generic [ref=e26]: A
        - generic [ref=e27]:
          - paragraph [ref=e28]: admin
          - paragraph [ref=e29]: admin@atalaia-tintas.com
        - img [ref=e30]
    - generic [ref=e32]:
      - navigation "Navegação principal" [ref=e33]:
        - generic [ref=e34]:
          - paragraph [ref=e35]: Menu
          - link "Painel" [ref=e36] [cursor=pointer]:
            - /url: /dashboard
            - generic [ref=e37]:
              - img [ref=e38]
              - generic [ref=e43]: Painel
          - link "PDV" [ref=e44] [cursor=pointer]:
            - /url: /pdv
            - generic [ref=e45]:
              - img [ref=e46]
              - generic [ref=e50]: PDV
          - link "Pedidos" [ref=e51] [cursor=pointer]:
            - /url: /sales/orders
            - generic [ref=e52]:
              - img [ref=e53]
              - generic [ref=e60]: Pedidos
          - link "Vendas" [ref=e61] [cursor=pointer]:
            - /url: /sales
            - generic [ref=e62]:
              - img [ref=e63]
              - generic [ref=e67]: Vendas
          - link "Recebíveis" [ref=e68] [cursor=pointer]:
            - /url: /recebiveis
            - generic [ref=e69]:
              - img [ref=e70]
              - generic [ref=e74]: Recebíveis
          - link "Clientes" [ref=e75] [cursor=pointer]:
            - /url: /customers
            - generic [ref=e76]:
              - img [ref=e77]
              - generic [ref=e82]: Clientes
          - link "Pigmentos" [ref=e83] [cursor=pointer]:
            - /url: /pigments
            - generic [ref=e84]:
              - img [ref=e85]
              - generic [ref=e89]: Pigmentos
          - link "Cores Definidas" [ref=e90] [cursor=pointer]:
            - /url: /colors
            - generic [ref=e91]:
              - img [ref=e92]
              - generic [ref=e98]: Cores Definidas
          - link "Fórmulas" [ref=e99] [cursor=pointer]:
            - /url: /formulas
            - generic [ref=e100]:
              - img [ref=e101]
              - generic [ref=e105]: Fórmulas
          - link "Misturas" [ref=e106] [cursor=pointer]:
            - /url: /mixtures
            - generic [ref=e107]:
              - img [ref=e108]
              - generic [ref=e112]: Misturas
            - generic [ref=e113]: "0"
          - link "Estoque" [ref=e114] [cursor=pointer]:
            - /url: /inventory
            - generic [ref=e115]:
              - img [ref=e116]
              - generic [ref=e121]: Estoque
          - link "Etiquetas" [ref=e122] [cursor=pointer]:
            - /url: /labels
            - generic [ref=e123]:
              - img [ref=e124]
              - generic [ref=e127]: Etiquetas
          - link "Tintometria" [ref=e128] [cursor=pointer]:
            - /url: /tintometry
            - generic [ref=e129]:
              - img [ref=e130]
              - generic [ref=e134]: Tintometria
          - link "Estoque Pigmentos" [ref=e135] [cursor=pointer]:
            - /url: /tintometry/stock
            - generic [ref=e136]:
              - img [ref=e137]
              - generic [ref=e141]: Estoque Pigmentos
          - link "Nota Fiscal" [ref=e142] [cursor=pointer]:
            - /url: /fiscal
            - generic [ref=e143]:
              - img [ref=e144]
              - generic [ref=e150]: Nota Fiscal
          - generic [ref=e151]:
            - paragraph [ref=e152]: Ações Rápidas
            - link "Nova Mistura" [ref=e153] [cursor=pointer]:
              - /url: /mixtures?action=new
              - img [ref=e154]
              - text: Nova Mistura
            - link "Nova Tintometria" [ref=e157] [cursor=pointer]:
              - /url: /tintometry
              - img [ref=e158]
              - text: Nova Tintometria
            - link "Gerar Etiqueta" [ref=e162] [cursor=pointer]:
              - /url: /labels?action=generate
              - img [ref=e163]
              - text: Gerar Etiqueta
        - generic [ref=e167]:
          - paragraph [ref=e168]: Status
          - generic [ref=e169]:
            - generic [ref=e170]: Misturas Hoje
            - generic [ref=e171]: "0"
          - generic [ref=e173]: Modelos Ativos
          - generic [ref=e175]: Estoque Baixo
          - generic [ref=e177]: Etiquetas Hoje
        - paragraph [ref=e179]: Atalaia Tintas v1.0
      - main "Conteúdo principal" [ref=e180]:
        - generic [ref=e182]:
          - generic [ref=e183]:
            - generic [ref=e184]:
              - heading "Boa noite, admin!" [level=1] [ref=e185]
              - paragraph [ref=e186]: sábado, 18 de abril de 2026
            - link "Nova Mistura" [ref=e187] [cursor=pointer]:
              - /url: /mixtures?action=new
              - img [ref=e188]
              - text: Nova Mistura
          - generic [ref=e191]:
            - generic [ref=e192]:
              - img [ref=e194]
              - generic [ref=e198]:
                - paragraph [ref=e199]: "0"
                - paragraph [ref=e200]: Modelos Ativos
            - generic [ref=e201]:
              - img [ref=e203]
              - generic [ref=e207]:
                - paragraph [ref=e208]: "0"
                - paragraph [ref=e209]: Misturas Hoje
            - generic [ref=e210]:
              - img [ref=e212]
              - generic [ref=e216]:
                - paragraph [ref=e217]: "0"
                - paragraph [ref=e218]: Estoque Baixo
            - generic [ref=e219]:
              - img [ref=e221]
              - generic [ref=e224]:
                - paragraph [ref=e225]: "0"
                - paragraph [ref=e226]: Etiquetas Hoje
          - generic [ref=e227]:
            - link "Nova Mistura Criar mistura de tinta" [ref=e228] [cursor=pointer]:
              - /url: /mixtures?action=new
              - img [ref=e230]
              - generic [ref=e233]:
                - paragraph [ref=e234]: Nova Mistura
                - paragraph [ref=e235]: Criar mistura de tinta
              - img [ref=e236]
            - link "Gerar Etiqueta Etiquetas para misturas" [ref=e238] [cursor=pointer]:
              - /url: /labels?action=generate
              - img [ref=e240]
              - generic [ref=e243]:
                - paragraph [ref=e244]: Gerar Etiqueta
                - paragraph [ref=e245]: Etiquetas para misturas
              - img [ref=e246]
            - link "Catálogo de Cores Explorar cores disponíveis" [ref=e248] [cursor=pointer]:
              - /url: /colors
              - img [ref=e250]
              - generic [ref=e256]:
                - paragraph [ref=e257]: Catálogo de Cores
                - paragraph [ref=e258]: Explorar cores disponíveis
              - img [ref=e259]
            - link "Controle de Estoque Gerenciar pigmentos" [ref=e261] [cursor=pointer]:
              - /url: /inventory
              - img [ref=e263]
              - generic [ref=e268]:
                - paragraph [ref=e269]: Controle de Estoque
                - paragraph [ref=e270]: Gerenciar pigmentos
              - img [ref=e271]
          - generic [ref=e273]:
            - generic [ref=e274]:
              - generic [ref=e275]:
                - heading "Alertas de Estoque" [level=2] [ref=e276]
                - link "Ver todos" [ref=e277] [cursor=pointer]:
                  - /url: /inventory
                  - text: Ver todos
                  - img [ref=e278]
              - generic [ref=e280]:
                - img [ref=e282]
                - paragraph [ref=e287]: Estoque OK
                - paragraph [ref=e288]: Todos os pigmentos com nível adequado
            - generic [ref=e289]:
              - generic [ref=e290]:
                - heading "Cores Populares" [level=2] [ref=e291]
                - link "Ver catálogo" [ref=e292] [cursor=pointer]:
                  - /url: /colors
                  - text: Ver catálogo
                  - img [ref=e293]
              - generic [ref=e295]:
                - img [ref=e297]
                - paragraph [ref=e303]: Nenhuma cor cadastrada
                - paragraph [ref=e304]: Adicione cores ao catálogo
  - generic [ref=e305]:
    - img [ref=e307]
    - button "Open Tanstack query devtools" [ref=e356] [cursor=pointer]:
      - img [ref=e357]
```

# Test source

```ts
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
> 143 |     await expect(page.getByText('Bom dia, Test!')).toBeVisible();
      |                                                    ^ Error: expect(locator).toBeVisible() failed
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