#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Import explicitly supplied, timestamped recent YouTube activity records.

No network or credential access; input is a verified batch from the account owner
or an authorized source. Never infer timestamps from relative UI labels.
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse
from history import connect, ingest_bytes, timestamp, get_setting

MAX_BATCH = 16 * 1024 * 1024
HOSTS = {'www.youtube.com','youtube.com','m.youtube.com','music.youtube.com','youtu.be'}

def account_key(label):
    if not isinstance(label,str) or not label.strip():
        raise ValueError('An owner-selected account label is required')
    return hashlib.sha256(label.strip().encode('utf-8')).hexdigest()

def bind(db,label):
    key=account_key(label)
    previous=get_setting(db,'account_key')
    if previous and previous!=key:
        raise ValueError('Account mismatch: use a different database')
    if not previous and db.execute('SELECT count(*) FROM events').fetchone()[0]:
        raise ValueError('Existing unbound index: verify ownership, then use bind-existing explicitly')
    with db: db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)',('account_key',key))
    return key

def bind_existing(db,label):
    key=account_key(label); previous=get_setting(db,'account_key')
    if previous and previous!=key: raise ValueError('Account mismatch')
    with db: db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)',('account_key',key))
    return key

def plan(db, now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None: raise ValueError('Timezone required')
    # No checkpoint advances on partial UI traversal. Retain overlap to handle late events.
    latest=get_setting(db,'complete_increment_end')
    start=(datetime.fromisoformat(latest)-timedelta(days=2)) if latest else now-timedelta(days=14)
    start=min(start,now-timedelta(days=2))
    return {'from':start.isoformat(),'through':now.isoformat(),'account_bound':bool(get_setting(db,'account_key')),
            'strategy':'explicitly authorized recent records; not a live API','full_export':'provider schedule; do not request at every start'}

def import_batch(db,batch,label):
    key=account_key(label)
    if batch.get('account_key')!=key: raise ValueError('Batch/account mismatch')
    if batch.get('source') not in ('owner_export','authorized_recent_activity'):
        raise ValueError('Unsupported source')
    a=timestamp(batch.get('from')); b=timestamp(batch.get('through'))
    if a>b: raise ValueError('Invalid coverage range')
    rows=batch.get('events'); complete=batch.get('complete')
    if not isinstance(rows,list) or type(complete) is not bool: raise ValueError('Invalid batch')
    groups={'watch':[],'search':[]}
    # Fail closed before writing any row; unknown timestamps and non-YouTube links are excluded.
    for row in rows:
        if not isinstance(row,dict): raise ValueError('Invalid activity row')
        kind=row.get('kind'); platform=row.get('platform'); title=row.get('title'); raw=row.get('url','')
        stamp=timestamp(row.get('time'))
        if kind not in groups or platform not in ('youtube','music','unknown') or not isinstance(title,str) or not title.strip() or not a<=stamp<=b: raise ValueError('Invalid event kind, platform, title or timestamp')
        if not isinstance(raw,str): raise ValueError('Invalid URL')
        if raw:
            u=urlparse(raw)
            if u.scheme!='https' or u.hostname not in HOSTS or u.username or u.password: raise ValueError('Non-YouTube or unsafe URL')
        if kind=='watch' and (not raw or not re.search(r'(?:[?&]v=|youtu\.be/|/(?:shorts|live)/)[A-Za-z0-9_-]{11}(?:[?&#/]|$)',raw)):
            raise ValueError('Watch row requires verified video link')
        channel=row.get('channel','')
        if not isinstance(channel,str): raise ValueError('Invalid channel')
        groups[kind].append({'title':('Watched ' if kind=='watch' else 'Searched for ')+title.strip(),'titleUrl':raw,'time':stamp,'products':['YouTube Music' if platform=='music' else 'YouTube'],'subtitles':[{'name':channel}] if channel else []})
    previous=get_setting(db,'account_key')
    if not previous or previous!=key: raise ValueError('Bind and verify account before importing')
    expected=plan(db,datetime.fromisoformat(b))['from']
    # Only a fully traversed overlap with previous completed coverage can move cursor.
    advance=bool(complete and a<=timestamp(expected) and rows)
    reports=[]
    for kind,records in groups.items():
        if records:
            reports.append(ingest_bytes(db,kind+'-history.json',json.dumps(records,ensure_ascii=False,sort_keys=True).encode()))
    if any(x['skipped'] for x in reports): advance=False
    old=get_setting(db,'complete_increment_end')
    if old and b<=old: advance=False
    if advance:
        with db: db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)',('complete_increment_end',b))
    return {'reports':reports,'coverage_from':a,'coverage_through':b,'source_claimed_complete':complete,'checkpoint_advanced':advance,'remote_freshness_verified':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',required=True);p.add_argument('--account-label',required=True);s=p.add_subparsers(dest='cmd',required=True)
    s.add_parser('bind');s.add_parser('bind-existing');s.add_parser('plan');i=s.add_parser('import');i.add_argument('batch')
    a=p.parse_args()
    try:
        with connect(a.db) as db:
            if a.cmd=='bind': result={'account_key':bind(db,a.account_label)}
            elif a.cmd=='bind-existing': result={'account_key':bind_existing(db,a.account_label)}
            elif a.cmd=='plan':
                if get_setting(db,'account_key')!=account_key(a.account_label): raise ValueError('Bind matching account first')
                result=plan(db);result['account_key']=account_key(a.account_label)
            else:
                path=Path(a.batch)
                if path.stat().st_size>MAX_BATCH: raise ValueError('Batch exceeds limit')
                data=json.loads(path.read_text(encoding='utf-8-sig'))
                if not isinstance(data,dict): raise ValueError('Expected a JSON object')
                result=import_batch(db,data,a.account_label)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (OSError,ValueError,TypeError) as e:
        print(json.dumps({'status':'error','error':str(e)}),file=sys.stderr);return 1
if __name__=='__main__':sys.exit(main())
