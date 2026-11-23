import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'desktop'))
from smart import spaced_locations

def loc(i,x,z,score,dim='overworld'):
    return dict(id=str(i),x=x,z=z,score=score,dimension=dim,chests=20)
a=[loc(1,0,0,95),loc(2,200,0,80),loc(3,2048,0,85),loc(4,100,0,90,'nether'),loc(5,-2047,0,70)]
assert {l['id'] for l in spaced_locations(a,2048)}=={'1','3','4'}
assert len(spaced_locations(a,0))==5 and len(a)==5
print('PASS: spacing, boundary, dimensions, original data retained')
