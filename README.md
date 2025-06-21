# Práctica GCP Parte 1: Despliegue desde la UI

## Objetivo
En esta práctica aprenderemos a desplegar servicios en Google Cloud Platform usando la interfaz de usuario. Crearemos:
- Un Cloud Run que funcione como API con traducción automática
- Un Cloud Storage bucket con archivos
- Una VM de Compute Engine
- Integración con Cloud Translation API
- Configuraremos permisos y accesos seguros

## Prerrequisitos
- Cuenta de Google Cloud Platform
- Proyecto creado en GCP
- Facturación habilitada en el proyecto
- Google Cloud SDK (gcloud) instalado y configurado

### Instalación y Configuración de gcloud

#### 1. Instalar Google Cloud SDK
Sigue las instrucciones de instalación para tu sistema operativo:
- **Documentación oficial**: https://cloud.google.com/sdk/docs/install

**Instalación rápida:**
```bash
# Linux/macOS
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Windows (PowerShell)
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
& $env:Temp\GoogleCloudSDKInstaller.exe
```

#### 2. Inicializar y Autenticar gcloud
```bash
# Inicializar gcloud (esto abrirá el navegador para autenticación)
gcloud init

# Verificar que está correctamente configurado
gcloud config list
gcloud auth list

# Configurar el proyecto por defecto (si no se hizo en init)
gcloud config set project [TU-PROJECT-ID]
```

#### 3. Verificar Configuración
```bash
# Verificar que todo funciona
export PROJECT_ID=$(gcloud config get-value project)
echo "Tu Project ID es: $PROJECT_ID"
gcloud projects describe $PROJECT_ID
```

## Arquitectura del Sistema
```
            VM (Compute Engine) ← SSH Connection
                ↓
Internet →  Cloud Run API ← Cloud Translation API
                ↓
            Cloud Storage Bucket              
```

## Paso 1: Configuración Inicial del Proyecto

### 1.1 Crear un Proyecto (si no tienes uno)
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Selecciona el selector de proyectos en la parte superior
3. Clic en "Nuevo Proyecto"
4. Asigna un nombre descriptivo (ej: `gcp-practica-2025`)
5. Presiona "Crear"

### 1.2 Habilitar APIs Necesarias
1. Ve a "APIs y servicios" → "Biblioteca"
2. Busca y habilita las siguientes APIs:
   - Cloud Run API
   - Cloud Storage API
   - Compute Engine API
   - Cloud Resource Manager API
   - IAM API
   - Cloud Translation API

**Comando alternativo desde Cloud Shell:**
```bash
gcloud services enable run.googleapis.com storage.googleapis.com compute.googleapis.com cloudresourcemanager.googleapis.com iam.googleapis.com translate.googleapis.com
```

## Paso 2: Crear y Configurar Cloud Storage

### 2.1 Crear el Bucket
1. Ve a "Cloud Storage" → "Buckets"
2. Clic en "Crear"
3. Configuración del bucket:
   - **Nombre**: `practica-gcp-storage-[TU-NOMBRE]` (debe ser único globalmente)
   - **Tipo de ubicación**: Región
   - **Ubicación**: `us-central1` (o la más cercana)
   - **Clase de almacenamiento predeterminada**: Standard
   - **Control de acceso**: Uniforme
4. Presiona "Crear"

### 2.2 Subir Archivos de Prueba
1. Entra al bucket creado
2. Selecciona "Cargar archivos"
3. Sube los archivos que encontrarás en la carpeta `sample-files/` de esta práctica:
   - `info.json`
   - `welcome.txt`
   - `data.csv`

**Alternativamente, puedes crear estos archivos directamente:**
- Selecciona "Crear carpeta" (opcional)
- Usa "Editar como texto" para crear archivos simples

## Paso 3: Configurar Permisos y Service Account

### 3.1 Crear Service Account
1. Ve a "IAM y administración" → "Cuentas de servicio"
2. Selecciona "Crear cuenta de servicio"   
3. Configuración:
   - **Nombre**: `cloud-run-translator-api`
   - **ID de cuenta de servicio**: `cloud-run-translator-api`
   - **Descripción**: "Service account para Cloud Run acceder a Storage y Translation"
