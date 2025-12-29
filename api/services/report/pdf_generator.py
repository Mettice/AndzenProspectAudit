"""
PDF generation utilities for reports.
"""
from pathlib import Path
from typing import Optional
import platform
import asyncio
from concurrent.futures import ThreadPoolExecutor


async def generate_pdf_weasyprint(html_path: Path) -> Optional[Path]:
    """
    Generate PDF from HTML using WeasyPrint.
    
    Falls back gracefully if WeasyPrint is not installed.
    """
    try:
        from weasyprint import HTML, CSS
        
        pdf_path = html_path.with_suffix('.pdf')
        
        # Read HTML content
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Generate PDF
        HTML(string=html_content, base_url=str(html_path.parent)).write_pdf(
            pdf_path,
            stylesheets=[
                CSS(string='''
                    @page {
                        size: A4;
                        margin: 15mm;
                    }
                    .page-break {
                        page-break-after: always;
                    }
                ''')
            ]
        )
        
        return pdf_path
        
    except ImportError:
        print("WeasyPrint not installed - PDF generation skipped")
        return None
    except Exception as e:
        print(f"PDF generation failed: {e}")
        return None


async def generate_pdf_playwright(html_path: Path) -> Optional[Path]:
    """
    Generate PDF using Playwright browser automation.
    
    Fallback option when WeasyPrint is not available.
    Uses sync Playwright on Windows to avoid asyncio subprocess issues.
    """
    pdf_path = html_path.with_suffix('.pdf')
    
    # On Windows, use sync Playwright in a thread to avoid asyncio subprocess issues
    if platform.system() == "Windows":
        try:
            from playwright.sync_api import sync_playwright
            
            def _generate_sync():
                """Run sync Playwright in a thread."""
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    
                    # Load the HTML file
                    page.goto(f"file://{html_path.absolute()}")
                    
                    # Wait for charts and content to load
                    page.wait_for_timeout(2000)  # Wait 2 seconds for JS to execute
                    
                    # Generate PDF with print settings
                    page.pdf(
                        path=str(pdf_path),
                        format='A4',
                        margin={
                            'top': '15mm',
                            'right': '15mm', 
                            'bottom': '15mm',
                            'left': '15mm'
                        },
                        print_background=True,
                        prefer_css_page_size=True
                    )
                    
                    browser.close()
                
                return pdf_path
            
            # Run sync Playwright in a thread pool to avoid asyncio issues
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, _generate_sync)
                return result
                
        except ImportError:
            raise ImportError("Playwright not installed. Install with: pip install playwright && playwright install chromium")
        except Exception as e:
            raise Exception(f"Playwright sync PDF generation failed: {e}")
    
    # Use async Playwright on non-Windows
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Load the HTML file
            await page.goto(f"file://{html_path.absolute()}")
            
            # Wait for charts and content to load
            await page.wait_for_timeout(2000)  # Wait 2 seconds for JS to execute
            
            # Generate PDF with print settings
            await page.pdf(
                path=str(pdf_path),
                format='A4',
                margin={
                    'top': '15mm',
                    'right': '15mm', 
                    'bottom': '15mm',
                    'left': '15mm'
                },
                print_background=True,
                prefer_css_page_size=True
            )
            
            await browser.close()
        
        return pdf_path
        
    except ImportError:
        raise ImportError("Playwright not installed. Install with: pip install playwright && playwright install chromium")
    except Exception as e:
        raise Exception(f"Playwright async PDF generation failed: {e}")

