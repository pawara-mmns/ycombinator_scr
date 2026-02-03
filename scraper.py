import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# Configuration
URL = "https://news.ycombinator.com/"
DATA_FILE = "data.json"

def fetch_data():
    try:
        response = requests.get(URL)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {URL}: {e}")
        return None

def parse_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
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
                    link = URL + link

                articles.append({
                    "title": title,
                    "url": link,
                    "timestamp": datetime.now().isoformat()
                })
        except AttributeError:
            continue
            
    return articles

def load_existing_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_data(data):
    # Determine uniqueness by URL
    existing_data = load_existing_data()
    existing_urls = {item['url'] for item in existing_data}
    
    new_items_count = 0
    for item in data:
        if item['url'] not in existing_urls:
            existing_data.append(item)
            new_items_count += 1
            
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=4, ensure_ascii=False)
        
    print(f"Scraping complete. Added {new_items_count} new items.")

def main():
    print(f"Starting scrape of {URL}...")
    html = fetch_data()
    if html:
        articles = parse_html(html)
        if articles:
            print(f"Found {len(articles)} articles.")
            save_data(articles)
        else:
            print("No articles found.")
    else:
        print("Failed to retrieve data.")

if __name__ == "__main__":
    main()
