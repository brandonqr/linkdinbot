# Usa una imagen base con Python y Chrome
FROM joyzoursky/python-chromedriver:3.8-selenium

# Crea un directorio para nuestro código
WORKDIR /app

# Copia el script y el archivo requirements.txt al contenedor
COPY linkedin_bot.py .
COPY requirements.txt .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./linkedin_bot.py"]
