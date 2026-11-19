#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Read-only export importer and local query utility. No network access."""
import argparse, hashlib, json, re, sqlite3, sys, zipfile, time, unicodedata
from difflib import SequenceMatcher
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs
try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

def connect(path):
    db=sqlite3.connect(path)
    db.row_factory=sqlite3.Row
    db.executescript('''CREATE TABLE IF NOT EXISTS events (fingerprint TEXT PRIMARY KEY, stamp TEXT NOT NULL, kind TEXT NOT NULL, platform TEXT NOT NULL, title TEXT NOT NULL, channel TEXT NOT NULL, url TEXT NOT NULL, video_id TEXT NOT NULL); CREATE INDEX IF NOT EXISTS events_stamp ON events(stamp); CREATE INDEX IF NOT EXISTS events_video ON events(video_id);''')
    try:
        db.execute('CREATE VIRTUAL TABLE IF NOT EXISTS event_fts USING fts5(fingerprint UNINDEXED,title,channel)')
    except sqlite3.OperationalError:
        pass
    db.execute('CREATE TABLE IF NOT EXISTS imported_files (digest TEXT PRIMARY KEY, imported_at TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS import_quality (digest TEXT PRIMARY KEY, skipped INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
    db.commit()
    return db

def timestamp(value):
    if not value: raise ValueError('missing timestamp')
    # datetime.fromisoformat accepts up to six fractional digits in older Python.
    value=re.sub(r'(\.\d{6})\d+',r'\1',str(value)).replace('Z','+00:00')
    d=datetime.fromisoformat(value)
    if d.tzinfo is None: raise ValueError('missing timezone')
    return d.astimezone(timezone.utc).isoformat(timespec='microseconds')

def parse_record(r, hint):
    t=str(r.get('title','')).strip(); url=str(r.get('titleUrl','') or '')
    if not t: raise ValueError('missing title')
    if len(t)>32768 or len(url)>8192: raise ValueError('title exceeds input limit')
    kind='search' if 'search' in hint or re.match(r'^(searched for|buscaste|has buscado)\b',t,re.I) else 'watch' if 'watch' in hint or re.match(r'^(watched|viste|has visto)\b',t,re.I) else 'other'
    title=re.sub(r'^(watched|searched for|viste|buscaste|has visto|has buscado)\s+','',t,flags=re.I)
    p=urlparse(url); host=(p.hostname or '').lower()
    # Only links to recognized YouTube hosts; never return arbitrary or credential-bearing URLs.
    if url and (p.scheme!='https' or host not in ('www.youtube.com','youtube.com','m.youtube.com','music.youtube.com','youtu.be') or p.username or p.password or p.port not in (None,443)):
        raise ValueError('unsafe or non-YouTube activity URL')
    products=' '.join(map(str,r.get('products',[]) or [])); header=str(r.get('header',''))
    platform='music' if host=='music.youtube.com' or 'youtube music' in (products+' '+header).lower() else 'youtube' if host in ('www.youtube.com','youtube.com','m.youtube.com','youtu.be') else 'unknown'
    vid=''
    if host in ('www.youtube.com','youtube.com','m.youtube.com','music.youtube.com'):
        vid=parse_qs(p.query).get('v',[''])[0] if p.path=='/watch' else ''
        if not vid and p.path.startswith(('/shorts/','/live/','/embed/')): vid=p.path.split('/')[2]
    elif host=='youtu.be': vid=p.path.strip('/').split('/')[0]
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}',vid): vid=''
    if kind!='watch': vid=''
    if kind not in ('watch','search'): raise ValueError('unsupported event')
    # Strip arbitrary redirect links and tracking parameters; keep a known video URL or no link.
    if kind=='watch' and url:
        if not vid: raise ValueError('watch URL has no valid video ID')
        url=('https://music.youtube.com/watch?v=' if platform=='music' else 'https://www.youtube.com/watch?v=')+vid
    elif kind=='search' and url:
        if host=='youtu.be' or p.path not in ('/results','/search'):
            raise ValueError('unsupported search URL')
        # Search terms are already stored in the title; avoid exposing URL parameters.
        url=''
    channel=' | '.join(str(x.get('name','')) for x in r.get('subtitles',[]) or [] if isinstance(x,dict))
    stamp=timestamp(r.get('time'))
    fp=hashlib.sha256(json.dumps([stamp,kind,vid or url or title],ensure_ascii=False).encode()).hexdigest()
    return fp,stamp,kind,platform,title,channel,url,vid

