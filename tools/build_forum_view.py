#!/usr/bin/env python3
"""Build the full-forum pages: index.html (a hub linking to the two threads),
posittron.html (the MTBS3D thread) and sun-temple.html (the Oculus thread),
every post, every avatar and every inline image, reproduced as they looked
on the forum.

This is the main entry point of the site. Unlike render_page.py (which
renders only Jordi Batalle's own posts into a clean article, as archive.html)
this renders *all* posts from all authors, downloading every avatar and
content image referenced so the pages have no external dependency.
"""

import html as html_mod
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

sys.path.insert(0, os.path.dirname(__file__))
import build_site as B  # reuse inline(), as_pre(), unwrap(), esc()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "sources", "raw-html")
IMAGES = os.path.join(ROOT, "images")
AVATAR_DIR = os.path.join(IMAGES, "avatars")
THREAD_DIR = os.path.join(IMAGES, "thread")
OUT_HUB = os.path.join(ROOT, "index.html")
OUT_POSITTRON = os.path.join(ROOT, "posittron.html")
OUT_SUNTEMPLE = os.path.join(ROOT, "sun-temple.html")

WAYBACK_HOST = re.compile(r"^https?://web\.archive\.org")
WAYBACK_TS = re.compile(r"^/web/\d+[a-z_]*/")

SKIP_IMG_SUBSTR = (
    "smilies", "imageset", "styles/", "avw.php", "static/images/",
    "images/ranks", "spacer.gif", "blank.gif",
)

# Already downloaded for the curated article: reuse instead of re-fetching.
CURATED_BY_BASENAME = {os.path.basename(v).split("?")[0].lower(): k
                        for k, v in {
    "01-truncated-cube-diagram.png": "Truncatedhexahedron_resized.png",
    "02-paper-and-foam-mockups.jpg": "JPEG Image (978128)-c.jpg",
    "03-power-supply-led-test.jpg": "JPEG Image (986569)-c.jpg",
    "04-panels-cut-out.jpg": "JPEG Image (990506)-c.jpg",
    "05-leds-soldered.jpg": "JPEG Image (991703)-c.jpg",
    "06-wiring-inside.jpg": "JPEG Image (992486)-c.jpg",
    "07-finished-prototype.jpg": "JPEG Image (1022195)-d.jpg",
    "08-prototype-front-lit.jpg": "JPEG Image (1023675)-d.jpg",
    "09-prototype-angled-lit.jpg": "JPEG Image (1023674)-c.jpg",
    "10-p3p-diagram.jpg": "P3P.jpg",
    "11-design-a-posittron.jpg": "01-Positron-MIX.jpg",
    "12-design-b-rift-hugger.jpg": "02- Hugger-MIX.jpg",
    "13-design-c-rift-and-hugger.jpg": "03- Rift_n_Hugger-MIX.jpg",
    "14-concept-render.jpg": "Posittron-experiment.jpg",
    "15-3d-printed-part.jpg": "3d-print.jpg",
}.items()}

VIDEOS = {
    "EzC-HDpv2xw": "PosiTTron: 6 DOF head-tracking prototype for VR - 01",
    "nsl43qbMnOA": "PosiTTron: 6 DOF head-tracking prototype for VR - 02",
}

SMILIES = {
    "icon_e_smile": "\U0001F642",     # :)
    "icon_e_biggrin": "\U0001F600",   # :D
    "icon_razz": "\U0001F61B",        # :-P
    "icon_lol": "\U0001F602",         # :lol:
    "icon_cool": "\U0001F60E",        # 8-)
    "icon_mrgreen": "\U0001F606",     # :mrgreen:
    "icon_idea": "\U0001F4A1",        # :idea:
    "icon_cry": "\U0001F622",         # :cry:
    "icon_sad": "\U0001F61E",         # :(
    "icon_wink": "\U0001F609",        # ;)
    "icon_neutral": "\U0001F610",     # :|
    "icon_surprised": "\U0001F62E",   # :o
    "icon_confused": "\U0001F615",    # :?
    "icon_exclaim": "❗",         # :!:
}

_avatar_cache = {}
_image_cache = {}
_counter = [0]

# Confirmed via the Wayback availability API to have zero snapshots at any
# timestamp, not just a rate-limit hiccup: no point retrying these.
KNOWN_UNRECOVERABLE = {
    "https://forums.oculus.com/download/file.php?avatar=163637_1418182409.png",
    "https://forums.oculus.com/download/file.php?avatar=14582_1414534557.png",
}


