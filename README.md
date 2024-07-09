# Web Scraping Project

## Description
This project involves creating a web scraper in Python 3.10 that extracts product data from a given URL, handles pagination, and outputs the data in JSON format. It includes the following operations:
- **Lister**: Extracts product URLs.
- **Crawler**: Collects specific data for each product.

## Requirements
- Python 3.10
- Libraries:
  - beautifulsoup4
  - requests
  - pillow
  - PyMuPDF
  - wheel
  - cairosvg
- Download Cairo
Install GTK package to the machine. In my case, gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe. Adding the bin path (C:\Program Files\GTK3-Runtime Win64\bin) to Environment Variables/Path.

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/LucasGentry/web_scraping.git

2. Set up Envrionment
- ```sh
  python -m venv venv
- Run venv/Scripts/activate to activate virtual environment.
- Go back to the project folder.
- ```sh
  pip install -r requirements.txt

3. Usage
```sh
python main.py -c <number_of_crawlers>
python main.py -c 5

4. Outut
products.json

## Optional Features
Parse PDFs for additional information (e.g., UN Number from section 14.1).
Convert product images to PNG thumbnails and save them in the images/ directory.
