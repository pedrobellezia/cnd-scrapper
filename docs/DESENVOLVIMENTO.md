# Guia de Desenvolvimento

Este guia descreve os passos necessários para expandir e manter os scrapers de CND (Certidão Negativa de Débitos) no sistema.

---

## Índice
1. [Adicionando uma Nova CND](#adicionando-uma-nova-cnd)
2. [Adicionando uma Nova CND Estadual](#adicionando-uma-nova-cnd-estadual)
3. [Adicionando uma Nova CND Municipal](#adicionando-uma-nova-cnd-municipal)
4. [Como levantar exceções (Raise)](#como-levantar-exceções-raise)
5. [Como resolver CAPTCHAs](#como-resolver-captchas)

---

## Adicionando uma Nova CND

### 1. Crie o Service
Crie um arquivo na pasta `app/services/` (ex: `app/services/federal.py`). A classe do serviço deve implementar a lógica de scraping utilizando o Playwright:

```python
from playwright.async_api import Page
from app.exceptions import handle_scrap_errors

class Federal:
    @staticmethod
    @handle_scrap_errors("federal")
    async def execute_scrap(page: Page, cnpj: str) -> bytes:
        await page.goto("https://portal-do-orgao.gov.br")
        
        # ...
        
        return pdf_bytes
```

> [!NOTE]
> - A organização do serviço dentro de uma classe é recomendada porém não é obrigatória.
> - O método/função que realiza o scrap deve obrigatoriamente retornar em `bytes` o PDF do documento gerado.

No arquivo `app/services/__init__.py`, exponha o novo serviço:
```python
from .estadual import Estadual
from .municipal import Municipal
from .trabalhista import Trabalhista
from .fgts import Fgts
from .federal import Federal 

__all__ = ["Estadual", "Municipal", "Trabalhista", "Fgts", "Federal"]
```

---

### 2. Crie o Schema (Opcional)
Se você precisar enviar parâmetros adicionais na requisição além do CNPJ, crie um schema específico herdando de `BaseCndRequest`. Caso contrário, você pode ignorar este passo e usar o `BaseCndRequest` diretamente no Router.

```python
from app.schemas import BaseCndRequest

class FederalCndRequest(BaseCndRequest):
    inscricao_estadual: str
```

No arquivo `app/schemas/__init__.py`, exponha o novo schema:
```python
from .requests import EstadualRequest, BaseCndRequest, MunicipalRequest, FederalCndRequest
from .errors import ErrorResponse, ErrorDetails

__all__ = [
    "BaseCndRequest",
    "EstadualRequest",
    "MunicipalRequest",
    "ErrorResponse",
    "ErrorDetails",
    "FederalCndRequest"
]
```

---

### 3. Crie o Router
```python
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from typing import Tuple
from playwright.async_api import Page, BrowserContext

from app.services import Federal
from app.core import get_tools
from app.schemas import BaseCndRequest  # Ou o seu schema personalizado

router = APIRouter()


@router.post("")
async def federal(
    data: BaseCndRequest, tools: Tuple[Page, BrowserContext] = Depends(get_tools)
) -> Response:
    page, context = tools
    pdf_bytes = await Federal.execute_scrap(page=page, cnpj=data.cnpj)
    return Response(content=pdf_bytes, media_type="application/pdf")
```

> [!NOTE]
> - A responsabilidade deste arquivo é exclusivamente: tratamento HTTP e validação dos dados recebidos. 
> - **`page`**: Utilizada para interagir diretamente e navegar pelas páginas do portal.
> - **`context`**: Utilizada para gerenciar cookies, local sessions e afins, portanto não é obrigatório.

#### Adicione no `__init__.py` do Router:
No arquivo `app/router/__init__.py`, exponha o novo router:
```python
from .estadual import router as estadual_router
from .municipal import router as municipal_router
from .trabalhista import router as trabalhista_router
from .fgts import router as fgts_router
from .federal import router as federal_router

__all__ = [
    "estadual_router",
    "municipal_router",
    "trabalhista_router",
    "fgts_router",
    "federal_router"
]
```

---

### 4. Adicione o Router no Core
Abra o arquivo `app/core/server_configs.py`. Importe o novo router e registre-o dentro da função `add_routes`:

```python
from app.router import federal_router

def add_routes(app: FastAPI):
    # ...
    app.include_router(
        federal_router, prefix="/federal", dependencies=[Depends(auth_key)]
    )
```

---

## Adicionando uma Nova CND Estadual

As CNDs estaduais já possuem um roteador e uma classe base configurados. O sistema mapeia e executa os scrapers de forma dinâmica baseado no código da UF enviado na requisição.

Para adicionar um novo estado (ex: Rio de Janeiro):
1. Abra o arquivo `app/services/estadual.py`.
2. Adicione um novo `@staticmethod` dentro da classe `Estadual` utilizando a sigla do estado em **letras minúsculas** como o nome do método:

```python
@staticmethod
async def rj(*, page: Page, context: BrowserContext, cnpj: str) -> bytes:
    logger.info("Starting Estadual RJ scrape for CNPJ: %s", cnpj)
    
    await page.goto("https://www.fazenda.rj.gov.br/certidao")
    
    # ... 
    
    logger.info("Estadual RJ scrape completed for CNPJ: %s", cnpj)    
    return pdf_bytes
```

---

## Adicionando uma Nova CND Municipal

Assim como no caso estadual, a lógica municipal é dinâmica. O roteador municipal despacha as requisições para métodos com nomenclatura padronizada.

Para adicionar um município (ex: Itajaí - SC):
1. Abra o arquivo `app/services/municipal.py`.
2. Adicione um novo `@staticmethod` na classe `Municipal` nomeado no formato `{uf}_{nome_municipio}` (tudo em letras minúsculas e sem acentos/caracteres especiais):

```python
@staticmethod
async def sc_itajai(page: Page, context: BrowserContext, cnpj: str) -> bytes:
    logger.info("Starting Municipal SC/Itajaí scrape for CNPJ: %s", cnpj)
    
    await page.goto("https://www.example.com/certidao")
    
    # ... 
    
    pdf_bytes = b"exemplo_pdf_bytes"
    
    logger.info("Municipal SC/Itajaí scrape completed for CNPJ: %s", cnpj)
    return pdf_bytes
```

### Integração com Betha Sistemas

Se o portal da CND municipal utilizar a plataforma **Betha Sistemas** (como no caso de Florianópolis - SC), o procedimento é diferente e exige um `@classmethod`:

1. Utilize o DevTools do seu navegador para inspecionar a página [Betha CDWeb](https://e-gov.betha.com.br/cdweb).
2. Identifique o id do estado no elemento de xpath `//select[@id="mainForm:estados"]`.
3. Identifique o id do município no elemento de xpath `//select[@id="mainForm:municipios"]`.
4. Defina o método utilizando esses IDs nos parâmetros `estado_id` e `municipio_id`, chamando o método auxiliar `__solve_betha`:

```python
@classmethod
async def sc_florianopolis(
    cls, page: Page, context: BrowserContext, cnpj: str
) -> bytes:
    download_info = await cls.__solve_betha(
        page, context, cnpj, municipio_id="94", estado_id="22"
    )

    download_path = await download_info.path()
    if not download_path:
        raise ScrapError(
            message=f"Falha ao obter PDF para {cnpj}",
            error_type=ErrorType.DownloadError,
        )
    pdf_bytes = Path(download_path).read_bytes()

    logger.info("Municipal SC/Florianopolis scrape completed for CNPJ: %s", cnpj)
    return pdf_bytes
```
---

## Como levantar exceções (Raise)

Para manter a consistência nas respostas da API e no fluxo de logging, utilize sempre a exceção personalizada `ScrapError` (importada de `app.exceptions`).

Você deve informar o `error_type` apropriado (que define o status HTTP retornado pelo servidor). Os tipos mapeados em `ErrorType` são:

* `CaptchaError` (Retorna HTTP 502): Use quando houver falhas ao resolver CAPTCHAs.
* `ElementNotFound` (Retorna HTTP 502): Use quando elementos esperados na página não puderam ser localizados.
* `TimeoutError` (Retorna HTTP 504): Levantado automaticamente se operações do Playwright estourarem o tempo limite.
* `DownloadError` (Retorna HTTP 502): Erro no download do PDF do documento emitido.
* `ScrapError` (Retorna HTTP 500): Falha interna genérica.
* `CndUnavailable` (Retorna HTTP 422): Use quando a consulta foi bem sucedida, mas o órgão informa que o CNPJ **possui débitos** pendentes e por isso a CND não pôde ser emitida.
 
### Exemplo prático:
```python
from app.exceptions import ScrapError, ErrorType

if await page.locator("//div[@id='mensagens-erro']").is_visible():
    raise ScrapError(
        message="A certidão não pôde ser emitida pois constam débitos de tributos estaduais.",
        error_type=ErrorType.CndUnavailable
    )
```

---

## Como resolver CAPTCHAs

A classe `CaptchaSolver` (em `app/utils/captcha_solver.py`) abstrai a comunicação com a API do 2captcha.

Primeiro, instancie o solver dentro do seu método de scraping:
```python
from app.core import CAPTCHA_API_KEY
from app.utils.captcha_solver import CaptchaSolver

solver = CaptchaSolver(api_key=CAPTCHA_API_KEY, page=page)
```

### 1. reCAPTCHA v2 (comum na maioria dos portais)
O método `auto_solve_v2` localiza automaticamente o iframe do reCAPTCHA v2 na página, obtém o `sitekey`, solicita a resolução e insere a resposta na área correta:
```python
result = await solver.auto_solve_v2()

if not result.get("success", False):
    raise ScrapError(
        message=result.get("error") or "Erro ao resolver CAPTCHA v2",
        error_type=ErrorType.CaptchaError,
    )
```
> [!WARNING]
> O método `auto_solve_v2` levantará um erro caso tenha mais de um Captcha do tipo v2 na página.

### 2. CAPTCHA Clássico (Imagem/Texto)
O método `solve_normal` tira um screenshot do elemento de imagem especificado (via XPath), envia a imagem codificada em base64 para decodificação e preenche a resposta no campo de input correspondente:
```python
result = await solver.solve_normal(
    img_xpath="//img[@id='captcha_imagem']",
    input_xpath="//input[@id='captcha_resposta']"
)

if not result.get("success", False):
    raise ScrapError(
        message=result.get("error") or "Erro ao resolver CAPTCHA de imagem",
        error_type=ErrorType.CaptchaError,
    )
```

### 3. Acesso Direto à API do 2captcha
Caso sua aplicação precise resolver outros formatos de CAPTCHA que não possuem métodos utilitários implementados diretamente nesta classe auxiliar (como o **ALTCHA**, por exemplo), você pode acessar diretamente a instância nativa do cliente do 2captcha por meio do atributo `solver.solver`.
Isso lhe dá acesso total a todos os métodos assíncronos oficiais da biblioteca `2captcha-python`.

Documentação oficial: [link](https://github.com/2captcha/2captcha-python)