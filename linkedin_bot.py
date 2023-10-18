import os
import logging
import time
import json
import random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient


# Constantes
LINKEDIN_URL = 'https://www.linkedin.com'
LINKEDIN_LOGIN_URL = 'https://www.linkedin.com/login'
COOKIES_PATH = "/data/linkedin_cookies.txt"
PROFILES_JSON_PATH = "/data/linkedin_profiles.json"
SCREENSHOT_PATH = "/data/mynetwork_screenshot.png"
LINKEDIN_SEARCH_URL='https://www.linkedin.com/search/results/people/?keywords=CEO%20OR%20Head%20OR%20Director%20sustainability%20technology&origin=GLOBAL_SEARCH_HEADER&sid=80j'
USERNAME = os.environ.get('LINKEDIN_USERNAME')
PASSWORD = os.environ.get('LINKEDIN_PASSWORD')
MONGO_CONNECTION_STRING = os.environ.get('MONGO_CONNECTION_STRING')

# Configuración del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LinkedInBot:

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option('prefs', {'intl.accept_languages': 'es-ES'})

        options.add_argument('--no-sandbox')
        options.add_argument('--headless')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 15)
        self.mongo_client = MongoClient(MONGO_CONNECTION_STRING)
        self.db = self.mongo_client.linkedin_data
        self.connect_to_mongo()
    
    def random_sleep(self, min_time=3, max_time=20):
        sleep_time = random.uniform(min_time, max_time)
        time.sleep(sleep_time)

    def load_cookies(self):
        try:
            # Navigate to LinkedIn before loading cookies
            self.driver.get(LINKEDIN_URL)
            self.random_sleep()

            with open(COOKIES_PATH, "r") as file:
                cookies = json.load(file)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
            self.driver.refresh()
            logger.info("Cookies loaded successfully")
            return True
        except FileNotFoundError:
            logger.warning("No cookie file found. Will attempt to authenticate with credentials.")
            return False


    def check_valid_cookies(self):
        try:
            self.driver.get(LINKEDIN_SEARCH_URL)
            self.random_sleep()
            return 'login' not in self.driver.current_url
        except:
            return False

    def authenticate(self):
        self.driver.get(LINKEDIN_LOGIN_URL)
        self.random_sleep()
        if 'login' in self.driver.current_url:
            self.driver.find_element_by_id('username').send_keys(USERNAME)
            self.driver.find_element_by_id('password').send_keys(PASSWORD + Keys.RETURN)
            self.random_sleep()
        if 'login' in self.driver.current_url:
            self.driver.save_screenshot(SCREENSHOT_PATH)
            logger.info(f"Screenshot saved to {SCREENSHOT_PATH}")
            logger.error("Failed to authenticate. Still on LinkedIn login page. Check your credentials.")
        else:
            self.save_cookies()

    def save_cookies(self):
        with open(COOKIES_PATH, 'w') as file:
            json.dump(self.driver.get_cookies(), file)
        logger.info(f"Cookies saved to {COOKIES_PATH}")

    def extract_profile_data(self):
        data = []
        while True:
            current_page_data = self.extract_profiles_from_current_page()
            data.extend(current_page_data)
            # Guardar los datos de la página actual
            self.save_profile_data(current_page_data)
            self.save_profile_data_to_mongo(current_page_data)


            try:
                # Desplazarse hasta el final de la página
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.random_sleep()  # Agregar un pequeño retraso para dar tiempo al navegador a desplazarse
                
                wait = WebDriverWait(self.driver, 10)
                next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.artdeco-pagination__button.artdeco-pagination__button--next.artdeco-button.artdeco-button--muted.artdeco-button--icon-right.artdeco-button--1.artdeco-button--tertiary.ember-view')))
                next_button.click()
                self.random_sleep()
            except Exception as e:
                logger.warning(f"Failed to extract profile from one of the list elements. Error: {e}")
                break
        return data


    def extract_profiles_from_current_page(self):
        profiles = []
        self.random_sleep()
        try:
            li_elements = self.driver.find_elements_by_tag_name('li')
            for li in li_elements:
                try:
                    profile_link_element = li.find_element_by_xpath('.//a[contains(@class, "app-aware-link")]')

                    profile_link = profile_link_element.get_attribute('href')
                    # logger.warning(f"profile_link: {profile_link}")

                    profile_name = li.find_element_by_xpath('.//span[contains(@class, "entity-result__title-text")]/a/span[@dir="ltr"]/span[@aria-hidden="true"]').text

                    # Obtener ID
                    try:
                        id_element = li.find_element_by_xpath('.//div[@class="entity-result" and @data-chameleon-result-urn]')

                        # Extraer el valor del atributo 'data-chameleon-result-urn'
                        id_value_element = id_element.get_attribute('data-chameleon-result-urn')

                        # Obtener el número deseado dividiendo el valor del atributo por ':'
                        id_value = id_value_element.split(':')[-1]
                    except:
                        id_value = 1
                    # Obtener el cargo
                    try:
                        job_title = li.find_element_by_css_selector('.entity-result__primary-subtitle').text
                    except:
                        job_title = None

                    # Obtener la ubicación
                    try:
                        location = li.find_element_by_css_selector('.entity-result__secondary-subtitle').text
                    except:
                        location = None

                    if profile_link.startswith('https://www.linkedin.com/in/'):
                        profiles.append({
                            'id': id_value,
                            'profile_link': profile_link,
                            'name': profile_name,
                            'job_title': job_title,
                            'location': location
                        })
                except Exception as e:
                    # logger.warning(f"Failed to extract profile from one of the list elements. Error: {e}")
                    continue
        except Exception as e:
            logger.warning(f"Failed to extract profiles from the current page. Error: {e}")
        return profiles


    def save_profile_data(self, new_data):
        # Cargar datos existentes
        try:
            with open(PROFILES_JSON_PATH, 'r') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        # Añadir nuevos datos a los existentes
        data.extend(new_data)

        # Guardar de nuevo al archivo
        with open(PROFILES_JSON_PATH, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logger.info(f"Data appended to {PROFILES_JSON_PATH}")

    def connect_to_mongo(self):
        try:
            logger.info("connect_to_mongo: ")
            connection_string = MONGO_CONNECTION_STRING
            self.client = MongoClient(connection_string)
            self.db = self.client['linkedin_data']  # Aquí 'linkedin_data' es el nombre de la base de datos. Puedes cambiarlo si lo deseas.
            self.collection = self.db['profiles']   # 'profiles' es el nombre de la colección donde se guardarán los datos.
        except Exception as e:
            logger.error(f"FAILED MMONGGOCOONECT {e}")

    def save_profile_data_to_mongo(self, new_data):
        logger.info("save_profile_data_to_mongo: ")
        try:
            if not new_data:
                logger.warning("No data to save to MongoDB.")
                return

            collection = self.db.profiles
            result = collection.insert_many(new_data)
            if result.acknowledged:
                logger.info(f"Data saved to MongoDB. Inserted IDs: {result.inserted_ids}")
            else:
                logger.warning("Data was not acknowledged by MongoDB.")
        except Exception as e:
            logger.error(f"Failed to save data to MongoDB. Error: {e}", exc_info=True)

    def close(self):
        self.driver.quit()
        self.mongo_client.close()

def main():
    bot = LinkedInBot()
    cookies_loaded = bot.load_cookies()
    valid_cookies = bot.check_valid_cookies() if cookies_loaded else False

    if not valid_cookies:
        bot.authenticate()
        if 'login' in bot.driver.current_url:  # Verificar si después de la autenticación todavía estamos en la página de login
            logger.error("Authentication failed. Aborting the script.")
            bot.close()
            return

    bot.extract_profile_data()
    # bot.save_profile_data_to_mongo(data)
    # bot.save_profile_data(data)
    bot.close()
    logger.info("LinkedIn bot finished its task.")

if __name__ == "__main__":
    main()