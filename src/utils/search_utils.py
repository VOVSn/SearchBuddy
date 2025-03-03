import requests
import urllib.parse
import logging
from constants import SEARCH_API_URL, NUM_SEARCH_RESULTS


def perform_search(query):
    """Perform a web search and return formatted results."""
    url = (f'{SEARCH_API_URL}?q={urllib.parse.quote(query)}'
           f'&format=json&language=en')
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