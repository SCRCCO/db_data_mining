import requests
import json
import re
import requests
from bs4 import BeautifulSoup
import json
import logging
import numpy as np

logging.basicConfig(filename='subito.it/subito_scraper.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_subito(search_query):
    results = []
    prices = []

    
    # Itera solo sulla prima pagina
    for page in range(0, 2):  # Solo la prima pagina
        # URL di ricerca su eBay per la pagina specifica
        url = f"https://www.subito.it/annunci-italia/vendita/usato/?q={search_query}&o={page}"
        
        # Effettua una richiesta GET alla pagina
        response = requests.get(url)
        
        # Controlla se la richiesta è stata effettuata con successo
        if response.status_code != 200:
            logging.error(f"Errore durante la richiesta: {response.status_code} - URL: {url}")
            continue
        
        # Analizza il contenuto della pagina con BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Trova tutti gli elementi che contengono le informazioni dei prodotti
        items = soup.find_all('div', class_='SmallCard-module_card__3hfzu items__item item-card item-card--small')


        
        for item in items:
            # Estrarre il titolo del prodotto
            children = item.contents[0].contents[0]
            title = children.find('h2')
            title_text = title.get_text() if title else "No title"
            
            # Estrarre il prezzo del prodotto
            
            price = children.find('div', class_='index-module_container__zrC59')
            price_tag = price.find('p').next.get_text()
            has_digits = any(char.isdigit() for char in price_tag)
    
            price_text = "".join(list(filter(lambda x: x.isdigit(), price_tag))) if (price_tag and has_digits) else "No price"

     

            link_url = item.find('a')['href'] if item else "No link"
      
            
            has_digits = any(char.isdigit() for char in price_text)
            if has_digits:
                    prices.append(float(price_text)

            
            )
       

            # Registra i dettagli del prezzo e del prodotto nel log
            logging.debug(f"Titolo: {title_text}, Prezzo: {price_text}, URL: {link_url}")

            
            # Aggiungere i risultati alla listaß
            results.append({
                'title': title_text,
                'price': price_text,
                'link': link_url,
            })
        
            
        
    return results


def calculate_average_price(prices):
    if not prices:
        return 0
    return sum(prices) / len(prices)


def remove_outliers_iqr(prices):
  """
  Removes outliers from a list of prices using the Interquartile Range (IQR) method.

  Args:
      prices: A list of numerical prices.

  Returns:
      A new list of prices without outliers.
  """

  if not prices:
      return prices  # Handle empty list gracefully

  try:
      q1 = np.percentile(prices, 25)
      q3 = np.percentile(prices, 75)
      iqr = q3 - q1
      lower_bound = q1 
      upper_bound = q3 

      filtered_prices = [price for price in prices if lower_bound <= price <= upper_bound]
      return filtered_prices
  except ValueError:  # Handle potential errors (e.g., non-numeric values)
      logging.warning("Error filtering prices using IQR: Prices might contain non-numeric values.")
      return prices  # Return the original list if filtering fails



search_query = "God of war ragnarok"
results = scrape_subito(search_query)

prices = []

for r in results:
    try:
        price = float(r['price'])
        prices.append(price)
    except ValueError:
        # Gestisce il caso in cui il prezzo non possa essere convertito in float
        continue

extracted_prices = remove_outliers_iqr(prices)
            





# Calcolare la media dei prezzi per articoli nuovi e usati
average_used_price = calculate_average_price(extracted_prices)

# Logging delle medie calcolate
print(f"Prezzo medio degli articoli usati: {average_used_price:.2f} EUR")

# Salvare i risultati filtrati in un file JSON
with open('subito.it/filtered_results_subito.json', 'w', encoding='utf-8') as file:
    json.dump(results, file, ensure_ascii=False, indent=4)

print("I risultati filtrati sono stati salvati in 'filtered_results_subito.json'.")
