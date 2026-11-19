# SPDX-License-Identifier: AGPL-3.0-only
"""Local semantic ranking. No network, no history leaves the machine."""
import math, re, unicodedata, hashlib, json
from collections import Counter

# Paired concept documents bridge languages and related terms without online services.
ANCHORS = [
'dark country country sombrio country oscuro southern gothic outlaw country dark western gothic cowboy ballad haunted western revenge graveyard dust devil swamp blues dark folk',
'country music musica country acoustic acoustic guitar americana bluegrass fiddle banjo honky tonk Nashville ranch cowboy vaquero western folk country rock',
'long mix compilation playlist hours hour nonstop continuous marathon recopilacion lista canciones larga horas musica continua album full collection',
'artificial intelligence ai generated animacion inteligencia artificial generated ai music visuals animated illustration synthetic video cinematic animation',
'sad melancholic somber gloomy triste melancolico sombrio loneliness heartbreak lament lonely sorrow grief',
'heavy metal rock hard rock guitar metalcore death metal doom metal goth screaming distortion',
'jazz smooth saxophone piano swing bebop jazz lounge instrumental',
'electronic techno edm house trance synthwave vaporwave dance electronic beats',
'hip hop rap trap reggaeton urbano freestyle hiphop',
'classical orchestral symphony classical music concerto musica clasica violin orchestra instrumental',
'anime ending opening fandub cover version castellano español latino japanese romaji anime song theme',
'ambient relaxing sleep meditation rain white noise calm peaceful dormir relajante naturaleza',
'game gameplay walkthrough video game tutorial gaming videojuegos',
'news politics noticias travel documentary science ciencia documentary documental',
'workout gym fitness exercise entrenamiento ejercicios',
'comedy funny humor divertido memes standup comedia',
'folk medieval tavern bard celtic nordic viking medieval folk music taberna',
'blues delta blues swamp blues blues rock guitar harmonica soulful blues',
'gospel spiritual church christian worship gospel praise religious religion iglesia',
'pop romantic love song romantica balada pop ballad amor',
'live concert performance concierto directos en vivo stage festival',
'soundtrack score soundtrack ost film movie cinematic pelicula banda sonora',
'country dark cowboy death hell whiskey saloon outlaw ghost rider desert western gothic country mix',
'playlist sleep background ambience background music musica fondo listening long mix hours',
'anime アニメ アニメソング anisong anime japanese japones 日本語 nihongo animation animacion',
'japanese subtitles japonés subtitulado subtitles subtitulos subbed 字幕 日本語字幕 nihongo jimaku',
'english subtitles english sub eng sub subtitulos ingles subtitulado ingles 英語字幕 英語 eigo jimaku',
'spanish subtitles spanish sub esp sub subtitulos español subtitulado español スペイン語字幕 西語字幕 スペイン語 supeingo jimaku',
'ending end theme ed エンディング エンディングテーマ 主題歌 ending theme tema final',
'opening opening theme op オープニング オープニングテーマ 主題歌 tema apertura',
'cover fandub カバー 歌ってみた utattemita cover song version cantada',
'romaji romanized lyrics ローマ字 歌詞 lyrics letras karaoke カラオケ',
'full song full version complete canción completa フル フルバージョン 完全版',
'parasyte parasite kiseijuu kiseiju 寄生獣 寄生獣セイの格率 kiseijuu sei no kakuritsu',
'japanese music jpop j-pop 日本の音楽 邦楽 音楽 歌 日本語曲',
'dark country ダークカントリー カントリー音楽 西部劇 ウエスタン cowboy dark western',
'playlist mix compilation メドレー 作業用bgm 作業用 音楽集 長時間 recopilacion mix'
]

def norm(s):
    return ''.join(''.join(x for x in unicodedata.normalize('NFKD',c) if not unicodedata.combining(x)) if 'LATIN' in unicodedata.name(c,'') else c for c in unicodedata.normalize('NFKC',s).casefold())

def tokens(s):
    # Mixed-script segmentation: Latin words and Japanese overlapping 1–3 grams.
    out=[]
    for w in re.findall(r'[\u3040-\u30ff\u3400-\u9fff]+|[^\W_]+',norm(s),re.UNICODE):
        if re.match(r'[\u3040-\u30ff\u3400-\u9fff]',w):
            out.extend(w[i:i+n] for n in (1,2,3) for i in range(len(w)-n+1))
        else: out.append(w)
    return out

def features(s):
    ts=tokens(s)
    return ts+[a+' '+b for a,b in zip(ts,ts[1:])]

class LocalSemantic:
    """TF-IDF + latent semantic analysis, fitted on authorized local catalog and bilingual anchors."""
    name='local-lsa-multilingual-v2'
    def rank(self, query, docs):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD
        from sklearn.preprocessing import normalize
        if not docs: return []
        # Fixed vocabulary fitting corpus excludes query to keep retrieval reproducible.
        corpus=ANCHORS+docs
        tf=TfidfVectorizer(analyzer=features,sublinear_tf=True,max_features=40000)
        x=tf.fit_transform(corpus); q=tf.transform([query])
        n=min(32,x.shape[0]-1,x.shape[1]-1)
        if n<2: return (x[len(ANCHORS):]@q.T).toarray().ravel().tolist()
        lsa=TruncatedSVD(n_components=n,random_state=17,n_iter=7)
        z=normalize(lsa.fit_transform(x)); v=normalize(lsa.transform(q))
        # Combine latent topic and direct lexical evidence. Unknown tokens yield zero.
        latent=(z[len(ANCHORS):]@v.T).ravel()
        literal=(x[len(ANCHORS):]@q.T).toarray().ravel()
        return [float(max(0,min(1,.75*a+.25*b))) for a,b in zip(latent,literal)]

class NeuralSemantic:
    """Optional pretrained local neural model, with content-addressed vector cache."""
    name='local-sentence-transformer'
    def __init__(self, path, db):
        import os
        from model_policy import validate
        p, signature=validate(path)
        os.environ['HF_HUB_OFFLINE']='1'; os.environ['TRANSFORMERS_OFFLINE']='1'
        from sentence_transformers import SentenceTransformer
        self.model=SentenceTransformer(str(p),local_files_only=True,trust_remote_code=False,device='cpu',model_kwargs={'use_safetensors':True},backend='torch')
        self.db=db
        self.key=signature
        db.execute('CREATE TABLE IF NOT EXISTS semantic_cache (model TEXT, document TEXT, vector BLOB NOT NULL, PRIMARY KEY(model,document))')
    def rank(self, query, docs):
        import numpy as np
        keys=[hashlib.sha256(x.encode()).hexdigest() for x in docs]; vectors={}; missing={}
        for k,d in zip(keys,docs):
            row=self.db.execute('SELECT vector FROM semantic_cache WHERE model=? AND document=?',(self.key,k)).fetchone()
            if row: vectors[k]=np.frombuffer(row[0],dtype='<f4')
            else: missing[k]=d
        if missing:
            items=list(missing.items()); vec=self.model.encode([d for _,d in items],normalize_embeddings=True,batch_size=32,show_progress_bar=False)
            with self.db:
                for (k,_),v in zip(items,vec):
                    v=np.asarray(v,dtype='<f4'); vectors[k]=v
                    self.db.execute('INSERT OR REPLACE INTO semantic_cache VALUES (?,?,?)',(self.key,k,v.tobytes()))
        q=self.model.encode([query],normalize_embeddings=True,show_progress_bar=False)[0]
        return [float(max(0,min(1,vectors[k]@q))) for k in keys]
