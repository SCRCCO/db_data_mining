import requests
from bs4 import BeautifulSoup
import json
import logging
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from nltk.tokenize import word_tokenize

import nltk

nltk.data.find('tokenizers/punkt')


# Configurazione del logger
logging.basicConfig(filename='ebay_scraper.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
def scrape_ebay(search_query):
    results = []
    removed_items = [] 
    prices = []
    
    # Itera solo sulla prima pagina
    for page in range(1, 2):  # Solo la prima pagina
        # URL di ricerca su eBay per la pagina specifica
        url = f"https://www.ebay.it/sch/i.html?_nkw={search_query}&_ipg=120&_pgn={page}&_sop=12"
        
        # Effettua una richiesta GET alla pagina
        response = requests.get(url)
        
        # Controlla se la richiesta è stata effettuata con successo
        if response.status_code != 200:
            logging.error(f"Errore durante la richiesta: {response.status_code} - URL: {url}")
            continue
        
        # Analizza il contenuto della pagina con BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Trova tutti gli elementi che contengono le informazioni dei prodotti
        items = soup.find_all('div', class_='s-item__info')[2:]


        
        for item in items:
            # Estrarre il titolo del prodotto
            title = item.find('div', class_='s-item__title')
            title_text = title.get_text() if title else "No title"
            
            # Estrarre il prezzo del prodotto
            price = item.find('span', class_='s-item__price')
            price_text = price.get_text() if price else "No price"
            
            # Aggiungi il prezzo alla lista dei prezzi
            try:
                price_value = extract_price(price_text)
                prices.append(price_value)
            except ValueError:
                # Ignora se non riesci ad estrarre il prezzo
                continue

            # Registra i dettagli del prezzo e del prodotto nel log
            logging.debug(f"Titolo: {title_text}, Prezzo: {price_text}, URL: {url}")
            
            # Estrarre il link al prodotto
            link = item.find('a', class_='s-item__link')
            link_url = link['href'] if link else "No link"
            
            # Estrarre lo stato del prodotto (nuovo o usato)
            condition = item.find('span', class_='SECONDARY_INFO')
            condition_text = condition.get_text() if condition else "No condition info"
            
            # Estrarre il tipo di vendita (asta o compralo subito)
            auction = item.find('span', class_='s-item__bids')
            auction_text = 'Auction' if auction else 'Buy It Now'
            
            # Aggiungere i risultati alla listaß
            results.append({
                'title': title_text,
                'price': price_text,
                'link': link_url,
                'condition': condition_text,
                'auction': auction_text
            })
        
        # Rimuovere gli outlier basandosi su diff interquartilistica
        if prices:
            q1 = np.percentile(prices, 25)
            q3 = np.percentile(prices, 75)
            iqr = q3 - q1
            lower_bound = q1 -0.5* iqr
            upper_bound = q3 + 0.5 * iqr
            results = [result for result, price in zip(results, prices) if lower_bound <= price <= upper_bound]
            
        
    return results

def calculate_average_price(prices):
    if not prices:
        return 0
    return sum(prices) / len(prices)

def extract_price(price_text):
    # Rimuove i caratteri non numerici e converte in float
    price_cleaned = ''.join(filter(lambda x: x.isdigit() or x in ['.', ','], price_text))
    # Sostituisci le virgole con punti per la formattazione dei numeri decimali
    price_cleaned = price_cleaned.replace(',', '.')
    return float(price_cleaned)

def word_difference(keyword, title):
    # Calcola la differenza nella lunghezza delle parole tra la keyword e il titolo
    keyword_words = keyword.split()
    title_words = title.split()
    return abs(len(title_words) - len(keyword_words))

# Utilizzare la funzione per fare lo scraping dei risultati di "Cyberpunk 2077 ps4"
search_query = "Penna bic"
results = scrape_ebay(search_query)

new_prices = []
used_prices = []

for r in results:
    try:
        price = extract_price(r['price'])
        if r['condition'] in ("Nuovo (Altro)", "Nuovo") and r['auction'] == "Buy It Now":
            new_prices.append(price)
        elif r['condition'] == "Di seconda mano" and r['auction'] == "Buy It Now":
            used_prices.append(price)
    except ValueError:
        # Gestisce il caso in cui il prezzo non possa essere convertito in float
        continue

# Calcolare la media dei prezzi per articoli nuovi e usati
average_new_price = calculate_average_price(new_prices)
average_used_price = calculate_average_price(used_prices)

# Logging delle medie calcolate
print(f"Prezzo medio degli articoli nuovi: {average_new_price:.2f} EUR")
print(f"Prezzo medio degli articoli usati: {average_used_price:.2f} EUR")

# Salvare i risultati filtrati in un file JSON
with open('filtered_results_ebay.json', 'w', encoding='utf-8') as file:
    json.dump(r, file, ensure_ascii=False, indent=4)

print("I risultati filtrati sono stati salvati in 'filtered_results_ebay.json'.")