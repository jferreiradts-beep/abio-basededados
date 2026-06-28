# Funções RPC do Supabase

Documentação das funções chamadas via `supabase.rpc(...)`, organizadas na ordem do fluxo de navegação. O SQL de cada função está no arquivo `.sql` correspondente nesta mesma pasta.

---

## Fluxo de navegação

```
/dashboard  →  /matricula  →  /formulario  →  /grupo
                                    │
                              menu lateral
                             (escopo aberto)
                                    │
                              /produtos  →  gerar PDF
```

---

## 1. Tela de matrícula — `/matricula`

### `dados_de_matricula`
**Arquivo:** `pag_matricula.py` · `colunaMatricula.baixar_dados()`

Chamada logo ao abrir a tela de matrícula. Retorna tudo que é necessário para montar a tela de uma vez só: dados gerais da matrícula, lista de grupos disponíveis (para o dropdown), associados vinculados, escopos e unidades de produção.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `matricula_input` | `text` | Código da matrícula (ex: `"03-147"`) |

**Retorna:** `jsonb` com as chaves `dados gerais`, `grupos`, `associados`, `escopos`, `uprods` — cada uma com lista de `{ id, nome }` ou campos equivalentes.

---

### `vincular_associado`
**Arquivo:** `pag_matricula.py` · `janelaNovoAssociado.ir()`

Chamada ao clicar em "Novo associado". Verifica se o CPF já existe; se não, cria o associado. Em seguida insere o vínculo na `rel_mat_asso` (ignorando duplicata com `ON CONFLICT`). Por fim, atualiza a materialized view `vw_dados_com_associado`.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `p_nome` | `text` | Nome do associado |
| `p_cpf` | `text` | CPF ou CNPJ (somente dígitos) |
| `p_matricula` | `text` | Código da matrícula |

**Retorna:** `integer` — ID do associado (novo ou já existente).

---

### `eliminar_e_atualizar`
**Arquivo:** `pag_matricula.py` · `Eliminar.eliminar()`

Chamada ao confirmar a eliminação de uma matrícula. Executa um `DELETE` dinâmico na tabela e coluna informadas (as FKs do banco cuidam da cascata), depois atualiza a materialized view.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `p_tabela` | `text` | Tabela alvo (ex: `"matriculas"`) |
| `p_coluna` | `text` | Coluna de filtro (ex: `"matricula"`) |
| `p_id` | `text` | Valor do filtro |

**Retorna:** `void`

---

## 2. Formulário genérico — `/formulario`

### `preencher_formulario`
**Arquivo:** `formulario_base.py` · `dadosFormulario.baixar_dados()`

Primeira coisa chamada ao entrar em qualquer formulário. Retorna a estrutura completa do formulário para o tipo informado: metadados dos campos (rótulo, ordem), valores atuais do registro e opções de todos os dropdowns (FKs resolvidas). Passando `p_registro = 0` retorna um template em branco para criação.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `p_tabela` | `text` | Tipo do registro: `"associado"`, `"escopo"`, `"grupo"`, `"uprod"`, `"nucleo"` |
| `p_registro` | `integer` | ID do registro (`0` = novo) |

**Retorna:** `jsonb` com `campos_fixos`, `campos_ajustaveis`, `dados_fixos`, `dados_ajustaveis`, `opcoes`.

> **Lógica de opções:** para cada campo com FK definida em `metadados`, a função faz um SELECT dinâmico. Se `metadados.filtro` estiver preenchido, aplica `WHERE filtro = p_registro`; caso contrário, retorna todos os registros da tabela de referência.

---

### `salvar_formulario`
**Arquivo:** `formulario_base.py` · `botoesFormulario.salvar()`

Chamada ao clicar em "Salvar". Se o `id` dentro de `dados_fixos` for `0` (ou nulo), faz INSERT e retorna o novo ID; caso contrário, faz UPDATE e reescreve os dados ajustáveis (`info_{tabela}`). Strings vazias são convertidas em `NULL`. Atualiza a materialized view ao final. Erros SQL são capturados e devolvidos como `{ status: "error", message: ... }`.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `p_tabela` | `text` | Tipo do registro |
| `p_dados` | `jsonb` | Dicionário completo com `dados_fixos` e `dados_ajustaveis` |

**Retorna:** `jsonb` — `{ "status": "success", "id": 7 }` ou `{ "status": "error", "message": "..." }`.

---

## 3. Menu lateral do escopo

> Visível quando o formulário aberto é do tipo `"escopo"`. As funções abaixo são chamadas ao clicar nos botões do menu lateral.

### `obter_info_escopo`
**Arquivo:** `formulario_coluna2.py` · `menuEscopo.obter_dados()`

Chamada ao montar o menu lateral. Retorna dois valores de resumo do escopo: a data de validade (calculada como data do último certificado emitido + 1 ano − 1 dia) e o nome do último acontecimento com `destaque = true`.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `p_escopo_id` | `integer` | ID do escopo |

**Retorna:** `json` — `{ "validade": "2026-03-14", "ultima_atualizacao": "Certificado emitido" }`.

---

### `obter_produtos`
**Arquivos:** `formulario_coluna2.py` · `verProdutos.obter_dados()` | `gerar_certificado.py` · `obterDados.obter_produtos()`

Retorna apenas os produtos **já vinculados** ao escopo, agrupados por grupo de produto, indexados pelo `tipo_escopo_id`. Usada em dois contextos:
- No menu lateral, para exibição em modo leitura ("Ver produtos").
- Na geração do PDF, para montar as páginas de produtos do certificado.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `p_escopo_id` | `integer` | ID do escopo |

