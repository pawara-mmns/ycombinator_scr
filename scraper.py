import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# Configuration
SOURCES = [
    {
        "url": "https://news.ycombinator.com/",
        "parser": "hn",
        "name": "Hacker News - Top"
    },
    {
        "url": "https://news.ycombinator.com/newest",
        "parser": "hn",
        "name": "Hacker News - Newest"
    }
]
DATA_FILE = "data.json"

def fetch_data(url):
    try:
        response = requests.get(url, timeout=10) # Added timeout
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_hn(soup, base_url):
    articles = []
    # Hacker News structure often changes, but usually relies on tr with class 'athing'
    rows = soup.find_all('tr', class_='athing')
    
    for row in rows:
        try:
            title_element = row.find('span', class_='titleline').find('a')
            if title_element:
                title = title_element.get_text()
                link = title_element['href']
                
                # Handle relative URLs (internal HN links)
                if not link.startswith('http'):
                    link = "https://news.ycombinator.com/" + link

                articles.append({
                    "title": title,
                    "url": link,
                    "timestamp": datetime.now().isoformat(),
                    "source": "Hacker News" 
                })
        except AttributeError:
            continue
    return articles

def parse_html(html_content, parser_type, url):
    if not html_content:
        return []
        
    soup = BeautifulSoup(html_content, 'html.parser')
    
    if parser_type == 'hn':
        return parse_hn(soup, url)
    
    return []

def load_existing_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

import subprocess

def save_and_commit(new_items, all_data):
    # We need to save the file and commit FOR EACH new item to have unique commits
    # This implies we are appending one by one and committing one by one.
    
    # Reload data to ensure we have the base state (though all_data passed in helps)
    # But to be safe and simple: 
    # 1. We have the full updated list 'all_data' which contains everything.
    # 2. But we need to 'replay' the saving for the new items to get individual commits.
    
    # Strategy: 
    # The 'all_data' passed here is actually the FINAL state. 
    # We should back up a bit. 
    # Let's refactor 'save_data' entirely.
    pass

def process_and_save(fetched_articles):
    existing_data = load_existing_data()
    existing_urls = {item['url'] for item in existing_data}
    
    new_items_count = 0
    commits_made = False
    
    for article in fetched_articles:
        if article['url'] not in existing_urls:
            # Add to memory
            existing_data.append(article)
            existing_urls.add(article['url'])
            
            # Save to file immediately
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=4, ensure_ascii=False)
            
            # Commit immediately
            try:
                print(f"Committing new article: {article['title']}")
                subprocess.run(["git", "add", DATA_FILE], check=True)
                subprocess.run(["git", "commit", "-m", f"Add article: {article['title']}"], check=True)
                commits_made = True
                new_items_count += 1
            except subprocess.CalledProcessError as e:
                print(f"Git commit failed: {e}")

    if commits_made:
        print(f"Pushing {new_items_count} new commits...")
        try:
            subprocess.run(["git", "push"], check=True)
            print("Push successful.")
        except subprocess.CalledProcessError as e:
            print(f"Git push failed: {e}")
    else:
        print("No new items to commit.")

def main():
    all_articles = []
    
    for source in SOURCES:
        print(f"Scraping {source['name']} ({source['url']})...")
        html = fetch_data(source['url'])
        if html:
            articles = parse_html(html, source['parser'], source['url'])
            if articles:
                print(f"Found {len(articles)} articles from {source['name']}.")
                all_articles.extend(articles)
            else:
                print(f"No articles found for {source['name']}.")
        else:
            print(f"Failed to retrieve data for {source['name']}.")
            
    if all_articles:
        process_and_save(all_articles)
    else:
        print("No articles found across all sources.")

if __name__ == "__main__":
    main()
