# PosiTTron archive

**Read it here: <https://christt105.github.io/posittron-archive/>**

A restored, self-contained archive of two pieces of work by **Jordi Batallé**
(`PatimPatam`), recovered after most of the places they were published went
offline or lost their images:

- **PosiTTron** (January 2013). A DIY 6-DOF positional tracking system for the
  Oculus Rift, built from cardboard, 22 LEDs and a PlayStation Eye camera, and
  documented in a ~5,000 word forum post on MTBS3D.
- **Sun Temple MOD: VR Navigation Experiments** (December 2014). An experiment
  in moving through VR environments without inducing simulation sickness.

Open `index.html` in any browser. No build step, no dependencies, no JavaScript.

## Why this exists

Of the four places this work was published, three no longer work properly:

| Source | Status |
| --- | --- |
| MTBS3D thread | Online, but **every image is dead** (they were hosted on Windows SkyDrive) |
| Oculus developer forum thread | **Gone**. Original URL dead, both migrated Meta URLs return 403 |
| Road to VR feature | Online |
| Unreal Engine forums thread | Online, but only the short version of the post |

Everything here was rebuilt from Internet Archive snapshots taken while the
images were still being served: 21 December 2013 and 28 March 2014 for the
MTBS3D thread, 19 April 2015 for the Oculus one.

The text is reproduced **verbatim and in its original order**, with the images
and videos restored to the positions they were written for. Nothing has been
edited, corrected, condensed or paraphrased.

## What is in here

```
index.html                          the archive page
images/                             15 images at original resolution
sources/mtbs3d-thread-full.txt      all 120 posts of the MTBS3D thread
sources/oculus-thread-full.txt      all 11 posts of the Oculus thread
sources/sun-temple-mod-README.txt   README.txt shipped inside the mod
sources/raw-html/                   the four Wayback captures, exactly as retrieved
tools/                              the scripts that produced the page
```

The `sources/raw-html/` captures are kept so every claim on the page can be
checked against what the Archive actually served, and so the material survives
even if the Archive itself becomes unreachable.

## Checking that nothing was altered

`tools/verify.py` diffs the text rendered on the page against the text in the
archived HTML, word by word, and fails if anything was dropped:

```sh
pip install beautifulsoup4
cd tools && POSITTRON_SRC=../sources/raw-html python3 verify.py
```

It should report `RESULT: no text lost`. The only two deliberate differences it
allows are phpBB's own `Code: Select all` button label, and long `-----` rules
that became `<hr>` elements.

The Sun Temple MOD download itself (a 507 MB packaged UE4 build) is too large
for the repository, so it is mirrored as a release asset:
[sun-temple-mod-2014](https://github.com/christt105/posittron-archive/releases/tag/sun-temple-mod-2014).
The original MediaFire link from the 2014 post is still live too, at
<https://www.mediafire.com/file/d51dzd5hv3r1mw3/Sun_Temple_VR_MOD.zip/file>.

## Publishing it

The page is a plain static site, so anything that serves files will do.

**GitHub Pages** (recommended, since the repository then doubles as the archive):

```sh
git init && git add . && git commit -m "feat: restore PosiTTron and Sun Temple archives"
gh repo create posittron-archive --public --source=. --push
gh api -X POST repos/:owner/posittron-archive/pages -f build_type=legacy \
  -F 'source[branch]=main' -F 'source[path]=/'
```

**Netlify / Vercel**: drag the folder onto their dashboard. No configuration,
no build command, output directory is the folder itself.

**Locally**: `python3 -m http.server` in this directory, or just open
`index.html`, which works from `file://` too.

## Credit and rights

All words, images, code and designs reproduced here are **Jordi Batallé's**,
written between January 2013 and December 2014. Forum replies quoted in the
restored threads belong to their respective authors. The Road to VR feature is
Ben Lang's and is only linked, not reproduced.

This is an archival reproduction assembled so the work stops depending on dead
links. It is meant to be handed over to its author, who should feel free to
take it, move it, rewrite it or ask for it to come down.
