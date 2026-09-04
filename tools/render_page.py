#!/usr/bin/env python3
"""Compose index.html for the PosiTTron archive."""

import html
import site_fragments as S

OUT = "/projects/posittron-archive/index.html"

CSS = """
:root{
  --bg:#0b0d10; --elev:#12151a; --panel:#161a20; --line:#262c35; --line-soft:#1d222a;
  --text:#e7eaee; --dim:#98a2b0; --faint:#6b7684;
  --accent:#6ec6ff; --accent-2:#ffcc66;
  --led-r:#ff5f5f; --led-g:#4ade80; --led-b:#60a5fa; --led-w:#f1f5f9; --led-y:#fbbf24;
  --ui:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --serif:"Charter","Iowan Old Style","Source Serif Pro",Georgia,Cambria,serif;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{
  margin:0;background:var(--bg);color:var(--text);font-family:var(--ui);
  font-size:17px;line-height:1.6;-webkit-font-smoothing:antialiased;
}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
img{max-width:100%;height:auto;display:block}
hr{border:0;border-top:1px solid var(--line);margin:2.5rem 0}

.wrap{max-width:1080px;margin:0 auto;padding:0 24px}
.narrow{max-width:720px;margin-left:auto;margin-right:auto}

/* ---------- nav ---------- */
nav{
  position:sticky;top:0;z-index:50;background:rgba(11,13,16,.82);
  backdrop-filter:saturate(150%) blur(12px);border-bottom:1px solid var(--line-soft);
}
nav .wrap{display:flex;align-items:center;gap:22px;height:54px;overflow-x:auto}
nav .brand{font-weight:650;letter-spacing:-.01em;color:var(--text);white-space:nowrap}
nav .brand span{color:var(--accent)}
nav .links{display:flex;gap:20px;margin-left:auto}
nav .links a{color:var(--dim);font-size:.87rem;white-space:nowrap}
nav .links a:hover{color:var(--text);text-decoration:none}

/* ---------- hero ---------- */
header.hero{
  position:relative;overflow:hidden;padding:88px 0 64px;
  border-bottom:1px solid var(--line-soft);
  background:
    radial-gradient(900px 380px at 18% -10%,rgba(110,198,255,.13),transparent 62%),
    radial-gradient(700px 340px at 88% 6%,rgba(255,204,102,.09),transparent 60%);
}
.leds{display:flex;gap:9px;margin-bottom:26px}
.leds i{width:9px;height:9px;border-radius:50%;display:block}
.leds i:nth-child(1){background:var(--led-r);box-shadow:0 0 12px var(--led-r)}
.leds i:nth-child(2){background:var(--led-g);box-shadow:0 0 12px var(--led-g)}
.leds i:nth-child(3){background:var(--led-b);box-shadow:0 0 12px var(--led-b)}
.leds i:nth-child(4){background:var(--led-w);box-shadow:0 0 12px var(--led-w)}
.leds i:nth-child(5){background:var(--led-y);box-shadow:0 0 12px var(--led-y)}
.eyebrow{
  font-size:.76rem;text-transform:uppercase;letter-spacing:.14em;
  color:var(--accent);font-weight:600;margin-bottom:18px;
}
h1{
  font-size:clamp(3rem,9vw,5.6rem);line-height:.98;margin:0 0 22px;
  letter-spacing:-.035em;font-weight:700;
}
h1 .tt{color:var(--accent)}
.lede{font-family:var(--serif);font-size:clamp(1.12rem,2.3vw,1.36rem);line-height:1.6;color:#cdd4dd;max-width:44rem;margin:0 0 30px}
.chips{display:flex;flex-wrap:wrap;gap:9px}
.chip{
  font-size:.8rem;color:var(--dim);border:1px solid var(--line);
  background:var(--elev);padding:6px 13px;border-radius:999px;
}
.chip b{color:var(--text);font-weight:600}

/* ---------- sections ---------- */
section{padding:76px 0;border-bottom:1px solid var(--line-soft)}
.sec-label{
  font-size:.74rem;text-transform:uppercase;letter-spacing:.15em;
  color:var(--faint);font-weight:600;margin-bottom:14px;
}
h2{font-size:clamp(1.7rem,3.6vw,2.4rem);line-height:1.15;letter-spacing:-.025em;margin:0 0 20px;font-weight:680}
.sec-intro{color:var(--dim);max-width:44rem;font-size:1.02rem}
.sec-intro strong{color:var(--text);font-weight:600}

/* ---------- callout ---------- */
.callout{
  border:1px solid var(--line);border-left:3px solid var(--accent);
  background:var(--elev);border-radius:0 10px 10px 0;padding:20px 24px;margin:28px 0;
}
.callout p{margin:0;color:#c9d1db;font-size:.97rem}
.callout p + p{margin-top:12px}

/* ---------- timeline ---------- */
.tl{list-style:none;margin:34px 0 0;padding:0 0 0 26px;border-left:1px solid var(--line);max-width:46rem}
.tl li{position:relative;padding:0 0 30px 22px}
.tl li::before{
  content:"";position:absolute;left:-31px;top:7px;width:9px;height:9px;border-radius:50%;
  background:var(--accent);box-shadow:0 0 0 4px var(--bg),0 0 12px rgba(110,198,255,.55);
}
.tl li.ctx::before{background:var(--faint);box-shadow:0 0 0 4px var(--bg)}
.tl .when{font-size:.79rem;color:var(--accent);font-weight:600;letter-spacing:.03em;text-transform:uppercase}
.tl li.ctx .when{color:var(--faint)}
.tl .what{margin-top:5px;color:#d5dbe3}
.tl li.ctx .what{color:var(--dim)}
.tl .what > em{color:var(--faint);font-style:normal;font-size:.9rem;display:block;margin-top:3px}

/* ---------- article ---------- */
.article{
  font-family:var(--serif);font-size:1.075rem;line-height:1.78;color:#dfe4ea;
  max-width:38rem;margin:0 auto;
}
.article p{margin:0 0 1.4em}
.article h3{
  font-family:var(--ui);font-size:.83rem;text-transform:uppercase;letter-spacing:.13em;
  color:var(--accent-2);font-weight:650;margin:2.8em 0 1em;padding-bottom:.6em;
  border-bottom:1px solid var(--line);
}
.article a{color:var(--accent);word-break:break-word}
.article ul,.article ol{margin:0 0 1.4em;padding-left:1.3em}
.article li{margin-bottom:.6em}
.article strong{color:#fff;font-weight:640}
.article hr{margin:2.4em 0}
.article blockquote{
  margin:1.6em 0;padding:14px 20px;border-left:2px solid var(--line);
  background:var(--elev);color:var(--dim);font-size:.98rem;border-radius:0 8px 8px 0;
}
.article blockquote cite{
  display:block;font-style:normal;font-family:var(--ui);font-size:.78rem;
  text-transform:uppercase;letter-spacing:.08em;color:var(--faint);margin-bottom:8px;
}

.article pre.ascii{
  font-family:var(--mono);font-size:.78rem;line-height:1.65;color:#c3cbd6;
  background:var(--elev);border:1px solid var(--line);border-radius:10px;
  padding:16px 18px;overflow-x:auto;margin:1.6em 0;white-space:pre;
}
.article pre.ascii a{font-family:inherit}

figure{margin:2.2em 0}
figure img{border:1px solid var(--line);border-radius:10px;background:#000;margin-inline:auto}
figure a:hover img{border-color:var(--accent)}
figcaption{
  font-family:var(--ui);font-size:.82rem;color:var(--faint);
  margin-top:10px;line-height:1.5;text-align:center;
}
figure.video .video-frame{
  position:relative;padding-bottom:56.25%;height:0;border:1px solid var(--line);
  border-radius:10px;overflow:hidden;background:#000;
}
figure.video iframe{position:absolute;inset:0;width:100%;height:100%;border:0}

/* wide figures break out of the text column */
@media(min-width:900px){
  .article figure{margin-left:-90px;margin-right:-90px}
}

/* ---------- post meta ---------- */
.postmeta{
  display:flex;flex-wrap:wrap;gap:8px 18px;align-items:baseline;
  font-family:var(--ui);font-size:.84rem;color:var(--faint);
  border:1px solid var(--line);background:var(--elev);border-radius:10px;
  padding:14px 18px;margin:0 auto 44px;max-width:38rem;
}
.postmeta .who{color:var(--text);font-weight:600}
.postmeta .sep{color:var(--line)}

/* ---------- followups ---------- */
.followup{max-width:38rem;margin:0 auto 56px;padding-top:8px}
.followup .fu-head{
  font-family:var(--ui);font-size:.78rem;text-transform:uppercase;letter-spacing:.1em;
  color:var(--faint);margin-bottom:18px;padding-bottom:10px;border-bottom:1px solid var(--line);
}
.followup .fu-head b{color:var(--accent-2);font-weight:600}

/* ---------- table ---------- */
.tablewrap{overflow-x:auto;margin-top:30px;border:1px solid var(--line);border-radius:12px}
table{width:100%;border-collapse:collapse;font-size:.9rem;min-width:640px}
th{
  text-align:left;font-size:.73rem;text-transform:uppercase;letter-spacing:.1em;
  color:var(--faint);font-weight:600;padding:14px 18px;background:var(--elev);
  border-bottom:1px solid var(--line);
}
td{padding:14px 18px;border-bottom:1px solid var(--line-soft);vertical-align:top;color:var(--dim)}
tr:last-child td{border-bottom:0}
td .t{color:var(--text);display:block;margin-bottom:3px}
td a{word-break:break-all;font-size:.84rem;font-family:var(--mono)}
.pill{
  display:inline-block;font-size:.72rem;font-weight:600;padding:3px 10px;border-radius:999px;
  text-transform:uppercase;letter-spacing:.06em;white-space:nowrap;
}
.pill.ok{background:rgba(74,222,128,.11);color:#6ee7a0;border:1px solid rgba(74,222,128,.26)}
.pill.dead{background:rgba(255,95,95,.11);color:#ff8f8f;border:1px solid rgba(255,95,95,.26)}
.pill.rec{background:rgba(110,198,255,.11);color:var(--accent);border:1px solid rgba(110,198,255,.26)}
.pill.part{background:rgba(251,191,36,.11);color:var(--led-y);border:1px solid rgba(251,191,36,.26)}

/* ---------- cards ---------- */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin-top:30px}
.card{border:1px solid var(--line);background:var(--elev);border-radius:12px;padding:20px 22px}
.card h4{margin:0 0 8px;font-size:.95rem;font-weight:640;color:var(--text)}
.card p{margin:0;font-size:.88rem;color:var(--dim);line-height:1.55}
.card .mono{font-family:var(--mono);font-size:.8rem;color:var(--accent)}

/* ---------- readme block ---------- */
pre.readme{
  font-family:var(--mono);font-size:.8rem;line-height:1.6;color:var(--dim);
  background:var(--elev);border:1px solid var(--line);border-radius:12px;
  padding:22px;overflow-x:auto;margin:28px auto 0;max-width:38rem;
}

/* ---------- footer ---------- */
footer{padding:64px 0 80px;color:var(--faint);font-size:.9rem}
footer .wrap{max-width:720px}
footer p{margin:0 0 14px;line-height:1.7}
footer strong{color:var(--dim);font-weight:600}

@media(max-width:640px){
  body{font-size:16px}
  section{padding:56px 0}
  header.hero{padding:56px 0 44px}
  nav .links{display:none}
  .article{font-size:1.03rem}
}

@media print{
  body{background:#fff;color:#111}
  nav,footer{display:none}
  section{border:0;padding:24px 0}
  .article,.lede{color:#111}
  h1,h2,.article h3,.article strong{color:#000}
  a{color:#0645ad}
  figure img{border:1px solid #ccc}
  .callout,.card,.postmeta,pre.readme{background:#f6f6f6;border:1px solid #ddd}
  .article figure{margin-left:0;margin-right:0}
}
"""

