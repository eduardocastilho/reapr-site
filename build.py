#!/usr/bin/env python3
"""Gera o site estático do REAPR Labs a partir de content/ para dist/.

Uso:
    python build.py            # gera dist/
    python build.py --drafts   # inclui rascunhos (draft: true), para prévia local
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
DIST = ROOT / "dist"

FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.S)
SLUG_OK = re.compile(r"^[a-z0-9][a-z0-9-]*$")

# Tipos de publicação e o prefixo de ID esperado (sistema de IDs da marca).
KINDS = {
    "LAB": "Case study",
    "RL": "Research",
    "MW": "Malware analysis",
    "NOTE": "Lab note",
}


class BuildError(Exception):
    pass


@dataclass
class Entry:
    section: str            # "writeups" | "tools" | "pages"
    slug: str
    meta: dict
    body_html: str
    toc_html: str = ""
    source: Path | None = None
    url: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def date(self) -> dt.date | None:
        d = self.meta.get("date")
        if isinstance(d, dt.datetime):
            return d.date()
        if isinstance(d, dt.date):
            return d
        if isinstance(d, str) and d:
            return dt.date.fromisoformat(d)
        return None


def read_entry(path: Path, section: str) -> Entry:
    text = path.read_text(encoding="utf-8")
    m = FRONT_MATTER.match(text)
    if not m:
        raise BuildError(f"{path}: falta o cabeçalho '---' com os metadados")
    meta = yaml.safe_load(m.group(1)) or {}
    if not isinstance(meta, dict):
        raise BuildError(f"{path}: cabeçalho inválido")
    slug = path.stem
    if not SLUG_OK.match(slug):
        raise BuildError(
            f"{path}: nome de arquivo inválido. Use minúsculas, números e hífen (ex.: lab-2026-001-prefetch.md)"
        )
    if not meta.get("title"):
        raise BuildError(f"{path}: 'title' é obrigatório")

    md = markdown.Markdown(
        extensions=["fenced_code", "tables", "footnotes", "attr_list", "def_list", "toc", "sane_lists"],
        extension_configs={"toc": {"permalink": False, "toc_depth": "2-3"}},
        output_format="html",
    )
    body = md.convert(m.group(2))
    entry = Entry(section=section, slug=slug, meta=meta, body_html=body, toc_html=md.toc, source=path)

    if section == "writeups":
        kind = str(meta.get("kind", "")).upper()
        if kind not in KINDS:
            raise BuildError(f"{path}: 'kind' deve ser um de {', '.join(KINDS)}")
        meta["kind"] = kind
        meta["kind_label"] = KINDS[kind]
        if kind != "NOTE":
            rid = str(meta.get("id", ""))
            if not re.fullmatch(rf"{kind}-\d{{4}}-\d{{3}}", rid):
                raise BuildError(f"{path}: 'id' deve seguir {kind}-AAAA-NNN (ex.: {kind}-2026-001)")
        if entry.date is None:
            raise BuildError(f"{path}: 'date' é obrigatório (AAAA-MM-DD)")
    if section == "tools":
        meta.setdefault("status", "In development")
    return entry


def load_section(section: str, include_drafts: bool) -> list[Entry]:
    folder = CONTENT / section
    if not folder.exists():
        return []
    entries = []
    for path in sorted(folder.glob("*.md")):
        if path.name.startswith("_"):  # modelos e arquivos ignorados
            continue
        e = read_entry(path, section)
        if e.meta.get("draft") and not include_drafts:
            continue
        entries.append(e)
    return entries


def build(include_drafts: bool = False) -> int:
    cfg = yaml.safe_load((ROOT / "site.yaml").read_text(encoding="utf-8")) or {}
    base = str(cfg.get("base_path") or "").rstrip("/")
    cfg["base_path"] = base

    writeups = load_section("writeups", include_drafts)
    writeups.sort(key=lambda e: (e.date or dt.date.min, e.meta.get("id", "")), reverse=True)
    tools = load_section("tools", include_drafts)
    tools.sort(key=lambda e: str(e.meta.get("title", "")).lower())
    pages = load_section("pages", include_drafts)

    for e in writeups:
        e.url = f"{base}/writeups/{e.slug}/"
    for e in tools:
        e.url = f"{base}/tools/{e.slug}/"
    for e in pages:
        e.url = f"{base}/{e.slug}/"

    ids = [e.meta.get("id") for e in writeups if e.meta.get("id")]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise BuildError(f"IDs repetidos: {', '.join(sorted(dupes))}")

    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=True,
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["isodate"] = lambda d: d.isoformat() if d else ""

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    shutil.copytree(STATIC, DIST / "static")

    common = {
        "site": cfg,
        "base": base,
        "year": dt.date.today().year,
        "build_date": dt.date.today().isoformat(),
    }

    def render(template: str, out: str, **ctx) -> None:
        target = DIST / out
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(env.get_template(template).render(**common, **ctx), encoding="utf-8")

    render("home.html", "index.html", writeups=writeups[:8], tools=tools, nav="home")
    render("list.html", "writeups/index.html", nav="writeups", heading="Writeups",
           intro="Lab notes, case studies and malware analysis. Each one states its question, environment, method and limitations.",
           entries=writeups, empty="The first writeups are on their way.")
    render("list.html", "tools/index.html", nav="tools", heading="Tools",
           intro="Small open-source tools built for the lab work, released with documentation.",
           entries=tools, empty="The first tool is in development.")
    for e in writeups:
        render("entry.html", f"writeups/{e.slug}/index.html", e=e, nav="writeups")
    for e in tools:
        render("entry.html", f"tools/{e.slug}/index.html", e=e, nav="tools")
    for e in pages:
        render("page.html", f"{e.slug}/index.html", e=e, nav=e.slug)
    render("404.html", "404.html", nav="")

    # Feed Atom simples para os writeups.
    render("feed.xml", "feed.xml", writeups=writeups)
    (DIST / ".nojekyll").write_text("", encoding="utf-8")
    # Domínio próprio: se existir um arquivo CNAME na raiz do projeto, ele vai para a raiz do site.
    if (ROOT / "CNAME").exists():
        shutil.copy(ROOT / "CNAME", DIST / "CNAME")

    print(f"ok: {len(writeups)} writeup(s), {len(tools)} ferramenta(s), {len(pages)} página(s) -> {DIST}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--drafts", action="store_true", help="inclui rascunhos (draft: true)")
    args = ap.parse_args()
    try:
        return build(include_drafts=args.drafts)
    except BuildError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
