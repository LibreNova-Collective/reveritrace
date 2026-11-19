# SPDX-License-Identifier: AGPL-3.0-only
import unittest
from history import connect
from incremental import account_key,bind,import_batch,plan
class IncrementalTests(unittest.TestCase):
    def setUp(self):
        self.db=connect(':memory:');bind(self.db,'test-account')
        self.batch={'source':'authorized_recent_activity','account_key':account_key('test-account'),'from':'2024-01-01T00:00:00Z','through':'2024-01-15T00:00:00Z','complete':True,'events':[{'kind':'watch','platform':'music','title':'Sample song','url':'https://music.youtube.com/watch?v=TESTVIDEO01','time':'2024-01-10T10:00:00Z'}]}
    def tearDown(self):self.db.close()
    def test_idempotent(self):
        r=import_batch(self.db,self.batch,'test-account');self.assertTrue(r['checkpoint_advanced']);self.assertEqual(r['reports'][0]['added'],1)
        r=import_batch(self.db,self.batch,'test-account');self.assertEqual(r['reports'][0]['added'],0);self.assertFalse(r['checkpoint_advanced'])
    def test_wrong_account(self):
        with self.assertRaises(ValueError):import_batch(self.db,self.batch,'other-account')
    def test_partial_no_cursor(self):
        self.batch['complete']=False;r=import_batch(self.db,self.batch,'test-account');self.assertFalse(r['checkpoint_advanced'])
    def test_bad_url_no_rows(self):
        self.batch['events'][0]['url']='https://example.org/watch?v=TESTVIDEO01'
        with self.assertRaises(ValueError):import_batch(self.db,self.batch,'test-account')
        self.assertEqual(self.db.execute('select count(*) from events').fetchone()[0],0)
    def test_no_skipping_gap(self):
        import_batch(self.db,self.batch,'test-account'); self.batch.update({'from':'2024-02-01T00:00:00Z','through':'2024-02-02T00:00:00Z'});self.batch['events'][0]['time']='2024-02-01T01:00:00Z'
        self.assertFalse(import_batch(self.db,self.batch,'test-account')['checkpoint_advanced'])
if __name__=='__main__':unittest.main()