TIMELINE = [
    ("8 January 2013", "PosiTTron is posted on the MTBS3D forums",
     "A ~5,000 word write-up under &ldquo;VR/AR Research &amp; Development&rdquo;, with build photos, latency measurements, a cost breakdown and two demo videos.", False),
    ("17 January 2013", "The P3P objection",
     "A reader proposes a simpler three-marker layout. The reply explains why three points are geometrically ambiguous, and it is the clearest short explanation of the problem in the whole thread.", False),
    ("26 January 2013", "Update log: the box filter",
     "Swapping a Gaussian blur for a normalised box filter cuts almost 2&nbsp;ms off the frame, taking the pipeline to roughly 8.3&nbsp;ms.", False),
    ("13 February 2013", "Cardboard templates and 3D printing",
     "Plans to release printable templates so anyone could build one from card, with 3D printing as the more expensive option.", False),
    ("15 February 2013", "Road to VR publishes a five-page feature",
     "Ben Lang runs the whole thing as a guest article. It is still online, and is the reason most of the images survived anywhere at all.", False),
    ("8 January 2014", "The thread ends",
     "120 posts from 27 people, one year to the day after it started.", False),
    ("July 2014", "Oculus ships the DK2",
     "Positional tracking by infrared LEDs embedded in the headset, read by a single external camera: the same family of solution, eighteen months later.", True),
    ("22 December 2014", "Sun Temple MOD: VR navigation experiments",
     "A different problem: moving through VR without making people sick. Posted to the Oculus developer forum and to the Unreal Engine forums.", False),
]

