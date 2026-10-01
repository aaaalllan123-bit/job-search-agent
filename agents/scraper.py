"""
Scraper agent: fetch job postings from target URLs.
Supports static HTTP fetching and dynamic browser rendering.
Includes retry logic and structured logging.
"""

import logging
import time
from dataclasses import dataclass
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def _make_selenium_driver(headless: bool = True):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


@dataclass
class RawJobPosting:
    title: str
    company: str
    location: str
    url: str
    raw_text: str
    source: str


class JobScraper:
    def __init__(self, max_retries: int = 3, backoff_seconds: float = 2.0):
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
        )

    def fetch_static(self, url: str) -> str:
        if url.startswith("file://"):
            path = url[7:]
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info("Fetching %s (attempt %d)", url, attempt)
                resp = self.session.get(url, timeout=30)
                resp.raise_for_status()
                return resp.text
            except Exception as exc:
                last_error = exc
                logger.warning("Fetch failed for %s on attempt %d: %s", url, attempt, exc)
                if attempt < self.max_retries:
                    time.sleep(self.backoff_seconds * attempt)
        raise last_error or RuntimeError(f"Failed to fetch {url}")

    def extract_links(self, html: str, base_url: str) -> List[str]:
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            if href.startswith("http"):
                links.append(href)
            elif href.startswith("/"):
                from urllib.parse import urljoin

                links.append(urljoin(base_url, href))
        return links

    def fetch_dynamic(self, url: str) -> str:
        last_error: Optional[Exception] = None
        driver = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info("Dynamic fetch %s (attempt %d)", url, attempt)
                driver = _make_selenium_driver(headless=True)
                driver.get(url)
                # Wait briefly for JS hydration; sites may need explicit waits.
                time.sleep(3)
                html = driver.page_source
                return html
            except Exception as exc:
                last_error = exc
                logger.warning("Dynamic fetch failed for %s on attempt %d: %s", url, attempt, exc)
                if attempt < self.max_retries:
                    time.sleep(self.backoff_seconds * attempt)
            finally:
                if driver is not None:
                    try:
                        driver.quit()
                    except Exception:
                        pass
        raise last_error or RuntimeError(f"Failed to dynamically fetch {url}")

    def _find_containers(self, soup, selectors: Optional[dict]):
        if selectors and "container" in selectors:
            for selector in selectors["container"].split(","):
                selector = selector.strip()
                containers = soup.select(selector)
                if containers:
                    return containers, selectors
        return None, None

    def _parse_postings(self, html: str, source_name: str, url: str, selectors: Optional[dict] = None, follow_links: bool = False, source_type: str = "static") -> List[RawJobPosting]:
        soup = BeautifulSoup(html, "html.parser")
        postings: List[RawJobPosting] = []

        containers, active_selectors = self._find_containers(soup, selectors)

        # Generic fallback heuristics
        if not containers:
            containers = (
                soup.find_all("div", class_=lambda x: x and "job" in x.lower())
                or soup.find_all("li", class_=lambda x: x and "job" in x.lower())
                or soup.find_all("article")
                or soup.find_all("section")
            )

        # Last resort: treat the whole body as one posting.
        if not containers:
            body = soup.find("body")
            if body:
                text = body.get_text(separator="\n", strip=True)
                if len(text) >= 15:
                    title_tag = soup.find("title")
                    title = title_tag.get_text(strip=True) if title_tag else source_name
                    postings.append(
                        RawJobPosting(
                            title=title,
                            company=source_name,
                            location="",
                            url=url,
                            raw_text=text,
                            source=source_name,
                        )
                    )
            return postings

        title_selectors = active_selectors.get("title", "") if active_selectors else ""
        link_selectors = active_selectors.get("link", "") if active_selectors else ""

        for container in containers[:50]:
            title = "Unknown"
            if title_selectors:
                for ts in title_selectors.split(","):
                    ts = ts.strip()
                    tag = container.select_one(ts)
                    if tag:
                        title = tag.get_text(strip=True)
                        break
            if title == "Unknown":
                title_tag = container.find(["h1", "h2", "h3", "h4"])
                title = title_tag.get_text(strip=True) if title_tag else "Unknown"

            text = container.get_text(separator="\n", strip=True)
            if len(text) < 15:
                continue

            job_url = url
            if link_selectors:
                for ls in link_selectors.split(","):
                    ls = ls.strip()
                    link = container.select_one(ls)
                    if link and link.get("href"):
                        from urllib.parse import urljoin
                        job_url = urljoin(url, link["href"])
                        break

            # Optionally fetch detail page to enrich job description.
            if follow_links and job_url != url:
                try:
                    if source_type == "dynamic":
                        detail_html = self.fetch_dynamic(job_url)
                    else:
                        detail_html = self.fetch_static(job_url)
                    detail_text = BeautifulSoup(detail_html, "html.parser").get_text(separator="\n", strip=True)
                    text = text + "\n\n" + detail_text
                except Exception as exc:
                    logger.warning("Failed to fetch detail page %s: %s", job_url, exc)

            postings.append(
                RawJobPosting(
                    title=title,
                    company=source_name,
                    location="",
                    url=job_url,
                    raw_text=text,
                    source=source_name,
                )
            )

        return postings

    def scrape_source(self, source: dict) -> List[RawJobPosting]:
        url = source["url"]
        source_name = source.get("name", url)
        source_type = source.get("type", "static")
        selectors = source.get("selectors")
        follow_links = source.get("follow_links", False)

        if source_type == "dynamic":
            html = self.fetch_dynamic(url)
        else:
            html = self.fetch_static(url)

        return self._parse_postings(html, source_name, url, selectors, follow_links=follow_links, source_type=source_type)