# Only recognized YouTube history JSON; never extract an archive to disk.
HISTORY_NAMES = {'watch-history.json','search-history.json'}
MAX_JSON = 256 * 1024 * 1024

def history_member(name):
    parts = name.replace('\\','/').lower().split('/')
    if any(x in ('', '.', '..') for x in parts): return False
    return parts[-1] in HISTORY_NAMES and any(x in ('youtube and youtube music','youtube','youtube music') for x in parts[:-1])

def ingest_bytes(db, name, raw):
    digest=hashlib.sha256(Path(name).name.lower().encode()+b'\0'+raw).hexdigest()
    if db.execute('SELECT 1 FROM imported_files WHERE digest=?',(digest,)).fetchone():
        quality=db.execute('SELECT skipped FROM import_quality WHERE digest=?',(digest,)).fetchone()
        return dict(file=name,status='unchanged',added=0,duplicates=0,skipped=quality[0] if quality else 0,quality_known=bool(quality))
    data=json.loads(raw.decode('utf-8-sig'))
    if not isinstance(data,list): raise ValueError('Expected Takeout JSON list')
    added=duplicates=skipped=0
    with db:
        for r in data:
            try:
                row=parse_record(r,name.lower())
                if row[2] not in ('watch','search'): raise ValueError('unsupported event')
                # Reject explicitly non-YouTube product markers in a supplied file.
                products=r.get('products') or []
                if products and (not isinstance(products,list) or any(str(x).casefold() not in ('youtube','youtube music','youtube and youtube music') for x in products)): raise ValueError('non-YouTube product')
            except (AttributeError,TypeError,ValueError): skipped+=1; continue
            cur=db.execute('INSERT OR IGNORE INTO events VALUES (?,?,?,?,?,?,?,?)',row)
            if cur.rowcount:
                added+=1
                try: db.execute('INSERT INTO event_fts VALUES (?,?,?)',(row[0],row[4],row[5]))
                except sqlite3.OperationalError: pass
            else:
                duplicates+=1
                # More explicit Music evidence can enrich an earlier normalized URL.
                if row[3]=='music': db.execute("UPDATE events SET platform='music' WHERE fingerprint=? AND platform!='music'",(row[0],))
        db.execute('INSERT INTO imported_files VALUES (?,?)',(digest,datetime.now(timezone.utc).isoformat()))
        db.execute('INSERT INTO import_quality VALUES (?,?)',(digest,skipped))
    return dict(file=name,status='imported',added=added,duplicates=duplicates,skipped=skipped)

def ingest(db, paths):
    report=[]
    for item in paths:
        path=Path(item)
        if path.is_symlink():
            report.append(dict(file=path.name,status='error',error='Symbolic links not accepted'));continue
        if path.is_dir():
            candidates=[x for x in path.rglob('*') if x.is_file() and not x.is_symlink() and (x.suffix.lower()=='.zip' or x.name.lower() in HISTORY_NAMES)]
            report.extend(ingest(db,sorted(candidates)));continue
        try:
            if path.suffix.lower()=='.zip':
                with zipfile.ZipFile(path) as z:
                    members=[m for m in z.infolist() if history_member(m.filename)]
                    if not members: report.append(dict(file=path.name,status='no_supported_history'))
                    for m in members:
                        if m.file_size>MAX_JSON: raise ValueError('History member exceeds size limit')
                        report.append(ingest_bytes(db,Path(m.filename).name,z.read(m)))
            elif path.name.lower() in HISTORY_NAMES:
                if path.stat().st_size>MAX_JSON: raise ValueError('History file exceeds size limit')
                report.append(ingest_bytes(db,path.name,path.read_bytes()))
            else: report.append(dict(file=path.name,status='unsupported'))
        except (OSError,ValueError,UnicodeError,zipfile.BadZipFile,RuntimeError) as e:
            report.append(dict(file=path.name,status='error',error=str(e)))
    return report

def normalize(t):
    from semantic import norm
    return norm(t)