4. Presiona "Crear y continuar"

### 3.2 Asignar Roles a la Service Account
En el paso 2 de la creación, asigna los siguientes roles para que el servicio pueda interactuar con otros productos de Google Cloud:
- **Storage Object Creator**: Permite al servicio leer y escribir archivos en el bucket de Cloud Storage (necesario para `GET /file/...` y `POST /upload`).
- **Cloud Translation API User**: Permite al servicio usar la API de traducción para traducir textos y archivos.
- **Vertex AI User**: Permite al servicio utilizar los modelos de IA de Vertex AI, como Gemini, para la funcionalidad de resumen (`GET /summarize/...`).

Presiona "Continuar" y luego "Listo".

## Paso 4: Desplegar Cloud Run

### 4.1 Preparar el Contenedor
1. Ve a "Cloud Run"
2. Haz clic en "Crear servicio"
3. Configuración del contenedor:
   - **Imagen del contenedor**: `gcr.io/[TU-PROJECT-ID]/translator-api:latest`
   - Primero necesitamos construir la imagen

### 4.2 Construir la Imagen del Contenedor

Tienes dos opciones para construir la imagen:

#### Opción A: Construcción Local
Si tienes Docker instalado en tu máquina local:

```bash
# Navegar al directorio del proyecto
cd parte1-ui-deployment/cloud-run-api

# Configurar el proyecto y verificar
export PROJECT_ID=$(gcloud config get-value project)
echo "Tu Project ID es: $PROJECT_ID"

# Construir la imagen localmente
docker build -t gcr.io/$PROJECT_ID/translator-api:latest .

# Subir la imagen al registro
docker push gcr.io/$PROJECT_ID/translator-api:latest
```

**Nota**: Asegúrate de tener Docker configurado para autenticarse con GCR:
```bash
gcloud auth configure-docker
```

O para redesplegar una vez que ya lo hemos desplegado :
**Opción A: Local**
docker build -t gcr.io/$PROJECT_ID/translator-api:latest .
docker push gcr.io/$PROJECT_ID/translator-api:latest

**Opción B: Cloud Build**
gcloud builds submit --tag gcr.io/$PROJECT_ID/translator-api:latest .


#### Opción B: Cloud Build (Recomendado desde Cloud Shell)
Este método utiliza Cloud Build para compilar tu imagen de contenedor directamente en GCP, lo cual es más rápido y no requiere Docker en tu máquina local.

1. Abre **Cloud Shell** desde la parte superior de la Google Cloud Console.
2. Dentro de Cloud Shell, clona el repositorio si es necesario y navega al directorio del código:
```bash
# Clonar el código de esta práctica
git clone [URL-DEL-REPOSITORIO] || echo "Usando archivos locales"

# Navegar al directorio
cd parte1-ui-deployment/cloud-run-api
```
3. Ejecuta el siguiente comando para compilar la imagen usando Cloud Build:
```bash
# Configurar el proyecto y verificar
export PROJECT_ID=$(gcloud config get-value project)
echo "Tu Project ID es: $PROJECT_ID"

# Construir la imagen con Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/translator-api:latest .
```
4. Puedes monitorear el progreso de la compilación en la sección **Cloud Build** → **Historial** de la consola.

### 4.3 Configurar el Servicio Cloud Run
Vuelve a Cloud Run y continúa:
1. **Imagen del contenedor**: `gcr.io/[TU-PROJECT-ID]/translator-api:latest`
2. **Configuración del servicio**:
   - **Nombre del servicio**: `translator-api`
   - **Región**: `us-central1`
   - **Asignar CPU solo durante las solicitudes**: ✓
3. **Configuración avanzada**:
   - **Variables de entorno**:
     - `BUCKET_NAME`: `practica-gcp-storage-[TU-NOMBRE]`
     - `PROJECT_ID`: `[TU-PROJECT-ID]`
   - **Service Account**: `cloud-run-translator-api@[TU-PROJECT-ID].iam.gserviceaccount.com`

### 4.4 Configurar Autenticación
1. En "Seguridad":
   - **Autenticación**: "Permitir invocaciones no autenticadas" ✓
2. Haz clic en "Crear"

