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
      - button "Menu do usuário" [ref=e24]:
        - generic [ref=e25]: A
        - generic [ref=e26]:
          - paragraph [ref=e27]: admin
          - paragraph [ref=e28]: admin@atalaia-tintas.com
        - img [ref=e29]
    - generic [ref=e31]:
      - navigation "Navegação principal" [ref=e32]:
        - generic [ref=e33]:
          - paragraph [ref=e34]: Menu
          - link "Painel" [ref=e35] [cursor=pointer]:
            - /url: /dashboard
            - generic [ref=e36]:
              - img [ref=e37]
              - generic [ref=e42]: Painel
          - link "PDV" [ref=e43] [cursor=pointer]:
            - /url: /pdv
            - generic [ref=e44]:
              - img [ref=e45]
              - generic [ref=e47]: PDV
          - link "Pedidos" [ref=e48] [cursor=pointer]:
            - /url: /sales/orders
            - generic [ref=e49]:
              - img [ref=e50]
              - generic [ref=e53]: Pedidos
          - link "Vendas" [ref=e54] [cursor=pointer]:
            - /url: /sales
            - generic [ref=e55]:
              - img [ref=e56]
              - generic [ref=e60]: Vendas
          - link "Recebíveis" [ref=e61] [cursor=pointer]:
            - /url: /recebiveis
            - generic [ref=e62]:
              - img [ref=e63]
              - generic [ref=e66]: Recebíveis
          - link "Clientes" [ref=e67] [cursor=pointer]:
            - /url: /customers
            - generic [ref=e68]:
              - img [ref=e69]
              - generic [ref=e74]: Clientes
          - link "Pigmentos" [ref=e75] [cursor=pointer]:
            - /url: /pigments
            - generic [ref=e76]:
              - img [ref=e77]
              - generic [ref=e79]: Pigmentos
          - link "Cores Definidas" [ref=e80] [cursor=pointer]:
            - /url: /colors
            - generic [ref=e81]:
              - img [ref=e82]
              - generic [ref=e88]: Cores Definidas
          - link "Fórmulas" [ref=e89] [cursor=pointer]:
            - /url: /formulas
            - generic [ref=e90]:
              - img [ref=e91]
              - generic [ref=e93]: Fórmulas
          - link "Misturas" [ref=e94] [cursor=pointer]:
            - /url: /mixtures
            - generic [ref=e95]:
              - img [ref=e96]
              - generic [ref=e100]: Misturas
            - generic [ref=e101]: "0"
          - link "Estoque" [ref=e102] [cursor=pointer]:
            - /url: /inventory
            - generic [ref=e103]:
              - img [ref=e104]
              - generic [ref=e108]: Estoque
          - link "Etiquetas" [ref=e109] [cursor=pointer]:
            - /url: /labels
            - generic [ref=e110]:
              - img [ref=e111]
              - generic [ref=e114]: Etiquetas
          - link "Tintometria" [ref=e115] [cursor=pointer]:
            - /url: /tintometry
            - generic [ref=e116]:
              - img [ref=e117]
              - generic [ref=e121]: Tintometria
          - link "Estoque Pigmentos" [ref=e122] [cursor=pointer]:
            - /url: /tintometry/stock
            - generic [ref=e123]:
              - img [ref=e124]
              - generic [ref=e126]: Estoque Pigmentos
          - link "Nota Fiscal" [ref=e127] [cursor=pointer]:
            - /url: /fiscal
            - generic [ref=e128]:
              - img [ref=e129]
              - generic [ref=e132]: Nota Fiscal
          - generic [ref=e133]:
            - paragraph [ref=e134]: Ações Rápidas
            - link "Nova Mistura" [ref=e135] [cursor=pointer]:
              - /url: /mixtures?action=new
              - img [ref=e136]
              - text: Nova Mistura
            - link "Nova Tintometria" [ref=e137] [cursor=pointer]:
              - /url: /tintometry
              - img [ref=e138]
              - text: Nova Tintometria
            - link "Gerar Etiqueta" [ref=e142] [cursor=pointer]:
              - /url: /labels?action=generate
              - img [ref=e143]
              - text: Gerar Etiqueta
        - generic [ref=e147]:
          - paragraph [ref=e148]: Status
          - generic [ref=e149]:
            - generic [ref=e150]: Misturas Hoje
            - generic [ref=e151]: "0"
          - generic [ref=e153]: Modelos Ativos
          - generic [ref=e155]: Estoque Baixo
          - generic [ref=e157]: Etiquetas Hoje
        - paragraph [ref=e159]: Atalaia Tintas v1.0
      - main "Conteúdo principal" [ref=e160]:
        - generic [ref=e162]:
          - generic [ref=e163]:
            - generic [ref=e164]:
              - heading "Boa noite, admin!" [level=1] [ref=e165]
              - paragraph [ref=e166]: sábado, 18 de abril de 2026
            - link "Nova Mistura" [ref=e167] [cursor=pointer]:
              - /url: /mixtures?action=new
              - img [ref=e168]
              - text: Nova Mistura
          - generic [ref=e169]:
            - generic [ref=e170]:
              - img [ref=e172]
              - generic [ref=e174]:
                - paragraph [ref=e175]: "0"
                - paragraph [ref=e176]: Modelos Ativos
            - generic [ref=e177]:
              - img [ref=e179]
              - generic [ref=e183]:
                - paragraph [ref=e184]: "0"
                - paragraph [ref=e185]: Misturas Hoje
            - generic [ref=e186]:
              - img [ref=e188]
              - generic [ref=e190]:
                - paragraph [ref=e191]: "0"
                - paragraph [ref=e192]: Estoque Baixo
            - generic [ref=e193]:
              - img [ref=e195]
              - generic [ref=e198]:
                - paragraph [ref=e199]: "0"
                - paragraph [ref=e200]: Etiquetas Hoje
          - generic [ref=e201]:
            - link "Nova Mistura Criar mistura de tinta" [ref=e202] [cursor=pointer]:
              - /url: /mixtures?action=new
              - img [ref=e204]
              - generic [ref=e205]:
                - paragraph [ref=e206]: Nova Mistura
                - paragraph [ref=e207]: Criar mistura de tinta
              - img [ref=e208]
            - link "Gerar Etiqueta Etiquetas para misturas" [ref=e210] [cursor=pointer]:
              - /url: /labels?action=generate
              - img [ref=e212]
              - generic [ref=e215]:
                - paragraph [ref=e216]: Gerar Etiqueta
                - paragraph [ref=e217]: Etiquetas para misturas
              - img [ref=e218]
            - link "Catálogo de Cores Explorar cores disponíveis" [ref=e220] [cursor=pointer]:
              - /url: /colors
              - img [ref=e222]
              - generic [ref=e228]:
                - paragraph [ref=e229]: Catálogo de Cores
                - paragraph [ref=e230]: Explorar cores disponíveis
              - img [ref=e231]
            - link "Controle de Estoque Gerenciar pigmentos" [ref=e233] [cursor=pointer]:
              - /url: /inventory
              - img [ref=e235]
              - generic [ref=e239]:
                - paragraph [ref=e240]: Controle de Estoque
                - paragraph [ref=e241]: Gerenciar pigmentos
              - img [ref=e242]
          - generic [ref=e244]:
            - generic [ref=e245]:
              - generic [ref=e246]:
                - heading "Alertas de Estoque" [level=2] [ref=e247]
                - link "Ver todos" [ref=e248] [cursor=pointer]:
                  - /url: /inventory
                  - text: Ver todos
                  - img [ref=e249]
              - generic [ref=e251]:
                - img [ref=e253]
                - paragraph [ref=e257]: Estoque OK
                - paragraph [ref=e258]: Todos os pigmentos com nível adequado
            - generic [ref=e259]:
              - generic [ref=e260]:
                - heading "Cores Populares" [level=2] [ref=e261]
                - link "Ver catálogo" [ref=e262] [cursor=pointer]:
                  - /url: /colors
                  - text: Ver catálogo
                  - img [ref=e263]
              - generic [ref=e265]:
                - img [ref=e267]
                - paragraph [ref=e273]: Nenhuma cor cadastrada
                - paragraph [ref=e274]: Adicione cores ao catálogo
  - generic [ref=e275]:
    - img [ref=e277]
    - button "Open Tanstack query devtools" [ref=e325] [cursor=pointer]:
      - img [ref=e326]
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