def fetch(url, dest, retries=6, backoff=3):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            with open(dest, "wb") as f:
                f.write(data)
            time.sleep(1.2)  # archive.org throttles bursts of requests
            return len(data)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_err = e
            time.sleep(backoff * (attempt + 1))
    raise last_err


def to_wayback_absolute(src, page_ts):
    """Turn a (possibly host-relative) wayback src into an absolute fetch URL."""
    if src.startswith("//"):
        src = "https:" + src
    if WAYBACK_HOST.match(src):
        return src
    if src.startswith("/web/"):
        return "https://web.archive.org" + src
    if src.startswith("/"):
        return f"https://web.archive.org/web/{page_ts}im_" + src
    return f"https://web.archive.org/web/{page_ts}im_/{src}"


WAYBACK_ANY = re.compile(r"/web/\d+[a-z_]*/(https?://.*)$")


def canonical_url(src):
    """Strip the wayback wrapper regardless of whether src is host-relative
    (/web/TS_/http://...) or already absolute (https://web.archive.org/web/TS_/http://...).
    """
    m = WAYBACK_ANY.search(src or "")
    return m.group(1) if m else B.unwrap(src)


def safe_name(name):
    name = urllib.parse.unquote(name.split("?")[0])
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")
    return name or "image"


def resolve_avatar(src, page_ts):
    if not src:
        return None
    real = canonical_url(src)
    key = real.lower()
    if key in _avatar_cache:
        return _avatar_cache[key]
    if real in KNOWN_UNRECOVERABLE:
        _avatar_cache[key] = None
        return None
    fname = safe_name(os.path.basename(urllib.parse.urlparse(real).path) or "avatar")
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(real).query)
    if "avatar" in qs:
        fname = safe_name(qs["avatar"][0])
        if "." not in fname:
            fname += ".jpg"
    dest = os.path.join(AVATAR_DIR, fname)
    rel = f"images/avatars/{fname}"
    if not os.path.exists(dest):
        url = to_wayback_absolute(src, page_ts)
        try:
            fetch(url, dest)
            print("  avatar:", fname)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print("  ! avatar failed:", url, e)
            _avatar_cache[key] = None
            return None
    _avatar_cache[key] = rel
    return rel


def resolve_content_image(src, page_ts):
    real = canonical_url(src)
    key = real.lower().split("#")[0]
    if key in _image_cache:
        return _image_cache[key]
    raw_base = urllib.parse.unquote(os.path.basename(urllib.parse.urlparse(real).path))
    curated = CURATED_BY_BASENAME.get(raw_base.lower())
    base = safe_name(raw_base)
    if curated:
        rel = f"images/{curated}"
        _image_cache[key] = rel
        return rel
    _counter[0] += 1
    fname = f"{_counter[0]:02d}-{base}"
    dest = os.path.join(THREAD_DIR, fname)
    rel = f"images/thread/{fname}"
    if not os.path.exists(dest):
        url = to_wayback_absolute(src, page_ts)
        try:
            fetch(url, dest)
            print("  image:", fname)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print("  ! image failed:", url, "->", e)
            _image_cache[key] = None
            return None
    _image_cache[key] = rel
    return rel


def is_content_img(node):
    src = node.get("src", "")
    return not any(s in src for s in SKIP_IMG_SUBSTR)


BULLET_LINE = re.compile(r"^\s*(?:[-*]|\d+[-.)])\s*\S")
COLUMN_GAP = re.compile(r"\S {3,}\S")


def pseudo_list_block(text):
    """phpBB let people post a <ul>/<ol> with no real <li> children: just
    space-aligned plain text. Tables (aligned columns) stay monospaced;
    simple one-marker-per-line bullets become a real wrapping list instead
    of forcing a horizontal scrollbar on long lines.
    """
    lines = [l for l in text.split("\n") if l.strip()]
    if any(COLUMN_GAP.search(l) for l in lines):
        return ("pre", text)
    if lines and all(BULLET_LINE.match(l) for l in lines):
        items = [re.sub(r"^\s*(?:[-*]|\d+[-.)])\s*", "", l).strip() for l in lines]
        return ("list", "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>")
    return ("p", "<br>".join(lines))