### 4.5 Verificar el Despliegue
1. Una vez desplegado, copia la URL del servicio
2. Prueba los endpoints:
   - `GET https://[TU-URL]/health` - Verificar que funciona
   - `GET https://[TU-URL]/info` - Información del servicio
   - `GET https://[TU-URL]/files` - Listar archivos del bucket
   - `GET https://[TU-URL]/languages` - Ver idiomas soportados
   - `GET https://[TU-URL]/file/info.json` - Leer archivo específico
   - `GET https://[TU-URL]/file/welcome.txt` - Leer archivo de texto
   - `GET https://[TU-URL]/file/welcome.txt?lang=es` - Leer y traducir archivo a español
   - `GET https://[TU-URL]/file/info.json?lang=fr` - Traducir archivo JSON al francés
   - `GET https://[TU-URL]/translate?text=Hello&target=es` - Traducir texto directamente
   - `GET https://[TU-URL]/translate?text=Good%20morning&target=de` - Traducir al alemán

## Paso 4.1 (Opcional): Desplegar Cloud Function para Leer Archivos
Como alternativa a usar el endpoint de Cloud Run para leer archivos, podemos crear una Cloud Function más ligera y específica para esta tarea.

### 4.1.1 Crear la Cloud Function
1. Ve a **Cloud Functions** en la consola de GCP.
2. Haz clic en **Crear función**.
3. **Configuración básica**:
   - **Entorno**: 1ª gen
   - **Nombre de la función**: `read-file-function`
   - **Región**: `us-central1`
   - **Activador HTTP**:
     - **Tipo de activador**: HTTP
     - **URL**: Anota la URL que se genera.
     - **Autenticación**: Permitir invocaciones no autenticadas.
4. Haz clic en **Guardar** y luego en **Siguiente**.

### 4.1.2 Configurar el Código
1. **Editor insertado**:
   - **Entorno de ejecución**: Python 3.9 (o superior)
   - **Punto de entrada**: `read_file`
2. **`main.py`**:
   - Copia y pega el contenido del archivo `cloud-function-read-file/main.py`.
3. **`requirements.txt`**:
   - Copia y pega el contenido de `cloud-function-read-file/requirements.txt`.
4. **Variables de entorno**:
   - En la sección de "Variables de entorno de ejecución", añade:
     - `BUCKET_NAME`: `practica-gcp-storage-[TU-NOMBRE]`
     - `PROJECT_ID`: `[TU-PROJECT-ID]`
5. **Cuenta de servicio**:
   - Asegúrate de que la función utiliza una cuenta de servicio con el rol **Visualizador de objetos de Storage** (`Storage Object Viewer`) para poder leer del bucket. Puedes usar la misma que creaste para Cloud Run o crear una nueva con permisos más restrictivos.
6. Haz clic en **Desplegar**.

### 4.1.3 Probar la Cloud Function
Una vez desplegada, puedes probarla usando `curl` o tu navegador:
```bash
# Reemplaza [URL-DE-TU-FUNCTION] con la URL del activador
curl "[URL-DE-TU-FUNCTION]/info.json"
```

## Paso 4.2 (Opcional): Configurar API Gateway
Para tener una URL de API más limpia y centralizada, podemos poner un API Gateway delante de nuestra Cloud Function.

### 4.2.1 Crear una Especificación de API
Crea un archivo local llamado `api-spec.yaml` con el siguiente contenido. Esta especificación define cómo las peticiones a la API se redirigen a la Cloud Function.

```yaml
swagger: '2.0'
info:
  title: File Reader API
  description: API para leer archivos desde Cloud Storage a través de una Cloud Function
  version: 1.0.0
schemes:
  - https
produces:
  - application/json
paths:
  /files/{filename}:
    get:
      summary: Obtiene el contenido de un archivo
      operationId: getFile
      parameters:
        - name: filename
          in: path
          required: true
          type: string
      x-google-backend:
        address: "[URL-DE-TU-FUNCTION-SIN-PATH]" # Pega aquí la URL base de tu función
        path_translation: APPEND_PATH_TO_ADDRESS
      responses:
        '200':
          description: Contenido del archivo
        '404':
          description: Archivo no encontrado
```
**Importante**: Reemplaza `[URL-DE-TU-FUNCTION-SIN-PATH]` con la URL de tu Cloud Function, pero sin ninguna ruta final (ej: `https://us-central1-tu-proyecto.cloudfunctions.net/read-file-function`).

