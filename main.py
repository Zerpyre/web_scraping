import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import fitz  # PyMuPDF
import json
import os
import argparse
from io import BytesIO
import cairosvg

# Base URL for the monounsaturated fatty acids category
BASE_URL = 'https://www.larodan.com/products/category/monounsaturated-fa/'

# Fetch the content of a given URL and return the HTML text
def fetch_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return None
        else:
            raise

# Parse HTML content and return a BeautifulSoup object
def parse_html(html):
    return BeautifulSoup(html, 'html.parser')

# Extract product URLs from a given page's HTML content
def get_product_urls(page_html):
    soup = parse_html(page_html)
    product_links = []
    for link in soup.select('a.woocommerce-LoopProduct-link'):
        product_links.append(link.get('href'))
    return product_links

# Handle pagination by iterating through pages and collecting all product URLs
def handle_pagination(initial_url):
    urls = []
    page_number = 1
    while True:
        url = f"{initial_url}/page/{page_number}/"
        page_html = fetch_page(url)
        if page_html is None:
            break
        product_urls = get_product_urls(page_html)
        if not product_urls:
            break
        urls.extend(product_urls)
        page_number += 1
    return urls

# Parse product page and extract relevant data into a dictionary
def parse_product_page(url):
    product_html = fetch_page(url)
    if product_html is None:
        return None
    soup = parse_html(product_html)

    def get_text_or_none(selector):
        element = soup.select_one(selector)
        return element.text.strip() if element else None

    def get_text_for(selector):
        element = soup.select_one(selector)
        if not element:
            return None
        structure = ''.join(str(item) for item in element.contents if item.name != 'span').strip()
        return structure

    def get_attr_or_none(selector, attr):
        element = soup.select_one(selector)
        return element[attr].strip() if element and element.has_attr(attr) else None

    def clean_price(price_str):
        # Remove any non-numeric characters except the decimal point
        cleaned = ''.join(c for c in price_str if c.isdigit() or c == '.')
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            print(f"Could not convert price: {price_str}")
            return None

    product_data = {
        'id': get_text_or_none('.product_meta .sku'),
        'name': get_text_or_none('.product-title'),
        'CAS': get_text_or_none('.product-main-info .product-prop:nth-of-type(2)').split(" ")[-1] if get_text_or_none('.product-main-info .product-prop:nth-of-type(2)') != None else None,
        'structure': get_text_for('.product-prop:contains("Molecular formula:")'),
        'smiles': get_text_for('.product-prop:contains("Smiles:")'),
        'description': soup.select_one('meta[name="description"]')['content'],
        'molecular_weight': get_text_for('.product-prop:contains("Molecular weight:")'),
        'url': url,
        'img': soup.select_one('.prod-structure img')['src'] if soup.select_one('.prod-structure img') else None,
        'pdf_msds': get_attr_or_none('.product-prop .button.alt', 'href'),
        'synonyms': get_text_for('.product-prop:contains("Synonyms:")').split(',') if get_text_for('.product-prop:contains("Synonyms:")') else None,
        'packaging': {
            package.select_one('td:nth-of-type(2)').text.split('-')[-1].strip(): clean_price(package.select_one('td:nth-of-type(3)').text.strip())
            for package in soup.select('.product-variations-table tr')
            if package.select_one('td:nth-of-type(3)')
        } if soup.select('.product-variations-table tr') else {}
    }

    # Logging product data for debugging
    # print(f"Parsed data for {url}: {product_data}")

    return product_data

# Save product image from URL to local path
def save_image(image_url, image_path):
    if image_url:
        response = requests.get(image_url)
        response.raise_for_status()
        try:
            cairosvg.svg2png(bytestring=response.content, write_to=image_path)
        except Exception as e:
            print("Error occured while converting svg to png", repr(e))

# Parse the text content of a PDF from a URL
def parse_pdf(pdf_url):
    if pdf_url and pdf_url.startswith('http'):
        response = requests.get(pdf_url)
        response.raise_for_status()
        pdf_document = fitz.open(stream=response.content, filetype="pdf")
        text = ""
        for page in pdf_document:
            text += page.get_text()
        return text
    return ""

# Save product data to a JSON file and process images and PDFs
def save_product_data(product_data, index):
    image_dir = 'images'
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)
    image_path = os.path.join(image_dir, f"{product_data['id']}.png")
    save_image(product_data['img'], image_path)
    product_data['image_path'] = image_path
    if product_data.get('pdf_msds') and product_data['pdf_msds'].startswith('http'):
        try:
            pdf_text = parse_pdf(product_data['pdf_msds'])
            if 'UN number' in pdf_text:
                product_data['UN number'] = pdf_text.split('UN number')[1].split('\n')[1].strip()
        except Exception as e:
            print("Error occured while reading a pdf file,", product_data['pdf_msds'], repr(e))
            
    with open(f'product.json', 'a') as file:
        try:
            json.dump(product_data, file, indent=4)
            file.write("\n")
        except Exception as e:
            print("Error occured while saving product data in", product_data['url'])
        finally:
            print('Processed', product_data['url'])

# Main function to handle the crawling and parsing process
def main(crawlers):
    print("Starting crawling and parsing. Please, wait.")
    # Test using one example
    # results = parse_product_page("https://www.larodan.com/product/10z-pentadecenoic-acid/")
    # save_product_data(results, 1)

    product_urls = handle_pagination(BASE_URL)
    with ThreadPoolExecutor(max_workers=crawlers) as executor:
        results = executor.map(parse_product_page, product_urls)
        for index, product_data in enumerate(results):
            if product_data:
                save_product_data(product_data, index)
    print("Done!")
# Entry point of the script
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Web scraping script with parallel crawlers.')
    parser.add_argument('-c', type=int, help='Number of parallel crawlers', default=1)
    args = parser.parse_args()
    main(args.c)
