"""GUI regression: invoke scan button and verify completed scan on synthetic world."""
import os,sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'desktop'))
from app import App
from test_scanner import create_region

def main():
    with tempfile.TemporaryDirectory() as temp:
        os.environ['LOCALAPPDATA']=temp
        folder=Path(temp)/'world'/'region';folder.mkdir(parents=True)
        create_region(folder/'r.0.0.mca')
        app=App();app.world=str(folder.parent);app.mode.set('Klassische Truhensuche')
        app.report_callback_exception=lambda *args: (_ for _ in ()).throw(args[1])
        errors=[];app.failed=lambda msg:errors.append(msg)
        app.scan_btn.invoke()
        assert app.scanning and str(app.scan_btn['state'])=='disabled'
        deadline=time.monotonic()+20
        def check():
            if errors or not app.scanning or time.monotonic()>deadline:app.quit()
            else:app.after(30,check)
        app.after(30,check);app.mainloop()
        assert not errors,errors
        assert not app.scanning and len(app.locations)==1
        assert str(app.scan_btn['state'])=='normal'
        app.destroy()
        print('PASS: GUI scan button, disabled during scan, enabled on completion, one found location')
if __name__=='__main__':main()
