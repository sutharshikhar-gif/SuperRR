"""Save one full-page PNG per Streamlit page. Install playwright and Chromium first."""
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = 'http://localhost:8501'
OUT = Path(__file__).parent
OUT.mkdir(parents=True, exist_ok=True)
PAGES = ['Overview','Pressure','Matches','Batters','Bowlers','Final 10','Reliability','Methodology']
HEADINGS = {'Overview':'Who Delivers','Pressure':'What is Pressure?','Matches':'Match Explorer','Batters':'Batter Deep-Dive',
            'Bowlers':'Bowler Deep-Dive','Final 10':'Final Top 10 and Evidence','Reliability':'Reliability and Limits',
            'Methodology':'Methodology and Downloads'}
with sync_playwright() as p:
    chrome = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    browser = p.chromium.launch(headless=True, executable_path=str(chrome) if chrome.exists() else None)
    page = browser.new_page(viewport={"width": 1680, "height": 1200}, device_scale_factor=1)
    page.goto(URL, wait_until='domcontentloaded', timeout=90000)
    page.wait_for_selector('.hero', timeout=90000)
    page.wait_for_timeout(1000)
    for i, name in enumerate(PAGES, 1):
        if i > 1:
            page.get_by_role('link', name=name, exact=True).click()
            page.get_by_text(HEADINGS[name],exact=False).first.wait_for(state='visible',timeout=30000)
            page.wait_for_timeout(1000)
        page.evaluate('window.scrollTo(0, 0)')
        page.wait_for_timeout(250)
        slug = name.lower().replace('?', '').replace(' ', '_').replace('-', '_')
        page.screenshot(path=str(OUT / f'{i:02d}_{slug}.png'), full_page=True, animations='disabled', timeout=90000)
    browser.close()
