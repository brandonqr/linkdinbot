# LinkedIn Automation Bot
Un bot automatizado para interactuar con LinkedIn utilizando Python y Selenium en un contenedor Docker.

## Pre-requisitos
Docker
Docker Compose

## Configuración
#### 1. Variables de entorno:

Configura tus credenciales de LinkedIn en el archivo `.env`:

```
LINKEDIN_USERNAME=tu_correo@ejemplo.com
LINKEDIN_PASSWORD=tu_contraseña`
````

⚠️ Advertencia: Nunca subas tu archivo `.env` a repositorios públicos o compartas tus credenciales.

#### 2. Volumen para cookies:

Crea un directorio llamado data en el mismo lugar que tu docker-compose.yml. Este directorio se utilizará para almacenar las cookies y mantener la sesión entre ejecuciones.

## Uso
Construir la imagen:

```
docker-compose build
```
Ejecutar el bot:

```
docker-compose up
````
## Advertencia
Este bot interactúa con LinkedIn de una manera automatizada, lo que puede violar los términos de servicio de LinkedIn. Úsalo bajo tu propio riesgo y asegúrate de revisar y adherirte a las políticas y términos de servicio de LinkedIn.

Puedes adaptar y expandir este *README.md* según las características adicionales de tu proyecto o cualquier otra información que consideres relevante.