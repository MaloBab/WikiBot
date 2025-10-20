#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Service d'interaction avec l'API Wikipedia
"""

import wikipedia
import random
from wikipedia.exceptions import DisambiguationError, PageError
from typing import Tuple, Optional


class WikipediaService:
    """Service d'interaction avec Wikipedia"""
    
    def __init__(self, lang: str = "fr", random_pages: int = 10):
        wikipedia.set_lang(lang)
        self.random_pages = random_pages
    
    def generate_path(self, max_attempts: int = 10) -> Optional[Tuple]:
        """
        Génère un parcours Wikipedia aléatoire
        Retourne: (page_start, page_end, attempts) ou None
        """
        for attempt in range(1, max_attempts + 1):
            try:
                # Générer articles aléatoires
                pages = wikipedia.random(pages=self.random_pages)
                art1 = random.choice(pages)
                art2 = random.choice(pages)
                
                # Article de départ
                try:
                    page1 = wikipedia.page(wikipedia.search(art1)[0])
                except DisambiguationError as e:
                    page1 = wikipedia.page(e.options[0])
                
                # Article d'arrivée (via un lien)
                try:
                    page2 = wikipedia.page(art2)
                except DisambiguationError as e:
                    page2 = wikipedia.page(e.options[0])
                
                if page2.links:
                    target = random.choice(page2.links)
                    target_search = wikipedia.search(target)
                    if target_search:
                        target_final = random.choice(target_search)
                        try:
                            page_target = wikipedia.page(target_final)
                        except DisambiguationError as e:
                            page_target = wikipedia.page(e.options[0])
                    else:
                        page_target = page2
                else:
                    page_target = page2
                
                return (page1, page_target, attempt)
                
            except PageError:
                continue
        
        return None
    
    def get_summary(self, article: str, sentences: int = 2) -> Optional[Tuple[str, str]]:
        """
        Récupère le sommaire d'un article
        Retourne: (article_name, summary) ou None
        """
        try:
            results = wikipedia.search(article)
            
            if not results:
                return None
            
            article_name = results[0]
            for result in results:
                if result.lower() == article.lower().replace('_', ' '):
                    article_name = result
                    break
            
            try:
                summary = wikipedia.summary(article_name, sentences)
            except DisambiguationError as e:
                article_name = e.options[0]
                summary = wikipedia.summary(article_name, sentences)
            
            return (article_name, summary)
            
        except (PageError, Exception):
            return None
