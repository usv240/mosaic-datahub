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
  const bad=[];document.querySelectorAll('*').forEach(el=>{if(el.offsetParent===null||![...el.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()))return;const cs=getComputedStyle(el);const fg=rgba(cs.color);if(!fg||fg.a<.6)return;const size=parseFloat(cs.fontSize),need=(size>=24||(size>=18.66&&+cs.fontWeight>=700))?3:4.5;const bg=background(el),r=ratio(blend(fg.rgb,bg,fg.a),bg);if(r<need)bad.push(`contrast ${r.toFixed(2)} needs ${need}: ${el.tagName.toLowerCase()}.${String(el.className).slice(0,30)} text=${el.textContent.trim().slice(0,30)} parent=${el.parentElement?.className||el.parentElement?.tagName}`)});return[...new Set(bad)]}
"""

SEMANTICS_JS = r"""
() => {const out=[];const named=el=>(el.getAttribute('aria-label')||el.getAttribute('title')||el.textContent||'').trim();document.querySelectorAll('button,a[href]').forEach(el=>{if(el.offsetParent!==null&&!named(el))out.push(`unnamed ${el.tagName.toLowerCase()}`)});document.querySelectorAll('input,select,textarea').forEach(el=>{if(!((el.labels&&el.labels.length)||el.getAttribute('aria-label')||el.getAttribute('aria-labelledby')))out.push(`unlabelled ${el.id||el.type}`)});const seen={};document.querySelectorAll('[id]').forEach(el=>{if(seen[el.id])out.push(`duplicate id ${el.id}`);seen[el.id]=1});const h1=[...document.querySelectorAll('h1')].filter(el=>el.offsetParent!==null);if(h1.length!==1)out.push(`expected one h1, found ${h1.length}`);if(!document.querySelector('main'))out.push('missing main landmark');const skip=document.querySelector('a[href^="#"]');if(!skip||!document.querySelector(skip.getAttribute('href')))out.push('missing valid skip link');if(!document.documentElement.lang)out.push('missing lang');return[...new Set(out)]}
"""


def _finish_case(page, start_selector: str) -> None:
    page.locator(start_selector).click()
    for _ in range(5):
        page.locator("#advance-demo-step").click(timeout=5_000)
    page.locator("#narrator.is-complete").wait_for(timeout=5_000)


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
                if route == "/":
                    landing = page.evaluate(
                        "() => ({scrollY: window.scrollY, search: location.search, hash: location.hash})"
                    )
                    if landing != {"scrollY": 0, "search": "", "hash": ""}:
                        findings.append(
                            f"{theme} /: landing did not open cleanly at top: {landing}"
                        )
                if route == "/":
                    page.locator(".help").hover()
                    page.wait_for_timeout(200)
                for issue in page.evaluate(CONTRAST_JS) + page.evaluate(SEMANTICS_JS):
                    findings.append(f"{theme} {route}: {issue}")
            page.close()

        journey = browser.new_page(viewport={"width": 1440, "height": 1000})
        journey.emulate_media(reduced_motion="reduce")
        journey.goto(BASE, wait_until="networkidle")
        help_button = journey.locator(".help")
        help_tip = journey.locator("#metric-k-help")
        if help_tip.is_visible():
            findings.append("metric help tooltip was visible before interaction")
        if (
            help_button.get_attribute("aria-describedby") != "metric-k-help"
            or help_button.get_attribute("aria-controls") != "metric-k-help"
        ):
            findings.append("metric help trigger lost its accessible tooltip relationship")
        help_button.hover()
        journey.wait_for_timeout(200)
        help_box = help_tip.bounding_box()
        panel_box = journey.locator(".finding-panel").bounding_box()
        if not help_tip.is_visible():
            findings.append("metric help tooltip did not open on hover")
        elif (
            not help_box
            or not panel_box
            or help_box["x"] < panel_box["x"] - 1
            or help_box["x"] + help_box["width"] > panel_box["x"] + panel_box["width"] + 1
            or help_box["y"] < panel_box["y"] - 1
            or help_box["y"] + help_box["height"] > panel_box["y"] + panel_box["height"] + 1
        ):
            findings.append(
                f"metric help tooltip escaped its card: tip={help_box}, panel={panel_box}"
            )
        journey.locator("#workspace-title").hover()
        journey.wait_for_timeout(200)
        if help_tip.is_visible():
            findings.append("metric help tooltip stayed open after mouseleave")
        help_button.focus()
        if not help_tip.is_visible():
            findings.append("metric help tooltip did not open on keyboard focus")
        help_button.press("Escape")
        journey.wait_for_timeout(200)
        if help_tip.is_visible() or not help_button.evaluate(
            "element => document.activeElement === element"
        ):
            findings.append("Escape did not dismiss help while retaining trigger focus")
        help_button.click()
        journey.mouse.move(8, 8)
        journey.wait_for_timeout(200)
        if not help_tip.is_visible() or help_button.get_attribute("aria-expanded") != "true":
            findings.append("metric help click did not pin the tooltip")
        journey.locator("#workspace-title").click()
        journey.wait_for_timeout(200)
        if help_tip.is_visible() or help_button.get_attribute("aria-expanded") != "false":
            findings.append("outside click did not dismiss the metric help tooltip")

        disclosure_state = journey.evaluate(
            """() => ({
                deepOpen: document.querySelectorAll('.depth-disclosure[open]').length,
                evidenceOpen: document.querySelectorAll('.evidence-disclosure[open]').length,
                evidenceRows: document.querySelectorAll('.evidence-disclosure').length
            })"""
        )
        if disclosure_state != {"deepOpen": 0, "evidenceOpen": 0, "evidenceRows": 4}:
            findings.append(f"landing disclosure hierarchy regressed: {disclosure_state}")
        journey.locator(".depth-disclosure > summary").click()
        if not journey.locator(".depth-disclosure .capability-grid").is_visible():
            findings.append("DataHub deep dive did not reveal its evidence")
        journey.locator(".depth-disclosure > summary").click()
        journey.locator("#run-demo").click()
        start_scroll = journey.evaluate("window.scrollY")
        journey.wait_for_timeout(2_200)
        if journey.locator("#narrator-step").text_content() != "Step 1 of 6":
            findings.append("waiting advanced the standalone demo beyond step 1")
        if journey.locator("#activity-log li").count() != 1:
            findings.append("standalone demo logged more than one step after one click")
        if journey.locator("#narrator.is-complete").count() != 0:
            findings.append("standalone demo completed without five Continue clicks")
        for _ in range(5):
            journey.locator("#advance-demo-step").click(timeout=5_000)
        journey.locator("#narrator.is-complete").wait_for(timeout=5_000)
        completed_scroll = journey.evaluate("window.scrollY")
        if abs(completed_scroll - start_scroll) > 20:
            findings.append(
                f"guided demo moved the page without consent: {start_scroll} -> {completed_scroll}"
            )
        if not journey.locator("#narrator-actions").is_visible():
            findings.append("guided demo did not expose completion choices")
        journey.locator("#review-attack").click()
        journey.locator("#attack-verdict").filter(has_text="REFUSED").wait_for(timeout=5_000)
        if journey.locator("#attack-rows").inner_text() != "0":
            findings.append("attack replay did not preserve the zero-row boundary")
        journey.locator("#review-pr").click()
        generated_path = journey.locator("#generated-path").inner_text()
        if not generated_path.startswith("models/") or not generated_path.endswith(".sql"):
            findings.append(f"generated-code payoff did not open on model SQL: {generated_path}")
        journey.goto(BASE + "/?case=research", wait_until="networkidle")
        deep_link = journey.evaluate(
            "() => ({scrollY: window.scrollY, search: location.search, hash: location.hash})"
        )
        if deep_link != {"scrollY": 0, "search": "?case=research", "hash": ""}:
            findings.append(f"scenario reload did not return to the top: {deep_link}")
        journey.goto(BASE, wait_until="networkidle")
        journey.locator("#hero-run").click()
        journey.wait_for_timeout(300)
        if journey.locator("#tour-controller").is_visible():
            findings.append("hero CTA started the case explorer instead of only revealing choices")
        if journey.locator("[data-tour-result].is-verified").count() != 0:
            findings.append("hero CTA ran a case without explicit consent")
        journey.locator("#run-all-scenarios").click()
        journey.locator("#tour-controller").wait_for(state="visible")
        if not journey.locator("#run-demo").is_hidden():
            findings.append("case explorer exposed a duplicate workspace Run control")
        journey.wait_for_timeout(300)
        for issue in journey.evaluate(CONTRAST_JS) + journey.evaluate(SEMANTICS_JS):
            findings.append(f"manual explorer: {issue}")
        if (
            journey.locator("[data-tour-scenario='research']").get_attribute("aria-pressed")
            != "true"
        ):
            findings.append("manual explorer did not select the research case")
        if journey.locator("[data-tour-result].is-verified").count() != 0:
            findings.append("opening the manual explorer auto-ran a case")
        if journey.locator(".run-progress .is-active").count() != 0:
            findings.append("opening the manual explorer started investigation steps")
        if "No actions yet" not in journey.locator("#activity-log").inner_text():
            findings.append("opening the manual explorer changed the evidence log")
        journey.locator("#run-tour-case").click()
        journey.wait_for_timeout(2_200)
        if journey.locator("#narrator-step").text_content() != "Step 1 of 6":
            findings.append("waiting advanced the explorer beyond step 1")
        if journey.locator("#activity-log li").count() != 1:
            findings.append("explorer logged more than one step after one click")
        for _ in range(3):
            journey.locator("#advance-demo-step").click(timeout=5_000)
        journey.locator("#reset-demo").click()
        journey.wait_for_timeout(500)
        if journey.locator("#run-tour-case").is_disabled():
            findings.append("resetting a case left the manual Run control disabled")
        if journey.locator("[data-tour-scenario='research']").is_disabled():
            findings.append("resetting a case left scenario selection disabled")
        if journey.locator("[data-tour-result].is-verified").count() != 0:
            findings.append("resetting a case incorrectly recorded a verified result")

        for index, name in enumerate(("research", "mitigated", "control", "audience"), start=1):
            if index > 1:
                journey.locator("#next-tour-case").click()
                if (
                    journey.locator(f"[data-tour-scenario='{name}']").get_attribute("aria-pressed")
                    != "true"
                ):
                    findings.append(f"Next case did not select {name}")
                if journey.locator(".run-progress .is-active").count() != 0:
                    findings.append(f"selecting {name} auto-started its investigation")
            _finish_case(journey, "#run-tour-case")
            verified = journey.locator("[data-tour-result].is-verified").count()
            if verified != index:
                findings.append(
                    f"manual explorer verified {verified} cases after explicit run {index}"
                )
            if index < 4 and not journey.locator("#tour-summary").is_hidden():
                findings.append("comparison opened before the user requested it")

        for issue in journey.evaluate(CONTRAST_JS) + journey.evaluate(SEMANTICS_JS):
            findings.append(f"completed manual explorer: {issue}")
        if not journey.locator("#compare-tour").is_visible():
            findings.append("manual explorer did not expose Compare results")
        if not journey.locator("#tour-summary").is_hidden():
            findings.append("fourth case auto-opened the comparison")
        journey.locator("#compare-tour").click()
        journey.locator("#tour-summary").wait_for(state="visible", timeout=5_000)
        journey.wait_for_timeout(500)
        summary_box = journey.locator("#tour-summary").bounding_box()
        summary_top = summary_box["y"] if summary_box else None
        if summary_top is None or summary_top < -5 or summary_top > 120:
            findings.append(f"requested comparison was not brought into view: top={summary_top}")
        verified_cases = journey.locator("[data-tour-result].is-verified").count()
        if verified_cases != 4:
            findings.append(f"manual explorer verified {verified_cases} cases instead of 4")
        if (
            journey.locator("[data-tour-result='control'] small").inner_text()
            != "Verified clear / no data query"
        ):
            findings.append("manual explorer did not preserve the negative-control refusal")
        if not journey.locator("#review-tour").is_visible():
            findings.append("manual explorer did not expose its comparison action")
        if journey.locator("#tour-summary .tour-adopt a").count() != 3:
            findings.append("manual explorer did not expose all adoption paths")
        journey.close()

        hydration_race = browser.new_page(viewport={"width": 1200, "height": 800})
        delayed_assessment = []
        hydration_race.route("**/api/assessment", lambda route: delayed_assessment.append(route))
        hydration_race.goto(BASE, wait_until="domcontentloaded")
        hydration_race.locator("#run-demo").wait_for()
        hydration_race.wait_for_timeout(200)
        if len(delayed_assessment) != 1:
            findings.append(
                f"late-hydration regression did not capture one assessment: {len(delayed_assessment)}"
            )
        else:
            hydration_race.locator("#run-demo").click()
            delayed_assessment[0].continue_()
            hydration_race.wait_for_timeout(900)
            hydration_state = hydration_race.evaluate(
                """() => ({
                    step: document.querySelector('#narrator-step').textContent,
                    logs: document.querySelectorAll('#activity-log li').length,
                    continueVisible: !document.querySelector('#advance-demo-step').hidden
                })"""
            )
            if hydration_state != {
                "step": "Step 1 of 6",
                "logs": 1,
                "continueVisible": True,
            }:
                findings.append(f"late hydration reset an active demo: {hydration_state}")
        hydration_race.close()

        receipt_failure = browser.new_page(viewport={"width": 1200, "height": 800})
        receipt_failure.route("**/api/redteam", lambda route: route.abort("timedout"))
        receipt_failure.goto(BASE, wait_until="networkidle")
        receipt_failure.locator("#run-demo").click()
        for _ in range(3):
            receipt_failure.locator("#advance-demo-step").click(timeout=5_000)
        receipt_failure.wait_for_timeout(300)
        receipt_state = receipt_failure.evaluate(
            """() => ({
                step: document.querySelector('#narrator-step').textContent,
                continueDisabled: document.querySelector('#advance-demo-step').disabled,
                complete: document.querySelector('#narrator').classList.contains('is-complete'),
                verdict: document.querySelector('#attack-verdict').textContent
            })"""
        )
        if (
            receipt_state["step"] != "Step 4 of 6"
            or receipt_state["continueDisabled"]
            or receipt_state["complete"]
            or receipt_state["verdict"] != "Receipt unavailable"
        ):
            findings.append(
                f"failed policy receipt deadlocked or advanced the demo: {receipt_state}"
            )
        receipt_failure.close()

        mobile = browser.new_page(viewport={"width": 390, "height": 844}, has_touch=True)
        mobile.goto(BASE, wait_until="networkidle")
        mobile_metrics = mobile.evaluate(
            """() => ({
                clientWidth: document.documentElement.clientWidth,
                scrollWidth: document.documentElement.scrollWidth,
                presetCount: document.querySelectorAll('.compact-presets .preset-card').length,
                horizontalScroll: (() => { window.scrollTo(999, 0); const x = window.scrollX; window.scrollTo(0, 0); return x; })()
            })"""
        )
        if mobile_metrics["horizontalScroll"] > 1:
            overflow_sources = mobile.evaluate(
                """() => [...document.querySelectorAll('*')].filter(element => {
                    const rect = element.getBoundingClientRect();
                    if (rect.right <= document.documentElement.clientWidth + 1) return false;
                    for (let parent = element.parentElement; parent && parent !== document.body; parent = parent.parentElement) {
                        if (/(auto|hidden|scroll)/.test(getComputedStyle(parent).overflowX)) return false;
                    }
                    return true;
                }).slice(0, 8).map(element => ({tag: element.tagName, id: element.id, className: String(element.className).slice(0, 60), right: Math.round(element.getBoundingClientRect().right)}))"""
            )
            findings.append(
                f"mobile landing has horizontal overflow: {mobile_metrics}; sources={overflow_sources}"
            )
        if mobile_metrics["presetCount"] != 4:
            findings.append(f"mobile case picker is incomplete: {mobile_metrics}")
        mobile_help = mobile.locator(".help")
        mobile_tip = mobile.locator("#metric-k-help")
        mobile_help.scroll_into_view_if_needed()
        mobile_help.click()
        mobile.wait_for_timeout(200)
        mobile_help_box = mobile_help.bounding_box()
        mobile_tip_box = mobile_tip.bounding_box()
        mobile_panel_box = mobile.locator(".finding-panel").bounding_box()
        if (
            not mobile_tip.is_visible()
            or not mobile_help_box
            or mobile_help_box["width"] < 32
            or mobile_help_box["height"] < 32
            or not mobile_tip_box
            or not mobile_panel_box
            or mobile_tip_box["x"] < mobile_panel_box["x"] - 1
            or mobile_tip_box["x"] + mobile_tip_box["width"]
            > mobile_panel_box["x"] + mobile_panel_box["width"] + 1
            or mobile.evaluate("document.documentElement.scrollWidth")
            > mobile.evaluate("document.documentElement.clientWidth") + 1
        ):
            findings.append(
                "mobile metric help target or popover regressed: "
                f"button={mobile_help_box}, tip={mobile_tip_box}, panel={mobile_panel_box}"
            )
        mobile.locator("#workspace-title").click()
        mobile.wait_for_timeout(200)
        if mobile_tip.is_visible():
            findings.append("mobile metric help did not dismiss after outside tap")
        mobile.locator("#run-all-scenarios").click()
        mobile.locator("#tour-controller").wait_for(state="visible")
        mobile_explorer = mobile.evaluate(
            """() => ({
                clientWidth: document.documentElement.clientWidth,
                scrollWidth: document.documentElement.scrollWidth,
                caseButtons: document.querySelectorAll('[data-tour-scenario]').length,
                actionButtons: document.querySelectorAll('.tour-actions button').length,
                runVisible: !!document.querySelector('#run-tour-case')?.offsetParent
            })"""
        )
        if (
            mobile_explorer["scrollWidth"] > mobile_explorer["clientWidth"] + 1
            or mobile_explorer["caseButtons"] != 4
            or mobile_explorer["actionButtons"] != 4
            or not mobile_explorer["runVisible"]
        ):
            findings.append(f"mobile manual explorer regressed: {mobile_explorer}")
        mobile.close()
        browser.close()
    if findings:
        print("\n".join(findings))
        return 1
    print(f"Accessibility check passed: {len(ROUTES) * len(THEMES)} page states.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
