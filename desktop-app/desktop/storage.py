"""Local SQLite region cache and user reviews; never writes to Minecraft worlds."""
import os, sqlite3, json, hashlib, multiprocessing
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from scanner import locate_dimensions, read_region, IMPORTANT

SCHEMA=1

def connect(root):
    base=Path(os.environ.get('LOCALAPPDATA') or Path.home()/'.cache')/'LostCityFinder'; base.mkdir(parents=True,exist_ok=True)
    key=hashlib.sha256(os.path.normcase(str(Path(root).resolve())).encode()).hexdigest()
    db=sqlite3.connect(base/(key+'.sqlite3'),timeout=30)
    db.execute('CREATE TABLE IF NOT EXISTS regions (path TEXT PRIMARY KEY, signature TEXT, payload TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS reviews (id TEXT PRIMARY KEY, label TEXT)'); db.commit(); return db

def signature(path,external):
    s=path.stat(); return json.dumps([SCHEMA,s.st_size,s.st_mtime_ns,external])

def process_region(dim,path):
    from smart import features
    rows=[]; entities=[]
    for x,z,data in read_region(Path(path)):
        rows.append([x,z,features(data)])
        for e in data.get('block_entities',data.get('Level',{}).get('TileEntities',[])) or []:
            if not isinstance(e,dict):continue
            kind=str(e.get('id','')).split(':')[-1]
            if kind not in IMPORTANT and not kind.endswith('shulker_box'):continue
            try: ex,ey,ez=(int(e[k]) for k in ('x','y','z'))
            except (KeyError,ValueError,TypeError):continue
            entities.append(dict(dimension=dim,x=ex,y=ey,z=ez,kind=kind))
    return rows,entities

def cached_scan(root,progress=None,force=False,workers=None):
    dims=locate_dimensions(root)
    if not dims:raise ValueError('Kein region-Ordner gefunden.')
    jobs=[]
    for dim,folder in dims:
        ext=defaultdict(list)
        for p in folder.glob('c.*.*.mcc'):
            try:
                _,x,z,_=p.name.split('.'); s=p.stat(); ext[int(x)//32,int(z)//32].append([p.name,s.st_size,s.st_mtime_ns])
            except (ValueError,OSError):pass
        for p in sorted(folder.glob('r.*.*.mca')):
            try:
                _,x,z,_=p.name.split('.'); sig=signature(p,sorted(ext[int(x),int(z)])); jobs.append((dim,str(p.resolve()),sig))
            except (ValueError,OSError):continue
    db=connect(root); meta=defaultdict(dict); chunks=defaultdict(set); ents=[]; hits=0; failures=0; count=0; pending=[]
    def merge(dim,payload):
        rows,entities=payload; ents.extend(entities)
        for x,z,f in rows:chunks[dim].add((x,z));meta[dim][x,z]=f
    def tick(name):
        nonlocal count
        count+=1
        if progress:progress(count,len(jobs),name)
    try:
        for dim,path,sig in jobs:
            row=db.execute('SELECT payload FROM regions WHERE path=? AND signature=?',(path,sig)).fetchone() if not force else None
            if row:
                try:merge(dim,json.loads(row[0]));hits+=1;tick('Cache: '+Path(path).name);continue
                except (ValueError,TypeError):pass
            pending.append((dim,path,sig))
        if pending:
            n=max(1,min(workers or (os.cpu_count() or 2),8,len(pending)))
            with ProcessPoolExecutor(max_workers=n, mp_context=multiprocessing.get_context("spawn")) as pool:
                iterator=iter(pending); active={}
                def submit():
                    try:dim,path,sig=next(iterator)
                    except StopIteration:return
                    active[pool.submit(process_region,dim,path)]=(dim,path,sig)
                for _ in range(n*2):submit()
                while active:
                    finished,_=wait(active,return_when=FIRST_COMPLETED)
                    for f in finished:
                        dim,path,sig=active.pop(f)
                        try:
                            payload=f.result();merge(dim,payload)
                            # Do not cache if changed during scan. External chunk changes are checked on next run.
                            s=Path(path).stat(); old=json.loads(sig)
                            if [s.st_size,s.st_mtime_ns]==old[1:3]:
                                db.execute('INSERT OR REPLACE INTO regions VALUES (?,?,?)',(path,sig,json.dumps(payload,separators=(',',':'))));db.commit()
                        except Exception:failures+=1
                        tick(Path(path).name);submit()
        if progress:progress(len(jobs),len(jobs),'Fertig')
        return ents,chunks,dict(regions=len(jobs),chunks=sum(map(len,chunks.values())),block_entities=len(ents),failed_regions=failures,meta=meta,cache_hits=hits,scanned_regions=len(pending))
    finally:db.close()

def reviews(root):
    with connect(root) as db:
        return dict(db.execute('SELECT id,label FROM reviews'))

def review(root,id,label):
    with connect(root) as db:
        if label=='Ungeprüft':db.execute('DELETE FROM reviews WHERE id=?',(id,))
        else:db.execute('INSERT OR REPLACE INTO reviews VALUES (?,?)',(id,label))
