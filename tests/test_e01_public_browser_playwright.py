"""Security and zero-cost preflight tests; no browser side effects."""
import unittest
from agents.e01_public_browser_playwright import (
 URLS,HOSTS,validate_public_url,classify_view)

class TestPublicBrowserPlaywright(unittest.TestCase):
 def test_only_three_explicit_public_urls(self):
  self.assertEqual(set(URLS),{
   "browser_canary","playwright_docs","agnes_public_docs"})
  for name,url in URLS.items():
   self.assertTrue(validate_public_url(name,url))
  for url in (
   "https://example.com.evil.invalid/",
   "http://example.com/",
   "https://example.com/?key=TOKEN",
   "https://user:pass@example.com/",
   "https://platform.agnes-ai.com/",
   "file:///etc/passwd"):
   self.assertFalse(validate_public_url("browser_canary",url))
 def test_false_html_or_errors_never_count(self):
  self.assertEqual(classify_view("browser_canary","Example Domain",200),
                   "PUBLIC_DOCUMENT_READ_ONLY")
  for code in (0,302,403,404,429,500):
   with self.subTest(code=code):
    self.assertNotEqual(classify_view("browser_canary","Example Domain",code),
                        "PUBLIC_DOCUMENT_READ_ONLY")
  self.assertNotEqual(classify_view("browser_canary","Sign in",200),
                      "PUBLIC_DOCUMENT_READ_ONLY")
 def test_public_document_is_not_provider_api_generation(self):
  self.assertEqual(classify_view("agnes_public_docs","Pricing Docs",200),
                   "PUBLIC_DOCUMENT_READ_ONLY")
  self.assertNotIn("platform.agnes-ai.com",HOSTS)
if __name__=="__main__":
 unittest.main()
