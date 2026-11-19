# SPDX-License-Identifier: AGPL-3.0-only
import argparse, json, tempfile, unittest, zipfile
from pathlib import Path
import history

class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.d=Path(self.t.name);self.db=history.connect(self.d/'index.sqlite')
        self.records=[{'title':'Watched Dark Country Mix','time':'2024-06-01T15:00:00Z','titleUrl':'https://www.youtube.com/watch?v=abcdefghijk','products':['YouTube']},{'title':'Watched Dark Country Mix','time':'2024-06-02T15:00:00Z','titleUrl':'https://music.youtube.com/watch?v=abcdefghijk','products':['YouTube Music']},{'title':'Watched Other','time':'2024-06-03T15:00:00Z','products':['Search']},{'title':'Watched Broken','time':'invalid'}]
        self.z=self.d/'takeout.zip'
        with zipfile.ZipFile(self.z,'w') as f:
            f.writestr('Takeout/YouTube and YouTube Music/history/watch-history.json',json.dumps(self.records));f.writestr('Takeout/Chrome/watch-history.json',json.dumps(self.records));f.writestr('Takeout/YouTube and YouTube Music/history/search-history.json',json.dumps([{'title':'Searched for country','time':'2024-06-02T15:01:00Z'}]));f.writestr('../escape.txt','bad')
    def tearDown(self):self.db.close();self.t.cleanup()
    def test_zip_scope_and_repeat(self):
        r=history.ingest(self.db,[self.z]);self.assertEqual(sum(x['added'] for x in r),3);self.assertEqual(sum(x['skipped'] for x in r),2);self.assertFalse((self.d.parent/'escape.txt').exists());self.assertTrue(all(x['status']=='unchanged' for x in history.ingest(self.db,[self.z])))
    def test_dates_expansion(self):
        history.ingest(self.db,[self.z]);a=argparse.Namespace(start='2024-06-01',end='2024-06-30',tz='UTC',kind='watch',platform='all',query='country sombrío',expand=True,model=None,limit=10);r=history.search(self.db,a);self.assertEqual(len(r),1);self.assertEqual(r[0]['distinct_days'],2);self.assertEqual(r[0]['platforms'],['music','youtube']);a.end='2024-06-01';self.assertEqual(history.search(self.db,a)[0]['events'],1)
    def test_corrupt_retry(self):
        f=self.d/'bad.zip';f.write_bytes(b'partial');self.assertEqual(history.ingest(self.db,[f])[0]['status'],'error');f.write_bytes(self.z.read_bytes());self.assertEqual(sum(x['added'] for x in history.ingest(self.db,[f])),3)
    def test_accent_typo(self):
        self.assertEqual(history.normalize('SOMBRÍO'),'sombrio');self.assertEqual(history.score('parasyte', ['parasytee'],True),1)
    def test_auto_import_folder(self):
        self.assertEqual(sum(x['added'] for x in history.ingest(self.db,[self.d])),3);self.assertTrue(all(x['status']=='unchanged' for x in history.ingest(self.db,[self.d])))
    def test_startup_persisted_folder(self):
        with self.db: self.db.execute('INSERT INTO settings VALUES (?,?)',('inbox',str(self.d)))
        r=history.startup(self.db);self.assertEqual(r['new_events'],3);self.assertFalse(r['remote_freshness_verified']);self.assertEqual(history.startup(self.db)['new_events'],0)
        with self.db: self.db.execute('UPDATE settings SET value=? WHERE key=?',(str(self.d/'missing'),'inbox'))
        self.assertEqual(history.startup(self.db)['status'],'source_unavailable')
    def test_japanese_normalization(self):
        self.assertEqual(history.normalize('スペイン語字幕 ガ'), 'スペイン語字幕 ガ')
        self.assertIn('英語字幕',history.clues('subtitulos ingles',True))
    def test_semantic_cross_language(self):
        from semantic import LocalSemantic
        docs=['寄生獣 エンディング スペイン語字幕','アニメ 英語字幕 主題歌','football news','料理 レシピ','dark outlaw country mix']
        for q,expected in [('ending parasyte subtitulos español',0),('anime japanese english subtitles',1),('dark country sombrio',4)]:
            scores=LocalSemantic().rank(q,docs); self.assertEqual(scores.index(max(scores)),expected)
    def test_semantic_search(self):
        history.ingest(self.db,[self.z]);a=argparse.Namespace(start='2024-06-01',end='2024-06-30',tz='UTC',kind='watch',platform='all',query='country sombrío',expand=True,model=None,semantic='local',limit=10)
        r=history.search(self.db,a); self.assertEqual(r[0]['video_id'],'abcdefghijk'); self.assertEqual(r[0]['semantic_engine'],'local-lsa-multilingual-v2')
if __name__=='__main__':unittest.main()
