from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import re
import json
import requests
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
import time

# Function to handle StaleElementReferenceException
def find_element_with_retry(driver, by, value, retries=3):
    
    for _ in range(retries):
        try:
            element = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((by, value)))
            return element
        except TimeoutException:
            print(
                f"Timeout waiting for element with {by}='{value}' to be present. Retrying...")
            return None
        except StaleElementReferenceException:
            print(f"Stale element exception occurred. Retrying...")
            return None
    raise NoSuchElementException(
        f"Unable to locate element with {by}='{value}' after {retries} retries.")



# Function to handle StaleElementReferenceException for doctor name link
def find_doctor_link_with_retry(driver, cpso_number, retries=3):
    for _ in range(retries):
        try:
            doctor_link = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located(
                    (By.XPATH, f'//a[contains(@href, "{cpso_number}")]')))
            return doctor_link
        except TimeoutException:
            print(
                f"Timeout waiting for doctor link with cpso '{cpso_number}' to be present. Retrying...")
        except StaleElementReferenceException:
            print(f"Stale element exception occurred. Retrying...")
    raise TimeoutException(
        f"Unable to locate doctor link with cpso '{cpso_number}' after {retries} retries.")



# Function to extract additional location details
def extract_additional_locations(driver):
    try:
        additional_locations_container = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located(
                (By.ID, 'additionallocations')))

        # Use BeautifulSoup to parse the inner HTML of the 'location_details' class div
        location_details_html = additional_locations_container.get_attribute(
            "innerHTML")
        soup = BeautifulSoup(location_details_html, 'html.parser')

        # Find the div with the class 'location_details'
        location_details_element = soup.find('div', class_='location_details')

        if location_details_element:
            # Initialize a list to store all location information
            all_locations = []

            # Initialize variables for the current location information
            current_location = {'Address': '', 'Phone': 'None', 'Fax': 'None'}
            # Convert stripped_strings to a list for indexing
            stripped_strings_list = list(
                location_details_element.stripped_strings)

            # Initialize a flag to track whether the current sibling is before 'Phone:'
            before_phone_flag = True

            for sibling_index, sibling in enumerate(stripped_strings_list):
                # Check if the sibling text starts with 'Phone:'
                if sibling.startswith('Phone:'):
                    # Set the phone information for the new location
                    current_location['Phone'] = stripped_strings_list[sibling_index + 1].strip()
                    before_phone_flag = False

                elif sibling.startswith('Fax:'):
                    # If 'Fax:' is found, set the fax information for the current location
                    current_location['Fax'] = stripped_strings_list[sibling_index + 1].strip()
                elif sibling.startswith('Electoral District:'):
                    current_location['Address'] = current_location['Address'].strip(
                    )
                    all_locations.append(current_location)
                    current_location = {'Address': '',
                                        'Phone': 'None', 'Fax': 'None'}
                    before_phone_flag = True
                elif sibling.startswith('County:'):
                    continue

                elif before_phone_flag:
                    # Check if the previous sibling was 'Electoral District:', skip adding the address
                    if stripped_strings_list[sibling_index - 1].strip() == 'Electoral District:':
                        continue
                    # Append the text to the address information for the current location
                    current_location['Address'] += ' '.join(
                        sibling.strip().split()).replace('Canada', '') + ' '
                else:
                    continue

            return all_locations

    except TimeoutException:
        #print("Timeout waiting for additional locations. Skipping...")
        return []
    

def extract_page_number(driver):
    try:
        # Find the element using a specific XPath
        page_number_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@class="search-results"]/div[@class="info-pages"]'))
        )

        # Extract the page number text
        page_number_text = page_number_element.text.strip()

        # Use regular expression to find the first number in the text
        match = re.search(r'\d+(?!.*\d)', page_number_text)

        # Extract the page number if the match is found
        page_number = int(match.group()) if match else None

        if page_number is not None:
            #print(f"Page number extracted successfully: {page_number}")
            return page_number
        else:
            #print("No match found for page number.")
            return None

    except TimeoutException:
        #print("Timed out after 5 seconds. Element not found.")
        return None
    except NoSuchElementException:
        #print("The specified element was not found.")
        return None
    except ValueError:
        #print("Error converting the page number to an integer.")
        return None
    