SOURCES = [
    ("Original thread (MTBS3D)",
     "https://www.mtbs3d.com/phpBB/viewtopic.php?f=138&amp;t=16072",
     "part", "Online, images dead",
     "The thread survives, but every image 404s: they were hosted on Windows SkyDrive, which stopped serving them years ago."),
    ("Wayback snapshot, page 1",
     "https://web.archive.org/web/20131221025253/http://www.mtbs3d.com/phpBB/viewtopic.php?f=138&amp;t=16072",
     "rec", "Recovered", "Captured 21 Dec 2013, while the images were still live. This is the source of the restoration above."),
    ("Wayback snapshot, pages 2 &amp; 3",
     "https://web.archive.org/web/20140328114110/http://www.mtbs3d.com/phpBB/viewtopic.php?f=138&amp;t=16072&amp;start=40",
     "rec", "Recovered", "Captured 28 Mar 2014. Together with page 1 these cover all 120 posts."),
    ("Road to VR feature",
     "https://www.roadtovr.com/posittron-diy-oculus-rift-positional-tracking-virtual-reality/",
     "ok", "Online", "Five-page guest article by Ben Lang, 15 Feb 2013. Still serving its images."),
    ("YouTube, demo 01",
     "https://www.youtube.com/watch?v=EzC-HDpv2xw", "ok", "Online", "Channel: PatimPatamVR."),
    ("YouTube, demo 02",
     "https://www.youtube.com/watch?v=nsl43qbMnOA", "ok", "Online", "Channel: PatimPatamVR."),
    ("Sun Temple thread (Oculus forums)",
     "https://forums.oculus.com/viewtopic.php?f=32&amp;t=18422",
     "dead", "Gone", "The original URL no longer resolves to the thread."),
    ("Sun Temple thread (migrated Meta URLs)",
     "https://communityforums.atmeta.com/t5/Game-Design/UE4-Sun-Temple-MOD-download-VR-Navigation-Experiments/td-p/272387",
     "dead", "403", "Meta migrated the forum twice. Both current URLs return 403 and are unreachable without an account."),
    ("Wayback snapshot, Oculus thread",
     "https://web.archive.org/web/20150419171040/https://forums.oculus.com/viewtopic.php?f=32&amp;t=18422",
     "rec", "Recovered", "Captured 19 Apr 2015. All 11 posts, including the full write-up restored above."),
    ("Sun Temple thread (Unreal Engine forums)",
     "https://forums.unrealengine.com/t/vr-navigation-experiments-sun-temple-mod/17664",
     "ok", "Online", "Survived Epic's forum migration, but it is the short version of the post."),
    ("Sun Temple MOD download",
     "https://www.mediafire.com/file/d51dzd5hv3r1mw3/Sun_Temple_VR_MOD.zip/file",
     "ok", "Online", "507&nbsp;MB packaged UE4 build. Still downloadable, on a free file host, eleven years on."),
]