### 4.2.2 Crear la API
1. Ve a **API Gateway** en la consola de GCP.
2. Haz clic en **Crear puerta de enlace**.
3. **Configuración de la API**:
   - **Nombre visible**: `file-reader-api`
   - **ID de la API**: `file-reader-api`
4. **Configuración de la API**:
   - Haz clic en **Subir una especificación de API**.
   - Sube el archivo `api-spec.yaml` que creaste.
   - **Nombre de la configuración**: `v1`
5. **Cuenta de servicio**: Selecciona una cuenta de servicio que tenga permisos para invocar Cloud Functions (el rol `Invocador de Cloud Functions` es suficiente).
6. Haz clic en **Crear**.

### 4.2.3 Probar el API Gateway
1. Una vez que la puerta de enlace esté creada y la configuración desplegada, anota la URL de la puerta de enlace.
2. Prueba el nuevo endpoint:
```bash
# Reemplaza [URL-DEL-GATEWAY] con la URL de tu API Gateway
curl "https://[URL-DEL-GATEWAY]/files/info.json"
```
Ahora tienes un endpoint de API profesional (`/files/{filename}`) que internamente llama a tu Cloud Function.

## Paso 5: Crear y Configurar VM

### 5.1 Crear la VM
1. Ve a "Compute Engine" → "Instancias de VM"
2. Haz clic en "Crear instancia"
3. Configuración:
   - **Nombre**: `practica-vm`
   - **Región**: `us-central1`
   - **Zona**: `us-central1-a`
   - **Tipo de máquina**: `e2-micro` (nivel gratuito)
   - **Imagen de arranque**: 
     - SO: Ubuntu
     - Versión: Ubuntu 20.04 LTS

### 5.2 Acceso a la VM
Durante la creación de la VM, en la sección **Seguridad y acceso**, puedes configurar cómo te conectarás.

**Opción 1: Acceso gestionado por Google (Recomendado)**
Si planeas conectarte a través de la consola de Google Cloud o con el comando `gcloud compute ssh`, no necesitas hacer nada. Google gestionará las claves SSH de forma segura por ti.

**Opción 2: Añadir tu propia clave SSH manualmente**
Si prefieres usar tu propio cliente SSH (como `ssh` en Linux/macOS o PuTTY en Windows) y conectarte directamente, puedes añadir tu clave pública.

1.  **Genera un par de claves SSH** si no tienes uno:
    ```bash
    # Este comando crea una clave privada (practica-gcp-vm) y una pública (practica-gcp-vm.pub)
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/practica-gcp-vm -C "tu_usuario"
    ```

2.  **Copia tu clave pública**:
    ```bash
    cat ~/.ssh/practica-gcp-vm.pub
    ```

3.  **Pega la clave en la consola de GCP**:
    - En la página de creación de la VM, ve a la sección `Seguridad y acceso`.
    - Despliega la opción `Claves SSH`.
    - Haz clic en `Añadir elemento` y pega el contenido completo de tu clave pública (`practica-gcp-vm.pub`). Google asociará automáticamente el nombre de usuario del comentario de la clave (`tu_usuario` en el ejemplo).

Esto te permitirá conectarte más tarde usando `ssh -i ~/.ssh/practica-gcp-vm tu_usuario@IP_EXTERNA_DE_LA_VM`.

### 5.3 Finalizar Creación de VM
1. Haz clic en "Crear"
2. Espera a que la VM inicie (estado "Running")

## Paso 6: Conectarse a la VM y Probar

### 6.1 Conectar a la VM
Tienes varias opciones para conectarte a tu VM:

**Opción A: Google Cloud Console (Recomendado)**
1. Ve a la lista de Instancias de VM en la consola.
2. Busca tu `practica-vm`.
3. Haz clic en el botón "SSH" que aparece a la derecha. Se abrirá una terminal segura en tu navegador.