def convert(postbody, page_ts):
    """phpBB postbody -> list of (kind, payload) blocks, generalised to any author."""
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
                rel = resolve_content_image(node.get("src", ""), page_ts)
                if rel:
                    blocks.append(("img", rel))
                continue
            if "smilies" in node.get("src", ""):
                stem = os.path.splitext(os.path.basename(node["src"]))[0]
                buf.append(" " + SMILIES.get(stem, node.get("alt", "")) + " ")
                continue
            brs = 0
            continue

        if isinstance(node, Tag) and node.name in ("ul", "ol"):
            brs = 0
            flush()
            lis = node.find_all("li", recursive=False)
            if lis:
                items = ["<li>" + "".join(B.inline(c) for c in li.children).strip() + "</li>"
                         for li in lis]
                blocks.append(("list", f"<{node.name}>" + "".join(items) + f"</{node.name}>"))
            else:
                text = B.as_pre(node)
                if text.strip():
                    blocks.append(pseudo_list_block(text))
            continue

        if isinstance(node, Tag) and node.name == "dl":
            brs = 0
            flush()
            code = node.find("dd")
            if code is not None:
                text = B.as_pre(code)
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
            text = "".join(B.inline(c) for c in body.children).strip() if body else ""
            blocks.append(("quote", (who, text)))
            continue

        if isinstance(node, Tag) and node.name == "blockquote":
            brs = 0
            flush()
            cite = node.select_one("cite")
            who = cite.get_text(strip=True).replace(" wrote:", "") if cite else ""
            if cite:
                cite.extract()
            blocks.append(("quote", (who, "".join(B.inline(c) for c in node.children).strip())))
            continue

        piece = B.inline(node)
        if piece.strip():
            brs = 0
        buf.append(piece)

    flush()
    return blocks


def render(blocks):
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
                out.append(f"<h4>{m.group(1).strip()}</h4>")
                continue
            out.append(f"<p>{payload}</p>")
        elif kind == "img":
            out.append(
                f'<figure><a href="{payload}" target="_blank" rel="noopener">'
                f'<img src="{payload}" alt="" loading="lazy"></a></figure>'
            )
        elif kind == "video":
            title = VIDEOS.get(payload, "Video")
            out.append(
                f'<figure class="video"><div class="video-frame">'
                f'<iframe src="https://www.youtube-nocookie.com/embed/{payload}" '
                f'title="{html_mod.escape(title)}" loading="lazy" allowfullscreen '
                f'referrerpolicy="strict-origin-when-cross-origin"></iframe></div></figure>'
            )
        elif kind == "list":
            out.append(payload)
        elif kind == "pre":
            out.append(f'<pre class="ascii">{payload}</pre>')
        elif kind == "quote":
            who, text = payload
            cite = f"<cite>{B.esc(who)} wrote:</cite>" if who else ""
            out.append(f"<blockquote>{cite}{text}</blockquote>")
    return "\n".join(out)


def field(text, label):
    m = re.search(rf"{label}:\s*([^\n]+?)(?:\s*(?:Joined|Posts|Location):|$)", text)
    return m.group(1).strip() if m else None


def parse_acidtech(path, page_ts, page_no):
    """mtbs3d_2013.html / page2 / page3 (acidtech phpBB skin)."""
    raw = open(path, encoding="utf-8", errors="replace").read()
    parts = re.split(r'(<a name="p\d+"[^>]*></a>)', raw)
    posts = []
    for i in range(1, len(parts) - 1, 2):
        pid = re.search(r"p\d+", parts[i]).group(0)
        soup = BeautifulSoup(parts[i + 1], "html.parser")
        author_el = soup.select_one(".postauthor")
        rank_el = soup.select_one(".posterrank")
        avatar_el = soup.select_one(".postavatar img")
        details_el = soup.select_one(".postdetails")
        subject_el = soup.select_one(".postsubject a")
        body_el = soup.select_one("div.postbody:not(.signature)") or soup.select_one(".postbody")
        bottoms = soup.select(".postbottom")
        date = bottoms[0].get_text(strip=True) if bottoms else None
        details_txt = details_el.get_text(" ", strip=True) if details_el else ""
        posts.append({
            "id": pid,
            "page": page_no,
            "author": author_el.get_text(strip=True) if author_el else "unknown",
            "author_color": (author_el.get("style", "") if author_el else ""),
            "rank": rank_el.get_text(strip=True) if rank_el else "",
            "avatar_rel": resolve_avatar(avatar_el["src"], page_ts) if avatar_el else None,
            "joined": field(details_txt, "Joined"),
            "posts_count": field(details_txt, "Posts"),
            "location": field(details_txt, "Location"),
            "subject": subject_el.get_text(strip=True) if subject_el else None,
            "date": date,
            "body_html": render(convert(body_el, page_ts)) if body_el else "",
        })
    return posts


