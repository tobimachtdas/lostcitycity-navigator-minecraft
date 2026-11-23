"""Modern Java chunk palette analysis and approximate top-down rendering."""
import math
from collections import Counter, defaultdict
from scanner import read_region, locate_dimensions

MASK=(1<<64)-1
AIR={'air','cave_air','void_air','structure_void','barrier'}

def name(p): return p.get('Name','minecraft:air').split(':')[-1]
def artificial(n):
    return n.endswith(('_concrete','_concrete_powder','_glazed_terracotta','_glass','_glass_pane','_planks','_stairs','_slab','_bricks','_rail','_fence','_door','_trapdoor','_wool')) or n in {'glass','glass_pane','bricks','stone_bricks','crafting_table','redstone_wire','redstone_block','repeater','comparator','beacon','enchanting_table','lantern','torch','wall_torch','sea_lantern','bookshelf','piston','sticky_piston','observer','dispenser','dropper','rail','powered_rail'}

def sections(data):
    for s in data.get('sections',[]):
        b=s.get('block_states',{}); p=b.get('palette',[])
        if p: yield int(s.get('Y',0)), [name(x) for x in p], b.get('data',[])

def indices(p,d):
    if len(p)==1: return [0]*4096
    bits=max(4,(len(p)-1).bit_length()); per=64//bits; mask=(1<<bits)-1
    if not d or len(d)<math.ceil(4096/per): return None
    return [((d[i//per]&MASK)>>((i%per)*bits))&mask for i in range(4096)]

def features(data):
    counts=Counter()
    for _,p,d in sections(data):
        wanted={i:n for i,n in enumerate(p) if artificial(n)}
        if not wanted: continue
        ix=indices(p,d)
        if ix is not None:
            for i,n in Counter(ix).items():
                if i in wanted: counts[wanted[i]]+=n
    st=data.get('structures',{}); starts=st.get('starts',{}); refs=st.get('References',st.get('references',{}))
    structures=sorted({k.split(':')[-1] for k,v in starts.items() if isinstance(v,dict) and v.get('id','INVALID')!='INVALID'} | {k.split(':')[-1] for k,v in refs.items() if v})
    ents=data.get('block_entities',data.get('Level',{}).get('TileEntities',[])) or []
    chests=sum(str(e.get('id','')).split(':')[-1] in {'chest','trapped_chest'} and not e.get('LootTable') for e in ents if isinstance(e,dict))
    return {'activity':max(0,int(data.get('InhabitedTime',data.get('Level',{}).get('InhabitedTime',0)))), 'materials':dict(counts),'structures':structures,'chests':chests,'loot_chests':sum(str(e.get('id','')).split(':')[-1] in {'chest','trapped_chest'} and bool(e.get('LootTable')) for e in ents if isinstance(e,dict))}

def chest_score(n):
    for threshold, score in [(100,98),(60,90),(40,75),(20,60),(10,40),(5,20),(1,5)]:
        if n>=threshold:return score
    return 0

def confidence(score):
    return 'Sehr hoch' if score>=90 else 'Hoch' if score>=75 else 'Interessant' if score>=60 else 'Möglich' if score>=40 else 'Gering'

def discover(meta, mode='city', minimum=60, natural=True, activity=True, radius=96, min_chests=0):
    # Fixed local windows around evidence-rich chunks, then suppress overlapping candidates.
    candidates=[]
    for dim, cells in meta.items():
        seeds=[(x,z) for (x,z),f in cells.items() if f['materials'] or f['chests'] or (activity and f['activity']>=12000)]
        r=max(1,math.ceil(radius/16))
        for x,z in seeds:
            f=cells[x,z]; local=[cells[a,b] for a in range(x-r,x+r+1) for b in range(z-r,z+r+1) if (a-x)**2+(b-z)**2<=r*r and (a,b) in cells]
            mats=Counter(); chests=0; loot=0; act=0; built=0; structs=set()
            for q in local:
                mats.update(q['materials']); chests+=q['chests']; loot+=q.get('loot_chests',0); act=max(act,q['activity']); built+=sum(q['materials'].values())>=32; structs.update(q['structures'])
            amount=sum(mats.values()); diversity=len(mats); special=sum(v for k,v in mats.items() if 'concrete' in k or 'redstone' in k or k in {'beacon','enchanting_table','repeater','comparator','glass','glass_pane'})
            a=min(25, 8*math.log2(1+act/12000)) if activity else 0
            m=min(35, 7*math.log2(1+amount/128)); d=min(15,diversity*1.5); b=min(20,built*2); s=min(20,5*math.log2(1+special/8)); c=min(20,chests*2)
            if mode=='city': score=m+d+b+s+a+c*.35
            elif mode=='base': score=m+d+s+a+c
            elif mode=='storage': score=c*2+m*.5+s+a
            elif mode=='activity': score=min(70,a*2.8)+m*.5+b*.5
            else: score=m+d+b+s+a+c
            # Chest abundance is a strong signal, independent of material score.
            if mode!='activity':
                score=max(chest_score(chests), min(85,score)*(.85 if chests<10 else 1))
                if chests<min_chests:continue
            if natural and structs: score-=20 if not special else 10
            if natural and loot: score-=min(20,20*loot/max(1,chests+loot))
            score=int(max(0,min(100,score)))
            if score<minimum: continue
            candidates.append({'id':f'{dim}:{x*16+8}:{z*16+8}', 'dimension':dim,'x':x*16+8,'y':64,'z':z*16+8,'score':score,'chests':chests,'loot_chests':loot,'confidence':confidence(score),'chest_score':chest_score(chests),'materials':dict(mats.most_common(12)),'structures':sorted(structs),'activity':act,'built_chunks':built,'visited':False,'extras':{},'_anchor':sum(f['materials'].values())+f['chests']*30})
    candidates.sort(key=lambda v:(-v['score'],-v['_anchor']))
    out=[]; bins=defaultdict(list); step=max(16,radius)
    for v in candidates:
        x,z=v['x'],v['z']; dim=v['dimension']; gx,gz=x//step,z//step
        if any((x-q['x'])**2+(z-q['z'])**2<=radius**2 for dx in (-1,0,1) for dz in (-1,0,1) for q in bins[dim,gx+dx,gz+dz]): continue
        v.pop('_anchor'); v['name']=f'Fundort #{len(out)+1}'; out.append(v); bins[dim,gx,gz].append(v)
    return out

COLORS={'grass_block':'#73994a','water':'#426eba','sand':'#d9cd94','gravel':'#8b8985','stone':'#858585','snow':'#f2f5f5','snow_block':'#f2f5f5','ice':'#9bc5df','lava':'#e77927','netherrack':'#783b39','end_stone':'#d8db9c','dirt':'#896344','cobblestone':'#777777','glass':'#a8cbd0','stone_bricks':'#999997','bricks':'#a45d4f','deepslate':'#45454b','bedrock':'#414141'}
DYES={'white':'#e8e8e0','orange':'#df832a','magenta':'#ae56a9','light_blue':'#65a4d6','yellow':'#e1c443','lime':'#80b52c','pink':'#d98eaa','gray':'#565b60','light_gray':'#a4a5a0','cyan':'#338d98','purple':'#7754a1','blue':'#44578b','brown':'#77503a','green':'#587637','red':'#a5463d','black':'#303034'}
def color(n):
    if n in COLORS:return COLORS[n]
    for k,v in DYES.items():
        if n.startswith(k+'_') and any(t in n for t in ('concrete','wool','terracotta','glass')): return v
    if 'leaves' in n:return '#386b39'
    if 'log' in n or 'wood' in n:return '#785c3b'
    if 'planks' in n or 'fence' in n:return '#be9763'
    if 'sandstone' in n:return '#d2be84'
    if 'brick' in n or 'stone' in n:return '#92918d'
    if 'grass' in n or 'moss' in n:return '#719447'
    if 'glass' in n:return '#a5c9ce'
    return '#a49d85' if artificial(n) else '#777c68'

def surface(data):
    """256 RGB pixels, top non-air block per column; modern padded palette."""
    result=[None]*256; remaining=256
    for sy,p,d in sorted(sections(data),reverse=True):
        if not any(n not in AIR for n in p):continue
        ix=indices(p,d)
        if ix is None:continue
        for col in range(256):
            if result[col] is not None:continue
            for y in range(15,-1,-1):
                i=ix[y*256+col]
                if i>=len(p) or p[i] in AIR:continue
                result[col]=bytes.fromhex(color(p[i])[1:]); remaining-=1; break
        if not remaining:break
    return b''.join(v or b'\x20\x3e\x35' for v in result)

def render(root,dim,cx,cz,r=4):
    # Only the requested area, no generation or world modification.
    side=(2*r+1)*16; pixels=bytearray(b'\x20\x3e\x35'*(side*side)); x0,z0=cx-r,cz-r
    for d,folder in locate_dimensions(root):
        if d!=dim:continue
        for rx in range(x0//32,(cx+r)//32+1):
            for rz in range(z0//32,(cz+r)//32+1):
                path=folder/f'r.{rx}.{rz}.mca'
                if not path.exists():continue
                for x,z,data in read_region(path, bounds=(x0,z0,cx+r,cz+r)):
                    tile=surface(data)
                    for row in range(16):
                        offset=((z-z0)*16+row)*side*3+(x-x0)*48
                        pixels[offset:offset+48]=tile[row*48:(row+1)*48]
    return side,bytes(pixels),x0*16,z0*16


def spaced_locations(locations, distance):
    """Return strongest independent targets, without deleting underlying detections."""
    if distance <= 0:
        return list(locations)
    bins = defaultdict(list)
    result = []
    ranked = sorted(locations, key=lambda l: (-int(l.get('review') == 'Eigener Bau'), -l['score'], -l.get('chests', 0), l['id']))
    for l in ranked:
        x,z,dim = l['x'],l['z'],l['dimension']
        gx,gz = x//distance,z//distance
        if any((x-q['x'])**2+(z-q['z'])**2 < distance**2 for dx in (-1,0,1) for dz in (-1,0,1) for q in bins.get((dim,gx+dx,gz+dz), ())):
            continue
        result.append(l)
        bins[dim,gx,gz].append(l)
    return result
