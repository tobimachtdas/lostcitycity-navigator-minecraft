"""Local web frontend bridge; world files are only read."""
import json, math, multiprocessing, secrets, sys, threading, time, subprocess, webbrowser, zlib, struct, os
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from storage import cached_scan, reviews, review
from smart import discover, render, spaced_locations
from scanner import cluster
ROOT=Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1])); TOKEN=secrets.token_urlsafe(24)
state={'busy':False,'progress':0,'message':'Bereit','world':'','locations':[],'stats':{},'epoch':0}; cells={}; meta={}; lock=threading.RLock(); tiles={}; tile_lock=threading.Lock()
def png(w,h,p):
    def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(b'\0'+p[y*w*3:(y+1)*w*3] for y in range(h))))+chunk(b'IEND',b'')
def run_scan(opt):
    global cells,meta
    start=time.monotonic(); world=opt['world']
    def progress(i,n,p):
        with lock:state.update(progress=int(i*100/max(n,1)),message=f'{i}/{n} Regionen · {p}')
    try:
        ent,c,s=cached_scan(world,progress,force=bool(opt.get('force')))
        mode=opt['mode']; r=int(opt['radius']); loc=cluster(ent,r,int(opt['minimum'])) if mode=='classic' else discover(s['meta'],mode,int(opt['score']),radius=max(64,r*3) if mode=='city' else r,min_chests=int(opt['chests']))
        labels=reviews(world)
        for l in loc:l['review']=labels.get(l['id'],'Ungeprüft')
        with lock:
            cells=c;meta=s.pop('meta');state.update(world=world,locations=loc,stats=s,busy=False,progress=100,message=f'{s["cache_hits"]} aus Cache · {s["scanned_regions"]} neu · {time.monotonic()-start:.1f} s',epoch=state['epoch']+1)
    except Exception as e:
        with lock:state.update(busy=False,message='Fehler: '+str(e))
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def send(self,data,kind='application/json',code=200):
        if not isinstance(data,bytes):data=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(code);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data)
    def auth(self):return self.headers.get('X-LCF-Token')==TOKEN
    def do_GET(self):
        u=urlparse(self.path); q=parse_qs(u.query)
        try:
            if u.path=='/' and q.get('token')==[TOKEN]:return self.send((ROOT/'frontend/index.html').read_bytes(),'text/html; charset=utf-8')
            if u.path in ('/app.js','/style.css'):return self.send((ROOT/'frontend'/u.path[1:]).read_bytes(),'text/javascript' if u.path.endswith('.js') else 'text/css')
            if not self.auth():return self.send({'error':'Nicht autorisiert'},code=403)
            if u.path=='/state':
                with lock:return self.send(state)
            if u.path=='/overview':
                dim=q['dim'][0]; heat=q.get('heat',['0'])[0]=='1'
                with lock:
                    c=cells.get(dim,set()); m=meta.get(dim,{})
                    if not c:return self.send({'bounds':[0,0,16,16],'points':[]})
                    x0=min(x for x,z in c);z0=min(z for x,z in c);x1=max(x for x,z in c)+1;z1=max(z for x,z in c)+1
                    step=max(1,math.ceil(max(x1-x0,z1-z0)/768)); p={}
                    for x,z in c:
                        k=((x-x0)//step,(z-z0)//step);a=m.get((x,z),{}).get('activity',0) if heat else 0;p[k]=max(a,p.get(k,0))
                    return self.send({'bounds':[x0*16,z0*16,x1*16,z1*16],'step':step*16,'points':[[x,z,a] for (x,z),a in p.items()]})
            if u.path=='/tile':
                dim=q['dim'][0];x=int(q['x'][0]);z=int(q['z'][0]);epoch=int(q['epoch'][0]); key=(epoch,dim,x,z)
                with lock:
                    if state['busy'] or epoch!=state['epoch']:return self.send({'error':'Veraltet'},code=409)
                    world=state['world']
                if abs(x)>234376 or abs(z)>234376:raise ValueError('Kachel außerhalb der Welt')
                with tile_lock:
                    if key not in tiles:
                        side,p,_,_=render(world,dim,x*8+4,z*8+4,4); # 144x144; crop to 128
                        p=b''.join(p[y*side*3:y*side*3+384] for y in range(128));tiles[key]=png(128,128,p)
                        if len(tiles)>160:tiles.pop(next(iter(tiles)))
                    return self.send(tiles[key],'image/png')
            self.send({'error':'Unbekannt'},code=404)
        except Exception as e:self.send({'error':str(e)},code=400)
    def do_POST(self):
        if not self.auth():return self.send({'error':'Nicht autorisiert'},code=403)
        try:
            n=int(self.headers.get('Content-Length','0')); assert 0<n<100000; o=json.loads(self.rfile.read(n)); path=self.path
            if path=='/pick':
                cmd=[sys.executable] if getattr(sys,'frozen',False) else [sys.executable,str(Path(__file__).resolve())]
                p=subprocess.run(cmd+['--pick-folder'],capture_output=True,encoding='utf-8',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));return self.send({'world':p.stdout.strip()})
            if path=='/youtube':
                webbrowser.open('https://www.youtube.com/@tobimachtdas');return self.send({'ok':True})
            if path=='/scan':
                with lock:
                    if state['busy']:raise ValueError('Scan läuft bereits')
                    if not (8<=int(o['radius'])<=128 and 2<=int(o['minimum'])<=500 and 0<=int(o['score'])<=100 and 0<=int(o['chests'])<=100000 and o['mode'] in ('city','base','storage','activity','all','classic')):raise ValueError('Suchfilter ungültig')
                    if not Path(o['world']).is_dir():raise ValueError('Weltordner ungültig')
                    state.update(busy=True,progress=0,message='Welt wird analysiert …')
                threading.Thread(target=run_scan,args=(o,),daemon=True).start();return self.send({'ok':True})
            if path=='/filter':
                with lock:
                    if int(o.get('epoch',-1))!=state['epoch']:raise ValueError('Veralteter Scan')
                    loc=[l for l in state['locations'] if not o.get('hide') or l.get('review') not in ('Fehlalarm','Generierte Struktur')];return self.send(spaced_locations(loc,max(0,int(o['distance']))))
            if path=='/review':
                with lock:
                    if state['busy'] or o['epoch']!=state['epoch']:raise ValueError('Veralteter Scan')
                    l=next(l for l in state['locations'] if l['id']==o['id']);label=o['label'];assert label in ('Ungeprüft','Eigener Bau','Anderer Spielerbau','Generierte Struktur','Fehlalarm');review(state['world'],l['id'],label);l['review']=label;return self.send({'ok':True})
            self.send({'error':'Unbekannt'},code=404)
        except Exception as e:self.send({'error':str(e)},code=400)
if __name__=='__main__':
    multiprocessing.freeze_support()
    if '--pick-folder' in sys.argv:
        root=tk.Tk();root.withdraw();root.attributes('-topmost',True)
        try:
            result=filedialog.askdirectory(parent=root)
            sys.stdout.buffer.write(result.encode('utf-8'));sys.stdout.flush()
        finally:root.destroy()
        sys.exit(0)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    url=f'http://127.0.0.1:{server.server_port}/?token={TOKEN}';print(url,flush=True)
    if '--browser' in sys.argv:webbrowser.open(url)
    if '--parent-pipe' in sys.argv:
        def monitor():
            try:sys.stdin.buffer.read()
            finally:server.shutdown()
        threading.Thread(target=monitor,daemon=True).start()
    try:server.serve_forever()
    finally:server.server_close()
