import sys,tempfile,os,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'desktop'))
from storage import cached_scan, review, reviews
from test_scanner import create_region

def main():
    with tempfile.TemporaryDirectory() as temp:
        os.environ['LOCALAPPDATA']=temp
        folder=Path(temp)/'world'/'region';folder.mkdir(parents=True)
        a=folder/'r.0.0.mca';b=folder/'r.1.0.mca';create_region(a);create_region(b)
        _,_,s=cached_scan(folder.parent,workers=2);assert s['scanned_regions']==2 and s['failed_regions']==0,s
        _,_,s=cached_scan(folder.parent);assert s['cache_hits']==2,s
        os.utime(a,ns=(a.stat().st_atime_ns,a.stat().st_mtime_ns+1000000000))
        _,_,s=cached_scan(folder.parent);assert s['cache_hits']==1 and s['scanned_regions']==1,s
        review(folder.parent,'test','Eigener Bau');assert reviews(folder.parent)['test']=='Eigener Bau'
        review(folder.parent,'test','Ungeprüft');assert not reviews(folder.parent)
        print('PASS: parallel scan, cache hits, invalidation, persistent reviews')
if __name__=='__main__':main()
