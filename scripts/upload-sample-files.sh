#!/bin/bash

# Script para subir archivos de muestra al bucket
# Ejecutar desde Cloud Shell o máquina con gcloud configurado

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}📁 Script para subir archivos de muestra al bucket${NC}"
echo "================================================"

# Solicitar nombre del bucket
if [ -z "$BUCKET_NAME" ]; then
    echo -e "${YELLOW}📝 Ingresa el nombre de tu bucket:${NC}"
    read -p "Bucket name: " BUCKET_NAME
fi

# Validar que el bucket existe
if ! gsutil ls "gs://$BUCKET_NAME" > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: El bucket gs://$BUCKET_NAME no existe o no tienes acceso${NC}"
    echo "Verifica el nombre del bucket y tus permisos"
    exit 1
fi

echo -e "${GREEN}✅ Bucket encontrado: gs://$BUCKET_NAME${NC}"

# Directorio con archivos de muestra
SAMPLE_DIR="../sample-files"

if [ ! -d "$SAMPLE_DIR" ]; then
    echo -e "${RED}❌ Error: Directorio $SAMPLE_DIR no encontrado${NC}"
    echo "Asegúrate de ejecutar este script desde el directorio scripts/"
    exit 1
fi

echo -e "${YELLOW}📤 Subiendo archivos de muestra...${NC}"

# Subir cada archivo
for file in "$SAMPLE_DIR"/*; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo -e "${BLUE}  Subiendo: $filename${NC}"
        
        if gsutil cp "$file" "gs://$BUCKET_NAME/$filename"; then
            echo -e "${GREEN}  ✅ $filename subido correctamente${NC}"
        else
            echo -e "${RED}  ❌ Error subiendo $filename${NC}"
        fi
    fi
done

echo ""
echo -e "${GREEN}🎉 Proceso completado!${NC}"
echo ""
echo -e "${YELLOW}📋 Archivos en el bucket:${NC}"
gsutil ls -l "gs://$BUCKET_NAME/"

echo ""
echo -e "${BLUE}🔗 Puedes ver los archivos en:${NC}"
echo "https://console.cloud.google.com/storage/browser/$BUCKET_NAME"
