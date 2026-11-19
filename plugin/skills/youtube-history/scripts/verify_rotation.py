#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Read-only content comparison for explicitly selected complete history ZIP sets."""
import argparse, json, sys, sqlite3, zipfile
from pathlib import Path
from history import connect, ingest, history_member

def snapshot(paths):
    # Reject archives with non-history files rather than permitting broad export cleanup.
    if not paths: raise ValueError('Empty archive set')
    kinds=set()
    for p in map(Path, paths):
        if not p.is_file() or p.is_symlink() or p.suffix.lower()!='.zip':
            raise ValueError('Expected regular ZIP archive')
        with zipfile.ZipFile(p) as z:
            members=[m for m in z.infolist() if not m.is_dir()]
            if not members: raise ValueError('Empty archive')
            for m in members:
                if history_member(m.filename): kinds.add(Path(m.filename).name.lower())
                elif Path(m.filename).name.lower() not in {'archive_browser.html','archive_browser.json'}:
                    raise ValueError('Archive contains non-history data')
    if kinds!={'watch-history.json','search-history.json'}: raise ValueError('Both history categories required')
    db=connect(':memory:')
    try:
        reports=ingest(db,paths)
        if not reports or any(r.get('status') not in ('imported','unchanged') or r.get('skipped',0) for r in reports):
            raise ValueError('Incomplete or invalid import')
        rows={r[0] for r in db.execute('SELECT fingerprint FROM events')}
        if not rows: raise ValueError('Empty history')
        return rows
    finally: db.close()

def compare(new,old):
    if {Path(p).resolve() for p in new}&{Path(p).resolve() for p in old}: raise ValueError('Archive sets overlap')
    a,b=snapshot(new),snapshot(old)
    missing=len(b-a)
    return {'safe_content_replacement':missing==0,'new_events':len(a),'old_events':len(b),'missing_old_events':missing,'remote_provenance_verified':False,'files_deleted':0}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--new',nargs='+',required=True);p.add_argument('--old',nargs='+',required=True);a=p.parse_args()
    try: result=compare(a.new,a.old)
    except (OSError,ValueError,RuntimeError,sqlite3.Error,zipfile.BadZipFile) as e: result={'safe_content_replacement':False,'error':str(e),'files_deleted':0}
    print(json.dumps(result));return 0 if result['safe_content_replacement'] else 1
if __name__=='__main__':sys.exit(main())
