# SPDX-License-Identifier: AGPL-3.0-only
import unittest,tempfile,zipfile,json
from pathlib import Path
from verify_rotation import compare
class RotationTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
 def archive(self,name,days,extra=False):
  p=self.root/name
  with zipfile.ZipFile(p,'w') as z:
   prefix='Takeout/YouTube and YouTube Music/history/'
   z.writestr(prefix+'watch-history.json',json.dumps([{'title':'Watched test','titleUrl':'https://www.youtube.com/watch?v=abcdefghijk','time':f'2024-06-{d:02}T12:00:00Z','products':['YouTube']} for d in days]))
   z.writestr(prefix+'search-history.json','[]')
   if extra:z.writestr('Takeout/Other/private.txt','test')
  return str(p)
 def test_superset(self):
  a=self.archive('a.zip',[1,2]);b=self.archive('b.zip',[1]);self.assertTrue(compare([a],[b])['safe_content_replacement']);self.assertTrue(Path(b).exists())
 def test_missing(self):
  a=self.archive('a.zip',[2]);b=self.archive('b.zip',[1]);self.assertFalse(compare([a],[b])['safe_content_replacement'])
 def test_unrelated(self):
  a=self.archive('a.zip',[1],True);b=self.archive('b.zip',[1]);self.assertRaises(ValueError,compare,[a],[b])
 def test_same_file(self):
  a=self.archive('a.zip',[1]);self.assertRaises(ValueError,compare,[a],[a])
if __name__=='__main__':unittest.main()
