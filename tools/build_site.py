#!/usr/bin/env python3
"""Rebuild the PosiTTron archive site from the Wayback Machine snapshots."""

import html as html_mod
import os
import re
import shutil
from bs4 import BeautifulSoup, Comment, NavigableString, Tag

SRC = os.environ.get("POSITTRON_SRC", "/tmp/posittron_research")
OUT = os.environ.get("POSITTRON_OUT", "/projects/posittron-archive")

IMAGE_MAP = {
    "Truncatedhexahedron_resized.png": "01-truncated-cube-diagram.png",
    "JPEG Image (978128)-c.jpg": "02-paper-and-foam-mockups.jpg",
    "JPEG Image (986569)-c.jpg": "03-power-supply-led-test.jpg",
    "JPEG Image (990506)-c.jpg": "04-panels-cut-out.jpg",
    "JPEG Image (991703)-c.jpg": "05-leds-soldered.jpg",
    "JPEG Image (992486)-c.jpg": "06-wiring-inside.jpg",
    "JPEG Image (1022195)-d.jpg": "07-finished-prototype.jpg",
    "JPEG Image (1023675)-d.jpg": "08-prototype-front-lit.jpg",
    "JPEG Image (1023674)-c.jpg": "09-prototype-angled-lit.jpg",
    "P3P.jpg": "10-p3p-diagram.jpg",
    "01-Positron-MIX.jpg": "11-design-a-posittron.jpg",
    "02- Hugger-MIX.jpg": "12-design-b-rift-hugger.jpg",
    "03- Rift_n_Hugger-MIX.jpg": "13-design-c-rift-and-hugger.jpg",
    "Posittron-experiment.jpg": "14-concept-render.jpg",
    "3d-print.jpg": "15-3d-printed-part.jpg",
}

LOCAL_SOURCE = {
    "01-truncated-cube-diagram.png": "11_Truncatedhexahedron_resized.png",
    "02-paper-and-foam-mockups.jpg": "4_JPEG_Image_(978128)-c.jpg",
    "03-power-supply-led-test.jpg": "17_JPEG_Image_(986569)-c.jpg",
    "04-panels-cut-out.jpg": "5_JPEG_Image_(990506)-c.jpg",
    "05-leds-soldered.jpg": "9_JPEG_Image_(991703)-c.jpg",
    "06-wiring-inside.jpg": "12_JPEG_Image_(992486)-c.jpg",
    "07-finished-prototype.jpg": "8_JPEG_Image_(1022195)-d.jpg",
    "08-prototype-front-lit.jpg": "15_JPEG_Image_(1023675)-d.jpg",
    "09-prototype-angled-lit.jpg": "14_JPEG_Image_(1023674)-c.jpg",
    "10-p3p-diagram.jpg": "16_P3P.jpg",
    "11-design-a-posittron.jpg": "13_01-Positron-MIX.jpg",
    "12-design-b-rift-hugger.jpg": "7_02-_Hugger-MIX.jpg",
    "13-design-c-rift-and-hugger.jpg": "10_03-_Rift_n_Hugger-MIX.jpg",
    "14-concept-render.jpg": "6_Posittron-experiment.jpg",
    "15-3d-printed-part.jpg": "18_3d-print.jpg",
}

ALT = {
    "01-truncated-cube-diagram.png": "Diagram of a truncated cube (truncated hexahedron)",
    "02-paper-and-foam-mockups.jpg": "Paper mockup of the truncated cube next to the black foam prototype on a cardboard stand",
    "03-power-supply-led-test.jpg": "LED driver power supply wired to a black panel with four LEDs, on a workbench",
    "04-panels-cut-out.jpg": "The individual black panels of the truncated-cube shell, cut out and laid flat",
    "05-leds-soldered.jpg": "Panels with LEDs and resistors soldered in place, next to a soldering station",
    "06-wiring-inside.jpg": "Inside view of the shell being assembled, showing the wiring loom taped to each panel",
    "07-finished-prototype.jpg": "The finished lit prototype next to the smaller paper reference cube",
    "08-prototype-front-lit.jpg": "Front view of the prototype in the dark with red, blue and white LEDs lit",
    "09-prototype-angled-lit.jpg": "Angled view of the lit prototype showing markers of several colours at once",
    "10-p3p-diagram.jpg": "Diagram illustrating the P3P pose-estimation ambiguity problem",
    "11-design-a-posittron.jpg": "Renders of the full PosiTTron HMD concept with front and rear marker modules",
    "12-design-b-rift-hugger.jpg": "Renders of the Rift-Hugger add-on concept",
    "13-design-c-rift-and-hugger.jpg": "Renders of the Rift-Hugger fitted around an existing Oculus Rift",
    "14-concept-render.jpg": "Concept render of the tracking HMD worn on a head, seen from the side",
    "15-3d-printed-part.jpg": "3D model of a printable housing part for the tracker",
}

