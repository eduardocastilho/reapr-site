# Site do REAPR Labs

Site estático com a identidade "Evidence Record" aprovada na Phase 3. Os writeups e as ferramentas ficam em Markdown. A cada push na branch `main`, o GitHub gera o site e publica no GitHub Pages.

O conteúdo público fica em inglês, que é o idioma principal da marca. Este README é interno.

## Estrutura

```
content/
  writeups/     um .md por writeup (LAB, RL, MW ou NOTE)
  tools/        um .md por ferramenta
  pages/        páginas avulsas (about.md vira /about/)
templates/      HTML das páginas (Jinja2)
static/         CSS e favicon
site.yaml       nome, URL e links do rodapé
build.py        gera o site em dist/
```

Arquivos que começam com `_` são ignorados. Os dois `_TEMPLATE.md` são modelos para copiar.

## Publicar um writeup

1. Copie `content/writeups/_TEMPLATE.md` para um nome como `lab-2026-001-prefetch-timestamps.md`. Use só minúsculas, números e hífen.
2. Preencha o cabeçalho:
   - `id` segue o sistema da marca: `LAB-AAAA-NNN`, `RL-AAAA-NNN` ou `MW-AAAA-NNN`.
   - `kind` deve bater com o prefixo do `id`.
   - `date` é a data de publicação.
3. Escreva seguindo as seções do modelo: pergunta, ambiente, método, observações, interpretação, hipóteses alternativas, limitações e reprodução.
4. Enquanto `draft: true` estiver no cabeçalho, o writeup não aparece no site. Apague a linha quando ele estiver pronto.
5. Rode o checklist pré-publicação (abaixo), faça commit e push.

As ferramentas seguem o mesmo processo, usando `content/tools/_TEMPLATE.md`.

Imagens: coloque-as em `static/img/` e use `![descrição](/static/img/arquivo.png)`. Se o site estiver num subcaminho (veja `base_path`), inclua esse caminho no início do endereço.

## Ver localmente antes de publicar

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (no Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
python build.py --drafts        # inclui os rascunhos
python -m http.server -d dist 8000
```

Abra http://localhost:8000. O build para com uma mensagem clara se faltar algum campo ou se um `id` estiver fora do padrão ou repetido.

## Colocar no ar (GitHub Pages)

1. Crie uma organização ou conta no GitHub para o REAPR, por exemplo `reapr-labs`, se ainda não existir.
2. Crie um repositório público chamado `reapr-labs.github.io` e envie esta pasta para ele.
3. No repositório, vá em **Settings › Pages › Build and deployment** e escolha **Source: GitHub Actions**.
4. Faça um push na `main`. Em cerca de 1 minuto o site aparece em `https://reapr-labs.github.io`.

Se você usar outro nome de repositório, o site fica em `https://<conta>.github.io/<repo>/`. Nesse caso, ajuste `base_path: "/<repo>"` no `site.yaml`.

### Domínio próprio (depois)

Quando o domínio estiver registrado:

1. Crie um arquivo `CNAME` na raiz do projeto, contendo só o domínio (por exemplo `reapr.com.br`). O build copia esse arquivo para o site.
2. Em **Settings › Pages › Custom domain**, informe o mesmo domínio. No registro do domínio, aponte o DNS para o GitHub Pages, conforme a documentação do GitHub.
3. Atualize `url` no `site.yaml` e mantenha `base_path: ""`.

## Antes de publicar qualquer coisa

Este checklist segue o contexto do estágio atual:

- [ ] Nada veio do empregador: dados, casos, clientes, ferramentas, licenças, infraestrutura ou horário de trabalho.
- [ ] O ambiente é um lab próprio, e os datasets e amostras são públicos (com link).
- [ ] Nenhum dado identificável de incidente real.
- [ ] Observação, interpretação e hipótese estão separadas, e as limitações estão escritas.
- [ ] As versões das ferramentas estão fixadas, e o método é reproduzível.
- [ ] O texto não sugere serviço, preço ou disponibilidade para atender incidentes.
- [ ] Antes do primeiro lançamento público: cláusulas de PI e atividades paralelas do contrato de trabalho verificadas, e checagem básica da marca (INPI).
