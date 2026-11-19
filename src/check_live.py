"""Check the live site: every page loads, every image, stylesheet, script and data file loads, every link resolves.

  python src/check_live.py [base_url]      default base: https://tejassnaikk.github.io/vehicle-complaint-classifier/
nhtsa.gov refuses automated clients (403), so those links are only listed.
"""
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://tejassnaikk.github.io/vehicle-complaint-classifier/").rstrip("/") + "/"
DOCS = Path(__file__).resolve().parents[1] / "docs"
UA = {"User-Agent": "Mozilla/5.0 (site check)"}


def get(url, head=False):
    req = urllib.request.Request(url, headers=UA, method="HEAD" if head else "GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.headers.get("content-type", ""), (b"" if head else r.read())
    except urllib.error.HTTPError as e:
        return e.code, "", b""
    except Exception as e:
        return 0, str(e), b""


def main():
    pages = sorted(p.name for p in DOCS.glob("*.html"))
    bad, ok, ext = [], 0, set()
    seen = set()
    for page in pages:
        st, ct, body = get(BASE + page)
        if st != 200 or "html" not in ct:
            bad.append((page, st, ct)); continue
        ok += 1
        h = body.decode("utf-8", "replace")
        for u in re.findall(r'(?:href|src)="([^"]+)"', h):
            if u.startswith(("#", "mailto:", "data:")):
                continue
            if u.startswith("http"):
                ext.add(u.split("#")[0]); continue
            seen.add(urljoin(BASE + page, u.split("#")[0]))
    for f in sorted((DOCS / "js").glob("*.js")):
        for u in re.findall(r"""["'](data/[\w.-]+)["']""", f.read_text()):
            seen.add(BASE + u)
    for u in sorted(seen):
        st, ct, _ = get(u, head=True)
        if st != 200:
            bad.append((u, st, ct))
        else:
            ok += 1
    gh_bad, gh_ok = [], 0
    for u in sorted(x for x in ext if "github.com/tejassnaikk" in x):
        st, _, _ = get(u, head=True)
        if st == 200:
            gh_ok += 1
        else:
            gh_bad.append((u, st))
    others = sorted(x for x in ext if "github.com/tejassnaikk" not in x)
    print(f"pages and site files OK: {ok}; failing: {len(bad)}")
    for b in bad:
        print("  FAIL", b)
    print(f"GitHub links OK: {gh_ok}; failing: {len(gh_bad)}")
    for b in gh_bad:
        print("  FAIL", b)
    print("other external links (not fetched, or blocked for bots):")
    for u in others:
        if "fonts.g" in u:
            continue
        st, _, _ = get(u, head=True)
        print(f"  {st} {u}")
    return 1 if bad or gh_bad else 0


if __name__ == "__main__":
    sys.exit(main())