DIMS = {
    "01-truncated-cube-diagram.png": (288, 300),
    "02-paper-and-foam-mockups.jpg": (500, 309),
    "03-power-supply-led-test.jpg": (800, 600),
    "04-panels-cut-out.jpg": (800, 600),
    "05-leds-soldered.jpg": (800, 600),
    "06-wiring-inside.jpg": (800, 600),
    "07-finished-prototype.jpg": (800, 470),
    "08-prototype-front-lit.jpg": (800, 570),
    "09-prototype-angled-lit.jpg": (800, 570),
    "10-p3p-diagram.jpg": (800, 474),
    "11-design-a-posittron.jpg": (1200, 800),
    "12-design-b-rift-hugger.jpg": (1200, 800),
    "13-design-c-rift-and-hugger.jpg": (1200, 800),
    "14-concept-render.jpg": (400, 400),
    "15-3d-printed-part.jpg": (800, 600),
}

VIDEOS = [
    ("EzC-HDpv2xw", "PosiTTron: 6 DOF head-tracking prototype for VR - 01"),
    ("nsl43qbMnOA", "PosiTTron: 6 DOF head-tracking prototype for VR - 02"),
]

WB = re.compile(r"^https?://web\.archive\.org/web/\d+[a-z_]*/")


def unwrap(url):
    url = WB.sub("", url or "")
    if url.startswith("./"):
        url = "https://www.mtbs3d.com/phpBB/" + url[2:]
    return url


def basename(src):
    src = unwrap(src).split("?")[0]
    name = src.rsplit("/", 1)[-1]
    from urllib.parse import unquote
    return unquote(name)


def esc(s):
    return html_mod.escape(s, quote=False)


def inline(node):
    """Render an inline node to safe HTML."""
    if isinstance(node, Comment):
        return ""  # phpBB wraps magic URLs in <!-- m --> markers
    if isinstance(node, NavigableString):
        return esc(str(node))
    if not isinstance(node, Tag):
        return ""
    if node.name == "br":
        return "<br>"
    if node.name == "img":
        return ""  # smilies
    if node.name == "a":
        href = unwrap(node.get("href", ""))
        text = "".join(inline(c) for c in node.children) or esc(href)
        return f'<a href="{html_mod.escape(href)}" target="_blank" rel="noopener">{text}</a>'
    if node.name == "span":
        style = node.get("style", "")
        inner = "".join(inline(c) for c in node.children)
        if "bold" in style:
            return f"<strong>{inner}</strong>"
        if "italic" in style:
            return f"<em>{inner}</em>"
        if "underline" in style:
            return f"<u>{inner}</u>"
        return inner
    if node.name in ("b", "strong"):
        return "<strong>" + "".join(inline(c) for c in node.children) + "</strong>"
    if node.name in ("i", "em"):
        return "<em>" + "".join(inline(c) for c in node.children) + "</em>"
    return "".join(inline(c) for c in node.children)


def as_pre(node):
    """Inline content of a node with <br> turned into real line breaks."""
    raw = "".join(inline(c) for c in node.children).replace("<br>", "\n")
    return "\n".join(l.rstrip() for l in raw.split("\n")).strip("\n")


def is_content_img(node):
    src = node.get("src", "")
    return "smilies" not in src and "imageset" not in src and "styles/" not in src


