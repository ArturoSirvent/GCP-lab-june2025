from flask import Flask, jsonify, request
from google.cloud import storage
from google.cloud import translate_v2 as translate
import vertexai
from vertexai.generative_models import GenerativeModel
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

# Inicializar Vertex AI para resúmenes
try:
    vertexai.init(project=PROJECT_ID, location="us-central1")
    generative_model = GenerativeModel("gemini-1.5-flash")
    logger.info("Cliente de Vertex AI inicializado")
except Exception as e:
    logger.error(f"Error conectando a Vertex AI: {e}")
    generative_model = None

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud para verificar que el servicio funciona"""
    status = {
        'status': 'healthy',
        'service': 'translator-storage-api',
        'bucket_configured': BUCKET_NAME is not None,
        'storage_client_ready': storage_client is not None,
        'translation_client_ready': translate_client is not None,
        'generative_model_ready': generative_model is not None
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
        'version': '2.1.0',
        'bucket': BUCKET_NAME,
        'project': PROJECT_ID,
        'features': ['storage', 'translation', 'summarization'],
        'endpoints': {
            'health': '/health',
            'list_files': '/files',
            'get_file': '/file/<filename>?lang=<target_lang>&source=<source_lang>',
            'summarize_file': '/summarize/<filename>?prompt=<custom_prompt>&max_length=<words>',
            'translate_direct': '/translate?text=<text>&target=<lang>&source=<lang>',
            'supported_languages': '/languages',
            'upload_file': '/upload (POST)',
            'info': '/info'
        },
        'examples': {
            'list_files': f'{request.url_root}files',
            'get_file': f'{request.url_root}file/info.json',
            'get_file_translated': f'{request.url_root}file/welcome.txt?lang=es',
            'summarize_file': f'{request.url_root}summarize/welcome.txt',
            'summarize_with_prompt': f'{request.url_root}summarize/info.json?prompt=Enfócate en las características técnicas&max_length=100',
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
        },
        'summarization_info': {
            'supported_params': {
                'prompt': 'Custom instructions for the summary (optional)',
                'max_length': 'Approximate number of words for the summary (optional)'
            },
            'examples': {
                'basic_summary': '?',
                'custom_prompt': '?prompt=Enfócate en los aspectos técnicos',
                'length_limit': '?max_length=50',
                'combined': '?prompt=Resume las características principales&max_length=100'
            },
            'supported_formats': ['text', 'json']
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

def summarize_content(content, custom_prompt=None, max_length=None):
    """Genera un resumen del contenido usando Vertex AI"""
    if not generative_model:
        return None, "Generative model not available"
    
    try:
        # Crear el prompt base
        base_prompt = "Por favor, proporciona un resumen claro y conciso del siguiente contenido"
        
        # Agregar parámetros opcionales al prompt
        if max_length:
            base_prompt += f" en aproximadamente {max_length} palabras"
        
        if custom_prompt:
            base_prompt += f". {custom_prompt}"
        
        # Construir el prompt completo
        full_prompt = f"{base_prompt}:\n\n{content}\n\nResumen:"
        
        # Generar el resumen
        response = generative_model.generate_content(full_prompt)
        
        if response.text:
            return {
                'summary': response.text.strip(),
                'original_length': len(content),
                'summary_length': len(response.text.strip()),
                'prompt_used': base_prompt
            }, None
        else:
            return None, "No se pudo generar el resumen"
            
    except Exception as e:
        logger.error(f"Error generando resumen: {e}")
        return None, str(e)

@app.route('/summarize/<path:filename>', methods=['GET'])
def summarize_file(filename):
    """Genera un resumen del contenido de un archivo específico"""
    if not bucket:
        return jsonify({'error': 'Storage client not configured'}), 500
    
    if not generative_model:
        return jsonify({'error': 'Generative model not configured'}), 500
    
    try:
        blob = bucket.blob(filename)
        
        if not blob.exists():
            return jsonify({'error': f'File {filename} not found'}), 404
        
        # Obtener parámetros opcionales
        custom_prompt = request.args.get('prompt')
        max_length = request.args.get('max_length')
        
        # Validar max_length si se proporciona
        if max_length:
            try:
                max_length = int(max_length)
                if max_length <= 0:
                    return jsonify({'error': 'max_length must be a positive integer'}), 400
            except ValueError:
                return jsonify({'error': 'max_length must be a valid integer'}), 400
        
        # Descargar contenido del archivo
        content = blob.download_as_text()
        
        # Preparar contenido para resumen
        content_to_summarize = content
        original_format = 'text'
        
        # Si es JSON, extraer el contenido de texto
        try:
            json_content = json.loads(content)
            original_format = 'json'
            # Convertir JSON a texto legible para el resumen
            if isinstance(json_content, dict):
                text_parts = []
                for key, value in json_content.items():
                    if isinstance(value, str):
                        text_parts.append(f"{key}: {value}")
                    elif isinstance(value, list) and all(isinstance(item, str) for item in value):
                        text_parts.append(f"{key}: {', '.join(value)}")
                    else:
                        text_parts.append(f"{key}: {json.dumps(value)}")
                content_to_summarize = "\n".join(text_parts)
            else:
                content_to_summarize = json.dumps(json_content, indent=2)
        except json.JSONDecodeError:
            # No es JSON, usar contenido como texto
            pass
        
        # Verificar que el contenido no esté vacío
        if not content_to_summarize.strip():
            return jsonify({'error': 'File content is empty'}), 400
        
        # Generar resumen
        summary_result, error = summarize_content(
            content_to_summarize, 
            custom_prompt, 
            max_length
        )
        
        if error:
            return jsonify({'error': error}), 500
        
        # Preparar respuesta
        response_data = {
            'filename': filename,
            'content_type': blob.content_type,
            'file_size': blob.size,
            'original_format': original_format,
            'summary_info': summary_result,
            'parameters': {
                'custom_prompt': custom_prompt,
                'max_length': max_length
            }
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error resumiendo archivo {filename}: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
