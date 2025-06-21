# Scripts de Ayuda para la Práctica

Esta carpeta contiene scripts útiles para facilitar la práctica de GCP.

## Scripts Disponibles

### 1. `generate-ssh-keys.sh`
Genera un par de claves SSH para conectarse a la VM de forma segura.

**Uso:**
```bash
cd scripts/
./generate-ssh-keys.sh
```

**Qué hace:**
- Genera claves RSA de 4096 bits
- Las guarda en `~/.ssh/practica-gcp-vm` y `~/.ssh/practica-gcp-vm.pub`
- Muestra la clave pública para copiar en GCP

### 2. `upload-sample-files.sh`
Sube los archivos de muestra al bucket de Cloud Storage.

**Uso:**
```bash
cd scripts/
export BUCKET_NAME="tu-bucket-name"
./upload-sample-files.sh
```

**Prereq:**
- Tener gcloud configurado
- Permisos de escritura en el bucket

### 3. `test-api.sh`
Script completo para probar todos los endpoints de la API desde la VM.

**Uso:**
```bash
# Desde la VM (después de conectarse por SSH)
curl -O https://raw.githubusercontent.com/[tu-repo]/scripts/test-api.sh
chmod +x test-api.sh
export API_URL="https://tu-cloud-run-url"
./test-api.sh
```

**Qué prueba:**
- Health check (`/health`)
- Información del servicio (`/info`)
- Listado de archivos (`/files`)
- Lectura de archivos específicos (`/file/*`)

## Orden de Uso Recomendado

1. **Antes de crear la VM**: Ejecuta `generate-ssh-keys.sh`
2. **Después de crear el bucket**: Ejecuta `upload-sample-files.sh`
3. **Desde la VM**: Ejecuta `test-api.sh`

## Notas Importantes

- Todos los scripts incluyen validaciones y mensajes de error útiles
- Los scripts usan colores para facilitar la lectura
- Incluyen instalación automática de dependencias cuando es necesario

## Troubleshooting

### Script no ejecutable
```bash
chmod +x nombre-del-script.sh
```

### gcloud no configurado
```bash
gcloud auth login
gcloud config set project [PROJECT-ID]
```

### Permisos insuficientes
Verifica que tu usuario/service account tenga los roles necesarios en IAM.
