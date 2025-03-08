import logging
import random

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import requests
import urllib.parse
from urllib.robotparser import RobotFileParser

from constants import (
    SEARCH_API_URL, NUM_SEARCH_RESULTS, NUM_RESEARCH_URLS, USER_AGENTS,
    MAX_SCRAPED_CONTENT_LENGTH,SCRAPE_DELAY, RESPECT_ROBOTS_TXT
)


def perform_search(query):
    """Perform a web search and return formatted results."""
    url = (f'{SEARCH_API_URL}?q={urllib.parse.quote(query)}'
           f'&format=json')
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        results = data.get('results', [])[:NUM_SEARCH_RESULTS]
        formatted_results = []
        for i, result in enumerate(results, 1):
            title = result.get('title', 'No title')
            snippet = result.get('content', 'No snippet')
            formatted_results.append(f'{i}. Title: {title}\nSnippet: {snippet}\n')
        return '\n'.join(formatted_results)
    except Exception as e:
        logging.error(f'Search API error: {str(e)}')
        return 'Failed to retrieve search results.'
    
async def fetch_page(session, url, logger):
    """Fetch page content asynchronously with robots.txt check."""
    if RESPECT_ROBOTS_TXT:
        rp = RobotFileParser()
        rp.set_url(f'{url}/robots.txt')
        try:
            rp.read()
            if not rp.can_fetch(random.choice(USER_AGENTS), url):
                logger.warning(f'Robots.txt disallows scraping: {url}')
                return None
        except Exception as e:
            logger.warning(f'Failed to fetch robots.txt for {url}: {e}')
            # Proceed with scraping if robots.txt is missing

    headers = {'User-Agent': random.choice(USER_AGENTS)}
    try:
        async with session.get(url, headers=headers, timeout=10) as response:
            response.raise_for_status()
            text = await response.text()
            soup = BeautifulSoup(text, 'html.parser')
            content = ' '.join(
                tag.get_text(strip=True)
                for tag in soup.find_all(['p', 'div'])
                if tag.get_text(strip=True)
            )
            return content[:MAX_SCRAPED_CONTENT_LENGTH]
    except Exception as e:
        logger.error(f'Failed to scrape {url}: {e}')
        return None

async def perform_research_search(query, logger):
    """Perform search and scrape top URLs."""
    url = f'{SEARCH_API_URL}?q={urllib.parse.quote(query)}&format=json&language=en'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                results = data.get('results', [])[:NUM_RESEARCH_URLS]
                if not results:
                    logger.error('No search results returned.')
                    return []

                tasks = []
                for result in results:
                    url = result.get('url')
                    if url:
                        tasks.append(fetch_page(session, url, logger))
                        await asyncio.sleep(SCRAPE_DELAY / 1000)

                contents = await asyncio.gather(*tasks)
                return [
                    {'url': result['url'], 'title': result['title'], 'content': content}
                    for result, content in zip(results, contents)
                    if content
                ]
    except Exception as e:
        logger.error(f'Search API error: {e}')
        return []