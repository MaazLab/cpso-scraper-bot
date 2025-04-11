import json
import logging
from utils import find_element_with_retry, find_doctor_link_with_retry, extract_additional_locations, extract_page_number, load_json, scrape_doctor_data, fill_form
import time
import re
import requests
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium import webdriver
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup


# Set up logging
logging.basicConfig(filename='cpso_scraper.log', level=logging.ERROR)

# Set the path to your ChromeDriver executable
chrome_driver_path = "/usr/bin/chromedriver"

# Define the URL
url = "https://register.cpso.on.ca"

# Set the Chrome options
chrome_options = webdriver.ChromeOptions()
# Run Chrome in headless mode (no GUI)
# chrome_options.add_argument("--headless")

# Create a Chrome webdriver instance
chrome_service = ChromeService(chrome_driver_path)
driver = webdriver.Chrome(service=chrome_service, options=chrome_options)


# Navigate to the URL
driver.get(url+"/Advanced-Search/")

# Find the City/Town dropdown element using label text
city_dropdown_label_text = 'City/Town:'
city_dropdown_label = find_element_with_retry(driver,
    By.XPATH, f'//*[text()="{city_dropdown_label_text}"]')


# Find the associated dropdown element using XPath
city_dropdown = Select(driver.find_element(
    By.XPATH, f'//label[text()="{city_dropdown_label_text}"]/following-sibling::select'))

# Get all options from the dropdown
all_cities = [option.text.strip() for option in city_dropdown.options[1:]]

# Initialize a list to store all doctor data
all_doctor_data = []

# Initialize a set to store unique doctors
unique_doctors = set()

# Read existing JSON data from the input file
# with open("/home/maaz-rafiq/work/welab_health/workload-utilites/CPSO Scraping/cpso_doctors2.json", "r") as json_file:
#     json_data = json.load(json_file)

file_path = 'cpso.json'

if not os.path.exists(file_path):
    with open(file_path, "w") as file:
        json.dump([], file)

with open(file_path, "r") as json_file:
    json_data = json.load(json_file)

# print("JSON Data: ", json_data)
# print("TYPE: ", type(json_data))
# Iterate through doctors and filter duplicates
for doctor in json_data:
    
    cpso_number = doctor.get("CPSO Number")

    # Check if CPSO Number is not in the set (i.e., not a duplicate)
    if cpso_number not in unique_doctors:
        unique_doctors.add(cpso_number)

# Iterate through each option, select it using Selenium, and retrieve doctor information
for city_name in all_cities[1:]:

    driver = fill_form(driver, city_name, postal_code=None)

    try:
        # Wait for the search results to load
        print("Waiting for the search results to load ...")
        WebDriverWait(driver, 20).until(
        EC.any_of(
            EC.presence_of_element_located((By.CLASS_NAME, "search-results")),
        )
    )
    except TimeoutException:
        print(f"Timed out waiting after clicking submit for city: {city_name}")
        driver.refresh()
        break
    
    # Get the HTML content after the form submission
    html = driver.page_source

    print("BeautifulSoup Searched Results...")
    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    print("Looking for Maximum Results Limit ...")
    max_res_div = soup.find('div', {'id': 'maximumResultsCountMessageDesktop'})
    display_status = max_res_div.get('style').split(";")[0].split(":")[-1].strip()


    if display_status == "block":
            print("Maximum Results has reached")
            print("Using postal code to filter results ...")
            
            driver.get(url+"/Advanced-Search/")
            
            print("Loading JSON file containing postal codes ...")
            # Load the JSON file containing postal codes
            postal_codes_file_path = "postal_codes.json"
            
            postal_codes_json = load_json(postal_codes_file_path)
            
            # Extract the postal code for the selected city
            postal_codes = postal_codes_json.get(city_name)
            print(f"Postal_codes of {city_name} \n {postal_codes}" )
            
            for postal_code in postal_codes:

                print("Postal Code: ", postal_code)

                driver = fill_form(driver, city_name, postal_code)

                try:
                    # Wait for the search results to load
                    print("Waiting for the search results to load ...")
                    WebDriverWait(driver, 20).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CLASS_NAME, "search-results")),
                    )
                )
                except TimeoutException:
                    print(f"Timed out waiting after clicking submit for city: {city_name}")
                    break
                
                while True:
                    
                    
                    # Get the HTML content after the form submission
                    html = driver.page_source

                    print("BeautifulSoup Searched Results...")
                    # Parse the HTML content with BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')

                    print("Extracting Total Pages ...")
                    page_number = extract_page_number(driver)

                    if not page_number:
                        print(f"No pages found for {city_name} postal code {postal_code}.")
                        driver.get(url+"/Advanced-Search/")
                        break
                
                    else:
                        print(f"Total Pages in {city_name} postal code {postal_code}: {page_number}")
                        
                        doctors_list = soup.find(
                        'table', {"id":'physicianTable'}).find_all('tr', {"id": "physician-extra-info"})

                        print(f"Total Doctors in a page: {len(doctors_list)}")

                        # Store the extracted information
                        for result in doctors_list:
                            doc_extra_info_url = result.get('data-href')
                            print("result.get('data-href') : ", result.get('data-href'))
                            
                            doctor_data = scrape_doctor_data(url, doc_extra_info_url)

                            print("Scraped Data: \n")
                            print(doctor_data)
                            print("=================================")

                            json_data.append(doctor_data)
                            with open(file_path, "w") as json_file:
                                json.dump(json_data, json_file, indent=2)

                        print("Looking for Next page ...")
                        try:
                            next_page_link_xpath = f"//a[@class='page-select-link' and contains(text(), 'Next page')]"
                            
                            next_page_link_exists = driver.find_element(
                                By.XPATH, next_page_link_xpath)
                            
                            print("Next Page Found")
                            print("Clicking Next Page ...")

                            next_page_link_exists.click()
                            driver.implicitly_wait(5)
                        except NoSuchElementException:
                            print("No Next Page Found")
                            driver.get(url+"/Advanced-Search/")
                            break


            
    
    elif display_status == "none":
        print("Maximum Results has not reached")
        while True:


            print("Extracting Total Pages ...")
            page_number = extract_page_number(driver)
            print(f"Total Pages in {city_name}: {page_number}")


            # Extract information based on the HTML structure
            doctors_list = soup.find(
                'table', {"id":'physicianTable'}).find_all('tr', {"id": "physician-extra-info"})

            print(f"Total Doctors in a page: {len(doctors_list)}")

            print("--------------------------------")

            # Store the extracted information
            for result in doctors_list:
                doc_extra_info_url = result.get('data-href')
                print("result.get('data-href') : ", result.get('data-href'))
                
                doctor_data = scrape_doctor_data(url, doc_extra_info_url)
                

                print("Scraped Data: \n")
                print(doctor_data)
                print("=================================")

                json_data.append(doctor_data)
                with open(file_path, "w") as json_file:
                    json.dump(json_data, json_file, indent=2)

            print("Looking for Next page ...")
            try:
                next_page_link_xpath = f"//a[@class='page-select-link' and contains(text(), 'Next page')]"
                
                next_page_link_exists = driver.find_element(
                    By.XPATH, next_page_link_xpath)
                
                print("Next Page Found")
                print("Clicking Next Page ...")

                next_page_link_exists.click()
                driver.implicitly_wait(5)
            except NoSuchElementException:

                print("No Next Page Found")
                break

        print(city_name + " Done")
        driver.get(url+"/Advanced-Search/")


# Close the browser window
driver.quit()
