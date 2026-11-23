import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'desktop'))
from smart import chest_score, discover
assert [chest_score(n) for n in (4,10,20,40,60,100)]==[5,40,60,75,90,98]
def run(n, structures=(), loot=0, **kwargs):
    f={'materials':{},'chests':n,'loot_chests':loot,'activity':0,'structures':list(structures)}
    return discover({'overworld':{(0,0):f}},minimum=0,**kwargs)
assert run(100)[0]['score']==98
assert run(100,['village'])[0]['score']==78
assert run(100,loot=100)[0]['score']==88
assert not run(10,min_chests=20)
print('PASS: confidence thresholds, structure/loot penalties and chest filter')