def convert(postbody):
    """Turn a phpBB postbody into a list of (kind, payload) blocks."""
    blocks, buf, brs = [], [], 0

    def flush():
        nonlocal buf
        txt = "".join(buf).strip()
        if txt:
            blocks.append(("p", txt))
        buf = []

    for node in postbody.children:
        if isinstance(node, Tag) and node.name == "br":
            brs += 1
            if brs >= 2:
                flush()
            elif buf:
                buf.append("<br>")
            continue

        if isinstance(node, Tag) and node.name == "img":
            if is_content_img(node):
                brs = 0
                flush()
                name = IMAGE_MAP.get(basename(node["src"]))
                if name:
                    blocks.append(("img", name))
                continue
            brs = 0
            continue

        if isinstance(node, Tag) and node.name in ("ul", "ol"):
            brs = 0
            flush()
            lis = node.find_all("li", recursive=False)
            if lis:
                items = ["<li>" + "".join(inline(c) for c in li.children).strip() + "</li>"
                         for li in lis]
                blocks.append(("list", f"<{node.name}>" + "".join(items) + f"</{node.name}>"))
            else:
                # phpBB let people post <ul> blocks with no <li> at all: the body is
                # space-aligned plain text, so keep it monospaced instead of dropping it.
                text = as_pre(node)
                if text.strip():
                    blocks.append(("pre", text))
            continue

        if isinstance(node, Tag) and node.name == "dl":
            brs = 0
            flush()
            code = node.find("dd")
            if code is not None:
                text = as_pre(code)
                if text.strip():
                    blocks.append(("pre", text))
            continue

        if isinstance(node, Tag) and node.name in ("object", "embed", "iframe"):
            brs = 0
            flush()
            raw = str(node)
            m = re.search(r"youtube\.com/v/([A-Za-z0-9_-]{6,15})", raw)
            if m and not any(k == "video" and v == m.group(1) for k, v in blocks):
                blocks.append(("video", m.group(1)))
            continue

        if isinstance(node, Tag) and node.name == "div" and "quotewrapper" in (node.get("class") or []):
            brs = 0
            flush()
            title = node.select_one(".quotetitle")
            body = node.select_one(".quotecontent")
            who = title.get_text(strip=True).replace(" wrote:", "") if title else ""
            text = "".join(inline(c) for c in body.children).strip() if body else ""
            blocks.append(("quote", (who, text)))
            continue

        if isinstance(node, Tag) and node.name == "blockquote":
            brs = 0
            flush()
            cite = node.select_one("cite")
            who = cite.get_text(strip=True).replace(" wrote:", "") if cite else ""
            if cite:
                cite.extract()
            blocks.append(("quote", (who, "".join(inline(c) for c in node.children).strip())))
            continue

        piece = inline(node)
        if piece.strip():
            brs = 0
        buf.append(piece)

    flush()
    return blocks


def render(blocks):
    """Render blocks to HTML, promoting short all-bold paragraphs to headings."""
    out = []
    for kind, payload in blocks:
        if kind == "p":
            payload = re.sub(r"(?:<br>\s*)+$", "", payload.strip())
            plain = re.sub(r"<[^>]+>", "", payload).strip()
            if not plain:
                continue
            if re.fullmatch(r"[-–—_=\s]{8,}", plain):
                out.append("<hr>")
                continue
            m = re.fullmatch(r"<strong>(.*?)</strong>", payload, re.S)
            if m and len(plain) < 90:
                out.append(f"<h3>{m.group(1).strip()}</h3>")
                continue
            out.append(f"<p>{payload}</p>")
        elif kind == "img":
            cap = ALT.get(payload, "")
            w, h = DIMS.get(payload, (None, None))
            size = f' width="{w}" height="{h}"' if w else ""
            out.append(
                f'<figure><a href="images/{payload}" target="_blank" rel="noopener">'
                f'<img src="images/{payload}" alt="{html_mod.escape(cap)}"{size} decoding="async"></a>'
                f'<figcaption>{esc(cap)}</figcaption></figure>'
            )
        elif kind == "video":
            title = dict(VIDEOS).get(payload, "Video")
            out.append(
                f'<figure class="video"><div class="video-frame">'
                f'<iframe src="https://www.youtube-nocookie.com/embed/{payload}" '
                f'title="{html_mod.escape(title)}" loading="lazy" allowfullscreen '
                f'referrerpolicy="strict-origin-when-cross-origin"></iframe></div>'
                f'<figcaption>{esc(title)} &middot; '
                f'<a href="https://www.youtube.com/watch?v={payload}" target="_blank" rel="noopener">'
                f'watch on YouTube</a></figcaption></figure>'
            )
        elif kind == "list":
            out.append(payload)
        elif kind == "pre":
            out.append(f'<pre class="ascii">{payload}</pre>')
        elif kind == "quote":
            who, text = payload
            cite = f"<cite>{esc(who)} wrote:</cite>" if who else ""
            out.append(f"<blockquote>{cite}{text}</blockquote>")
    return "\n".join(out)


