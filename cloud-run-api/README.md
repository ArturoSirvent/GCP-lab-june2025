# Translator Storage API - Cloud Run Service

Esta aplicación Flask proporciona una API para interactuar con Google Cloud Storage, traducir contenido usando Cloud Translation API, y generar resúmenes usando Vertex AI.

## Endpoints Disponibles

- `GET /health` - Health check del servicio
- `GET /files` - Listar todos los archivos en el bucket
- `GET /file/<filename>` - Obtener contenido de un archivo específico
- `GET /file/<filename>?lang=<target>&source=<source>` - Obtener archivo traducido
- `GET /summarize/<filename>` - Generar resumen del contenido de un archivo
- `GET /summarize/<filename>?prompt=<custom>&max_length=<words>` - Resumen personalizado
- `GET /translate?text=<text>&target=<lang>&source=<lang>` - Traducir texto directamente
- `POST /translate` - Traducir texto (JSON payload)
- `GET /languages` - Obtener idiomas soportados
- `POST /upload` - Subir un archivo (para pruebas)
- `GET /info` - Información del servicio

## Parámetros de Traducción

- `lang` o `target`: Idioma de destino (ej: es, fr, de, en)
- `source`: Idioma de origen (por defecto: auto-detección)

## Parámetros de Resumen

- `prompt`: Instrucciones personalizadas para el resumen (opcional)
- `max_length`: Número aproximado de palabras para el resumen (opcional)

## Ejemplos de Uso

### Leer archivo sin traducir
```
GET /file/welcome.txt
```

### Leer archivo traducido al español
```
GET /file/welcome.txt?lang=es
```

### Generar resumen básico
```
GET /summarize/welcome.txt
```

### Resumen personalizado con prompt
```
GET /summarize/info.json?prompt=Enfócate en las características técnicas
```

### Resumen corto con límite de palabras
```
GET /summarize/welcome.txt?max_length=50
```

### Resumen completo con prompt y límite
```
GET /summarize/info.json?prompt=Resume los aspectos principales&max_length=100
```

### Traducir texto directamente
```
GET /translate?text=Hello World&target=es
```

### Obtener idiomas soportados
```
GET /languages
```

## Variables de Entorno Requeridas

- `BUCKET_NAME`: Nombre del bucket de Cloud Storage
- `PROJECT_ID`: ID del proyecto de GCP (requerido para Vertex AI)
- `PORT`: Puerto donde ejecutar el servicio (por defecto 8080)

## Servicios de GCP Utilizados

- **Cloud Storage**: Para almacenar y leer archivos
- **Cloud Translation API**: Para traducir contenido de texto
- **Vertex AI**: Para generar resúmenes usando Gemini 1.5 Flash

## Construcción Local

```bash
# Construir imagen
docker build -t storage-api .

# Ejecutar localmente (con credenciales configuradas)
docker run -p 8080:8080 \
  -e BUCKET_NAME=tu-bucket \
  -e PROJECT_ID=tu-project \
  -e GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json \
  -v /path/to/credentials.json:/path/to/credentials.json \
  storage-api
```

## Despliegue en Cloud Run

```bash
# Construir y subir imagen
gcloud builds submit --tag gcr.io/PROJECT-ID/translator-api

# Desplegar en Cloud Run
gcloud run deploy translator-api \
  --image gcr.io/PROJECT-ID/translator-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars BUCKET_NAME=tu-bucket,PROJECT_ID=tu-project \
  --service-account=cloud-run-translator-api@PROJECT-ID.iam.gserviceaccount.com
```
