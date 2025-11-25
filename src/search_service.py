import os
import requests
import json
from dotenv import load_dotenv

class SearchService:
    """
    Palvelu Google-hakujen tekemiseen (Custom Search JSON API).
    """
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.cx = os.getenv("GOOGLE_SEARCH_CX")

    def search(self, query, num_results=3):
        """
        Suorittaa Google-haun.
        
        Args:
            query (str): Hakusana.
            num_results (int): Tulosten määrä (max 10).
            
        Returns:
            list: Lista hakutuloksista (title, link, snippet).
            str: Virheilmoitus jos epäonnistui, muuten None.
        """
        if not self.api_key or not self.cx:
            return [], "Google Search API -avain tai CX-tunnus puuttuu .env-tiedostosta."

        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.api_key,
            'cx': self.cx,
            'q': query,
            'num': num_results
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if 'items' in data:
                for item in data['items']:
                    results.append({
                        'title': item.get('title'),
                        'link': item.get('link'),
                        'snippet': item.get('snippet')
                    })
            return results, None
            
        except Exception as e:
            return [], f"Virhe Google-haussa: {str(e)}"
