import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'desktop'))
from smart import features, surface, discover, indices
p=[{'Name':'minecraft:air'},{'Name':'minecraft:red_concrete'}]
d=[0]*256
for i in range(256):d[i//16]|=1<<((i%16)*4)
chunk={'sections':[{'Y':4,'block_states':{'palette':p,'data':d}}], 'InhabitedTime':720000}
f=features(chunk)
assert f['materials']['red_concrete']==256,f
assert surface(chunk)==bytes.fromhex('a5463d')*256
meta={'overworld':{(x,z):f for x in range(4) for z in range(4)}}
r=discover(meta,minimum=65)
assert len(r)==1 and r[0]['score']>=65,r
print('PASS: packed palette, surface color, discovery and local suppression')