**Opción B: gcloud CLI (desde tu terminal local)**
Asegúrate de tener `gcloud` instalado y configurado.
```bash
# Conéctate a la VM usando su nombre y zona
gcloud compute ssh practica-vm --zone=us-central1-a
```
`gcloud` se encargará de gestionar las claves SSH por ti.

**Opción C: Cliente SSH estándar (si añadiste tu clave manualmente)**
```bash
# Obtén la IP externa de tu VM desde la consola de GCP
export VM_EXTERNAL_IP=[IP-EXTERNA-VM]

# Conéctate usando tu clave privada
ssh -i ~/.ssh/practica-gcp-vm tu_usuario@$VM_EXTERNAL_IP
```

### 6.2 Instalar Herramientas en la VM
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar curl y jq para APIs
sudo apt install curl jq -y

# Verificar conectividad
curl -I https://www.google.com
```

### 6.3 Probar la API desde la VM
```bash
# Definir la URL de tu Cloud Run
export API_URL="https://[TU-CLOUD-RUN-URL]"

# ========================================
# 1. ENDPOINTS BÁSICOS DE VERIFICACIÓN
# ========================================

# Probar health check
curl "$API_URL/health" | jq .

# Información completa del servicio
curl "$API_URL/info" | jq .

# ========================================
# 2. GESTIÓN DE ARCHIVOS EN STORAGE
# ========================================

# Listar todos los archivos en el bucket
curl "$API_URL/files" | jq .

# Leer archivo JSON específico
curl "$API_URL/file/info.json" | jq .

# Leer archivo de texto plano
curl "$API_URL/file/welcome.txt"

# Leer archivo CSV (si existe)
curl "$API_URL/file/data.csv"

# Nota sobre archivos en carpetas:
# Si un archivo está en una carpeta (ej: 'documentos/reporte.txt'),
# accede a él incluyendo la ruta completa en la URL.
# curl "$API_URL/file/documentos/reporte.txt"

# ========================================
# 3. FUNCIONES DE TRADUCCIÓN BÁSICA
# ========================================

# Ver idiomas soportados por Translation API
curl "$API_URL/languages" | jq .

# Traducir texto directamente (GET)
curl "$API_URL/translate?text=Hello%20World&target=es" | jq .

# Traducir con detección automática de idioma
curl "$API_URL/translate?text=Bonjour%20le%20monde&target=en" | jq .

# Traducir especificando idioma fuente
curl "$API_URL/translate?text=Hola%20mundo&source=es&target=fr" | jq .

# Traducir frases más largas (usar codificación URL)
curl "$API_URL/translate?text=This%20is%20a%20beautiful%20day&target=es" | jq .

# ========================================
# 4. TRADUCCIÓN DE ARCHIVOS
# ========================================

# Leer archivo de texto traducido al español
curl "$API_URL/file/welcome.txt?lang=es" | jq .

# Leer archivo JSON traducido al francés
curl "$API_URL/file/info.json?lang=fr" | jq .

# Leer archivo traducido al alemán
curl "$API_URL/file/welcome.txt?lang=de" | jq .

# Leer archivo traducido al italiano
curl "$API_URL/file/info.json?lang=it" | jq .

# Leer archivo traducido al portugués
curl "$API_URL/file/welcome.txt?lang=pt" | jq .

# Leer archivo con idioma fuente específico
curl "$API_URL/file/info.json?source=en&lang=ja" | jq .

# ========================================
# 5. TRADUCCIÓN USANDO POST (JSON)
# ========================================

# Traducir usando POST con JSON
curl -X POST "$API_URL/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you today?",
    "target": "es",
    "source": "en"
  }' | jq .

# Traducir texto más complejo con POST
curl -X POST "$API_URL/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Machine learning is revolutionizing technology",
    "target": "fr"
  }' | jq .

# ========================================
# 6. SUBIR ARCHIVOS (PARA PRUEBAS)
# ========================================

# Subir un archivo de texto
curl -X POST "$API_URL/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test.txt",
    "content": "This is a test file created via API"
  }' | jq .

# Subir un archivo JSON
curl -X POST "$API_URL/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test.json",
    "content": {
      "message": "Hello from API",
      "timestamp": "'$(date -Iseconds)'",
      "test": true
    }
  }' | jq .

