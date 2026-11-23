"""Synthetic Java 1.21-style .mca chunk integration test."""
import sys,tempfile,struct,zlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'desktop'))
from scanner import scan,cluster,export

def nb_str(s):
    raw=s.encode();return struct.pack('>H',len(raw))+raw

def named(t,name,data):return bytes([t])+nb_str(name)+data

def int_tag(k,n):return named(3,k,struct.pack('>i',n))

def str_tag(k,v):return named(8,k,nb_str(v))

def compound_payload(e):return str_tag('id',e['id'])+int_tag('x',e['x'])+int_tag('y',e['y'])+int_tag('z',e['z'])+b'\x00'

def create_region(path):
    ents=[{'id':'minecraft:chest','x':x,'y':70,'z':z} for x,z in [(0,0),(1,0),(3,0),(4,0)]]
    ents.append({'id':'minecraft:furnace','x':2,'y':70,'z':2})
    body=named(9,'block_entities',b'\x0a'+struct.pack('>i',len(ents))+b''.join(compound_payload(e) for e in ents))+b'\x00'
    raw=b'\x0a'+nb_str('')+body
    compressed=zlib.compress(raw);chunk=struct.pack('>I',len(compressed)+1)+b'\x02'+compressed
    pad=((len(chunk)+4095)//4096)*4096
    header=bytearray(8192);header[:4]=(2).to_bytes(3,'big')+bytes([pad//4096])
    path.write_bytes(bytes(header)+chunk.ljust(pad,b'\0'))

with tempfile.TemporaryDirectory() as temp:
    folder=Path(temp)/'world'/'region';folder.mkdir(parents=True)
    create_region(folder/'r.0.0.mca')
    ents,chunks,stats=scan(folder.parent)
    found=cluster(ents,32,4)
    assert stats['chunks']==1,stats
    assert len(ents)==5,ents
    assert len(found)==1 and found[0]['chests']==4 and found[0]['extras']['furnace']==1,found
    target=Path(temp)/'locations.json';export(target,found)
    assert 'lostcityfinder' in target.read_text()
    print('PASS: Synthetic region scan, block entities, clustering, JSON export')
