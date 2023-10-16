import os
import logging
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import json



# Configuración del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configura tus credenciales
# Obtén tus credenciales de las variables de entorno
USERNAME = os.environ.get('LINKEDIN_USERNAME')
PASSWORD = os.environ.get('LINKEDIN_PASSWORD')
MESSAGE = 'Hola [nombre], me gustaría conectarme contigo por...'

logger.info("Starting LinkedIn bot")

# Opciones para el driver
options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--headless')
options.add_argument('--disable-dev-shm-usage')

# Configura el WebDriver (Chrome con opciones)
driver = webdriver.Chrome(options=options)

def extract_profiles_data(driver):
    """Extrae los datos de los perfiles de la página actual y devuelve una lista de diccionarios."""
    profiles = []

    # Localizar todos los elementos que representan a los perfiles
    profile_elements = driver.find_elements_by_css_selector('.search-result__info')

    for profile in profile_elements:
        # Extracción de la URL, nombre, puesto y lugar de trabajo
        try:
            link = profile.find_element_by_tag_name('a').get_attribute('href')
            name = profile.find_element_by_css_selector('.name.actor-name').text
            position = profile.find_element_by_css_selector('.subline-level-1').text
            location = profile.find_element_by_css_selector('.subline-level-2').text
            profiles.append({
                'url': link,
                'name': name,
                'position': position,
                'location': location
            })
        except Exception as e:
            logger.warning(f"Failed to extract profile data. Error: {e}")

    return profiles





# Visita LinkedIn
driver.get('https://www.linkedin.com')

# Carga las cookies previamente guardadas
cookies_loaded = False
valid_cookies = False  # <-- Añade esta línea para inicializar 'valid_cookies' antes de cualquier lógica

try:
    with open("/data/linkedin_cookies.txt", "r") as file:
        cookies = json.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)
    driver.refresh()
    cookies_loaded = True
    logger.info("Cookies loaded successfully")
except FileNotFoundError:
    logger.warning("No cookie file found. Will attempt to authenticate with credentials.")

# Comprueba si las cookies son válidas.
if cookies_loaded:
    try:
        # Intenta acceder a una página que solo es accesible cuando estás conectado
        driver.get('https://www.linkedin.com/search/results/people/?keywords=CEO%20OR%20Head%20OR%20Director%20sustainability%20technology&origin=GLOBAL_SEARCH_HEADER&sid=80j')
        time.sleep(5)  # Espera un poco para asegurarte de que la página esté completamente cargada.
       
        # Si no estás en la página de inicio de sesión, suponemos que la cookie es válida.
        if 'login' not in driver.current_url:
            valid_cookies = True
            logger.info("Valid cookies detected. Proceeding with the next steps.")
            
            # Tomar una captura de pantalla
            screenshot_path = "/data/mynetwork_screenshot.png"
            driver.save_screenshot(screenshot_path)
            logger.info(f"Screenshot saved to {screenshot_path}")
        else:
            valid_cookies = False
    except:
        valid_cookies = False

if not valid_cookies or not cookies_loaded:
    logger.info("Attempting to authenticate with provided credentials.")
    driver.get('https://www.linkedin.com/login')
    time.sleep(3) # Dale unos segundos para cargar la página de inicio de sesión
    
    # Verifica si estás en la página de inicio de sesión antes de intentar enviar las credenciales
    if 'login' in driver.current_url:
        logger.info("On LinkedIn login page. Sending credentials.")
        driver.find_element_by_id('username').send_keys(USERNAME)
        driver.find_element_by_id('password').send_keys(PASSWORD + Keys.RETURN)
        time.sleep(5)  # Espera para que la página cargue y la sesión se establezca
        
        # Verifica si todavía estás en la página de inicio de sesión
        if 'login' in driver.current_url:
            # Tomar una captura de pantalla
            screenshot_path = "/data/mynetwork_screenshot.png"
            driver.save_screenshot(screenshot_path)
            logger.info(f"Screenshot saved to {screenshot_path}")
            logger.error("Failed to authenticate. Still on LinkedIn login page. Check your credentials.")
        else:
            # Guarda las cookies después de iniciar sesión para usos futuros
            with open("/data/linkedin_cookies.txt", "w") as file:
                json.dump(driver.get_cookies(), file)
            logger.info("Authentication successful. Cookies saved for future sessions.")
    else:
        logger.error("Failed to navigate to LinkedIn login page.")
        # Aquí deberías agregar el código para iniciar sesión de nuevo.

# ... (resto de tu código)
if valid_cookies:
    data = []  # Para almacenar todos los datos de los perfiles

    # Mientras haya un botón de "Siguiente" activo, sigue extrayendo datos y avanzando páginas
    while True:
        data.extend(extract_profiles_data(driver))

        # Intentar hacer clic en el botón "Siguiente"
        try:
            next_button = driver.find_element_by_xpath('//button[@aria-label="Siguiente"]')
            next_button.click()
            time.sleep(5)  # Espera un poco para que la nueva página cargue
        except Exception as e:
            logger.info("No more pages to navigate or an error occurred.")
            break



    # Guarda los datos en un archivo JSON
    with open('/data/linkedin_profiles.json', 'w') as file:
        json.dump(data, file)
    logger.info(f"Data saved to /data/linkedin_profiles.json")
# Cierra el navegador al finalizar
driver.quit()
logger.info("LinkedIn bot finished its task.")
