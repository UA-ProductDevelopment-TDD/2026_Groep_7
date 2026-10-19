#!/usr/bin/env python3
"""Controleer of paden tussen backticks in de .md-bestanden bestaan.

Gebruik: python3 scripts/check-verwijzingen.py
Slaat over: shared/bronnen/ (alleen-lezen), placeholders (<...>, *), lokaal/,
paden die nog niet bestaan door afspraak (concept/concept.md, prototype/).
Eén regel per kapotte verwijzing: bestand:regel  pad
"""
import re, subprocess, sys
from pathlib import Path

# beschrijven bewust wat er vroeger of in vorige jaren stond
HISTORISCH = {"STRUCTUUR.md", "BESLUITEN.md", "LOGBOEK.md", "shared/vorige-jaren/README.md"}
root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
files = [f for f in subprocess.check_output(["git", "ls-files", "*.md"], cwd=root, text=True).split()
         if not f.startswith("shared/bronnen/") and f not in HISTORISCH]
SKIP = ("oplevering/README.md", "simulation/test_bittle.py",  # bestaan (nog) niet, bewust
        "...", "<", "*", "lokaal/", "prototype/", "concept.md", "http", "$", "~")
bad = 0
for f in files:
    for n, line in enumerate((root / f).read_text(encoding="utf-8").splitlines(), 1):
        for tok in re.findall(r"`([^`\s]+)`", line):
            tok = tok.rstrip(".,;:")
            if tok.strip("/").count("/") == 0 and not tok.endswith(".md"):
                continue  # losse mapnaam of branchcode
            if tok.startswith(("--", "-")) or any(s in tok for s in SKIP):
                continue
            if not re.search(r"(/|\.(md|py|sh|zip|json))$", tok) or tok.startswith("."):
                if not tok.endswith(".md"):
                    continue
            # relatief aan de root, de map van het bestand, shared/ of shared/bronnen/
            kandidaten = [root / tok, root / Path(f).parent / tok,
                          root / "shared" / tok, root / "shared/bronnen" / tok]
            if not any(k.exists() for k in kandidaten):
                print(f"{f}:{n}  {tok}"); bad += 1
print(f"{bad} kapotte verwijzing(en)")
sys.exit(1 if bad else 0)
