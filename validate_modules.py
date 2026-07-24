# -*- coding: utf-8 -*-
"""Valida los JSON de temas de saimap-teologia contra la especificación
del motor Duolingo (idéntica a saimap-idiomas/biblia, sin ejercicios speak).

Uso:  python validate_modules.py [carpeta_json ...]
Sin argumentos valida historia/json/1.1.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

EXPECTED = {"match": 4, "quiz": 9, "gap": 9, "wordbank": 8}
TOTAL = 30


def norm(s):
    s = s.lower()
    s = re.sub(r"[.,!?;:'\"«»“”‘’¿¡-]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def validate_exercise(ex, i):
    errs = []
    t = ex.get("type")
    if t == "match":
        pairs = ex.get("pairs", [])
        if len(pairs) != 5:
            errs.append(f"[{i}] match: {len(pairs)} parejas (deben ser 5)")
        for p in pairs:
            if not p.get("en") or not p.get("es"):
                errs.append(f"[{i}] match: pareja incompleta {p}")
    elif t == "quiz":
        opts = ex.get("options", [])
        if len(opts) != 3:
            errs.append(f"[{i}] quiz: {len(opts)} opciones (deben ser 3)")
        c = ex.get("correct")
        if not isinstance(c, int) or not 0 <= c <= 2:
            errs.append(f"[{i}] quiz: correct={c} inválido")
        if not ex.get("explanation"):
            errs.append(f"[{i}] quiz: falta explanation")
    elif t == "gap":
        text = ex.get("text", "")
        if text.count("___") != 1:
            errs.append(f"[{i}] gap: el texto debe contener exactamente un ___")
        opts = ex.get("options", [])
        if len(opts) != 3:
            errs.append(f"[{i}] gap: {len(opts)} opciones (deben ser 3)")
        if ex.get("answer") not in opts:
            errs.append(f"[{i}] gap: answer «{ex.get('answer')}» no está en options")
    elif t == "wordbank":
        answer_words = norm(ex.get("answer", "")).split(" ")
        tiles = [norm(w) for w in ex.get("tiles", [])]
        pool = list(tiles)
        for w in answer_words:
            if w in pool:
                pool.remove(w)
            elif w:
                errs.append(f"[{i}] wordbank: la palabra «{w}» de answer no está en tiles")
        if len(ex.get("tiles", [])) <= len([w for w in answer_words if w]):
            errs.append(f"[{i}] wordbank: no hay distractores (tiles <= palabras de answer)")
        if not ex.get("explanation"):
            errs.append(f"[{i}] wordbank: falta explanation")
    else:
        errs.append(f"[{i}] tipo desconocido: {t}")
    return errs


def validate_file(path):
    errs = []
    try:
        mod = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"JSON inválido: {e}"]
    for field in ("id", "module", "title", "subtitle"):
        if field not in mod:
            errs.append(f"falta el campo «{field}»")

    exs = mod.get("exercises")
    if exs is None:
        errs.append("falta el campo «exercises»")
    else:
        if len(exs) != TOTAL:
            errs.append(f"{len(exs)} ejercicios (deben ser {TOTAL})")
        counts = {}
        for i, ex in enumerate(exs):
            counts[ex.get("type")] = counts.get(ex.get("type"), 0) + 1
            errs.extend(validate_exercise(ex, i))
        for t, n in EXPECTED.items():
            if counts.get(t, 0) != n:
                errs.append(f"distribución: {t}={counts.get(t, 0)} (esperado {n})")
    return errs


def main():
    base = Path(__file__).parent / "historia" / "json"
    dirs = [Path(a) for a in sys.argv[1:]] or [base / "1.1"]
    total_files, bad = 0, 0
    for d in dirs:
        for f in sorted(d.glob("mod*.json")):
            total_files += 1
            errs = validate_file(f)
            if errs:
                bad += 1
                print(f"✗ {f.parent.name}/{f.name}")
                for e in errs[:12]:
                    print(f"    - {e}")
            else:
                print(f"✓ {f.parent.name}/{f.name}")
    print(f"\n{total_files - bad}/{total_files} archivos válidos")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
