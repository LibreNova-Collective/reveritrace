# SPDX-License-Identifier: AGPL-3.0-only
import unittest, json, tempfile, zipfile
from unittest.mock import patch
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
 def setUpClass(cls):
  workspace = tempfile.TemporaryDirectory()
  cls.addClassCleanup(workspace.cleanup)
  cls.output = Path(workspace.name)
  build(output=cls.output)
 def test_pages_and_links(self):
  site=self.output/'site'
  for f in PAGES.values():
   p=Links();p.feed((site/f).read_text());self.assertEqual(p.scripts,0)
   for link in p.links:
    if not link.startswith('https://'):self.assertTrue((site/link).is_file(),link)
 def test_source_and_license(self):
  site=self.output/'site'
  with zipfile.ZipFile(site/'ReveriTrace-source.zip') as z:
   self.assertIn('build_site.py',z.namelist());self.assertEqual(z.read('plugin/LICENSE'),(site/'LICENSE.txt').read_bytes())
  with zipfile.ZipFile(site/'ReveriTrace-plugin.zip') as z:
   m=json.loads(z.read('plugin.json'));self.assertEqual(m['license'],'AGPL-3.0-only');self.assertNotIn('author',m);self.assertNotIn('websiteURL',m['extensions']['com.openai']['interface'])
 def test_unapproved_release_refused(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'config.json';p.write_text('{}')
   with self.assertRaises(ValueError):build(p)
 def test_release_archives_follow_inventory(self):
  site = self.output / 'site'
  approved = (ROOT / 'release-files.txt').read_text().splitlines()
  with zipfile.ZipFile(site / 'ReveriTrace-source.zip') as archive:
   self.assertEqual(archive.namelist(), approved)
   self.assertIsNone(archive.testzip())
   self.assertTrue(all(entry.date_time == (1980, 1, 1, 0, 0, 0) for entry in archive.infolist()))
  with zipfile.ZipFile(site / 'ReveriTrace-plugin.zip') as archive:
   self.assertEqual(archive.namelist(), [name.removeprefix('plugin/') for name in approved if name.startswith('plugin/')])
   self.assertIsNone(archive.testzip())
   self.assertTrue(all(entry.date_time == (1980, 1, 1, 0, 0, 0) for entry in archive.infolist()))
   manifest = json.loads(archive.read('plugin.json'))
   interface = manifest['extensions']['com.openai']['interface']
   self.assertNotIn('.app.json', archive.namelist())
   self.assertIsNone(manifest.get('apps'))
   self.assertIsNone(manifest['extensions']['com.openai'].get('apps'))
   self.assertEqual(interface['category'], 'Productivity')
   self.assertLessEqual(len(interface['shortDescription']), 30)
   for key in ('logo', 'composerIcon'):
    icon = archive.read(interface[key])
    self.assertEqual(icon[:8], b'\x89PNG\r\n\x1a\n')
    self.assertEqual(tuple(int.from_bytes(icon[i:i+4], 'big') for i in (16, 20)), (512, 512))

 def test_unlisted_files_excluded_and_symlinks_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root = Path(d)
   (root / 'release-files.txt').write_text('plugin.json\n')
   (root / 'plugin.json').touch()
   private_file = root / 'private.json'
   private_file.touch()
   with patch('build_site.ROOT', root):
    from build_site import release_files
    self.assertEqual(list(release_files()), [('plugin.json', root / 'plugin.json')])
    (root / 'plugin.json').unlink()
    (root / 'plugin.json').symlink_to(private_file)
    with self.assertRaises(ValueError):
     list(release_files())

 def test_build_rejects_unexpected_output_files(self):
  with tempfile.TemporaryDirectory() as d:
   output = Path(d)
   (output / 'site').mkdir()
   (output / 'site' / 'private.json').touch()
   with self.assertRaisesRegex(ValueError, 'clean output'):
    build(output=output)

 def test_approvals_require_json_booleans(self):
  with tempfile.TemporaryDirectory() as d:
   config = Path(d) / 'config.json'
   config.write_text(json.dumps({
    'publisher': 'Synthetic publisher', 'base_url': 'https://preview.test',
    'support_url': 'https://support.test', 'effective_date': '2026-01-01',
    'publisher_verified': 'false', 'policies_approved': True, 'rights_confirmed': True,
   }))
   with self.assertRaisesRegex(ValueError, 'must confirm'):
    build(config, output=Path(d) / 'output')
 def test_approved_release_matches_site_and_archives(self):
  # Synthetic metadata exercises rendering without deploying or contacting GitHub.
  base = 'https://librenova-collective.github.io/reveritrace'
  support = 'https://github.com/LibreNova-Collective/reveritrace/issues'
  with tempfile.TemporaryDirectory() as d:
   root = Path(d)
   config = root / 'config.json'
   config.write_text(json.dumps({
    'publisher': 'Synthetic Publisher & Team', 'base_url': base + '/',
    'support_url': support, 'effective_date': '2026-01-01',
    'publisher_verified': True, 'policies_approved': True, 'rights_confirmed': True,
    'countries': ['ES', 'JP'],
   }))
   output = root / 'output'
   build(config, output=output)
   self.assertFalse(json.loads((output / 'build-status.json').read_text())['preview'])
   site = output / 'site'
   with zipfile.ZipFile(site / 'ReveriTrace-plugin.zip') as package, zipfile.ZipFile(
    site / 'ReveriTrace-source.zip'
   ) as source:
    manifest_bytes = package.read('plugin.json')
    self.assertEqual(source.read('plugin/plugin.json'), manifest_bytes)
    self.assertNotIn('config.json', source.namelist())
   listing = json.loads(manifest_bytes)['extensions']['com.openai']
   self.assertEqual(listing['interface']['developerName'], 'Synthetic Publisher & Team')
   self.assertEqual(listing['publication']['countries'], ['ES', 'JP'])
   for key, filename in PAGES.items():
    self.assertEqual(listing['interface'][key], f'{base}/{filename}')
    page = (site / filename).read_text()
    self.assertNotIn('PREVIEW', page)
    self.assertIn('Synthetic Publisher &amp; Team', page)
    if filename in {'privacy.html', 'terms.html'}:
     self.assertIn('2026-01-01', page)
    if filename != 'index.html':
     self.assertIn(support, page)
if __name__=='__main__':unittest.main()
