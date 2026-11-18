"""Public-source Chromium browser, replacing TinyFish for reproducible no-login audits.

GitHub Actions + Playwright. Never navigates authenticated sessions or performs
payments, logins, video submissions, CAPTCHA bypass, provider quota evasion,
background scraping, or posts. Public docs proof only.
"""
from __future__ import annotations
import json
import os
import re
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse

OUT=Path("artifacts/e01_public_browser_playwright")
URLS={
  "browser_canary":"https://example.com/",
  "playwright_docs":"https://playwright.dev/docs/ci",
  "agnes_public_docs":"https://wiki.agnes-ai.com/en/docs/pricing.md",
}
HOSTS={"example.com","playwright.dev","wiki.agnes-ai.com"}
NO_EXTERNAL_LOGIN=True
NO_GENERATION=True
NO_AUTOMATED_SIGNUP=True
NO_COST=True

def validate_public_url(name,url):
 if name not in URLS or URLS[name]!=url:return False
 p=urlparse(url)
 return (p.scheme=="https" and p.hostname in HOSTS and
         not p.username and not p.password and not p.query
         and not p.fragment and p.port is None)

def classify_view(name,title,status):
 if status is None:return "BLOCKED_NO_HTTP_STATUS"
 if status<200 or status>=300:return "BLOCKED_HTTP_STATUS"
 if not isinstance(title,str) or not title.strip():return "BLOCKED_EMPTY_TITLE"
 if name=="browser_canary" and "Example Domain" not in title:
  return "BLOCKED_UNEXPECTED_CANARY"
 return "PUBLIC_DOCUMENT_READ_ONLY"

def run():
 from playwright.sync_api import sync_playwright, Error as PlaywrightError
 OUT.mkdir(parents=True,exist_ok=True)
 report={
   "schema_version":"1.0.0",
   "project":"verbo-no-chao",
   "mode":"CHROMIUM_READ_ONLY_PUBLIC_BROWSER",
   "replaces":"TinyFish for public unauthenticated research, NOT cloud authenticated Work browser",
   "no_account":True,"no_token":True,"no_video_generation":True,
   "no_signup":True,"no_cost_incurred":True,
   "no_scraping_or_captcha_bypass":True,"cookies_exported":False,
   "browser_capability_confirmed":False,"third_party_video_created":False,
   "entries":[]
 }
 try:
  with sync_playwright() as playwright:
   browser=playwright.chromium.launch(headless=True)
   context=browser.new_context(
     viewport={"width":1024,"height":768},
     locale="pt-BR",accept_downloads=False,
     ignore_https_errors=False,service_workers="block")
   page=context.new_page()
   for name,url in URLS.items():
    assert validate_public_url(name,url)
    rec={"source":name,"url":url,"result":"NOT_ATTEMPTED",
         "navigated":False,"no_login":True}
    try:
     response=page.goto(url,wait_until="domcontentloaded",timeout=26000)
     status=response.status if response is not None else None
     title=page.title()[:160]
     rec.update(status=status,title=title,navigated=True,
                result=classify_view(name,title,status))
     if name=="browser_canary" and rec["result"]=="PUBLIC_DOCUMENT_READ_ONLY":
      if page.locator("h1").count()>0:
       heading=page.locator("h1").first.inner_text(timeout=3000)
       if heading.strip()=="Example Domain":
        rec["public_heading_verified"]=True
       else:
        rec["result"]="BLOCKED_UNEXPECTED_CANARY_HEADING"
      else:
       rec["result"]="BLOCKED_CANARY_HEADING_ABSENT"
     if name=="playwright_docs" and rec["result"]=="PUBLIC_DOCUMENT_READ_ONLY":
      if "Playwright" in title and page.locator("body").count()>0:
       rec["official_document_title_verified"]=True
       rec["screenshot"]="official_playwright_public_page.png"
       page.screenshot(path=str(OUT/rec["screenshot"]),
                       full_page=False,animations="disabled")
       report["browser_capability_confirmed"]=True
      else:
       rec["result"]="BLOCKED_OFFICIAL_DOC_NOT_VERIFIED"
    except (PlaywrightError,ValueError) as e:
     rec.update(result="BLOCKED_PUBLIC_SITE_OR_BROWSER",
                reason=type(e).__name__,navigated=False)
    report["entries"].append(rec)
   context.close()
   browser.close()
 except (PlaywrightError,OSError) as err:
  report["fatal_error_type"]=type(err).__name__
 report["status"]=("PHYSICAL_CHROMIUM_PUBLIC_BROWSER_VERIFIED_NO_LOGIN"
      if report["browser_capability_confirmed"]
      else "BLOCKED_BROWSER_PROOF_NOT_OBTAINED")
 (OUT/"public_browser_proof.json").write_text(
    json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":report["status"],
   "public_sources_checked":len(report["entries"]),
   "no_login":True,"no_video_generated":True},ensure_ascii=False),flush=True)
 return 0 if report["browser_capability_confirmed"] else 2

if __name__=="__main__":
 raise SystemExit(run())
