import subprocess,sys,json,urllib.request,time,tempfile,os
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
root=Path(__file__).resolve().parents[1]
p=subprocess.Popen([sys.executable,str(root/'desktop/webapp.py')],stdout=subprocess.PIPE,text=True)
try:
    url=p.stdout.readline().strip();u=urlsplit(url);base=f'{u.scheme}://{u.netloc}';token=parse_qs(u.query)['token'][0]
    def req(path,data=None):
        return urllib.request.urlopen(urllib.request.Request(base+path,headers={'X-LCF-Token':token,'Content-Type':'application/json'},data=None if data is None else json.dumps(data).encode()),timeout=15)
    assert b'LOST CITY FINDER' in urllib.request.urlopen(url).read()
    assert not json.load(req('/state'))['busy']
    try:urllib.request.urlopen(base+'/state');raise AssertionError('missing auth')
    except urllib.error.HTTPError as e:assert e.code==403
    with tempfile.TemporaryDirectory() as d:
        (Path(d)/'region').mkdir()
        (Path(d)/'region'/'r.0.0.mca').write_bytes(bytes(8192))
        json.load(req('/scan',dict(world=d,mode='city',radius=32,minimum=4,score=60,chests=0,force=True)))
        for i in range(150):
            s=json.load(req('/state'))
            if not s['busy']:break
            time.sleep(.1)
        assert s['epoch']==1,s
        assert json.load(req('/filter',dict(epoch=1,distance=2048,hide=False)))==[]
        assert req('/tile?dim=overworld&x=0&z=0&epoch=1').read().startswith(b'\x89PNG')
    print('PASS: HTTP authentication, scan, filter, PNG terrain endpoint')
finally:
    p.terminate();p.wait(timeout=10)
