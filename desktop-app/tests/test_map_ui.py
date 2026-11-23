import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'desktop'))
from app import App
from types import SimpleNamespace
app=App(); app.geometry('1450x900'); app.update(); app.preview_enabled.set(False)
app.chunks={'overworld':{(x,z) for x in range(475) for z in range(475)}}
app.stats={'meta':{}};app.all_locations=[dict(id=str(i),name=f'Fundort #{i+1}',score=85,chests=100,dimension='overworld',x=i*100,y=64,z=i*100) for i in range(65)]
app.city_distance.set("0"); t=time.monotonic();app.refresh_results();app.update();print('Overview seconds:',round(time.monotonic()-t,3))
assert app.results.size()==65 and app.results.winfo_height()>200
app.select_result(12); app.update(); x,y,u=app.transform(1200,1200);assert abs(x-app.canvas.winfo_width()/2)<1 and abs(y-app.canvas.winfo_height()/2)<1
app.step_result(1);assert app.results.curselection()==(13,)
app.start_drag(SimpleNamespace(x=100,y=100));app.drag_map(SimpleNamespace(x=130,y=140));app.click_map(None);app.reset_map();assert app.center is None and app.zoom==1
app.city_distance.set("2048");app.refresh_results();assert app.results.size()<65;app.city_distance.set("0");app.refresh_results();assert app.results.size()==65
app.destroy();print('PASS: 225625 chunks, 65 visible list entries, focus, next, drag and overview reset')
