# Visualizador de Mapas - Parroquias y Cobertura UMTS

Este proyecto contiene un script de Python para visualizar los límites de parroquias específicas y la cobertura UMTS de Azuay usando archivos shapefile del Consejo Nacional Electoral (CNE) de Ecuador y datos de cobertura móvil.

## Archivos del Proyecto

- `ejemplo_rapido_folium.py` - Script principal para crear mapas interactivos
- `requirements.txt` - Dependencias de Python necesarias
- `LIMITE_PARROQUIAL_CONALI_CNE_2022/` - Carpeta con archivos shapefile de límites parroquiales
- `AZUAY SHAPE/` - Carpeta con archivos shapefile de cobertura UMTS de Azuay

## Instalación

1. **Instalar Python**: Asegúrate de tener Python 3.7 o superior instalado.

2. **Instalar dependencias**: Ejecuta el siguiente comando en tu terminal:
   ```bash
   pip install -r requirements.txt
   ```

## Uso del Script

### Ejecutar el Script

En tu terminal, navega al directorio del proyecto y ejecuta:

```bash
py ejemplo_rapido_folium.py
```

### Opciones Disponibles

El script te mostrará un menú con las siguientes opciones:

#### 1. **Crear mapa de parroquia específica**
- Busca y grafica una parroquia específica
- Muestra límites administrativos
- Incluye información de parroquia, cantón, provincia y estado

#### 2. **Crear mapa de cobertura UMTS de Azuay**
- Visualiza la cobertura de red móvil UMTS en la provincia de Azuay
- Muestra regiones de cobertura con información técnica
- Útil para análisis de infraestructura de telecomunicaciones

#### 3. **Crear mapa combinado (parroquias + cobertura)**
- Combina ambos datasets en un solo mapa
- Muestra parroquias del cantón Cuenca junto con la cobertura UMTS
- Permite comparar límites administrativos con cobertura de red
- Incluye controles de capas para alternar entre vistas

#### 4. **Salir**
- Cierra el programa

## Características del Script

- **Búsqueda inteligente**: Busca la parroquia en diferentes campos del shapefile
- **Mapa interactivo**: Genera archivos HTML que puedes abrir en tu navegador web
- **Zoom y navegación**: Puedes hacer zoom, pan y explorar los datos
- **Popups informativos**: Muestra información detallada al hacer clic
- **Controles de capas**: En mapas combinados, puedes activar/desactivar capas
- **Manejo de errores**: Proporciona mensajes claros si algo falla
- **Exportación web**: Guarda automáticamente los mapas como archivos HTML

## Campos de Búsqueda Soportados

### Límites Parroquiales:
- `CODPRO`, `PROVINCIA`, `CANTON`, `CODPAR`, `PARROQUIA`, `ESTADO`

### Cobertura UMTS:
- Todos los campos disponibles en el shapefile de cobertura

## Datos Disponibles

### Límites Parroquiales (CNE 2022):
- **Total de registros**: 1,236
- **Parroquias únicas**: 1,081
- **Cantones únicos**: 221
- **Provincias únicas**: 25

### Cobertura UMTS Azuay (Junio 2023):
- Datos de cobertura de red móvil en la provincia de Azuay
- Información técnica de regiones UMTS
- Útil para análisis de infraestructura de telecomunicaciones

## Parroquias Disponibles

### Cantón Cuenca (Provincia Azuay):
- BAÑOS, CUMBE, CHAUCHA/ANGAS, CHECA JIDCAY, CHIQUINTAD
- LLACAO, MOLLETURO, MULTI/NULTI, OCTAVIO CORDERO PALACIOS
- PACCHA, QUINGEO, RICAURTE, SAN JOAQUIN, SANTA ANA
- SAYAUSI, SIDCAY, SININCAY, TARQUI, TURI, VALLE
- VICTORIA DEL PORTETE, YANUNCAY, EL BATAN, SUCRE
- HUAYNACAPAC, SAN SEBASTIAN, RAMIREZ DAVALOS, SAGRARIO
- SAN BLAS, CAÑARIBAMBA, MONAY, TOTORACOCHA, EL VECINO
- BELLAVISTA, HERMANO MIGUEL, MACHANGARA

## Personalización

### Cambiar Parroquia (Opción 1):
```python
NOMBRE_PARROQUIA = "TU_PARROQUIA_AQUI"
```

### Cambiar Rutas de Shapefiles:
```python
# Para límites parroquiales
RUTA_SHAPEFILE = "ruta/a/tu/archivo_parroquias.shp"

# Para cobertura UMTS
RUTA_SHAPEFILE = "ruta/a/tu/archivo_cobertura.shp"
```

## Solución de Problemas

### Error: "No se encontró la parroquia especificada"

1. Verifica que el nombre de la parroquia esté escrito correctamente
2. El script mostrará los campos disponibles para ayudarte
3. Puedes usar coincidencias parciales (el script las detectará automáticamente)

### Error: "No se pudo cargar el shapefile"

1. Verifica que la ruta al archivo .shp sea correcta
2. Asegúrate de que todos los archivos del shapefile estén presentes (.shp, .shx, .dbf, .prj)
3. Verifica que tengas permisos de lectura en la carpeta

### Error de Dependencias

Si tienes problemas con las bibliotecas:

```bash
# Actualizar pip
python -m pip install --upgrade pip

# Instalar dependencias una por una
pip install geopandas
pip install folium
pip install shapely
pip install fiona
pip install pyproj
```

## Formato de los Datos

Los archivos shapefile contienen:
- **Geometría**: Polígonos que definen los límites o regiones
- **Atributos**: Información descriptiva de cada elemento
- **Sistema de coordenadas**: Definido en el archivo .prj

## Casos de Uso

### Para Administradores Públicos:
- Visualizar límites administrativos de parroquias
- Analizar cobertura de servicios en diferentes áreas
- Planificar infraestructura y servicios

### Para Analistas de Telecomunicaciones:
- Estudiar cobertura de red en la provincia de Azuay
- Comparar cobertura con límites administrativos
- Identificar áreas con necesidades de infraestructura

### Para Investigadores:
- Análisis geográfico de límites administrativos
- Estudios de cobertura de servicios
- Investigación en geografía y telecomunicaciones

## Ejemplos de Uso

### Mapa de Parroquia:
```python
NOMBRE_PARROQUIA = "BAÑOS"
```
Resultado: `mapa_parroquia_baños.html`

### Mapa de Cobertura UMTS:
Opción 2 del menú
Resultado: `mapa_cobertura_umts_azuay.html`

### Mapa Combinado:
Opción 3 del menú
Resultado: `mapa_combinado_cuenca_umts.html`

## Licencia

Este proyecto está disponible para uso educativo y de investigación.

---

**Nota**: Este script está diseñado específicamente para trabajar con los archivos de límites parroquiales del CNE de Ecuador y datos de cobertura UMTS de Azuay. Para otros datasets, pueden ser necesarias modificaciones.
