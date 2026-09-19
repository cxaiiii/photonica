"""Validate community projects and build community/gallery.json (the list Photonica shows in Community > Browse).

    python tools/build_gallery.py          # validate, then write community/gallery.json
    python tools/build_gallery.py --check  # validate only (pull requests)
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "community" / "projects"
GALLERY = ROOT / "community" / "gallery.json"
RAW = "https://raw.githubusercontent.com/cxaiiii/photonica/main/community/projects/"
MAX_BYTES = 2 * 1024 * 1024


def text(d, key, limit):
    v = d.get(key, "")
    return v.strip()[:limit] if isinstance(v, str) else ""


def check(path):
    """Returns (entry, problems)."""
    problems = []
    if path.suffix != ".photonica":
        return None, [f"{path.name}: only .photonica files belong in community/projects"]
    if path.stat().st_size > MAX_BYTES:
        return None, [f"{path.name}: larger than 2 MB"]
    try:
        d = json.loads(path.read_text(encoding="utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return None, [f"{path.name}: not valid JSON ({e})"]
    if not isinstance(d, dict) or d.get("format") != "photonica-project":
        return None, [f"{path.name}: not a Photonica project (save it with File > Save in Photonica)"]
    title, author = text(d, "title", 120), text(d, "author", 80)
    if not title:
        problems.append(f"{path.name}: needs a title (File > Project info)")
    if not author:
        problems.append(f"{path.name}: needs an author (File > Project info)")
    elems = d.get("elements", [])
    if not isinstance(elems, list) or len(elems) > 200:
        problems.append(f"{path.name}: at most 200 parts")
    if not isinstance(d.get("screens", []), list) or len(d.get("screens", [])) > 4:
        problems.append(f"{path.name}: at most 4 screens")
    entry = {
        "title": title,
        "author": author,
        "description": text(d, "description", 400),
        "url": RAW + path.name,
        "parts": len(elems) if isinstance(elems, list) else 0,
    }
    return entry, problems


def main():
    only_check = "--check" in sys.argv
    entries, problems = [], []
    for p in sorted(PROJECTS.iterdir()):
        if p.is_dir() or p.name.startswith("."):
            continue
        e, pr = check(p)
        problems += pr
        if e and not pr:
            entries.append(e)
    for pr in problems:
        print("::error::" + pr)
    if problems:
        sys.exit(1)
    print(f"{len(entries)} projects OK")
    if only_check:
        return
    entries.sort(key=lambda e: e["title"].lower())
    gallery = {"format": "photonica-gallery", "version": 1, "projects": entries}
    GALLERY.write_text(json.dumps(gallery, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {GALLERY.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