def parse_prosilver(path, page_ts, page_no):
    """oculus_2015.html (prosilver-ish phpBB skin)."""
    raw = open(path, encoding="utf-8", errors="replace").read()
    soup = BeautifulSoup(raw, "html.parser")
    posts = []
    for post_div in soup.select("div.post"):
        pid = post_div.get("id")
        if not pid:
            continue
        profile = post_div.find_next("dl", class_="postprofile")
        author_link = profile.select_one(".username, .username-coloured") if profile else None
        avatar_img = profile.select_one("img") if profile else None
        author_p = post_div.select_one("p.author")
        body_el = post_div.select_one(".postbody .content") or post_div.select_one(".content")
        date = None
        if author_p:
            m = re.search(r"\xbb\s*(.+?)\s*$", author_p.get_text(" ", strip=True))
            date = m.group(1).strip() if m else None
        dd_text = " ".join(dd.get_text(" ", strip=True) for dd in (profile.select("dd") if profile else []))
        subject_el = post_div.find_previous("h3")
        posts.append({
            "id": pid.lstrip("p"),
            "page": page_no,
            "author": author_link.get_text(strip=True) if author_link else "unknown",
            "author_color": (author_link.get("style", "") if author_link else ""),
            "rank": "",
            "avatar_rel": resolve_avatar(avatar_img["src"], page_ts) if avatar_img and avatar_img.get("src") else None,
            "joined": field(dd_text, "Joined"),
            "posts_count": field(dd_text, "Posts"),
            "location": field(dd_text, "Location"),
            "subject": subject_el.get_text(strip=True) if subject_el else None,
            "date": date,
            "body_html": render(convert(body_el, page_ts)) if body_el else "",
        })
    return posts


POST_CARD = """
<article class="post" id="p{id}">
  <aside class="post-side">
    <div class="avatar">{avatar}</div>
    <div class="uname"{color}>{author}</div>
    {rank}
    <dl class="pdetails">
      {joined}{postsc}{loc}
    </dl>
  </aside>
  <div class="post-main">
    <div class="post-meta"><span class="pdate">{date}</span> <a class="panchor" href="#p{id}">#p{id}</a></div>
    <div class="post-body">
      {body}
    </div>
  </div>
</article>
"""


def avatar_html(rel, author):
    if rel:
        return f'<img src="{html_mod.escape(rel)}" alt="{html_mod.escape(author)}" width="87" height="87" loading="lazy">'
    initials = "".join(w[0] for w in re.findall(r"[A-Za-z0-9]+", author)[:2]).upper() or "?"
    return f'<div class="avatar-fallback">{html_mod.escape(initials)}</div>'


def dd(label, value):
    return f"<dd><strong>{label}:</strong> {html_mod.escape(value)}</dd>" if value else ""


def render_post(p):
    color = f' style="{html_mod.escape(p["author_color"])}"' if p.get("author_color") else ""
    rank = f'<div class="rank">{html_mod.escape(p["rank"])}</div>' if p.get("rank") else ""
    return POST_CARD.format(
        id=p["id"].lstrip("p"),
        avatar=avatar_html(p["avatar_rel"], p["author"]),
        color=color,
        author=html_mod.escape(p["author"]),
        rank=rank,
        joined=dd("Joined", p.get("joined")),
        postsc=dd("Posts", p.get("posts_count")),
        loc=dd("Location", p.get("location")),
        date=html_mod.escape(p.get("date") or ""),
        body=p["body_html"] or "<p><em>(empty post)</em></p>",
    )


