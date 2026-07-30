from __future__ import annotations

import os
import sys
from urllib.error import URLError
from urllib.request import urlopen

BASE = os.getenv("MOSAIC_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
ROUTES = ("/", "/runs", "/settings")
THEMES = ("dark", "light")

CONTRAST_JS = r"""
() => {
  const lin=c=>{c/=255;return c<=.04045?c/12.92:Math.pow((c+.055)/1.055,2.4)};
  const lum=([r,g,b])=>.2126*lin(r)+.7152*lin(g)+.0722*lin(b);
  const ratio=(a,b)=>{const [x,y]=[lum(a),lum(b)].sort((p,q)=>q-p);return(x+.05)/(y+.05)};
  function rgba(s){const m=(s||'').match(/[\d.]+/g);if(!m)return null;const unit=s.startsWith('color(')?255:1;return{rgb:m.slice(0,3).map(v=>Math.round(+v*unit)),a:m.length>3?+m[3]:1}}
  const blend=(fg,bg,a)=>fg.map((c,i)=>Math.round(c*a+bg[i]*(1-a)));
  function background(el){const stack=[];for(let n=el;n&&n!==document.documentElement;n=n.parentElement){const c=rgba(getComputedStyle(n).backgroundColor);if(c&&c.a>0){stack.push(c);if(c.a>=.999)break}}const root=rgba(getComputedStyle(document.documentElement).backgroundColor);let out=root&&root.a>=.999?root.rgb:[255,255,255];for(let i=stack.length-1;i>=0;i--)out=blend(stack[i].rgb,out,stack[i].a);return out}
  const bad=[];document.querySelectorAll('*').forEach(el=>{if(el.offsetParent===null||![...el.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()))return;const cs=getComputedStyle(el);const fg=rgba(cs.color);if(!fg||fg.a<.6)return;const size=parseFloat(cs.fontSize),need=(size>=24||(size>=18.66&&+cs.fontWeight>=700))?3:4.5;const bg=background(el),r=ratio(blend(fg.rgb,bg,fg.a),bg);if(r<need)bad.push(`contrast ${r.toFixed(2)} needs ${need}: ${el.tagName.toLowerCase()}.${String(el.className).slice(0,30)}`)});return[...new Set(bad)]}
"""

SEMANTICS_JS = r"""
() => {const out=[];const named=el=>(el.getAttribute('aria-label')||el.getAttribute('title')||el.textContent||'').trim();document.querySelectorAll('button,a[href]').forEach(el=>{if(el.offsetParent!==null&&!named(el))out.push(`unnamed ${el.tagName.toLowerCase()}`)});document.querySelectorAll('input,select,textarea').forEach(el=>{if(!((el.labels&&el.labels.length)||el.getAttribute('aria-label')||el.getAttribute('aria-labelledby')))out.push(`unlabelled ${el.id||el.type}`)});const seen={};document.querySelectorAll('[id]').forEach(el=>{if(seen[el.id])out.push(`duplicate id ${el.id}`);seen[el.id]=1});const h1=[...document.querySelectorAll('h1')].filter(el=>el.offsetParent!==null);if(h1.length!==1)out.push(`expected one h1, found ${h1.length}`);if(!document.querySelector('main'))out.push('missing main landmark');const skip=document.querySelector('a[href^="#"]');if(!skip||!document.querySelector(skip.getAttribute('href')))out.push('missing valid skip link');if(!document.documentElement.lang)out.push('missing lang');return[...new Set(out)]}
"""


def main() -> int:
    from playwright.sync_api import sync_playwright

    try:
        with urlopen(BASE, timeout=5) as response:  # noqa: S310 - configurable test URL
            if response.status != 200:
                return 1
    except (URLError, OSError):
        print(f"No Mosaic server at {BASE}")
        return 1
    findings = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for theme in THEMES:
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.goto(BASE, wait_until="networkidle")
            page.evaluate("theme => localStorage.setItem('mosaic-theme', theme)", theme)
            for route in ROUTES:
                page.goto(BASE + route, wait_until="networkidle")
                page.wait_for_timeout(250)
                for issue in page.evaluate(CONTRAST_JS) + page.evaluate(SEMANTICS_JS):
                    findings.append(f"{theme} {route}: {issue}")
            page.close()
        browser.close()
    if findings:
        print("\n".join(findings))
        return 1
    print(f"Accessibility check passed: {len(ROUTES) * len(THEMES)} page states.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
