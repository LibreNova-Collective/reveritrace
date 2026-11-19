# SPDX-License-Identifier: AGPL-3.0-only
"""Conservative admission policy for separately obtained local model artifacts.
Metadata is an owner assertion, not proof of rights. No downloads or remote APIs.
"""
import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

# Conservative technical gate, not an exhaustive legal compatibility determination.
ALLOWED_LICENSES = frozenset({'Apache-2.0','MIT','BSD-2-Clause','BSD-3-Clause','CC0-1.0','AGPL-3.0-only','AGPL-3.0-or-later'})
MODULES = frozenset({'sentence_transformers.models.Transformer','sentence_transformers.models.Pooling','sentence_transformers.models.Normalize','sentence_transformers.models.Transformer.Transformer','sentence_transformers.models.Pooling.Pooling','sentence_transformers.models.Normalize.Normalize'})
SAFE_SUFFIXES = frozenset({'.json','.txt','.md','.safetensors','.model','.vocab','.spm','.tiktoken'})
MANIFEST = 'reveritrace-model.json'
MAX_CONFIG = 8 * 1024 * 1024
MAX_FILES = 512


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def read_json(path):
    if path.stat().st_size>MAX_CONFIG: raise ValueError('MODEL_CONFIG_SIZE')
    return json.loads(path.read_text(encoding='utf-8'))


def reject_dynamic(value):
    if isinstance(value,dict):
        for k,v in value.items():
            if k in ('auto_map','custom_pipelines','trust_remote_code') and v: raise ValueError('MODEL_DYNAMIC_CODE')
            if k in ('tokenizer_file','vocab_file','merges_file','sentencepiece_model_file') and v:
                if not isinstance(v,str) or Path(v).name!=v or '/' in v or '\\' in v or ':' in v: raise ValueError('MODEL_EXTERNAL_PATH')
            reject_dynamic(v)
    elif isinstance(value,list):
        for x in value: reject_dynamic(x)


def validate(path):
    supplied=Path(path).expanduser()
    if not supplied.is_dir() or supplied.is_symlink(): raise ValueError('MODEL_DIRECTORY')
    root=supplied.resolve()
    manifest=root/MANIFEST
    if not manifest.is_file() or manifest.is_symlink(): raise ValueError('MODEL_MANIFEST_REQUIRED')
    m=read_json(manifest)
    if not isinstance(m,dict) or m.get('license') not in ALLOWED_LICENSES or m.get('rights_reviewed') is not True: raise ValueError('MODEL_LICENSE_REVIEW_REQUIRED')
    for key in ('source','revision','license_url'):
        if not isinstance(m.get(key),str) or not m[key].strip(): raise ValueError('MODEL_PROVENANCE_REQUIRED')
    for key in ('source','license_url'):
        u=urlparse(m[key]);
        if u.scheme!='https' or not u.hostname or u.username or u.password: raise ValueError('MODEL_PROVENANCE_URL')
    declared=m.get('sha256')
    if not isinstance(declared,dict) or not declared: raise ValueError('MODEL_HASHES_REQUIRED')
    seen={}; weights=False; count=0
    for directory, dirs, files in os.walk(root,followlinks=False):
        for d in dirs:
            if (Path(directory)/d).is_symlink() or d.startswith('.'): raise ValueError('MODEL_UNSAFE_DIRECTORY')
        for name in files:
            f=Path(directory)/name; rel=f.relative_to(root).as_posix()
            if rel==MANIFEST: continue
            count+=1
            if count>MAX_FILES or f.is_symlink() or not f.is_file(): raise ValueError('MODEL_UNSAFE_FILE')
            if f.name.startswith('.') or (f.suffix.lower() not in SAFE_SUFFIXES and f.name not in ('LICENSE','NOTICE','COPYING')): raise ValueError('MODEL_UNSAFE_FORMAT')
            if f.suffix.lower()=='.safetensors': weights=True
            if f.suffix.lower()=='.json': reject_dynamic(read_json(f))
            h=declared.get(rel)
            if not isinstance(h,str) or not re.fullmatch('[0-9a-f]{64}',h) or digest(f)!=h: raise ValueError('MODEL_HASH_MISMATCH')
            seen[rel]=h
    if set(seen)!=set(declared) or not weights: raise ValueError('MODEL_INCOMPLETE_OR_NO_SAFETENSORS')
    if not (root/'modules.json').is_file(): raise ValueError('MODEL_MODULES_REQUIRED')
    modules=read_json(root/'modules.json')
    if not isinstance(modules,list) or not modules: raise ValueError('MODEL_UNSUPPORTED_MODULE')
    for module in modules:
        if not isinstance(module,dict) or module.get('type') not in MODULES: raise ValueError('MODEL_UNSUPPORTED_MODULE')
        location=module.get('path','')
        if not isinstance(location,str) or (location and (Path(location).is_absolute() or '\\' in location or ':' in location or any(p in ('','.','..') for p in location.split('/')))): raise ValueError('MODEL_EXTERNAL_PATH')
        if not (root/location).is_dir(): raise ValueError('MODEL_EXTERNAL_PATH')
    if not any(Path(k).name in ('LICENSE','LICENSE.txt','LICENSE.md','COPYING') for k in seen): raise ValueError('MODEL_LICENSE_TEXT_REQUIRED')
    signature=hashlib.sha256(json.dumps({'files':seen,'source':m['source'],'revision':m['revision'],'license':m['license']},sort_keys=True).encode()).hexdigest()
    return root,signature
