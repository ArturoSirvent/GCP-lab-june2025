#!/bin/bash

# Script para probar la API desde la VM
# Este script debe ejecutarse DENTRO de la VM

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Script de pruebas para la API de Translator Storage${NC}"
echo "============================================"

# Solicitar URL de la API
if [ -z "$API_URL" ]; then
    echo -e "${YELLOW}📝 Ingresa la URL de tu Cloud Run API:${NC}"
    read -p "URL: " API_URL
fi

# Validar que la URL no esté vacía
if [ -z "$API_URL" ]; then
    echo -e "${RED}❌ Error: URL no puede estar vacía${NC}"
    exit 1
fi

# Función para hacer peticiones con formato bonito
make_request() {
    local endpoint=$1
    local description=$2
    
    echo ""
    echo -e "${BLUE}🔍 Probando: $description${NC}"
    echo -e "${YELLOW}Endpoint: $API_URL$endpoint${NC}"
    echo "----------------------------------------"
    
    response=$(curl -s -w "\n%{http_code}" "$API_URL$endpoint")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✅ Status: $http_code OK${NC}"
        echo "$body" | jq . 2>/dev/null || echo "$body"
    else
        echo -e "${RED}❌ Status: $http_code Error${NC}"
        echo "$body"
    fi
}

# Verificar que jq esté instalado
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️  jq no está instalado. Instalando...${NC}"
    sudo apt update && sudo apt install -y jq
fi

# Verificar que curl esté instalado
if ! command -v curl &> /dev/null; then
    echo -e "${YELLOW}⚠️  curl no está instalado. Instalando...${NC}"
    sudo apt update && sudo apt install -y curl
fi

# Realizar pruebas
echo -e "${GREEN}🚀 Iniciando pruebas...${NC}"

# 1. Health check
make_request "/health" "Health Check"

# 2. Info del servicio
make_request "/info" "Información del Servicio"

# 3. Listar archivos
make_request "/files" "Listar Archivos del Bucket"

# 4. Leer archivo JSON
make_request "/file/info.json" "Leer Archivo JSON"

# 5. Leer archivo de texto
make_request "/file/welcome.txt" "Leer Archivo de Texto"

# 6. Leer archivo CSV
make_request "/file/data.csv" "Leer Archivo CSV"

# 7. Pruebas de traducción
make_request "/languages" "Idiomas Soportados"

# 8. Traducir texto directamente
make_request "/translate?text=Hello%20World&target=es" "Traducir Texto Directamente"

# 9. Leer archivo traducido al español
make_request "/file/welcome.txt?lang=es" "Leer Archivo Traducido al Español"

# 10. Leer archivo traducido al francés
make_request "/file/welcome.txt?lang=fr" "Leer Archivo Traducido al Francés"

# 11. Traducir JSON al alemán
make_request "/file/info.json?lang=de" "Traducir Archivo JSON al Alemán"

# Resumen final
# Probar endpoint de resumen
echo ""
echo -e "${BLUE}📝 Probando endpoint de resumen${NC}"
echo "------------------------------------"

# Resumen básico
make_request "/summarize/welcome.txt" "Resumen Básico de Archivo de Texto"

# Resumen con prompt personalizado
make_request "/summarize/info.json?prompt=Enfócate en las características técnicas del proyecto" "Resumen con Prompt Personalizado"

# Resumen con límite de palabras
make_request "/summarize/multilingual.json?max_length=50" "Resumen Corto (50 palabras)"

# Resumen con prompt y límite combinados
make_request "/summarize/welcome.txt?prompt=Resume los aspectos más importantes&max_length=100" "Resumen Completo con Parámetros"

echo ""
echo "============================================"
echo -e "${GREEN}🎉 Pruebas completadas!${NC}"
echo ""
echo -e "${YELLOW}💡 Consejos adicionales:${NC}"
echo "- Revisa los logs en Cloud Run si algo falla"
echo "- Verifica permisos de la service account"
echo "- Asegúrate de que los archivos estén en el bucket"
echo "- Prueba diferentes idiomas de traducción"
echo "- Los resúmenes usan Vertex AI (Gemini 1.5 Flash)"
echo ""
echo -e "${BLUE}🌍 Códigos de idioma populares:${NC}"
echo "- es: Español"
echo "- fr: Francés" 
echo "- de: Alemán"
echo "- it: Italiano"
echo "- pt: Portugués"
echo "- ja: Japonés"
echo "- ko: Coreano"
echo "- zh: Chino"
echo ""
echo -e "${BLUE}📝 Parámetros de resumen:${NC}"
echo "- prompt: Instrucciones personalizadas para el resumen"
echo "- max_length: Número aproximado de palabras (ej: 50, 100, 200)"
echo ""
echo -e "${BLUE}🔗 URLs útiles:${NC}"
echo "- Cloud Run: https://console.cloud.google.com/run"
echo "- Cloud Storage: https://console.cloud.google.com/storage" 
echo "- Vertex AI: https://console.cloud.google.com/vertex-ai"
echo "- Logs: https://console.cloud.google.com/logs"