# Auditable bilingual query expansion. This is heuristic, not an embedding model.
CONCEPTS=[('dark country','country sombrio','country oscuro','southern gothic','outlaw country','dark western','gothic country','swamp blues','dark folk'),('cowboy','vaquero','western','wild west','old west'),('mix','playlist','compilation','recopilacion','hour','hora','nonstop'),('anime','fandub','cover','ending','opening','romaji'),('ai generated','generado por ia','ai animation','animacion ia','ai music'),('japanese','japones','nihongo','日本語'),('subtitulos ingles','subtitulado ingles','english subtitles','eng sub','英語字幕'),('subtitulos espanol','subtitulado espanol','spanish subtitles','esp sub','スペイン語字幕','西語字幕'),('romaji','romanized','ローマ字'),('parasyte','kiseijuu','kiseiju','寄生獣'),('ending','エンディング'),('opening','オープニング'),('cover','fandub','カバー','歌ってみた'),('full version','cancion completa','フルバージョン')]

def clues(query, expand):
    terms=[normalize(x.strip()) for x in (query or '').split('|') if x.strip()]
    if expand:
        q=' '.join(terms)
        for family in CONCEPTS:
            if any(normalize(t) in q for t in family): terms.extend(map(normalize,family))
    return list(dict.fromkeys(terms))

def score(hay,terms,expand):
    hits=sum(t in hay for t in terms)
    if not expand or hits: return hits
    words=re.findall(r'\w+',hay)
    return int(any(len(t)>=5 and ' ' not in t and any(SequenceMatcher(None,t,w).ratio()>=.85 for w in words) for t in terms))

def search(db,a):
    try: tz=timezone.utc if a.tz=='UTC' else ZoneInfo(a.tz)
    except Exception as e: raise ValueError('Timezone unavailable; install system tzdata or use UTC') from e
    cond=[]; params=[]
    if a.start:
        cond.append('stamp>=?'); params.append(datetime.combine(date.fromisoformat(a.start),datetime.min.time(),tz).astimezone(timezone.utc).isoformat(timespec='microseconds'))
    if a.end:
        cond.append('stamp<?'); params.append(datetime.combine(date.fromisoformat(a.end)+timedelta(days=1),datetime.min.time(),tz).astimezone(timezone.utc).isoformat(timespec='microseconds'))
    if a.kind!='all': cond.append('kind=?');params.append(a.kind)
    if a.platform!='all': cond.append('platform=?');params.append(a.platform)
    engine=getattr(a,'semantic','off')
    if engine!='off' and getattr(a,'model',None): engine='neural'
    terms=clues(a.query,a.expand or engine!='off')
    groups={}
    for r in db.execute('SELECT * FROM events'+(' WHERE '+' AND '.join(cond) if cond else ''),params):
        hay=normalize(r['title']+' '+r['channel'])
        hits=score(hay,terms,a.expand or engine!='off')
        if terms and not hits and engine=='off': continue
        key=(r['kind'],r['video_id'] or r['url'] or r['title'].casefold())
        g=groups.setdefault(key,dict(title=r['title'],channel=r['channel'],url=r['url'],video_id=r['video_id'],kind=r['kind'],platforms=set(),events=0,days=set(),times=[],clue_hits=0))
        dt=datetime.fromisoformat(r['stamp']).astimezone(tz)
        g['events']+=1;g['days'].add(dt.date().isoformat());g['times'].append(dt.isoformat());g['platforms'].add(r['platform']);g['clue_hits']=max(g['clue_hits'],hits)
    results=[]
    for g in groups.values():
        g['platforms']=sorted(g['platforms']);g['days']=sorted(g['days']);g['distinct_days']=len(g['days']);g['times'].sort();results.append(g)
    if engine!='off' and a.query and results:
        from semantic import LocalSemantic, NeuralSemantic
        try:
            model=NeuralSemantic(a.model,db) if engine=='neural' else LocalSemantic()
            values=model.rank(a.query.replace('|',' '),[g['title']+' '+g['channel'] for g in results])
        except (ImportError,OSError,ValueError,RuntimeError,TypeError) as e:
            print(json.dumps({'semantic_status':'unavailable','engine':engine,'error':str(e)},ensure_ascii=False),file=sys.stderr)
            if engine=='neural':
                try:
                    model=LocalSemantic(); values=model.rank(a.query.replace('|',' '),[g['title']+' '+g['channel'] for g in results])
                except (ImportError,ValueError,RuntimeError): model=None
            else: model=None
        if model is not None:
            for g,v in zip(results,values):
                g['semantic_score']=round(v,4); g['semantic_engine']=model.name
                g['rank_score']=round(.8*v+.2*min(1,g['clue_hits']/max(1,min(3,len(terms)))),4)
            results=[g for g in results if g['clue_hits'] or g['semantic_score']>=.10]
            return sorted(results,key=lambda g:(g['rank_score'],g['distinct_days'],g['events']),reverse=True)[:a.limit]
        results=[g for g in results if g['clue_hits']]
    return sorted(results,key=lambda g:(g['clue_hits'],g['distinct_days'],g['events']),reverse=True)[:a.limit]

