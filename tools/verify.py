#!/usr/bin/env python3
"""Check that the rendered page reproduces the source posts without dropping text."""

import difflib
import re
from bs4 import BeautifulSoup

import build_site as B


def words(text):
    text = text.replace(" ", " ")
    return re.findall(r"[^\s]+", text)


def rendered_text(fragment):
    soup = BeautifulSoup(fragment, "html.parser")
    for fc in soup.select("figcaption"):
        fc.decompose()  # captions are ours, not the author's
    return soup.get_text(" ")


def source_text(postbody):
    soup = BeautifulSoup(str(postbody), "html.parser")
    for img in soup.find_all("img"):
        img.decompose()
    for obj in soup.find_all(["object", "embed", "param", "script"]):
        obj.decompose()
    return soup.get_text(" ")


def compare(label, postbody, fragment):
    src = words(source_text(postbody))
    got = words(rendered_text(fragment))
    sm = difflib.SequenceMatcher(None, src, got, autojunk=False)
    missing, added = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("delete", "replace"):
            missing.append(" ".join(src[i1:i2]))
        if tag in ("insert", "replace"):
            added.append(" ".join(got[j1:j2]))
    # Deliberate transformations, not lost content:
    #   long ---- rules become <hr>; "Code: Select all" is phpBB's own UI chrome.
    def expected(s):
        s = s.strip()
        return not s or set(s) <= set("-–—_= ") or s == "Code: Select all"

    missing = [m for m in missing if not expected(m)]
    added = [a for a in added if a.strip()]
    ratio = sm.ratio()
    print(f"--- {label}: {len(src)} source words, {len(got)} rendered, "
          f"similarity {ratio:.4f}")
    for m in missing:
        print(f"    MISSING: {m[:300]!r}")
    for a in added:
        print(f"    ADDED  : {a[:300]!r}")
    if not missing and not added:
        print("    exact match")
    return not missing


mtbs = B.load_posts(f"{B.SRC}/mtbs3d_2013.html", r'(<a name="p\d+"[^>]*></a>)')
mtbs2 = B.load_posts(f"{B.SRC}/mtbs3d_page2.html", r'(<a name="p\d+"[^>]*></a>)')
ocu = B.load_posts(f"{B.SRC}/oculus_2015.html", r'(<[^>]+id="p\d+"[^>]*>)')
by_id = {p["id"]: p for p in mtbs + mtbs2}

ok = True
ok &= compare("PosiTTron main post", mtbs[0]["body"], B.render(B.convert(mtbs[0]["body"])))
ok &= compare("Sun Temple main post", ocu[0]["body"], B.render(B.convert(ocu[0]["body"])))
for pid in ["p93912", "p95701", "p99624"]:
    p = by_id[pid]
    ok &= compare(f"follow-up {pid}", p["body"], B.render(B.convert(p["body"])))

print()
print("RESULT:", "no text lost" if ok else "TEXT LOST — see MISSING above")
