# CND Scrapper

O **CND Scrapper** é uma API de scraping desenvolvida com FastAPI e Playwright para realizar o download de diversas Certidões Negativas de Débitos.

---

## CNDs Suportadas

- **FGTS** - [link](https://consulta-crf.caixa.gov.br/consultacrf/pages/consultaEmpregador.jsf)
- **Trabalhista** - [link](https://cndt-certidao.tst.jus.br/inicio.faces)

### Estaduais
- **Espírito Santo** (ES) - [link](https://s2-internet.sefaz.es.gov.br/certidao/cnd)
- **Rio Grande do Sul** (RS) - [link](https://www.sefaz.rs.gov.br/sat/CertidaoSitFiscalSolic.aspx)
- **Santa Catarina** (SC) - [link](https://sat.sef.sc.gov.br/tax.NET/Sat.CtaCte.Web/SolicitacaoCnd.aspx)
- **São Paulo** (SP) - [link](https://www10.fazenda.sp.gov.br/CertidaoNegativaDeb/Pages/EmissaoCertidaoNegativa.aspx)

### Municipais

- **Espírito Santo (ES):**
  - Vitória - [link](https://tributario.vitoria.es.gov.br/Servicos/CertidaoNegativa/CertidaoNegativa.aspx)
- **Minas Gerais (MG):**
  - Pará de Minas - [link](https://e-gov.betha.com.br/cdweb/)
- **Rio Grande do Sul (RS):**
  - Nova Prata - [link](https://novaprata.multi24h.com.br/multi24/sistemas/portal/)
- **Santa Catarina (SC):**
  - Balneário Camboriú - [link](https://cidadao.bc.sc.gov.br/cidadao/balneario_camboriu/portal/servicos/certidoes/emissao?params=MTU%3D)
  - Blumenau - [link](https://www.blumenau.sc.gov.br/cidadao/pages/siatu/cnd/EmissaoCND.aspx)
  - Braço do Norte - [link](https://e-gov.betha.com.br/cdweb/)
  - Criciúma - [link](https://e-gov.betha.com.br/cdweb/)
  - Florianópolis - [link](https://e-gov.betha.com.br/cdweb/)
  - Içara - [link](https://icara-sc.prefeituramoderna.com.br/meuiptu/index.php)
  - Itapema - [link](https://itapema-sc.prefeituramoderna.com.br/meuiptu/index.php)
  - Joinville - [link](https://tmiweb.joinville.sc.gov.br/sefaz/jsp/cnd/index.jsp)
  - Lages - [link](https://e-gov.betha.com.br/cdweb/)
- **São Paulo (SP):**
  - São Paulo - [link](https://duc.prefeitura.sp.gov.br/certidoes/forms_anonimo/frmConsultaEmissaoCertificado.aspx)

---

## Solicitar Novas CNDs

Caso precise de uma CND que ainda não esteja implementada, você pode abrir uma issue diretamente no repositório utilizando os links abaixo:

* [Solicitar Nova CND Estadual](https://github.com/pedrobellezia/cnd-scrapper/issues/new?template=cnd_estadual.yml)
* [Solicitar Nova CND Municipal](https://github.com/pedrobellezia/cnd-scrapper/issues/new?template=cnd_municipal.yml)
* [Solicitar Outros Tipos de CND](https://github.com/pedrobellezia/cnd-scrapper/issues/new?template=cnd_outras.yml)

---

## Tecnologias Utilizadas

- **Linguagem:** Python
- **Framework:** FastAPI
- **Scraping:** Playwright
- **Resolução de CAPTCHA:** [2captcha](https://github.com/2captcha/2captcha-python)

---

## .env

Copie o arquivo `.env.example` para `.env` e preencha as variáveis necessárias:

```bash
cp .env.example .env
```

Campos configuráveis no `.env`:

| Variável                  | Descrição                                                                  | Exemplo                                      |
|:--------------------------|:---------------------------------------------------------------------------|:---------------------------------------------|
| `CAPTCHA_API_KEY`         | Chave de API do [2captcha](https://2captcha.com/).                         | `sua_chave_aqui`                             |
| `HEADLESS`                | Define se o navegador deve rodar em modo headless (sem interface gráfica). | `False`                                      |
| `MAX_CONCURRENT_BROWSERS` | Número máximo de instâncias de navegadores simultâneas.                    | `3`                                          |
| `API_KEY`                 | Token estático utilizado para proteger os endpoints da API (Bearer Auth).  | `meu_token_secreto`                          |
| `ALLOWED_ORIGINS`         | Origens CORS permitidas (separadas por vírgula).                           | `http://localhost:3000`                      |
| `HOST`                    | IP ou host onde a aplicação escutará.                                      | `0.0.0.0`                                    |
| `PORT`                    | Porta na qual a API será exposta.                                          | `5049`                                       |

> [!NOTE]
> Todas as rotas são testadas utilizando `HEADLESS=False`. A execução com `HEADLESS=True` pode falhar em algumas certidões devido a mecanismos de detecção de bots.
>
> É recomendado gerar a chave `API_KEY` utilizando a biblioteca `secrets`:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

---

## Instalação e Execução

### Opção 1: Execução Local

1. **Instale o `uv`** (caso não tenha instalado):
   [Guia de instalação](https://docs.astral.sh/uv/getting-started/installation/#installation-methods)

2. **Instale as dependências e prepare o ambiente virtual**:
   ```bash
   uv sync
   ```

3. **Instale os navegadores do Playwright**:
   ```bash
   uv run playwright install chromium
   ```

4. **Inicie o servidor**:
   ```bash
   uv run -m app.app
   ```

### Opção 2: Execução com Docker (Recomendado)

1. **Construa e inicie os containers**:
   ```bash
   docker compose up --build -d
   ```

A API estará disponível por padrão no endereço: `http://localhost:5049/docs`

---

## Como Usar a API

### 1. Swagger

* `http://{HOST}:<PORT>/docs`
 
### 2. OpenAPI

* `http://{HOST}:<PORT>/openapi.json`

---

### 3. Endpoints Disponíveis

> [!NOTE]
> Todos os endpoints de consulta de CND listados abaixo retornam diretamente o arquivo **PDF** da certidão gerada (`Content-Type: application/pdf`) em caso de sucesso.

#### FGTS

* **Rota:** `/fgts`
* **Método:** `POST`
* **Headers:**
  - `Content-Type: application/json`
  - `Authorization: Bearer <API_KEY>`
* **Body:**
  ```json
  {
    "cnpj": "12.345.678/0001-90"
  }
  ```
* **Retorno:** Arquivo PDF (`application/pdf`)

---

#### Trabalhista

* **Rota:** `/trabalhista`
* **Método:** `POST`
* **Headers:**
  - `Content-Type: application/json`
  - `Authorization: Bearer <API_KEY>`
* **Body:**
  ```json
  {
    "cnpj": "12.345.678/0001-90"
  }
  ```
* **Retorno:** Arquivo PDF (`application/pdf`)

---

#### Estadual

* **Rota:** `/estadual`
* **Método:** `POST`
* **Headers:**
  - `Content-Type: application/json`
  - `Authorization: Bearer <API_KEY>`
* **Body:**
  ```json
  {
    "cnpj": "12.345.678/0001-90",
    "uf": "sp"
  }
  ```
* **Retorno:** Arquivo PDF (`application/pdf`)

---

#### Municipal

* **Rota:** `/municipal`
* **Método:** `POST`
* **Headers:**
  - `Content-Type: application/json`
  - `Authorization: Bearer <API_KEY>`
* **Body:**
  ```json
  {
    "cnpj": "12.345.678/0001-90",
    "uf": "sc",
    "municipio": "blumenau"
  }
  ```
* **Retorno:** Arquivo PDF (`application/pdf`)
  > Todos os parâmetros solicitados nas rotas são sanitizados pela própria aplicação.
  > - "12.345.678/0001-90" => "12345678000190"
  > - "São Paulo" => "sao_paulo"
  > - "SP" => "sp"

##### Exemplo de Uso (curl):
```bash
curl -X POST http://localhost:5049/fgts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <API_KEY>" \
  -d '{"cnpj": "12345678000190"}' \
  --output certidao_fgts.pdf
```

### 4. Tratamento de Erros

#### Erros de Validação (HTTP 422 Unprocessable Entity)
```json
{
  "error": "RequestValidationError",
  "message": "Houve um erro de validação nos dados enviados",
  "details": {
    "cnpj": "Value error, CNPJ deve conter exatamente 14 dígitos"
  }
}
```



#### Erros de Scraping
Erros que ocorrem durante um scraping.
```json
{
  "error": "TimeoutError",
  "message": "Timeout durante a execução do scraper",
  "details": {
    "cnpj": "12345678000190",
    "cnd_type": "fgts",
    "url": "https://consulta-crf.caixa.gov.br/consultacrf/pages/consultaEmpregador.jsf",
    "screenshot": "error_1689258900.png"
  }
}
```

#### Tabela de Mapeamento de Erros do Scraper

|          Código HTTP          | Tipo de Erro (`error`) | Descrição                                                                                      |
|:-----------------------------:|:-----------------------|:-----------------------------------------------------------------------------------------------|
|      **502 Bad Gateway**      | `ElementNotFound`      | Um elemento HTML aguardado na página não foi localizado pelo Playwright.                       |
|    **504 Gateway Timeout**    | `TimeoutError`         | Uma ação (carregamento, cliques, etc.) ultrapassou o tempo limite configurado.                 |
|      **502 Bad Gateway**      | `DownloadError`        | A certidão foi gerada com sucesso, mas a tentativa de download do arquivo PDF falhou.          |
|      **502 Bad Gateway**      | `CaptchaError`         | Falha na resolução do CAPTCHA.                                                                 |
| **422 Unprocessable Entity**  | `CndUnavailable`       | O portal não disponibilizou a emissão da certidão para o contribuinte por conta de pendências. |
| **500 Internal Server Error** | `ScrapError`           | Qualquer erro inesperado.                                                                      |

### Captura de Tela de Erros
Para ajudar na depuração de eventuais erros, o scraper captura uma imagem da página no instante em que ocorre um erro. Essa imagem é servida através da rota:
```
http://{HOST}:{PORT}/screenshot/{nome_do_arquivo_de_erro}.png
```

---

## Desenvolvimento e Arquitetura

* **[Estrutura e Arquitetura Geral](docs/README.md)**
* **[Guia Prático de Desenvolvimento](docs/DESENVOLVIMENTO.md)**

