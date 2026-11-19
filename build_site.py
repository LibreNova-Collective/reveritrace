#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Build a review preview or publisher-approved static release; no network calls."""
import argparse, html, json, shutil, zipfile, re, hashlib
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parent
PAGES={'websiteURL':'index.html','supportURL':'support.html','privacyPolicyURL':'privacy.html','termsOfServiceURL':'terms.html'}
def https(value):
    u=urlsplit(value)
    if u.scheme!='https' or not u.hostname or u.username or u.password or u.query or u.fragment or len(value)>900:
        raise ValueError('Use a real HTTPS URL without credentials, query or fragment')
    return value.rstrip('/')
def build(config=None):
    cfg=json.loads(Path(config).read_text()) if config else None
    if config and not isinstance(cfg,dict): raise ValueError('Configuration must be an object')
    if cfg is not None:
        for key in ('publisher','base_url','support_url','effective_date'):
            if not isinstance(cfg.get(key),str) or not cfg[key].strip(): raise ValueError('Missing '+key)
        if len(cfg['publisher'])>80 or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',cfg['effective_date']): raise ValueError('Invalid publisher or date')
        if not cfg.get('publisher_verified') or not cfg.get('policies_approved') or not cfg.get('rights_confirmed'): raise ValueError('Publisher must confirm identity, policy and rights before build')
        base=https(cfg['base_url']); support=https(cfg['support_url'])
        if 'example.com' in base or 'example.com' in support: raise ValueError('Placeholder URLs are not supported')
    out=ROOT/'dist'; out.mkdir(exist_ok=True)
    site=out/'site'; site.mkdir(exist_ok=True)
    shutil.copy2(ROOT/'plugin/assets/icon.png',site/'icon.png'); shutil.copy2(ROOT/'plugin/LICENSE',site/'LICENSE.txt')
    shutil.copy2(ROOT/'style.css',site/'style.css')
    (site/'.nojekyll').touch()
    manifest=json.loads((ROOT/'plugin/plugin.json').read_text())
    interface=manifest['extensions']['com.openai']['interface']
    if cfg is not None:
        manifest['author']={'name':cfg['publisher']}; interface['developerName']=cfg['publisher']
        interface.update({k:base+'/'+v for k,v in PAGES.items()})
        if cfg.get('all_available_countries') is True: manifest['extensions']['com.openai']['publication']['countries']=[]
        elif cfg.get('countries'):
            if not all(re.fullmatch(r'[A-Z]{2}',c) for c in cfg['countries']): raise ValueError('Invalid country codes')
            manifest['extensions']['com.openai']['publication']['countries']=cfg['countries']
    # Include original corresponding source and the local website generator, not dependencies or user files.
    source=site/'ReveriTrace-source.zip'
    with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted((ROOT/'plugin').rglob('*')):
            if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc':
                name=f.relative_to(ROOT/'plugin').as_posix()
                if name=='plugin.json': z.writestr('plugin/'+name,json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
                else: z.write(f,'plugin/'+name)
        for n in ('build_site.py','style.css','README.md','test_site.py'):
            z.write(ROOT/n,n)
        for f in (ROOT/'kit/docs').glob('*'):
            if f.is_file(): z.write(f,'kit/docs/'+f.name)
    plugin_zip=site/'ReveriTrace-plugin.zip'
    with zipfile.ZipFile(plugin_zip,'w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted((ROOT/'plugin').rglob('*')):
            if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc':
                n=f.relative_to(ROOT/'plugin').as_posix()
                if n=='plugin.json':z.writestr(n,json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
                else:z.write(f,n)
    name=html.escape(cfg['publisher']) if cfg else 'Publisher identity pending verification'
    effective=html.escape(cfg['effective_date']) if cfg else 'Pending approval'
    contact=f'<a href="{html.escape(support,quote=True)}">Official support channel</a>' if cfg else 'Support channel pending publisher setup.'
    nav='<nav aria-label="Main"><a href="index.html">Home</a><a href="support.html">Support</a><a href="privacy.html">Privacy</a><a href="terms.html">Terms</a><a href="LICENSE.txt">License</a></nav>'
    foot=f'<footer><p>Publisher: {name}</p><p>Independent of Google and YouTube. <a href="ReveriTrace-source.zip">Corresponding source (AGPL-3.0)</a> · <a href="LICENSE.txt">Full license</a></p></footer>'
    def page(title,body):
        draft='' if cfg else '<aside role="note">PREVIEW — not published; publisher and legal approval pending.</aside>'
        return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'self\'; img-src \'self\'; base-uri \'none\'; form-action \'none\'"><title>{title} | ReveriTrace</title><link rel="stylesheet" href="style.css"><link rel="icon" href="icon.png"></head><body><header><a class="brand" href="index.html"><img src="icon.png" alt="" width="40" height="40">ReveriTrace</a>{nav}</header><main>{draft}{body}</main>{foot}</body></html>'
    pages={
      'index.html':('Find videos you remember','''<div class="hero"><p class="eyebrow">OPEN SOURCE · FREE SOFTWARE · AGPL-3.0</p><h1>Find videos you remember.</h1><p class="lead">Rediscover YouTube videos and YouTube Music tracks from your own authorized history exports.</p><div class="actions"><a class="primary" href="ReveriTrace-plugin.zip">Download plugin source</a><a href="support.html">Get started</a></div></div><section class="grid"><article><h2>Search across languages</h2><p>English, Spanish and Japanese title clues, dates and repeated activity.</p></article><article><h2>Keep data in your control</h2><p>Local SQLite indexing with a compatible runtime; no publisher-operated history server.</p></article><article><h2>Open by design</h2><p>Original software under AGPL-3.0. External models and dependencies retain their own terms.</p></article></section><h2>How it works</h2><ol><li>Export only watch and search history from your own <a href="https://takeout.google.com/">Google Takeout</a> account.</li><li>Provide the ZIP or JSON to a compatible execution environment.</li><li>Search using dates, approximate titles and descriptive clues.</li></ol><p>No direct OAuth or continuous background service is bundled. The current release is a candidate, not an approved marketplace listing. <a href="ReveriTrace-source.zip">Download full corresponding source.</a></p>'''),
      'support.html':('Support',f'''<h1>Support</h1><p>{contact}</p><h2>Getting started</h2><ol><li>Open Google Takeout and select only YouTube and YouTube Music history in JSON format.</li><li>Save your export to your own device.</li><li>Use a compatible local runtime or an authorized host; review which provider receives the file.</li></ol><h2>Troubleshooting</h2><p>Check date coverage and the active account. For missing files, incomplete imports or unsupported features, consult the documentation in the <a href="ReveriTrace-source.zip">source archive</a>.</p><p>Never include passwords, cookies, verification numbers or personal viewing histories in a public support request. Use synthetic examples.</p>'''),
      'privacy.html':('Privacy policy',f'''<h1>Privacy policy</h1><p>Effective date: {effective}. Publisher: {name}.</p><h2>Data handled by the software</h2><p>The local CLI reads authorized YouTube history files, creates a user-selected SQLite database and can process metadata in local semantic models. It does not transmit that database to a publisher server. It does not include telemetry or bundled OAuth credentials. The local database is not encrypted by ReveriTrace.</p><h2>Website and external services</h2><p>This static website has no analytics scripts, ads, cookies set by its code, tracking pixels or data collection forms. The host may process ordinary request information under its own privacy policies. When used through ChatGPT, Google or another connector, those providers may process and retain information under their own terms. The publisher cannot promise on-device processing for third-party environments.</p><h2>Retention, deletion and support</h2><p>Remove local databases, auxiliary files and backups to delete local data. Manage host attachments and provider authorization separately. Use only synthetic information in support requests; public issue trackers are public. For privacy-related questions use {contact}.</p>'''),
      'terms.html':('Terms of use',f'''<h1>Terms of use</h1><p>Effective date: {effective}. Publisher: {name}.</p><h2>Authorized use</h2><p>Use only data you own or have authorization to process. Respect third-party service terms. No direct Google login is provided by this edition. Missing or deleted history may not be recoverable; candidate ranking is not proof of playback.</p><h2>Software rights</h2><p>The original software is licensed under <a href="LICENSE.txt">AGPL-3.0-only</a>. These website terms do not restrict rights granted by that license, including compliant commercial use. Any covered distribution and network interaction with a modified version must meet applicable AGPL requirements. External models and dependencies retain their own licenses. Contributions are welcomed but not compulsory.</p><p>Official downloads are offered at no charge. Third-party services may have their own terms and costs. See {contact} for questions.</p>''')}
    for fname,(title,body) in pages.items(): (site/fname).write_text(page(title,body),encoding='utf-8')
    summary={'preview':not bool(cfg),'plugin_sha256':hashlib.sha256(plugin_zip.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'url_verification':'not performed; verify deployed public pages before submission'}
    (out/'build-status.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--approved-config');a=p.parse_args();build(a.approved_config)
