
import os
import json
from google.cloud import storage

# Configuración desde variables de entorno
BUCKET_NAME = os.environ.get('BUCKET_NAME')
PROJECT_ID = os.environ.get('PROJECT_ID')

# Inicializar clientes de GCP
try:
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    print(f"Conectado al bucket: {BUCKET_NAME}")
except Exception as e:
    print(f"Error conectando a Storage: {e}")
    storage_client = None
    bucket = None

def read_file(request):
    """
    Cloud Function para leer un archivo de Cloud Storage.
    """
    if not bucket:
        return (json.dumps({'error': 'Storage client not configured'}), 500, {'Content-Type': 'application/json'})

    # Obtener el nombre del archivo de la URL
    filename = request.path.strip("/")
    if not filename:
        return (json.dumps({'error': 'Filename not provided in the URL path.'}), 400, {'Content-Type': 'application/json'})

    try:
        blob = bucket.blob(filename)

        if not blob.exists():
            return (json.dumps({'error': f'File {filename} not found'}), 404, {'Content-Type': 'application/json'})

        # Descargar contenido
        content = blob.download_as_text()

        # Preparar respuesta base
        response_data = {
            'filename': filename,
            'content_type': blob.content_type,
            'size': blob.size,
            'data': content
        }

        return (json.dumps(response_data), 200, {'Content-Type': 'application/json'})

    except Exception as e:
        print(f"Error obteniendo archivo {filename}: {e}")
        return (json.dumps({'error': str(e)}), 500, {'Content-Type': 'application/json'})
