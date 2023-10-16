# Usa una imagen base con Python y Chrome
FROM joyzoursky/python-chromedriver:3.8-selenium

# Crea un directorio para nuestro código
WORKDIR /app

# Copia el script al contenedor
COPY linkedin_bot.py .

# Instala las dependencias
RUN pip install selenium

CMD ["python", "./linkedin_bot.py"]