CSS = """
:root{
  --bg:#f4f6f8; --panel:#fff; --line:#d3dae3; --text:#1b2733; --dim:#5c6b7a;
  --accent:#2e6ea6; --author-bg:#e7edf3;
  --ui:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:var(--ui);font-size:15px;line-height:1.55}
a{color:var(--accent)}
img{max-width:100%;height:auto}
.topbar{position:sticky;top:0;z-index:10;background:#1b2733;color:#fff;padding:10px 20px;display:flex;gap:16px;align-items:center}
.topbar a{color:#cfe0ef;text-decoration:none;font-size:.9rem}
.topbar a:hover{text-decoration:underline}
.topbar .title{font-weight:700;margin-right:auto}
.wrap{max-width:960px;margin:0 auto;padding:24px 16px 80px}
.thread-header{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:18px 22px;margin-bottom:18px}
.thread-header h1{margin:0 0 6px;font-size:1.35rem}
.thread-header .src{color:var(--dim);font-size:.85rem}
.page-sep{text-align:center;color:var(--dim);font-size:.8rem;margin:26px 0 10px;text-transform:uppercase;letter-spacing:.04em}
.post{display:flex;gap:0;background:var(--panel);border:1px solid var(--line);border-radius:6px;margin-bottom:14px;overflow:hidden}
.post-side{width:170px;flex:none;background:var(--author-bg);padding:14px;border-right:1px solid var(--line);font-size:.82rem}
.avatar img{border-radius:4px;border:1px solid var(--line)}
.avatar-fallback{width:87px;height:87px;border-radius:4px;background:#94a8bd;color:#fff;display:flex;align-items:center;justify-content:center;font-size:1.6rem;font-weight:700}
.uname{font-weight:700;margin-top:8px;word-break:break-word}
.rank{color:var(--dim);font-style:italic;font-size:.78rem}
.pdetails{margin:8px 0 0;font-size:.76rem;color:var(--dim)}
.pdetails dd{margin:0}
.post-main{flex:1;min-width:0;padding:14px 18px}
.post-meta{display:flex;justify-content:space-between;color:var(--dim);font-size:.8rem;border-bottom:1px dashed var(--line);padding-bottom:8px;margin-bottom:10px}
.post-body{overflow-wrap:break-word}
.post-body p{margin:.6em 0}
.post-body ul,.post-body ol{margin:.6em 0;padding-left:1.4em}
.post-body li{margin:.3em 0}
.post-body blockquote{background:#eef2f6;border-left:3px solid var(--accent);margin:.8em 0;padding:.5em .9em;font-size:.93em}
.post-body blockquote cite{display:block;font-weight:700;font-size:.8em;color:var(--dim);margin-bottom:.3em;font-style:normal}
.post-body figure{margin:.8em 0}
.post-body pre.ascii{background:#0f1720;color:#d7e2ec;padding:10px;border-radius:4px;overflow-x:auto;font-family:var(--mono);font-size:.82em}
.post-body .video-frame{position:relative;padding-top:56.25%}
.post-body .video-frame iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.hub-card{display:block;text-decoration:none;color:inherit;margin-bottom:14px}
.hub-card:hover{border-color:var(--accent)}
@media (max-width: 640px){
  .post{flex-direction:column}
  .post-side{width:auto;border-right:0;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:10px}
  .pdetails{display:none}
  .avatar img,.avatar-fallback{width:44px;height:44px}
}
"""


def render_thread(title, source_note, groups):
    parts = [f'<div class="thread-header"><h1>{html_mod.escape(title)}</h1>'
             f'<div class="src">{source_note}</div></div>']
    for label, posts in groups:
        if label:
            parts.append(f'<div class="page-sep">{html_mod.escape(label)}</div>')
        for p in posts:
            parts.append(render_post(p))
    return "\n".join(parts)


def page_shell(title, description, topbar_title, topbar_links, body):
    links_html = "\n  ".join(f'<a href="{href}">{label}</a>' for href, label in topbar_links)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="author" content="Jordi Batall&eacute; (PatimPatam)">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:image" content="images/07-finished-prototype.jpg">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><circle cx='16' cy='16' r='9' fill='%236ec6ff'/></svg>">
<style>{CSS}</style>
</head>
<body>
<div class="topbar">
  <span class="title">{topbar_title}</span>
  {links_html}
