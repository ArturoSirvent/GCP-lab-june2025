#!/bin/bash

# Script para generar claves SSH para la práctica
# Uso: ./generate-ssh-keys.sh

echo "🔑 Generando claves SSH para la práctica de GCP..."

# Crear directorio .ssh si no existe
mkdir -p ~/.ssh

# Generar par de claves
ssh-keygen -t rsa -b 4096 -C "practica-gcp-vm-$(date +%Y%m%d)" -f ~/.ssh/practica-gcp-vm -N ""

echo ""
echo "✅ Claves generadas exitosamente:"
echo "   - Clave privada: ~/.ssh/practica-gcp-vm"
echo "   - Clave pública: ~/.ssh/practica-gcp-vm.pub"
echo ""
echo "📋 COPIA LA SIGUIENTE CLAVE PÚBLICA para agregarla en GCP:"
echo "=================================================="
cat ~/.ssh/practica-gcp-vm.pub
echo "=================================================="
echo ""
echo "📝 Instrucciones:"
echo "1. Copia la clave pública mostrada arriba"
echo "2. Ve a Compute Engine > Metadatos > Claves SSH"
echo "3. Haz clic en 'Editar' y luego 'Agregar elemento'"
echo "4. Pega la clave pública"
echo "5. Asegúrate de que el usuario sea 'practica-user'"
echo ""
echo "🔌 Para conectarte a la VM usa:"
echo "ssh -i ~/.ssh/practica-gcp-vm practica-user@[IP-EXTERNA-VM]"