# Function to extract and click the next page or next group link
def click_next_page_or_group(driver, actual_page):
    # Extract all page links
    page_links = driver.find_elements(
        By.XPATH, '//nav[@aria-label="Search Results Pagination"]//a[@id]')
    # Check if the next page link exists
    next_page_link_xpath = f'//a[text()="{actual_page}"]'
    next_page_link_exists = driver.find_elements(
        By.XPATH, next_page_link_xpath)

    # Check if the "Next 5" link exists
    next_group_link_xpath = '//a[contains(@id, "lnbNextGroup") and not(contains(@class, "aspNetDisabled"))]'
    next_group_link_exists = driver.find_elements(
        By.XPATH, next_group_link_xpath)

    # Extract the text from each link
    page_texts = [link.text.strip() for link in page_links]

    if not next_page_link_exists and not next_group_link_exists:
        print("Break Loop")
        return  # Break out of the pagination loop if neither link is found

    # Check if the actual_page is in the list of page texts
    if str(actual_page) in page_texts:
        # Click the link with the actual_page text
        driver.find_element(By.XPATH, f'//a[text()="{actual_page}"]').click()
    else:
        # Click the "Next 5" link
        driver.find_element(
            By.XPATH, '//a[@id="p_lt_ctl01_pageplaceholder_p_lt_ctl03_CPSO_DoctorSearchResults_lnbNextGroup"]').click()

def load_json(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {file_path}")
        return None



def scrape_doctor_data(url, doc_extra_info_url):
    
    # GET HTML content of the doctor's extra info page and pass it to BeautifulSoup
    print(f"Requesting Doctor's Info page {url+doc_extra_info_url} ...")
    doc_extra_info_pg = requests.get(url+doc_extra_info_url)

    print("BeautifulSoup Doctor's Info ...")
    doc_extra_info_soup = BeautifulSoup(doc_extra_info_pg.content, 'html.parser')

    doctor_name = doc_extra_info_soup.find('h1',{'class':'doctor-name scrp-contactname-value'}).text.strip() if doc_extra_info_soup.find('h1',{'class':'doctor-name scrp-contactname-value'}) else None

    doc_last_name, doc_first_name = doctor_name.split(",") if doctor_name else (None, None)
    # print("doctor_name: ", doctor_name)

    cpso_number = doc_extra_info_soup.find('span', {'class':'scrp-cpsonumber-value'}).text.strip() if doc_extra_info_soup.find('span', {'class':'scrp-cpsonumber-value'}) else None
    # print("cpso_number: ", cpso_number)

    # Extract the <p> tag containing location, phone, and fax information
    info_div = doc_extra_info_soup.find('div', {'id':'practice-information'})

    doc_loc_phone_fax_div_list = info_div.find_all('div',{'class': 'list-content'})
    
    
    doctor_locations = [] ; doctor_phones = [] ; doctor_fax = []
    print("Extracting Address, Phone Number and Fax...")
    for div in doc_loc_phone_fax_div_list:
        
        address_divs = div.find_all('div', {'class': 'list-content-section scrp-practiceaddress'})
        phone_divs = div.find_all('div', {'class': 'list-content-section scrp-phone'})
        fax_divs = div.find_all('div', {'class': 'list-content-section scrp-fax'})

        for address_div in address_divs:
            address_span = address_div.find("span", {'class': 'scrp-practiceaddress-value'})
            doctor_locations.append(address_span.text.strip() if address_span else None)
        
        for phone_div in phone_divs:
            phone_span = phone_div.find("span", {'class': 'scrp-phone-value'})
            doctor_phones.append(phone_span.text.strip() if phone_span else None)

        for fax_div in fax_divs:
            fax_span = fax_div.find("span", {'class': 'scrp-fax-value'})
            doctor_fax.append(fax_span.text.strip() if fax_span else None)
    
    print("Total Adresses: ",len(doctor_locations))



    print("Extracting Specialization...")
    # Extract the specialization
    specialization = doc_extra_info_soup.find('div', {'class':'scrp-specialtyname-value'}).text.strip() if doc_extra_info_soup.find('div', {'class':'scrp-specialtyname-value'}) else None
    # print("specialization: ", specialization)

    return {
        'FirstName': doc_first_name,
        "LastName": doc_last_name,
        'CPSONumber': cpso_number,
        'Location': doctor_locations,
        'Phone': doctor_phones,
        'Fax': doctor_fax,
        'Specialization': specialization
    }


def fill_form(driver, city_name, postal_code):
    
    # Re-find the City/Town dropdown element
    city_dropdown = Select(find_element_with_retry( driver, By.ID, "cityDropDown"))
    print("Selected city: ", city_name)
    # Select the option
    city_dropdown.select_by_visible_text(city_name)

    if postal_code:
        # Find the Postal Code input field
        postal_code_input = find_element_with_retry(driver, By.ID, "postalCode")
        # Enter the postal code
        postal_code_input.send_keys(postal_code)

    # Find the "Submit" button
    submit_button = find_element_with_retry( driver, By.CLASS_NAME, "search-button")

    # Scroll to the element
    actions = ActionChains(driver)
    actions.move_to_element(submit_button).perform()



    print("Clicked Search ...")
    # Click the "Submit" button
    submit_button.click()

    time.sleep(5)
    return driver
    