**Retorna:** `json` — dicionário indexado pelo `tipo_escopo_id`, com listas de `{ grupo, produtos: [...] }`.

---

### `obter_associados_por_escopo`
**Arquivo:** `formulario_coluna2.py` · `nomesCertificado.obter_dados()`

Chamada ao abrir a janela "Editar nomes no certificado". Retorna todos os associados da matrícula do escopo, com o campo `vinculo` (booleano) indicando quais estão marcados para aparecer no certificado.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `p_escopo_id` | `integer` | ID do escopo |

**Retorna:** `json` — `{ "matricula": "03-147", "associados": [ { "id", "nome", "cpf", "vinculo" } ] }`.

---

### `atualizar_relacao_nm`
**Arquivos:** `formulario_coluna2.py` · `nomesCertificado.salvar_janela_nomes()` | `lista_produtos.py` · `linhaBotoes.salvar_produtos()`

Faz um **replace completo** de qualquer relação N:M: apaga todos os vínculos do lado fixo e reinseere apenas os IDs informados. A coluna oposta da tabela de junção é descoberta automaticamente via `information_schema`. Usada em dois contextos:
- Salvar os associados vinculados ao certificado (tabela `rel_ass_esc`).
- Salvar os produtos selecionados para o escopo (tabela `rel_esc_prod`).

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `p_tabela` | `text` | Tabela de junção (`"rel_ass_esc"` ou `"rel_esc_prod"`) |
| `p_coluna_fixa` | `text` | Coluna do lado fixo (sempre `"escopo_id"`) |
| `p_valor_fixo` | `integer` | ID do escopo |
| `p_ids_opostos` | `integer[]` | IDs que devem permanecer vinculados; lista vazia = remove todos |

**Retorna:** `void`

---

## 4. Dashboard do grupo — `/grupo`

### `painel_do_grupo`
**Arquivo:** `grupo_dashboard.py` · `grupoBase.obter_dados()`

Chamada ao entrar na tela do grupo. Retorna os dados gerais do grupo (nome, núcleo, coordenador, facilitador) e a lista completa de matrículas com seus escopos, validade e último movimento, que alimenta a tabela ordenável da tela.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `p_grupo_id` | `integer` | ID do grupo |

**Retorna:** `jsonb` com `dados_gerais` e `detalhe` (lista de matrículas).

> **Validade:** calculada como `data do último acontecimento tipo_id=1 + val_duracao meses − 1 dia`, usando o campo `val_duracao` do escopo.  
> **Último movimento:** último acontecimento com data ≤ hoje, qualquer tipo.

---

## 5. Editor de produtos — `/produtos`

### `fn_produtos_por_escopo`
**Arquivo:** `lista_produtos.py` · `dadosProdutos.atualizar_dados()`

Chamada ao entrar na tela de edição de produtos. Retorna **todos** os produtos disponíveis para o tipo de escopo, com o campo `incluso` indicando quais já estão vinculados ao escopo. A distinção em relação a `obter_produtos` é que esta função é para edição (mostra todos, com checkbox), enquanto `obter_produtos` é para leitura (mostra só os vinculados).

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `p_tipo` | `integer` | ID do tipo de escopo |
| `p_escopo_id` | `integer` | ID do escopo |

**Retorna:** `json` com `escopo` (metadados de identificação) e `grupos` — lista de `{ id, nome, produtos: [ { id, nome, incluso } ] }`.

---

## 6. Geração do certificado PDF

### `obter_dados_escopo`
**Arquivo:** `gerar_certificado.py` · `obterDados.obter_dados_capa()`

Chamada ao gerar o certificado (ou FRI). Retorna todos os dados necessários para a capa: informações da unidade de produção, tipo de escopo, data de emissão (último certificado emitido) e lista de associados com flag de vínculo. O Python valida os campos obrigatórios logo depois — se algum faltar, lança `ValueError` antes de iniciar o PDF.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `p_escopo_id` | `integer` | ID do escopo |

**Retorna:** `json` com `matricula`, `unidade_producao`, `endereco`, `municipio`, `estado`, `tipo_certificado`, `tipo_abreviatura`, `mensagem`, `data_emissao`, `associados`.

> **Campos obrigatórios validados em Python:** `matricula`, `unidade_producao`, `endereco`, `municipio`, `estado`, `tipo_certificado`, `data_emissao`.

---

## Resumo

| # | Função RPC | Operação | Quando é chamada |
|---|---|---|---|
| 1 | `dados_de_matricula` | Leitura | Ao abrir `/matricula` |
| 2 | `vincular_associado` | Escrita | Ao salvar novo associado |
| 3 | `eliminar_e_atualizar` | Escrita | Ao confirmar eliminação da matrícula |
| 4 | `preencher_formulario` | Leitura | Ao abrir qualquer `/formulario` |
| 5 | `salvar_formulario` | Escrita | Ao clicar "Salvar" no formulário |
| 6 | `obter_info_escopo` | Leitura | Ao montar o menu lateral do escopo |
| 7 | `obter_produtos` | Leitura | Ao abrir "Ver produtos" e ao gerar PDF |
| 8 | `obter_associados_por_escopo` | Leitura | Ao abrir "Editar nomes no certificado" |
| 9 | `atualizar_relacao_nm` | Escrita | Ao salvar nomes ou produtos do escopo |
| 10 | `painel_do_grupo` | Leitura | Ao abrir `/grupo` |
| 11 | `fn_produtos_por_escopo` | Leitura | Ao abrir `/produtos` (editor) |
| 12 | `obter_dados_escopo` | Leitura | Ao gerar certificado ou FRI |
