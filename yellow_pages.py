#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import fake_useragent
import requests
from lxml import html
import csv
from urllib.parse import urljoin
from datetime import datetime


def parse_listing(keyword, place):
    base_url = "https://www.yellowpages.com"
    ua = fake_useragent.UserAgent()
    headers = {'User-Agent': ua.random}

    all_scraped_results = []
    for key in keyword:
        url = "{}/search?search_terms={}&geo_location_terms={}".format(base_url, key, place)
        while url:
            print("retrieving ", url)
            response = requests.get(url, verify=True, headers=headers)
            if response.status_code == 200:
                parser = html.fromstring(response.text)
                parser.make_links_absolute(base_url)
                # Process the page as before, adding results to all_scraped_results
                scraped_results = process_page(parser, response)
                all_scraped_results += scraped_results
                # Find the next page
                next_page = parser.xpath("//a[@class='next ajax-page']/@href")
                if next_page:
                    url = urljoin(base_url, next_page[0])
                    time.sleep(2)  # Respectful crawling by sleeping between requests
                else:
                    url = None
            elif response.status_code == 404:
                print("Could not find a location matching", place)
                break
            else:
                print("Failed to process page")
                break
    return all_scraped_results


def process_page(parser, response):
    XPATH_LISTINGS = "//div[@class='search-results organic']//div[@class='v-card']"
    listings = parser.xpath(XPATH_LISTINGS)
    scraped_results = []

    for results in listings:
        # Same extraction code as your original script
        XPATH_BUSINESS_NAME = ".//a[@class='business-name']//text()"
        XPATH_BUSSINESS_PAGE = ".//a[@class='business-name']//@href"
        XPATH_TELEPHONE = ".//div[@class='phones phone primary']//text()"
        XPATH_ADDRESS = ".//div[@class='info']//div//p[@itemprop='address']"
        XPATH_STREET = ".//div[@class='street-address']//text()"
        XPATH_LOCALITY = ".//div[@class='locality']//text()"
        XPATH_REGION = ".//div[@class='info']//div//p[@itemprop='address']//span[@itemprop='addressRegion']//text()"
        XPATH_ZIP_CODE = ".//div[@class='info']//div//p[@itemprop='address']//span[@itemprop='postalCode']//text()"
        XPATH_RANK = ".//div[@class='info']//h2[@class='n']/text()"
        XPATH_CATEGORIES = ".//div[@class='info']//div[contains(@class,'info-section')]//div[@class='categories']//text()"
        XPATH_WEBSITE = ".//div[@class='info']//div[contains(@class,'info-section')]//div[@class='links']//a[contains(@class,'website')]/@href"
        XPATH_RATING = ".//div[@class='info']//div[contains(@class,'info-section')]//div[contains(@class,'result-rating')]//span//text()"

        raw_business_name = results.xpath(XPATH_BUSINESS_NAME)
        raw_business_telephone = results.xpath(XPATH_TELEPHONE)
        raw_business_page = results.xpath(XPATH_BUSSINESS_PAGE)
        raw_categories = results.xpath(XPATH_CATEGORIES)
        raw_website = results.xpath(XPATH_WEBSITE)
        raw_rating = results.xpath(XPATH_RATING)
        raw_street = results.xpath(XPATH_STREET)
        raw_locality = results.xpath(XPATH_LOCALITY)
        raw_region = results.xpath(XPATH_REGION)
        raw_zip_code = results.xpath(XPATH_ZIP_CODE)
        raw_rank = results.xpath(XPATH_RANK)

        business_name = ''.join(raw_business_name).strip() if raw_business_name else None
        telephone = ''.join(raw_business_telephone).strip() if raw_business_telephone else None
        business_page = ''.join(raw_business_page).strip() if raw_business_page else None
        rank = ''.join(raw_rank).replace('.\xa0', '') if raw_rank else None
        category = ','.join(raw_categories).strip() if raw_categories else None
        website = ''.join(raw_website).strip() if raw_website else None
        rating = ''.join(raw_rating).replace("(", "").replace(")", "").strip() if raw_rating else None
        street = ''.join(raw_street).strip() if raw_street else None
        locality = ''.join(raw_locality).replace(',\xa0', '').strip() if raw_locality else None
        region = ''.join(raw_region).strip() if raw_region else None
        zipcode = ''.join(raw_zip_code).strip() if raw_zip_code else None

        business_details = {
            'business_name': business_name,
            'telephone': telephone,
            'business_page': business_page,
            'rank': rank,
            'category': category,
            'website': website,
            'rating': rating,
            'street': street,
            'locality': locality,
            'region': region,
            'zipcode': zipcode,
            'listing_url': response.url
        }
        scraped_results.append(business_details)
    return scraped_results


def remove_duplicates(data):
    business_name_set = set()
    unique_data = []
    duplicates = []

    for entry in data:
        business_name = entry['business_name']
        if business_name not in business_name_set:
            unique_data.append(entry)
            business_name_set.add(business_name)
        else:
            duplicates.append(entry)

    return unique_data, duplicates


if __name__ == "__main__":
    keyword_input = input('Enter the search keywords separated by comma: ')
    keywords = keyword_input.split(',')

    place = input('Enter the place name: ')

    scraped_data = parse_listing(keywords, place)

    if scraped_data:
        current_time = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{place}_{current_time}.csv"
        print(f"Writing scraped data to {filename}")
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['rank', 'business_name', 'telephone', 'business_page', 'category', 'website', 'rating',
                          'street', 'locality', 'region', 'zipcode', 'listing_url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for data in scraped_data:
                writer.writerow(data)
        print("Scraping completed and data saved to the CSV file.")

        total_entries = len(scraped_data)
        print(f"Total entries: {total_entries}")

        duplicates_option = input("Do you want to remove duplicates? (y/n): ")
        if duplicates_option.lower() in ('y', 'yes'):
            unique_data, duplicates = remove_duplicates(scraped_data)

            if duplicates:
                duplicates_filename = f"duplicates_{current_time}.csv"
                print(f"Writing duplicate entries to {duplicates_filename}")
                with open(duplicates_filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                    writer.writeheader()
                    for data in duplicates:
                        writer.writerow(data)
                print(f"Duplicate entries ({len(duplicates)}) saved to the CSV file.")

                # Remove duplicates from the original scraped_data and update the CSV file
                scraped_data = unique_data

                # Rewrite the original CSV file with the unique entries
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                    writer.writeheader()
                    for data in scraped_data:
                        writer.writerow(data)

                print("Duplicates removed from the original CSV file.")

            if unique_data:
                # Optional: Save unique_data to a separate CSV file if needed
                pass
        else:
            unique_data = scraped_data

        # Optional: Save unique_data to a separate CSV file if needed

    else:
        print("No data scraped.")
