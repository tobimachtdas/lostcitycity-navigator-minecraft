"""Read-only Minecraft Java region scanner, Python standard library only."""
import gzip
import json
import math
import re
import struct
import zlib
from collections import defaultdict
from pathlib import Path

class NBTError(Exception): pass

class NBT:
    def __init__(self, blob): self.d = memoryview(blob); self.i = 0
    def take(self,n):
        if n<0 or self.i+n>len(self.d): raise NBTError('Truncated NBT')
        v=self.d[self.i:self.i+n]; self.i+=n; return v
    def number(self,fmt): return struct.unpack('>'+fmt,self.take(struct.calcsize('>'+fmt)))[0]
    def string(self): return bytes(self.take(self.number('H'))).decode('utf-8','replace')
    def payload(self,t,depth=0):
        if depth>80: raise NBTError('NBT nesting too deep')
        if t==0:return None
        if t==1:return self.number('b')
        if t==2:return self.number('h')
        if t==3:return self.number('i')
        if t==4:return self.number('q')
        if t==5:return self.number('f')
        if t==6:return self.number('d')
        if t==7:
            n=self.number('i'); return bytes(self.take(n))
        if t==8:return self.string()
        if t==9:
            kind=self.number('b'); n=self.number('i')
            if n<0 or n>10000000:raise NBTError('Invalid list')
            return [self.payload(kind,depth+1) for _ in range(n)]
        if t==10:
            out={}
            while True:
                kind=self.number('b')
                if not kind:break
                name=self.string(); out[name]=self.payload(kind,depth+1)
            return out
        if t in (11,12):
            n=self.number('i'); raw=self.take(n*(4 if t==11 else 8)); return [v[0] for v in struct.iter_unpack('>i' if t==11 else '>q',raw)]
        raise NBTError(f'Unsupported tag {t}')
    def root(self):
        if self.number('b')!=10:raise NBTError('Root is not a compound')
        self.string(); return self.payload(10)

IMPORTANT={'chest','trapped_chest','barrel','furnace','blast_furnace','smoker','hopper','brewing_stand','shulker_box','sign','hanging_sign','bed','beacon'}
CHEST={'chest','trapped_chest'}
REGION_RE=re.compile(r'r\.(-?\d+)\.(-?\d+)\.mca$')

def read_region(path, bounds=None):
    """Yield (chunk_x, chunk_z, chunk_nbt), safely skipping invalid/unsupported chunks."""
    match=REGION_RE.match(path.name)
    if not match:return
    rx,rz=map(int,match.groups())
    with path.open('rb') as f:
        header=f.read(4096)
        if len(header)<4096:return
        for slot in range(1024):
            item=header[slot*4:slot*4+4]; sector=int.from_bytes(item[:3],'big'); count=item[3]
            if not sector or not count:continue
            cx=rx*32+slot%32; cz=rz*32+slot//32
            if bounds and not (bounds[0]<=cx<=bounds[2] and bounds[1]<=cz<=bounds[3]):continue
            try:
                f.seek(sector*4096); size=int.from_bytes(f.read(4),'big'); flag=f.read(1)
                if size<1 or size>max(count*4096,16*1024*1024):continue
                comp=f.read(size-1)
                if len(comp)!=size-1:continue
                scheme=flag[0]&127
                if flag[0]&128:
                    external=path.parent/f'c.{cx}.{cz}.mcc'
                    if not external.is_file():continue
                    comp=external.read_bytes()
                if scheme==1: raw=gzip.decompress(comp)
                elif scheme==2: raw=zlib.decompress(comp)
                elif scheme==3: raw=comp
                else: continue
                if len(raw)>64*1024*1024:continue
                yield cx,cz,NBT(raw).root()
            except (OSError,EOFError,ValueError,IndexError,zlib.error,NBTError,struct.error):continue

def locate_dimensions(root):
    root=Path(root)
    # support standard single player, vanilla server, Spigot world_nether/world_the_end
    items=[]; seen=set()
    for base in [root,root/'world',root.parent/(root.name+'_nether'),root.parent/(root.name+'_the_end')]:
        for dim,folder in [('overworld',base/'region'),('nether',base/'DIM-1'/'region'),('end',base/'DIM1'/'region')]:
            if not folder.is_dir():continue
            resolved=str(folder.resolve())
            if resolved in seen:continue
            seen.add(resolved)
            actual=dim
            if base.name.endswith('_nether'):actual='nether'
            if base.name.endswith('_the_end'):actual='end'
            items.append((actual,folder))
    return items

