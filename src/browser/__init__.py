"""Browser module - Browser automation with Playwright"""

from src.browser.browser_controller import BrowserController
from src.browser.page_analyzer import PageAnalyzer
from src.browser.actions import BrowserActions

__all__ = ['BrowserController', 'PageAnalyzer', 'BrowserActions']