</div>
<div class="wrap">
{body}
</div>
</body>
</html>
"""


def main():
    os.makedirs(AVATAR_DIR, exist_ok=True)
    os.makedirs(THREAD_DIR, exist_ok=True)

    mtbs_pages = [
        (os.path.join(RAW, "mtbs3d_2013.html"), "20131221025253", 1),
        (os.path.join(RAW, "mtbs3d_page2.html"), "20140328113948", 2),
        (os.path.join(RAW, "mtbs3d_page3.html"), "20140328114110", 3),
    ]
    mtbs_posts = []
    groups = []
    for path, ts, page_no in mtbs_pages:
        page_posts = parse_acidtech(path, ts, page_no)
        print(path, "->", len(page_posts), "posts")
        mtbs_posts.extend(page_posts)
        groups.append((f"Page {page_no}", page_posts))

    ocu_posts = parse_prosilver(os.path.join(RAW, "oculus_2015.html"), "20150419171040", 1)
    print("oculus_2015.html ->", len(ocu_posts), "posts")

    mtbs_html = render_thread(
        "POSITTRON: yet another proposal for positional head-tracking",
        'MTBS3D forum &middot; started by PatimPatam (Jordi Batallé), 8 Jan 2013 &middot; '
        '<a href="sources/raw-html/mtbs3d_2013.html" target="_blank" rel="noopener">raw capture</a>',
        groups,
    )
    ocu_html = render_thread(
        "VR Navigation Experiments (UE4 Sun Temple MOD)",
        'Oculus VR Forums &middot; started by PatimPatam (Jordi Batallé), 22 Dec 2014 &middot; '
        '<a href="sources/raw-html/oculus_2015.html" target="_blank" rel="noopener">raw capture</a>',
        [(None, ocu_posts)],
    )

    disclaimer = ('  <p style="color:#5c6b7a;font-size:.85rem">\n'
                  '    Every post, exactly as written, restored from Wayback Machine captures.\n'
                  '    Avatars and inline images are downloaded locally; nothing here is hotlinked.\n'
                  '  </p>')

    hub_body = (
        f"{disclaimer}\n"
        f'  <a class="thread-header hub-card" href="posittron.html">'
        f'<h1>POSITTRON: yet another proposal for positional head-tracking</h1>'
        f'<div class="src">MTBS3D forum &middot; started 8 Jan 2013 &middot; {len(mtbs_posts)} posts</div></a>\n'
        f'  <a class="thread-header hub-card" href="sun-temple.html">'
        f'<h1>VR Navigation Experiments (UE4 Sun Temple MOD)</h1>'
        f'<div class="src">Oculus VR Forums &middot; started 22 Dec 2014 &middot; {len(ocu_posts)} posts</div></a>\n'
        f'  <p style="margin-top:24px"><a href="archive.html">Prefer a single curated article instead? &rarr;</a></p>'
    )
    hub_page = page_shell(
        "PosiTTron &amp; Sun Temple MOD: full forum threads, recovered",
        "Every post from the PosiTTron (2013) and Sun Temple MOD (2014) forum threads by "
        "Jordi Batall&eacute; (PatimPatam), restored from Internet Archive snapshots after "
        "the originals went offline.",
        "PosiTTron archive &middot; full forum threads",
        [("archive.html", "curated article view &rarr;")],
        hub_body,
    )

    posittron_page = page_shell(
        "PosiTTron: full MTBS3D forum thread, recovered",
        "All 120 posts of the 2013 PosiTTron thread on MTBS3D, restored from a Wayback "
        "Machine snapshot with every avatar and inline image downloaded locally.",
        "PosiTTron archive &middot; MTBS3D thread",
        [("index.html", "all threads"), ("sun-temple.html", "Sun Temple MOD thread &rarr;")],
        f"{disclaimer}\n  {mtbs_html}",
    )

    suntemple_page = page_shell(
        "Sun Temple MOD: full Oculus forum thread, recovered",
        "All 11 posts of the 2014 Sun Temple MOD / VR navigation thread on the Oculus "
        "developer forums, restored from a Wayback Machine snapshot after the original "
        "went offline (the migrated Meta URLs now return 403).",
        "PosiTTron archive &middot; Sun Temple MOD thread",
        [("index.html", "all threads"), ("posittron.html", "&larr; PosiTTron thread")],
        f"{disclaimer}\n  {ocu_html}",
    )

    for out, page in ((OUT_HUB, hub_page), (OUT_POSITTRON, posittron_page), (OUT_SUNTEMPLE, suntemple_page)):
        with open(out, "w", encoding="utf-8") as f:
            f.write(page)
        print("wrote", out)
    print(len(mtbs_posts) + len(ocu_posts), "posts total")


if __name__ == "__main__":
    main()
