# Translator Storage API - Cloud Run Service

Esta aplicación Flask proporciona una API completa para:
- 📁 **Almacenamiento**: Leer y gestionar archivos en Google Cloud Storage
- 🌍 **Traducción**: Traducir contenido usando Cloud Translation API
- 📝 **Resúmenes**: Generar resúmenes inteligentes usando Vertex AI (Gemini 1.5 Flash)

## 🚀 Funcionalidades Principales

### 📁 Gestión de Archivos
- Listar archivos del bucket
- Leer contenido de archivos (texto, JSON)
- Subir archivos para pruebas

### 🌍 Traducción Automática
- Traducir archivos completos a diferentes idiomas
- Traducir texto directamente
- Auto-detección de idioma origen
- Soporte para múltiples formatos (texto plano, JSON)

### 📝 Resúmenes Inteligentes
- Generar resúmenes automáticos de archivos
- Instrucciones personalizadas con prompts
- Control de longitud del resumen
- Funciona con archivos de texto y JSON

## Endpoints Disponibles

### 🔍 Estado y Información
- `GET /health` - Health check del servicio
- `GET /info` - Información completa del servicio y ejemplos

### 📁 Archivos
- `GET /files` - Listar todos los archivos en el bucket
- `GET /file/<filename>` - Obtener contenido de un archivo específico
- `POST /upload` - Subir un archivo (para pruebas)

### 🌍 Traducción
- `GET /file/<filename>?lang=<target>&source=<source>` - Obtener archivo traducido
- `GET /translate?text=<text>&target=<lang>&source=<lang>` - Traducir texto directamente
- `POST /translate` - Traducir texto (JSON payload)
- `GET /languages` - Obtener idiomas soportados

### 📝 Resúmenes
- `GET /summarize/<filename>` - Generar resumen básico del archivo
- `GET /summarize/<filename>?prompt=<custom>` - Resumen con instrucciones personalizadas
- `GET /summarize/<filename>?max_length=<words>` - Resumen con límite de palabras
- `GET /summarize/<filename>?prompt=<custom>&max_length=<words>` - Resumen completo

## 📋 Parámetros

### Traducción
- `lang` o `target`: Idioma de destino (ej: es, fr, de, en)
- `source`: Idioma de origen (por defecto: auto-detección)

### Resúmenes
- `prompt`: Instrucciones personalizadas para el resumen *(opcional)*
- `max_length`: Número aproximado de palabras para el resumen *(opcional)*

## 💡 Ejemplos de Uso

### 📁 Gestión de Archivos
```bash
# Listar archivos disponibles
GET /files

# Leer contenido original
GET /file/welcome.txt
```

### 🌍 Traducción
```bash
# Archivo traducido al español
GET /file/welcome.txt?lang=es

# Traducir JSON al francés
GET /file/info.json?lang=fr&source=en

# Traducción directa
GET /translate?text=Hello World&target=es
```

### 📝 Resúmenes
```bash
# Resumen básico
GET /summarize/welcome.txt

# Resumen con instrucciones personalizadas
GET /summarize/info.json?prompt=Enfócate en las características técnicas del proyecto

# Resumen corto (50 palabras aprox.)
GET /summarize/welcome.txt?max_length=50

# Resumen completo con ambos parámetros
GET /summarize/info.json?prompt=Describe las funcionalidades principales&max_length=100
```

### 🔍 Información del Sistema
```bash
# Estado del servicio
GET /health

# Información completa y ejemplos
GET /info

# Idiomas soportados para traducción
GET /languages
```

## ⚙️ Configuración

### Variables de Entorno Requeridas
- `BUCKET_NAME`: Nombre del bucket de Cloud Storage
- `PROJECT_ID`: ID del proyecto de GCP (requerido para Vertex AI)
- `PORT`: Puerto donde ejecutar el servicio (por defecto 8080)

### Servicios de GCP Utilizados
- **Cloud Storage**: Para almacenar y leer archivos
- **Cloud Translation API**: Para traducir contenido de texto
- **Vertex AI**: Para generar resúmenes usando Gemini 1.5 Flash

### Permisos Necesarios
La service account debe tener acceso a:
- Cloud Storage (roles/storage.objectViewer)
- Cloud Translation API (roles/cloudtranslate.user)
- Vertex AI (roles/aiplatform.user)

## 📦 Respuesta de Resumen

Ejemplo de respuesta del endpoint `/summarize/`:

```json
{
  "filename": "welcome.txt",
  "content_type": "text/plain",
  "file_size": 1024,
  "original_format": "text",
  "summary_info": {
    "summary": "Este archivo contiene un mensaje de bienvenida que explica las funcionalidades principales de la API...",
    "original_length": 1024,
    "summary_length": 156,
    "prompt_used": "Por favor, proporciona un resumen claro y conciso"
  },
  "parameters": {
    "custom_prompt": "Enfócate en las características técnicas",
    "max_length": 100
  }
}
```

## 🛠️ Desarrollo Local

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

## 🚀 Despliegue en Cloud Run

```bash
# Construir y subir imagen
gcloud builds submit --tag gcr.io/PROJECT-ID/translator-api

# Desplegar en Cloud Run con todas las funcionalidades
gcloud run deploy translator-api \
  --image gcr.io/PROJECT-ID/translator-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars BUCKET_NAME=tu-bucket,PROJECT_ID=tu-project \
  --service-account=cloud-run-translator-api@PROJECT-ID.iam.gserviceaccount.com
```

## 🧪 Pruebas

Usa el script de pruebas incluido:

```bash
# Ejecutar todas las pruebas (traducción + resumen)
./scripts/test-api.sh
```

El script probará automáticamente:
- ✅ Health check
- ✅ Listado de archivos
- ✅ Lectura de archivos
- ✅ Traducción a diferentes idiomas
- ✅ Resúmenes básicos y personalizados
- ✅ Información del servicio

---

## 🔄 Funcionalidades v2.1.0

### 📝 Resúmenes Inteligentes
- Resúmenes automáticos usando Vertex AI (Gemini 1.5 Flash)
- Prompts personalizados para dirigir el tipo de resumen
- Control de longitud del resumen generado
- Soporte múltiple para archivos de texto y JSON
- Parámetros opcionales - usa solo lo que necesites
