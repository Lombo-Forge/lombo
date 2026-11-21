"""Checks for the static site in site/. Run with: python3 -m unittest discover -s tests"""

import re
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

ALLOWED_HOSTS = {"github.com", "ko-fi.com", "www.gnu.org", "openfontlicense.org"}
PLACEHOLDER_HOST = "lombo-forge.github.io"  # the manifest address constant, see docs/site.md


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.imgs = []
        self.ids = set()
        self.landmarks = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag in ("header", "main", "footer", "nav"):
            self.landmarks.add(tag)
        if tag == "img":
            self.imgs.append(a)
        for key in ("href", "src"):
            if key in a:
                self.refs.append(a[key])


def parse(name):
    p = Page()
    p.feed((SITE / name).read_text(encoding="utf-8"))
    return p


class SiteTest(unittest.TestCase):
    def test_manifest_copy_matches(self):
        subprocess.run(["sh", str(ROOT / "scripts" / "build-site.sh")], check=True, capture_output=True)
        self.assertEqual((ROOT / "manifest.json").read_bytes(), (SITE / "manifest.json").read_bytes())

    def test_links_and_assets(self):
        page = parse("index.html")
        css = (SITE / "style.css").read_text(encoding="utf-8")
        refs = page.refs + re.findall(r"url\(['\"]?([^'\")]+)", css)
        for ref in refs:
            u = urlparse(ref)
            if u.scheme in ("http", "https"):
                self.assertIn(u.hostname, ALLOWED_HOSTS, f"external URL not allowed: {ref}")
            elif u.scheme:
                self.fail(f"unexpected scheme: {ref}")
            elif u.path:
                self.assertTrue((SITE / u.path).is_file(), f"missing local file: {ref}")
            elif u.fragment:
                self.assertIn(u.fragment, page.ids, f"missing anchor: {ref}")

    def test_no_external_requests_loaded(self):
        # Images, stylesheets and fonts must be local; only <a> links may leave the site.
        text = (SITE / "index.html").read_text(encoding="utf-8")
        for m in re.finditer(r"<(?:img|link|script|iframe)\b[^>]*?(?:src|href)=\"(https?:[^\"]+)", text):
            self.fail(f"external resource: {m.group(1)}")
        self.assertNotIn("<script", text)

    def test_images_have_alt_and_size(self):
        for img in parse("index.html").imgs:
            self.assertIn("alt", img, f"img without alt: {img}")
            self.assertTrue(img.get("width") and img.get("height"), f"img without size: {img}")

    def test_landmarks(self):
        self.assertEqual({"header", "main", "footer"}, parse("index.html").landmarks)

    def test_manifest_url_constant_in_one_place(self):
        text = (SITE / "index.html").read_text(encoding="utf-8")
        self.assertEqual(text.count(PLACEHOLDER_HOST), 1)

    def test_disclaimer_and_kofi(self):
        text = (SITE / "index.html").read_text(encoding="utf-8")
        self.assertIn("not affiliated with or endorsed by the Jellyfin project", text)
        self.assertIn("https://ko-fi.com/datlombardo", text)


if __name__ == "__main__":
    unittest.main()
