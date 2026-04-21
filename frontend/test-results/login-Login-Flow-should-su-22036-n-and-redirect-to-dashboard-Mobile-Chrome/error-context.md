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
      - button "Abrir menu de navegação" [ref=e6]:
        - img [ref=e7]
      - link "Ir para dashboard" [ref=e8] [cursor=pointer]:
        - /url: /dashboard
        - img [ref=e10]
      - button "Abrir instruções de uso" [ref=e14]:
        - img [ref=e15]
      - button "Menu do usuário" [ref=e19]:
        - generic [ref=e20]: A
    - generic [ref=e21]:
      - navigation "Navegação principal" [ref=e22]:
        - button "Fechar menu" [ref=e23]:
          - img [ref=e24]
        - generic [ref=e27]:
          - paragraph [ref=e28]: Menu
          - link "Painel" [ref=e29] [cursor=pointer]:
            - /url: /dashboard
            - generic [ref=e30]:
              - img [ref=e31]
              - generic [ref=e36]: Painel
          - link "PDV" [ref=e37] [cursor=pointer]:
            - /url: /pdv
            - generic [ref=e38]:
              - img [ref=e39]
              - generic [ref=e41]: PDV
          - link "Pedidos" [ref=e42] [cursor=pointer]:
            - /url: /sales/orders
            - generic [ref=e43]:
              - img [ref=e44]
              - generic [ref=e47]: Pedidos
          - link "Vendas" [ref=e48] [cursor=pointer]:
            - /url: /sales
            - generic [ref=e49]:
              - img [ref=e50]
              - generic [ref=e54]: Vendas
          - link "Recebíveis" [ref=e55] [cursor=pointer]:
            - /url: /recebiveis
            - generic [ref=e56]:
              - img [ref=e57]
              - generic [ref=e60]: Recebíveis
          - link "Clientes" [ref=e61] [cursor=pointer]:
            - /url: /customers
            - generic [ref=e62]:
              - img [ref=e63]
              - generic [ref=e68]: Clientes
          - link "Pigmentos" [ref=e69] [cursor=pointer]:
            - /url: /pigments
            - generic [ref=e70]:
              - img [ref=e71]
              - generic [ref=e73]: Pigmentos
          - link "Cores Definidas" [ref=e74] [cursor=pointer]:
            - /url: /colors
            - generic [ref=e75]:
              - img [ref=e76]
              - generic [ref=e82]: Cores Definidas
          - link "Fórmulas" [ref=e83] [cursor=pointer]:
            - /url: /formulas
            - generic [ref=e84]:
              - img [ref=e85]
              - generic [ref=e87]: Fórmulas
          - link "Misturas" [ref=e88] [cursor=pointer]:
            - /url: /mixtures
            - generic [ref=e89]:
              - img [ref=e90]
              - generic [ref=e94]: Misturas
            - generic [ref=e95]: "0"
          - link "Estoque" [ref=e96] [cursor=pointer]:
            - /url: /inventory
            - generic [ref=e97]:
              - img [ref=e98]
              - generic [ref=e102]: Estoque
          - link "Etiquetas" [ref=e103] [cursor=pointer]:
            - /url: /labels
            - generic [ref=e104]:
              - img [ref=e105]
              - generic [ref=e108]: Etiquetas
          - link "Tintometria" [ref=e109] [cursor=pointer]:
            - /url: /tintometry
            - generic [ref=e110]:
              - img [ref=e111]
              - generic [ref=e115]: Tintometria
          - link "Estoque Pigmentos" [ref=e116] [cursor=pointer]:
            - /url: /tintometry/stock
            - generic [ref=e117]:
              - img [ref=e118]
              - generic [ref=e120]: Estoque Pigmentos
          - link "Nota Fiscal" [ref=e121] [cursor=pointer]:
            - /url: /fiscal
            - generic [ref=e122]:
              - img [ref=e123]
              - generic [ref=e126]: Nota Fiscal
          - generic [ref=e127]:
            - paragraph [ref=e128]: Ações Rápidas
            - link "Nova Mistura" [ref=e129] [cursor=pointer]:
              - /url: /mixtures?action=new
              - img [ref=e130]
              - text: Nova Mistura
            - link "Nova Tintometria" [ref=e131] [cursor=pointer]:
              - /url: /tintometry
              - img [ref=e132]
              - text: Nova Tintometria
            - link "Gerar Etiqueta" [ref=e136] [cursor=pointer]:
              - /url: /labels?action=generate
              - img [ref=e137]
              - text: Gerar Etiqueta
        - generic [ref=e141]:
          - paragraph [ref=e142]: Status
          - generic [ref=e143]:
            - generic [ref=e144]: Misturas Hoje
            - generic [ref=e145]: "0"
          - generic [ref=e147]: Modelos Ativos
          - generic [ref=e149]: Estoque Baixo
          - generic [ref=e151]: Etiquetas Hoje
        - paragraph [ref=e153]: Atalaia Tintas v1.0
      - main "Conteúdo principal" [ref=e154]:
        - generic [ref=e156]:
          - generic [ref=e157]:
            - generic [ref=e158]:
              - heading "Boa noite, admin!" [level=1] [ref=e159]
              - paragraph [ref=e160]: sábado, 18 de abril de 2026
            - link "Nova Mistura" [ref=e161] [cursor=pointer]:
              - /url: /mixtures?action=new
              - img [ref=e162]
              - text: Nova Mistura
          - generic [ref=e163]:
            - generic [ref=e164]:
              - img [ref=e166]
              - generic [ref=e168]:
                - paragraph [ref=e169]: "0"
                - paragraph [ref=e170]: Modelos Ativos
            - generic [ref=e171]:
              - img [ref=e173]
              - generic [ref=e177]:
                - paragraph [ref=e178]: "0"
                - paragraph [ref=e179]: Misturas Hoje
            - generic [ref=e180]:
              - img [ref=e182]
              - generic [ref=e184]:
                - paragraph [ref=e185]: "0"
                - paragraph [ref=e186]: Estoque Baixo
            - generic [ref=e187]:
              - img [ref=e189]
              - generic [ref=e192]:
                - paragraph [ref=e193]: "0"
                - paragraph [ref=e194]: Etiquetas Hoje
          - generic [ref=e195]:
            - link "Nova Mistura Criar mistura de tinta" [ref=e196] [cursor=pointer]:
              - /url: /mixtures?action=new
              - img [ref=e198]
              - generic [ref=e199]:
                - paragraph [ref=e200]: Nova Mistura
                - paragraph [ref=e201]: Criar mistura de tinta
              - img [ref=e202]
            - link "Gerar Etiqueta Etiquetas para misturas" [ref=e204] [cursor=pointer]:
              - /url: /labels?action=generate
              - img [ref=e206]
              - generic [ref=e209]:
                - paragraph [ref=e210]: Gerar Etiqueta
                - paragraph [ref=e211]: Etiquetas para misturas
              - img [ref=e212]
            - link "Catálogo de Cores Explorar cores disponíveis" [ref=e214] [cursor=pointer]:
              - /url: /colors
              - img [ref=e216]
              - generic [ref=e222]:
                - paragraph [ref=e223]: Catálogo de Cores
                - paragraph [ref=e224]: Explorar cores disponíveis
              - img [ref=e225]
            - link "Controle de Estoque Gerenciar pigmentos" [ref=e227] [cursor=pointer]:
              - /url: /inventory
              - img [ref=e229]
              - generic [ref=e233]:
                - paragraph [ref=e234]: Controle de Estoque
                - paragraph [ref=e235]: Gerenciar pigmentos
              - img [ref=e236]
          - generic [ref=e238]:
            - generic [ref=e239]:
              - generic [ref=e240]:
                - heading "Alertas de Estoque" [level=2] [ref=e241]
                - link "Ver todos" [ref=e242] [cursor=pointer]:
                  - /url: /inventory
                  - text: Ver todos
                  - img [ref=e243]
              - generic [ref=e245]:
                - img [ref=e247]
                - paragraph [ref=e251]: Estoque OK
                - paragraph [ref=e252]: Todos os pigmentos com nível adequado
            - generic [ref=e253]:
              - generic [ref=e254]:
                - heading "Cores Populares" [level=2] [ref=e255]
                - link "Ver catálogo" [ref=e256] [cursor=pointer]:
                  - /url: /colors
                  - text: Ver catálogo
                  - img [ref=e257]
              - generic [ref=e259]:
                - img [ref=e261]
                - paragraph [ref=e267]: Nenhuma cor cadastrada
                - paragraph [ref=e268]: Adicione cores ao catálogo
  - generic [ref=e269]:
    - img [ref=e271]
    - button "Open Tanstack query devtools" [ref=e319] [cursor=pointer]:
      - img [ref=e320]
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