def load_posts(path, pattern):
    with open(path, encoding="utf-8", errors="replace") as f:
        raw = f.read()
    parts = re.split(pattern, raw)
    posts = []
    for i in range(1, len(parts) - 1, 2):
        pid = re.search(r"p\d+", parts[i]).group(0)
        soup = BeautifulSoup(parts[i + 1], "html.parser")
        body = soup.select_one(".postbody .content") or soup.select_one(".postbody") \
            or soup.select_one(".content")
        author = soup.select_one(".postauthor") or soup.select_one(".username") \
            or soup.select_one(".username-coloured")
        bottom = soup.select_one(".postbottom")
        date = bottom.get_text(strip=True) if bottom else None
        if date is None:
            ap = soup.select_one(".author")
            if ap:
                m = re.search(r"»\s*(.+)", ap.get_text(" ", strip=True))
                date = m.group(1).strip() if m else None
        posts.append({
            "id": pid,
            "author": author.get_text(strip=True) if author else "unknown",
            "date": date,
            "body": body,
        })
    return posts


def main():

    os.makedirs(f"{OUT}/images", exist_ok=True)
    os.makedirs(f"{OUT}/sources/raw-html", exist_ok=True)

    for new, old in LOCAL_SOURCE.items():
        shutil.copy2(f"{SRC}/images/{old}", f"{OUT}/images/{new}")

    for f in ["mtbs3d_2013.html", "mtbs3d_page2.html", "mtbs3d_page3.html", "oculus_2015.html"]:
        shutil.copy2(f"{SRC}/{f}", f"{OUT}/sources/raw-html/{f}")

    shutil.copy2(f"{SRC}/mtbs3d_FULL_THREAD.txt", f"{OUT}/sources/mtbs3d-thread-full.txt")
    shutil.copy2(f"{SRC}/oculus_sun_temple_thread.txt", f"{OUT}/sources/oculus-thread-full.txt")
    shutil.copy2(f"{SRC}/sun_temple_README.txt", f"{OUT}/sources/sun-temple-mod-README.txt")

    mtbs = load_posts(f"{SRC}/mtbs3d_2013.html", r'(<a name="p\d+"[^>]*></a>)')
    ocu = load_posts(f"{SRC}/oculus_2015.html", r'(<[^>]+id="p\d+"[^>]*>)')

    mtbs2 = load_posts(f"{SRC}/mtbs3d_page2.html", r'(<a name="p\d+"[^>]*></a>)')
    by_id = {p["id"]: p for p in mtbs + mtbs2}

    posittron_html = render(convert(mtbs[0]["body"]))
    suntemple_html = render(convert(ocu[0]["body"]))

    followups = []
    for pid in ["p93912", "p95701", "p99624"]:
        p = by_id[pid]
        followups.append({
            "id": pid,
            "date": p["date"],
            "html": render(convert(p["body"])),
        })

    with open(f"{SRC}/sun_temple_README.txt", encoding="utf-8") as f:
        readme_txt = f.read().strip()

    with open(f"{SRC}/site_fragments.py", "w", encoding="utf-8") as f:
        f.write("POSITTRON = " + repr(posittron_html) + "\n")
        f.write("SUNTEMPLE = " + repr(suntemple_html) + "\n")
        f.write("FOLLOWUPS = " + repr(followups) + "\n")
        f.write("README_TXT = " + repr(readme_txt) + "\n")

    print("posittron:", posittron_html.count("<p>"), "paragraphs,",
          posittron_html.count("<figure>"), "figures,", posittron_html.count("<h3>"), "headings,",
          posittron_html.count("<blockquote>"), "quotes")
    print("suntemple:", suntemple_html.count("<p>"), "paragraphs,",
          suntemple_html.count("<h3>"), "headings")
    for f_ in followups:
        print("  followup", f_["id"], f_["date"], "|", f_["html"].count("<p>"), "p,",
              f_["html"].count("<figure>"), "fig")
    print("images copied:", len(os.listdir(f"{OUT}/images")))


if __name__ == "__main__":
    main()
