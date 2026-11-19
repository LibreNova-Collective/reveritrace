# SPDX-License-Identifier: AGPL-3.0-only
import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from model_policy import validate,digest,MANIFEST
from semantic import NeuralSemantic
from history import connect,ingest_bytes,startup

class ModelPolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.p=Path(self.tmp.name)
        (self.p/'LICENSE').write_text('Synthetic test fixture; not a real model license.')
        (self.p/'model.safetensors').write_bytes(b'fixture-not-real-weights')
        (self.p/'modules.json').write_text(json.dumps([{'idx':0,'name':'0','path':'','type':'sentence_transformers.models.Transformer'}]))
        (self.p/'config.json').write_text(json.dumps({'model_type':'bert'}))
        self.record()
    def tearDown(self): self.tmp.cleanup()
    def record(self,**kw):
        m={'license':'Apache-2.0','rights_reviewed':True,'source':'https://example.org/test-only','revision':'synthetic-test','license_url':'https://example.org/test-only/license','sha256':{x.relative_to(self.p).as_posix():digest(x) for x in self.p.rglob('*') if x.is_file() and x.name!=MANIFEST}}
        m.update(kw); (self.p/MANIFEST).write_text(json.dumps(m))
    def test_valid_manifest(self):
        self.assertEqual(validate(self.p)[0],self.p.resolve())
    def test_noncommercial_rejected(self):
        self.record(license='CC-BY-NC-4.0')
        with self.assertRaisesRegex(ValueError,'LICENSE_REVIEW'):validate(self.p)
    def test_missing_review(self):
        self.record(rights_reviewed=False)
        with self.assertRaisesRegex(ValueError,'LICENSE_REVIEW'):validate(self.p)
    def test_pickle_rejected(self):
        (self.p/'pytorch_model.bin').write_bytes(b'x');self.record()
        with self.assertRaisesRegex(ValueError,'UNSAFE_FORMAT'):validate(self.p)
    def test_modified_weight(self):
        (self.p/'model.safetensors').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'HASH_MISMATCH'):validate(self.p)
    def test_dynamic_code(self):
        (self.p/'config.json').write_text('{"auto_map":{"AutoModel":"unknown.Custom"}}'); self.record()
        with self.assertRaisesRegex(ValueError,'DYNAMIC_CODE'):validate(self.p)
    def test_custom_module(self):
        (self.p/'modules.json').write_text('[{"type":"unknown.Custom","path":""}]'); self.record()
        with self.assertRaisesRegex(ValueError,'UNSUPPORTED_MODULE'):validate(self.p)
    def test_path_escape(self):
        (self.p/'modules.json').write_text('[{"type":"sentence_transformers.models.Transformer","path":"../other"}]'); self.record()
        with self.assertRaisesRegex(ValueError,'EXTERNAL_PATH'):validate(self.p)
    def test_no_weights(self):
        (self.p/'model.safetensors').unlink(); self.record()
        with self.assertRaisesRegex(ValueError,'NO_SAFETENSORS'):validate(self.p)
    def test_symlink(self):
        (self.p/'linked.txt').symlink_to(self.p/'LICENSE'); self.record()
        with self.assertRaisesRegex(ValueError,'UNSAFE_FILE'):validate(self.p)
    def test_missing_manifest_before_import(self):
        (self.p/MANIFEST).unlink()
        with self.assertRaisesRegex(ValueError,'MANIFEST_REQUIRED'):NeuralSemantic(self.p,connect(':memory:'))
    def test_loader_flags_mock(self):
        # Real weights deliberately not bundled; verify invocation contract only.
        import types,sys
        from unittest.mock import Mock
        module=types.ModuleType('sentence_transformers');module.SentenceTransformer=Mock()
        db=connect(':memory:')
        with patch.dict(sys.modules,{'sentence_transformers':module}): NeuralSemantic(self.p,db)
        kw=module.SentenceTransformer.call_args.kwargs
        self.assertTrue(kw['local_files_only']);self.assertFalse(kw['trust_remote_code']);self.assertTrue(kw['model_kwargs']['use_safetensors']);db.close()
    def test_partial_quality_persists(self):
        db=connect(':memory:'); raw=b'[{"title":"bad","time":"invalid"}]'
        self.assertEqual(ingest_bytes(db,'watch-history.json',raw)['skipped'],1)
        self.assertEqual(ingest_bytes(db,'watch-history.json',raw)['skipped'],1);db.close()
if __name__=='__main__':unittest.main()