def timeline_html():
    rows = []
    for when, what, detail, ctx in TIMELINE:
        cls = ' class="ctx"' if ctx else ""
        rows.append(
            f'<li{cls}><div class="when">{when}</div>'
            f'<div class="what">{what}<em>{detail}</em></div></li>'
        )
    return '<ul class="tl">' + "".join(rows) + "</ul>"


def sources_html():
    rows = []
    for name, url, pill, label, note in SOURCES:
        rows.append(
            f"<tr><td><span class=\"t\">{name}</span>"
            f'<a href="{url}" target="_blank" rel="noopener">{url}</a></td>'
            f'<td><span class="pill {pill}">{label}</span></td>'
            f"<td>{note}</td></tr>"
        )
    return (
        '<div class="tablewrap"><table><thead><tr>'
        "<th>Source</th><th>Status</th><th>Notes</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>"
    )


def followups_html():
    out = []
    for f in S.FOLLOWUPS:
        out.append(
            f'<div class="followup"><div class="fu-head">'
            f'<b>PatimPatam</b> &middot; {html.escape(f["date"] or "")} '
            f'&middot; post {f["id"][1:]}</div>'
            f'<div class="article">{f["html"]}</div></div>'
        )
    return "".join(out)


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PosiTTron: Jordi Batall&eacute;'s DIY VR positional tracking, recovered</title>
<meta name="description" content="A restored archive of PosiTTron (2013), a DIY 6-DOF positional tracking system for the Oculus Rift built by Jordi Batall&eacute;, plus the 2014 Sun Temple VR navigation experiments. Rebuilt from Internet Archive snapshots after the original images and forum threads went offline.">
<meta name="author" content="Jordi Batall&eacute; (PatimPatam)">
<meta property="og:type" content="article">
<meta property="og:title" content="PosiTTron: DIY VR positional tracking, 2013">
<meta property="og:description" content="Cardboard, 22 LEDs and a PlayStation Eye. Recovered from dead links and broken images.">
<meta property="og:image" content="images/07-finished-prototype.jpg">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><circle cx='16' cy='16' r='9' fill='%236ec6ff'/></svg>">
<style>%%CSS%%</style>
</head>
<body>

