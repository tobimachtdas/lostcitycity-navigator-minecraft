import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]/'desktop'))
from app import App, CREATOR_URL
app=App(); app.update()
assert 'tobimachtdas' in app.title()
assert app.creator_btn.winfo_ismapped()
with patch('app.webbrowser.open',return_value=True) as browser:
    app.creator_btn.invoke()
    browser.assert_called_once_with(CREATOR_URL,new=2)
app.destroy()
print('PASS: creator credit, visible and functional YouTube button')
