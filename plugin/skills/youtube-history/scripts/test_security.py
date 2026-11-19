# SPDX-License-Identifier: AGPL-3.0-only
import json, unittest
from history import connect, ingest_bytes, parse_record, history_member

class SecurityTests(unittest.TestCase):
    def row(self,url):
        return {'title':'Watched Sample','time':'2024-01-01T00:00:00Z','titleUrl':url,'products':['YouTube']}
    def test_untrusted_links(self):
        for url in ['https://example.org/watch?v=abcdefghijk','javascript:alert(1)','https://youtube.com@evil.example/watch?v=abcdefghijk','https://youtube.com:8443/watch?v=abcdefghijk','https://user:pass@youtube.com/watch?v=abcdefghijk','http://youtube.com/watch?v=abcdefghijk','https://youtube.com/redirect?q=https://example.org']:
            with self.subTest(url=url), self.assertRaises(ValueError): parse_record(self.row(url),'watch-history.json')
    def test_canonical_video_link(self):
        self.assertEqual(parse_record(self.row('https://youtu.be/abcdefghijk?si=tracking#fragment'),'watch-history.json')[6],'https://www.youtube.com/watch?v=abcdefghijk')
    def test_no_traversal_members(self):
        self.assertFalse(history_member('../YouTube/watch-history.json'))
        self.assertFalse(history_member('/YouTube/watch-history.json'))
        self.assertTrue(history_member('Takeout/YouTube/history/watch-history.json'))
    def test_reject_invalid_import(self):
        db=connect(':memory:')
        try:
            r=ingest_bytes(db,'watch-history.json',json.dumps([self.row('https://evil.example/watch?v=abcdefghijk')]).encode())
            self.assertEqual(r['skipped'],1)
            self.assertEqual(db.execute('select count(*) from events').fetchone()[0],0)
        finally: db.close()
    def test_search_url_not_exposed(self):
        r=self.row('https://www.youtube.com/results?search_query=private'); r['title']='Searched for private'
        self.assertEqual(parse_record(r,'search-history.json')[6],'')
if __name__=='__main__':unittest.main()