<nav><div class="wrap">
  <div class="brand">Posi<span>TT</span>ron</div>
  <div class="links">
    <a href="#about">About</a>
    <a href="#timeline">Timeline</a>
    <a href="#posittron">The 2013 post</a>
    <a href="#followups">Follow-ups</a>
    <a href="#suntemple">Sun Temple</a>
    <a href="#archive">Sources</a>
  </div>
</div></nav>

<header class="hero"><div class="wrap">
  <div class="leds"><i></i><i></i><i></i><i></i><i></i></div>
  <div class="eyebrow">Recovered from the dead web &middot; 2013&ndash;2014</div>
  <h1>Posi<span class="tt">TT</span>ron</h1>
  <p class="lede">
    In January 2013, <strong>Jordi Batall&eacute;</strong> built a working 6-DOF positional
    tracking system for the Oculus Rift out of cardboard, 22&nbsp;LEDs and a PlayStation Eye
    camera, then wrote up every detail on a forum that has since lost all of its images.
    This page puts the whole thing back together.
  </p>
  <div class="chips">
    <span class="chip"><b>Jordi Batall&eacute;</b> &middot; PatimPatam</span>
    <span class="chip">MTBS3D &middot; <b>120 posts</b> over one year</span>
    <span class="chip"><b>15 images</b> recovered</span>
    <span class="chip"><b>2 threads</b> restored</span>
  </div>
</div></header>

<section id="about"><div class="wrap narrow">
  <div class="sec-label">What this is</div>
  <h2>Four links, three of them broken</h2>
  <p class="sec-intro">
    This work was published in four places. Today, the original MTBS3D thread is still
    online but <strong>every single image in it is dead</strong>. They lived on Windows
    SkyDrive, which stopped serving them. The Oculus forum follow-up is <strong>gone
    entirely</strong>: the original URL gives nothing, and both of Meta's migrated
    replacements return 403. Only the Road to VR feature and the Unreal Engine thread
    still work as intended.
  </p>
  <div class="callout">
    <p>
      Everything below was rebuilt from Internet Archive snapshots taken while the images
      were still alive: 21&nbsp;December&nbsp;2013 and 28&nbsp;March&nbsp;2014 for the
      MTBS3D thread, 19&nbsp;April&nbsp;2015 for the Oculus one.
    </p>
    <p>
      The text is reproduced verbatim, in its original order, with the images and videos
      back in the positions they were written for. Nothing has been edited, corrected or
      summarised.
    </p>
  </div>
</div></section>

<section id="timeline"><div class="wrap narrow">
  <div class="sec-label">Timeline</div>
  <h2>Two years of it</h2>
  <p class="sec-intro">The greyed-out entry is context, not part of the work.</p>
  %%TIMELINE%%
</div></section>

<section id="posittron"><div class="wrap">
  <div class="narrow">
    <div class="sec-label">Restored &middot; MTBS3D, VR/AR Research &amp; Development</div>
    <h2>POSITTRON: yet another proposal for positional head-tracking</h2>
  </div>
  <div class="postmeta">
    <span class="who">PatimPatam</span>
    <span class="sep">|</span>
    <span>Tue 8 Jan 2013, 1:04&nbsp;am</span>
    <span class="sep">|</span>
    <span>last edited Sat 26 Jan 2013</span>
    <span class="sep">|</span>
    <span>Barcelona</span>
  </div>
  <article class="article">%%POSITTRON%%</article>
