from flask import Flask, jsonify, request
from google.cloud import storage
from google.cloud import translate_v2 as translate
import os
import json
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuración desde variables de entorno
BUCKET_NAME = os.environ.get('BUCKET_NAME')
PROJECT_ID = os.environ.get('PROJECT_ID')

# Inicializar clientes de GCP
try:
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    logger.info(f"Conectado al bucket: {BUCKET_NAME}")
except Exception as e:
    logger.error(f"Error conectando a Storage: {e}")
    storage_client = None
    bucket = None

try:
    translate_client = translate.Client()
    logger.info("Cliente de Translation API inicializado")
except Exception as e:
    logger.error(f"Error conectando a Translation API: {e}")
    translate_client = None

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud para verificar que el servicio funciona"""
    status = {
        'status': 'healthy',
        'service': 'translator-storage-api',
        'bucket_configured': BUCKET_NAME is not None,
        'storage_client_ready': storage_client is not None,
        'translation_client_ready': translate_client is not None
    }
    return jsonify(status)

def translate_text(text, target_language, source_language='auto'):
    """Traduce texto usando Cloud Translation API"""
    if not translate_client:
        return None, "Translation client not available"
    
    try:
        # Preparar argumentos para la API
        translate_args = {
            'target_language': target_language
        }
        
        # Solo agregar source_language si no es 'auto'
        if source_language and source_language != 'auto':
            translate_args['source_language'] = source_language
        
        if isinstance(text, list):
            # Si es una lista, traducir cada elemento
            results = []
            for item in text:
                result = translate_client.translate(item, **translate_args)
                results.append({
                    'original': item,
                    'translated': result['translatedText'],
                    'detected_language': result.get('detectedSourceLanguage', source_language)
                })
            return results, None
        else:
            # Traducir texto simple
            result = translate_client.translate(text, **translate_args)
            return {
                'original': text,
                'translated': result['translatedText'],
                'detected_language': result.get('detectedSourceLanguage', source_language)
            }, None
    except Exception as e:
        logger.error(f"Error en traducción: {e}")
        return None, str(e)

@app.route('/translate', methods=['GET', 'POST'])
def translate_direct():
    """Endpoint para traducir texto directamente"""
    if not translate_client:
        return jsonify({'error': 'Translation client not configured'}), 500
    
    try:
        if request.method == 'GET':
            text = request.args.get('text')
            target_lang = request.args.get('target', 'en')
            source_lang = request.args.get('source', 'auto')
        else:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
            text = data.get('text')
            target_lang = data.get('target', 'en')
            source_lang = data.get('source', 'auto')
        
        if not text:
            return jsonify({'error': 'Text parameter is required'}), 400
        
        translation, error = translate_text(text, target_lang, source_lang)
        
        if error:
            return jsonify({'error': error}), 500
        
        return jsonify({
            'translation': translation,
            'target_language': target_lang,
            'source_language': source_lang
        })
    
    except Exception as e:
        logger.error(f"Error en traducción directa: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/languages', methods=['GET'])
def get_supported_languages():
    """Obtener idiomas soportados por Translation API"""
    if not translate_client:
        return jsonify({'error': 'Translation client not configured'}), 500
    
    try:
        languages = translate_client.get_languages()
        return jsonify({
            'supported_languages': languages,
            'count': len(languages)
        })
    except Exception as e:
        logger.error(f"Error obteniendo idiomas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/files', methods=['GET'])
def list_files():
    """Listar todos los archivos en el bucket"""
    if not bucket:
        return jsonify({'error': 'Storage client not configured'}), 500
    
    try:
        blobs = bucket.list_blobs()
        files = []
        
        for blob in blobs:
            file_info = {
                'name': blob.name,
                'size': blob.size,
                'created': blob.time_created.isoformat() if blob.time_created else None,
                'content_type': blob.content_type,
                'url': f'/file/{blob.name}'
            }
            files.append(file_info)
        
        return jsonify({
            'bucket': BUCKET_NAME,
            'files': files,
            'count': len(files)
        })
    
    except Exception as e:
        logger.error(f"Error listando archivos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/file/<path:filename>', methods=['GET'])
def get_file(filename):
    """Obtener el contenido de un archivo específico con opción de traducción"""
    if not bucket:
        return jsonify({'error': 'Storage client not configured'}), 500
    
    try:
        blob = bucket.blob(filename)
        
        if not blob.exists():
            return jsonify({'error': f'File {filename} not found'}), 404
        
        # Obtener parámetros de traducción
        target_lang = request.args.get('lang')
        source_lang = request.args.get('source', 'auto')
        
        # Descargar contenido
        content = blob.download_as_text()
        
        # Preparar respuesta base
        response_data = {
            'filename': filename,
            'content_type': blob.content_type,
            'size': blob.size,
        }
        
        # Intentar parsear como JSON si es posible
        try:
            json_content = json.loads(content)
            response_data['data'] = json_content
            response_data['format'] = 'json'
            
            # Si se solicita traducción y hay translate_client
            if target_lang and translate_client:
                # Traducir valores de texto en el JSON
                translated_data = {}
                for key, value in json_content.items():
                    if isinstance(value, str):
                        translation, error = translate_text(value, target_lang, source_lang)
                        if not error:
                            translated_data[key] = translation
                        else:
                            translated_data[key] = {'original': value, 'error': error}
                    elif isinstance(value, list) and all(isinstance(item, str) for item in value):
                        translation, error = translate_text(value, target_lang, source_lang)
                        if not error:
                            translated_data[key] = translation
                        else:
                            translated_data[key] = {'original': value, 'error': error}
                    else:
                        translated_data[key] = value
                
                response_data['translated_data'] = translated_data
                response_data['translation_info'] = {
                    'target_language': target_lang,
                    'source_language': source_lang
                }
                
        except json.JSONDecodeError:
            # Si no es JSON, tratar como texto
            response_data['data'] = content
            response_data['format'] = 'text'
            
            # Si se solicita traducción
            if target_lang and translate_client:
                translation, error = translate_text(content, target_lang, source_lang)
                if not error:
                    response_data['translated_data'] = translation
                    response_data['translation_info'] = {
                        'target_language': target_lang,
                        'source_language': source_lang
                    }
                else:
                    response_data['translation_error'] = error
        
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error obteniendo archivo {filename}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """Subir un archivo al bucket (para pruebas)"""
    if not bucket:
        return jsonify({'error': 'Storage client not configured'}), 500
    
    try:
        data = request.get_json()
        if not data or 'filename' not in data or 'content' not in data:
            return jsonify({'error': 'Missing filename or content'}), 400
        
        filename = data['filename']
        content = data['content']
        
        blob = bucket.blob(filename)
        
        # Determinar content type
        if filename.endswith('.json'):
            content_type = 'application/json'
            if isinstance(content, dict):
                content = json.dumps(content, indent=2)
        elif filename.endswith('.txt'):
            content_type = 'text/plain'
        else:
            content_type = 'application/octet-stream'
        
        blob.upload_from_string(content, content_type=content_type)
        
        return jsonify({
            'message': f'File {filename} uploaded successfully',
            'filename': filename,
            'size': len(content.encode('utf-8')),
            'url': f'/file/{filename}'
        })
    
    except Exception as e:
        logger.error(f"Error subiendo archivo: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/info', methods=['GET'])
def get_info():
    """Información sobre el servicio y configuración"""
    return jsonify({
        'service': 'Translator Storage API',
        'version': '2.0.0',
        'bucket': BUCKET_NAME,
        'project': PROJECT_ID,
        'features': ['storage', 'translation'],
        'endpoints': {
            'health': '/health',
            'list_files': '/files',
            'get_file': '/file/<filename>?lang=<target_lang>&source=<source_lang>',
            'translate_direct': '/translate?text=<text>&target=<lang>&source=<lang>',
            'supported_languages': '/languages',
            'upload_file': '/upload (POST)',
            'info': '/info'
        },
        'examples': {
            'list_files': f'{request.url_root}files',
            'get_file': f'{request.url_root}file/info.json',
            'get_file_translated': f'{request.url_root}file/welcome.txt?lang=es',
            'translate_text': f'{request.url_root}translate?text=Hello World&target=es',
            'health_check': f'{request.url_root}health',
            'supported_languages': f'{request.url_root}languages'
        },
        'translation_info': {
            'supported_params': {
                'lang or target': 'Target language code (e.g., es, fr, de)',
                'source': 'Source language code (default: auto)'
            },
            'examples': {
                'spanish': '?lang=es',
                'french': '?lang=fr',
                'german': '?lang=de',
                'detect_and_translate': '?lang=es&source=auto'
            }
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
