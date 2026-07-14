name: Solicitação de CND Estadual
description: Solicite a implementação de uma nova Certidão Negativa de Débitos Estadual.
title: "[CND Estadual] "
labels:
  - enhancement
  - estadual

body:
  - type: markdown
    attributes:
      value: |
        ## Nova CND Estadual

        Obrigado por contribuir com o projeto!

        Este formulário serve para solicitar a implementação de uma nova Certidão Negativa de Débitos (CND) Estadual.

        Quanto mais detalhes forem fornecidos, maiores as chances da implementação ser realizada rapidamente.

        **Antes de abrir esta issue:**
        - Verifique se a UF já não está implementada.
        - Verifique se já não existe uma issue semelhante aberta.

  - type: dropdown
    id: uf
    attributes:
      label: Estado (UF)
      description: Selecione o estado desejado.
      options:
        - AC
        - AL
        - AP
        - AM
        - BA
        - CE
        - DF
        - ES
        - GO
        - MA
        - MT
        - MS
        - MG
        - PA
        - PB
        - PR
        - PE
        - PI
        - RJ
        - RN
        - RS
        - RO
        - RR
        - SC
        - SP
        - SE
        - TO
    validations:
      required: true

  - type: input
    id: orgao
    attributes:
      label: Órgão responsável
      description: Informe qual órgão emite a certidão.
      placeholder: Secretaria da Fazenda de Santa Catarina
    validations:
      required: true

  - type: input
    id: url
    attributes:
      label: URL oficial
      description: Link oficial para emissão da certidão.
      placeholder: https://...
    validations:
      required: true

  - type: dropdown
    id: consulta
    attributes:
      label: Tipo de consulta
      options:
        - CPF
        - CNPJ
        - CPF e CNPJ
        - Outro
    validations:
      required: true

  - type: checkboxes
    id: recursos
    attributes:
      label: Recursos utilizados pela página
      description: Marque tudo que se aplicar.
      options:
        - label: CAPTCHA por imagem
        - label: reCAPTCHA
        - label: hCaptcha
        - label: CAPTCHA de áudio
        - label: Login obrigatório
        - label: Token CSRF
        - label: JavaScript obrigatório
        - label: Download em PDF
        - label: Download em HTML

  - type: textarea
    id: fluxo
    attributes:
      label: Como emitir a certidão?
      description: Explique o processo passo a passo.
      placeholder: |
        Exemplo:

        1. Acessar o portal
        2. Informar o CNPJ
        3. Resolver o CAPTCHA
        4. Clicar em Emitir
        5. A página redireciona para o PDF
    validations:
      required: true

  - type: textarea
    id: observacoes
    attributes:
      label: Informações adicionais
      description: Existe algum detalhe importante para implementação?

  - type: textarea
    id: anexos
    attributes:
      label: Arquivos úteis (opcional)
      description: Caso tenha, anexe HAR, HTML, screenshots ou qualquer outra informação útil.

  - type: checkboxes
    id: confirmacao
    attributes:
      label: Confirmação
      options:
        - label: Confirmo que a URL informada é oficial.
          required: true
        - label: Verifiquei que esta CND ainda não está implementada.
          required: true