</div></section>

<section id="followups"><div class="wrap">
  <div class="narrow">
    <div class="sec-label">Restored &middot; selected replies</div>
    <h2>Follow-ups from the thread</h2>
    <p class="sec-intro">
      Three later posts from the same thread, kept because each carries an image that
      exists nowhere else, and because the P3P answer is the best short explanation
      of why the obvious cheaper design does not work.
    </p>
  </div>
  %%FOLLOWUPS%%
</div></section>

<section id="suntemple"><div class="wrap">
  <div class="narrow">
    <div class="sec-label">Restored &middot; Oculus developer forum (now offline)</div>
    <h2>UE4 Sun Temple MOD: VR Navigation Experiments</h2>
    <p class="sec-intro">
      Almost two years later, a different problem: how do you move through a virtual
      environment without making people sick? This post only exists as an Internet Archive
      capture; all three of its live URLs are now dead or behind a login.
    </p>
  </div>
  <div class="postmeta">
    <span class="who">PatimPatam</span>
    <span class="sep">|</span>
    <span>Mon 22 Dec 2014, 10:32&nbsp;am</span>
    <span class="sep">|</span>
    <span>forums.oculus.com &middot; thread 18422</span>
  </div>
  <article class="article">%%SUNTEMPLE%%</article>
  <div class="narrow" style="margin-top:56px">
    <div class="sec-label">Shipped with the download</div>
    <h2 style="font-size:1.3rem">README.txt</h2>
  </div>
  <pre class="readme">%%README%%</pre>
</div></section>

<section id="archive"><div class="wrap">
  <div class="narrow">
    <div class="sec-label">The archive</div>
    <h2>Every source, and whether it still works</h2>
    <p class="sec-intro">
      Checked on 4 September 2026. Status reflects what the URL actually returned, not
      what it claims.
    </p>
  </div>
  %%SOURCES%%
  <div class="narrow" style="margin-top:56px">
    <div class="sec-label">Also in this repository</div>
    <h2 style="font-size:1.3rem">Raw material</h2>
  </div>
  <div class="cards">
    <div class="card">
      <h4>Full thread transcripts</h4>
      <p><span class="mono">sources/mtbs3d-thread-full.txt</span> holds all 120 posts with
      author and date. <span class="mono">sources/oculus-thread-full.txt</span> holds all 11.</p>
    </div>
    <div class="card">
      <h4>Original archived HTML</h4>
      <p><span class="mono">sources/raw-html/</span> holds the four Wayback captures exactly
      as retrieved, in case anything here needs checking against the source.</p>
    </div>
    <div class="card">
      <h4>Images</h4>
      <p><span class="mono">images/</span> holds 15 files at original resolution, pulled from
      the archived SkyDrive URLs before they disappear from the Archive too.</p>
    </div>
    <div class="card">
      <h4>The mod itself</h4>
      <p>The 507&nbsp;MB build is too large for a repository, but it is still live on
      MediaFire and a local copy has been kept.</p>
    </div>
  </div>
</div></section>

<footer><div class="wrap">
  <p>
    <strong>All words, images, code and designs on this page are Jordi Batall&eacute;'s</strong>,
    written between January 2013 and December 2014 and reproduced here unedited. The forum
    replies quoted belong to their respective authors.
  </p>
  <p>
    Assembled in September 2026 from Internet Archive snapshots, because a broken image and
    a 403 are all it takes for work like this to quietly stop existing. Three of the four
    original links had already failed by the time this was put together.
  </p>
</div></footer>

</body>
</html>
"""

page = (PAGE
        .replace("%%CSS%%", CSS)
        .replace("%%TIMELINE%%", timeline_html())
        .replace("%%POSITTRON%%", S.POSITTRON)
        .replace("%%FOLLOWUPS%%", followups_html())
        .replace("%%SUNTEMPLE%%", S.SUNTEMPLE)
        .replace("%%README%%", html.escape(S.README_TXT))
        .replace("%%SOURCES%%", sources_html()))

with open(OUT, "w", encoding="utf-8") as f:
    f.write(page)

print("wrote", OUT, len(page), "bytes")
