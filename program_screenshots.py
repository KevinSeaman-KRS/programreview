"""
Capture screenshots of program landing pages using Playwright.
POC: Just 2 programs to test the approach.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from playwright.async_api import async_playwright

PROGRAMS_POC = [
    {
        "name": "BA in Business Administration",
        "url": "https://www.uagc.edu/online-degrees/bachelors/business-administration",
        "filename": "screenshot_baba.png"
    },
    {
        "name": "Master of Business Administration",
        "url": "https://www.uagc.edu/online-degrees/masters/business-administration",
        "filename": "screenshot_mba.png"
    }
]

OUTPUT_DIR = "C:/Users/kseaman/Downloads/Cursor/screenshots"

async def capture_screenshots():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        
        for prog in PROGRAMS_POC:
            print(f"Capturing: {prog['name']}...")
            try:
                await page.goto(prog['url'], wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(2000)
                filepath = os.path.join(OUTPUT_DIR, prog['filename'])
                await page.screenshot(path=filepath, full_page=False)
                print(f"  Saved: {filepath}")
            except Exception as e:
                print(f"  ERROR: {e}")
        
        await browser.close()

asyncio.run(capture_screenshots())
print("\nDone!")
