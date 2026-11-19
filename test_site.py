# SPDX-License-Identifier: AGPL-3.0-only
import unittest, json, tempfile, zipfile
from pathlib import Path
from html.parser import HTMLParser
from build_site import build, ROOT, PAGES
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.scripts=0
 def handle_starttag(self,tag,attrs):
  self.scripts+=tag=='script'
  self.links += [v for k,v in attrs if k in ('href','src') and v]
class Site(unittest.TestCase):
 @classmethod
 def setUpClass(cls):build()
 def test_pages_and_links(self):
  site=ROOT/'dist/site'
  for f in PAGES.values():
   p=Links();p.feed((site/f).read_text());self.assertEqual(p.scripts,0)
   for link in p.links:
    if not link.startswith('https://'):self.assertTrue((site/link).is_file(),link)
 def test_source_and_license(self):
  site=ROOT/'dist/site'
  with zipfile.ZipFile(site/'ReveriTrace-source.zip') as z:
   self.assertIn('build_site.py',z.namelist());self.assertEqual(z.read('plugin/LICENSE'),(site/'LICENSE.txt').read_bytes())
  with zipfile.ZipFile(site/'ReveriTrace-plugin.zip') as z:
   m=json.loads(z.read('plugin.json'));self.assertEqual(m['license'],'AGPL-3.0-only');self.assertNotIn('author',m);self.assertNotIn('websiteURL',m['extensions']['com.openai']['interface'])
 def test_unapproved_release_refused(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'config.json';p.write_text('{}')
   with self.assertRaises(ValueError):build(p)
if __name__=='__main__':unittest.main()