def get_setting(db,key):
    row=db.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
    return row[0] if row else None

def startup(db,inbox=None):
    folder=inbox or get_setting(db,'inbox')
    now=datetime.now(timezone.utc).isoformat()
    if not folder: status={'status':'not_configured','checked_at':now,'new_events':0,'reports':[]}
    elif not Path(folder).is_dir(): status={'status':'source_unavailable','checked_at':now,'new_events':0,'reports':[]}
    else:
        reports=ingest(db,[folder]); errors=sum(x.get('status')=='error' or x.get('skipped',0)>0 or x.get('quality_known') is False for x in reports)
        supported=any(x.get('status') in ('imported','unchanged') for x in reports)
        status={'status':'partial' if errors else 'checked_local_snapshot' if supported else 'no_history_files','checked_at':now,'new_events':sum(x.get('added',0) for x in reports),'reports':reports}
    status['local_index_events']=db.execute('SELECT count(*) FROM events').fetchone()[0]
    status['remote_freshness_verified']=False
    with db: db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)',('last_startup',json.dumps(status,ensure_ascii=False)))
    return status

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',required=True);p.add_argument('--inbox',help='Override authorized export folder for this invocation'); sub=p.add_subparsers(dest='cmd',required=True)
    i=sub.add_parser('import');i.add_argument('files',nargs='+');sub.add_parser('stats');sub.add_parser('start');c=sub.add_parser('configure');c.add_argument('--inbox',dest='configured_inbox');c.add_argument('--model',dest='configured_model');w=sub.add_parser('sync');w.add_argument('folder');w.add_argument('--watch',action='store_true');w.add_argument('--interval',type=int,default=300)
    s=sub.add_parser('search');s.add_argument('--from',dest='start');s.add_argument('--to',dest='end');s.add_argument('--tz',default='UTC');s.add_argument('--query');s.add_argument('--expand',action='store_true');s.add_argument('--semantic',choices=['local','off','neural'],default='local');s.add_argument('--model',help='Existing local sentence-transformers model directory');s.add_argument('--kind',choices=['watch','search','other','all'],default='watch');s.add_argument('--platform',choices=['youtube','music','unknown','all'],default='all');s.add_argument('--limit',type=int,default=50)
    a=p.parse_args()
    try:
        with connect(a.db) as db:
            if a.cmd=='configure':
                if not a.configured_inbox and not a.configured_model: raise ValueError('Specify an authorized inbox or local model directory')
                for key,value in [('inbox',a.configured_inbox),('model',a.configured_model)]:
                    if value:
                        folder=Path(value).expanduser().resolve()
                        if not folder.is_dir(): raise ValueError('Authorized directory must exist')
                        with db: db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)',(key,str(folder)))
                result=startup(db)
            elif a.cmd=='start': result=startup(db,a.inbox)
            elif a.cmd=='sync':
                if not Path(a.folder).is_dir() or a.interval<5: raise ValueError('Invalid folder or interval')
                while True:
                    result=startup(db,a.folder); print(json.dumps(result,ensure_ascii=False),flush=True)
                    if not a.watch: return int(result['status']=='partial')
                    time.sleep(a.interval)
            elif a.cmd=='import': result=ingest(db,a.files)
            else:
                status=startup(db,a.inbox); print(json.dumps({'auto_import':status},ensure_ascii=False),file=sys.stderr)
                if a.cmd=='stats': result=[dict(r) for r in db.execute('SELECT kind,platform,count(*) AS events,min(stamp) AS earliest,max(stamp) AS latest FROM events GROUP BY kind,platform')]
                else:
                    if a.limit<1 or a.start and a.end and a.start>a.end: raise ValueError('invalid date range or limit')
                    if a.semantic!='off' and not a.model: a.model=get_setting(db,'model')
                    if a.semantic=='neural' and not a.model: raise ValueError('Neural mode requires --model local directory')
                    result=search(db,a)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except KeyboardInterrupt: return 0
    except (OSError,ValueError,sqlite3.Error,ImportError) as e: print('History error: '+str(e),file=sys.stderr);return 1
    return 0
if __name__=='__main__': sys.exit(main())