def scan(root,progress=None,smart=False):
    dimensions=locate_dimensions(root)
    if not dimensions:raise ValueError('Kein region-Ordner gefunden. Bitte den Minecraft-Weltordner auswählen.')
    regions=[(dim,p) for dim,folder in dimensions for p in sorted(folder.glob('r.*.*.mca'))]
    findings=[]; chunks=defaultdict(set); failures=0; meta=defaultdict(dict)
    if smart:
        from smart import features
    for index,(dim,path) in enumerate(regions):
        if progress:progress(index,len(regions),path.name)
        try:
            for cx,cz,data in read_region(path):
                chunks[dim].add((cx,cz))
                if smart:meta[dim][cx,cz]=features(data)
                entities=data.get('block_entities')
                if entities is None:entities=data.get('Level',{}).get('TileEntities',[])
                for e in entities or []:
                    if not isinstance(e,dict):continue
                    kind=str(e.get('id','')).split(':')[-1]
                    if kind not in IMPORTANT and not kind.endswith('shulker_box'):continue
                    try:x,y,z=(int(e[k]) for k in ('x','y','z'))
                    except (KeyError,ValueError,TypeError):continue
                    findings.append({'dimension':dim,'x':x,'y':y,'z':z,'kind':kind})
        except (OSError,ValueError):failures+=1
    if progress:progress(len(regions),len(regions),'Fertig')
    return findings,chunks,{'regions':len(regions),'chunks':sum(map(len,chunks.values())),'block_entities':len(findings),'failed_regions':failures, 'meta':meta if smart else {}}

def cluster(findings,radius=32,minimum=4):
    # Spatial hashing + union-find; chain-linked groups are split by radius from anchor
    bydim=defaultdict(list)
    for e in findings:bydim[e['dimension']].append(e)
    results=[]
    for dim,entities in bydim.items():
        chests=[e for e in entities if e['kind'] in CHEST]
        grid=defaultdict(list)
        for i,c in enumerate(chests):grid[(c['x']//radius,c['z']//radius)].append(i)
        parent=list(range(len(chests)))
        def find(i):
            while parent[i]!=i:
                parent[i]=parent[parent[i]];i=parent[i]
            return i
        for i,c in enumerate(chests):
            gx,gz=c['x']//radius,c['z']//radius
            for dx in (-1,0,1):
                for dz in (-1,0,1):
                    for j in grid.get((gx+dx,gz+dz),[]):
                        if j>=i:continue
                        o=chests[j]
                        if (c['x']-o['x'])**2+(c['z']-o['z'])**2<=radius**2:
                            parent[find(i)]=find(j)
        groups=defaultdict(list)
        for i,c in enumerate(chests):groups[find(i)].append(c)
        for group in groups.values():
            if len(group)<minimum:continue
            x=round(sum(c['x'] for c in group)/len(group));z=round(sum(c['z'] for c in group)/len(group));y=round(sum(c['y'] for c in group)/len(group))
            # use center-proximal chest coordinates as navigable target
            anchor=min(group,key=lambda c:(c['x']-x)**2+(c['z']-z)**2)
            extras=defaultdict(int)
            for e in entities:
                if e['kind'] in CHEST:continue
                if (e['x']-x)**2+(e['z']-z)**2<=(radius*1.5)**2:extras[e['kind']]+=1
            score=len(group)*10+sum(extras.values())*3
            results.append({'id':f'{dim}:{anchor["x"]}:{anchor["z"]}', 'name':'Verdächtiger Fundort', 'dimension':dim,'x':anchor['x'],'y':anchor['y'],'z':anchor['z'],'chests':len(group),'extras':dict(extras),'score':score,'visited':False})
    results.sort(key=lambda x:-x['score'])
    for i,r in enumerate(results,1):r['name']=f'Fundort #{i}'
    return results

def export(path,results):
    payload={'format':'lostcityfinder','version':1,'locations':results}
    Path(path).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