# ========================================
# 7. PRUEBAS DE MÚLTIPLES IDIOMAS
# ========================================

# Probar múltiples traducciones del mismo texto
echo "Probando traducciones a múltiples idiomas:"
for lang in es fr de it pt ja zh ko; do
  echo "=== Traduciendo a $lang ==="
  curl -s "$API_URL/translate?text=Good%20morning%20everyone&target=$lang" | jq -r '.translation.translated'
done

# ========================================
# 8. VERIFICACIÓN DE ERRORES
# ========================================

# Probar archivo que no existe
curl "$API_URL/file/noexiste.txt" | jq .

# Probar traducción sin texto
curl "$API_URL/translate?target=es" | jq .

# Probar endpoint que no existe
curl "$API_URL/noexiste" | jq .

# ========================================
# 9. PRUEBAS DE RENDIMIENTO SIMPLE
# ========================================

# Hacer múltiples peticiones para probar rendimiento
echo "Probando múltiples peticiones..."
for i in {1..5}; do
  echo "Petición $i:"
  time curl -s "$API_URL/health" | jq -r '.status'
done

# ========================================
# 10. COMBINACIONES AVANZADAS
# ========================================

# Leer archivo, luego subirlo traducido
original_content=$(curl -s "$API_URL/file/welcome.txt")
echo "Contenido original: $original_content"

translated_content=$(curl -s "$API_URL/file/welcome.txt?lang=es" | jq -r '.translated_data.translated')
echo "Contenido traducido: $translated_content"

# Subir la versión traducida
curl -X POST "$API_URL/upload" \
  -H "Content-Type: application/json" \
  -d "{
    \"filename\": \"welcome_es.txt\",
    \"content\": \"$translated_content\"
  }" | jq .

# Verificar que se subió correctamente
curl "$API_URL/file/welcome_es.txt" | jq .

echo "Todas las pruebas completadas. Revisa los resultados arriba."
```


## Troubleshooting

### Problemas Comunes

#### Cloud Run no puede acceder al bucket o traducción
- Verificar que la Service Account tiene los roles correctos (Storage + Translation)
- Verificar que las APIs están habilitadas (Storage + Translation)
- Verificar que las variables de entorno están configuradas
- Revisar logs en Cloud Run

#### Traducción no funciona
- Verificar que Cloud Translation API está habilitada
- Verificar que la Service Account tiene el rol "Cloud Translate User"
- Probar con códigos de idioma válidos (es, fr, de, etc.)
- Revisar logs para errores específicos de traducción

#### No puedo conectarme a la VM por SSH
- Verificar que la clave SSH está correctamente configurada
- Verificar que el firewall permite conexiones SSH (puerto 22)
- Verificar la IP externa de la VM

#### API devuelve errores 500
- Revisar logs de Cloud Run en "Registros"
- Verificar que el bucket existe y es accesible
- Verificar la configuración de variables de entorno

### Comandos Útiles

```bash
# Ver logs de Cloud Run
gcloud run services logs read translator-api --region=us-central1

# Verificar permisos de Service Account
gcloud projects get-iam-policy [PROJECT-ID]

# Probar conectividad a bucket desde Cloud Shell
gsutil ls gs://[BUCKET-NAME]

# Probar Translation API desde Cloud Shell
gcloud ml translate detect-language --content="Hello World"

# Probar traducción específica
gcloud ml translate translate-text --content="Hello World" --target-language=es
```

## Limpieza de Recursos

**IMPORTANTE**: Para evitar cargos, elimina los recursos cuando termines:

1. **Eliminar Cloud Run**: Ve a Cloud Run → Selecciona el servicio → Eliminar
2. **Eliminar VM**: Ve a Compute Engine → Selecciona la VM → Eliminar
3. **Eliminar Bucket**: Ve a Cloud Storage → Selecciona el bucket → Eliminar
4. **Eliminar Service Account**: Ve a IAM → Cuentas de servicio → Eliminar

## Siguiente Paso
Una vez completada esta práctica, estarás listo para la **Parte 2: Despliegue usando gcloud CLI y automatización**.
