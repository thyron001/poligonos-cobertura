# Visualizador de Mapas - Parroquias con Cobertura UMTS

Este proyecto contiene un script de Python para visualizar los límites de una parroquia específica junto con la cobertura UMTS de Azuay usando archivos shapefile del Consejo Nacional Electoral (CNE) de Ecuador y datos de cobertura móvil.

## Archivos del Proyecto

- `ejemplo_rapido_folium.py` - Script principal para crear mapas combinados
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

### 1. Configurar la Parroquia

Abre el archivo `ejemplo_rapido_folium.py` y cambia la variable `NOMBRE_PARROQUIA`:

```python
NOMBRE_PARROQUIA = "BATAN"  # Cambiar por el nombre de la parroquia deseada
```

### 2. Ejecutar el Script

En tu terminal, navega al directorio del proyecto y ejecuta:

```bash
py ejemplo_rapido_folium.py
```

### 3. Resultado

El script:
- Cargará los datos del shapefile de límites parroquiales
- Buscará la parroquia especificada
- Cargará los datos de cobertura UMTS de Azuay
- Generará un mapa combinado con ambas capas
- Guardará el archivo HTML automáticamente
- Mostrará información detallada en la consola

## Características del Script

- **Búsqueda específica**: Busca y grafica solo la parroquia especificada
- **Mapa combinado**: Siempre incluye la parroquia + cobertura UMTS
- **Mapa interactivo**: Genera archivos HTML que puedes abrir en tu navegador web
- **Zoom automático**: Se centra automáticamente en la parroquia seleccionada
- **Popups informativos**: Muestra información detallada al hacer clic
- **Controles de capas**: Puedes activar/desactivar la parroquia y la cobertura UMTS
- **Estilos diferenciados**: La parroquia se muestra en rojo, la cobertura UMTS en azul
- **Manejo de errores**: Proporciona mensajes claros si algo falla
- **Exportación web**: Guarda automáticamente el mapa como archivo HTML

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

### Cambiar Parroquia:
```python
NOMBRE_PARROQUIA = "TU_PARROQUIA_AQUI"
```

### Cambiar Rutas de Shapefiles:
```python
# Para límites parroquiales
RUTA_PARROQUIAS = "ruta/a/tu/archivo_parroquias.shp"

# Para cobertura UMTS
RUTA_UMTS = "ruta/a/tu/archivo_cobertura.shp"
```

### Cambiar Estilos de Visualización:
```python
# Estilo de la parroquia
style_function=lambda feature: {
    'fillColor': '#FF6B6B',  # Color de relleno (rojo)
    'color': '#000000',      # Color del borde (negro)
    'weight': 2,             # Grosor del borde
    'fillOpacity': 0.7       # Transparencia
}

# Estilo de la cobertura UMTS
style_function=lambda feature: {
    'fillColor': '#4ECDC4',  # Color de relleno (azul)
    'color': '#000000',      # Color del borde (negro)
    'weight': 1,             # Grosor del borde
    'fillOpacity': 0.3       # Transparencia
}
```

## Solución de Problemas

### Error: "No se encontró la parroquia especificada"

1. Verifica que el nombre de la parroquia esté escrito correctamente
2. El script mostrará los campos disponibles para ayudarte
3. Puedes usar coincidencias parciales (el script las detectará automáticamente)

### Error: "No se pudo cargar el shapefile"

1. Verifica que las rutas a los archivos .shp sean correctas
2. Asegúrate de que todos los archivos del shapefile estén presentes (.shp, .shx, .dbf, .prj)
3. Verifica que tengas permisos de lectura en las carpetas

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
- Visualizar límites administrativos de parroquias específicas
- Analizar cobertura de servicios en áreas específicas
- Planificar infraestructura y servicios por parroquia

### Para Analistas de Telecomunicaciones:
- Estudiar cobertura de red en parroquias específicas
- Comparar cobertura con límites administrativos
- Identificar áreas con necesidades de infraestructura

### Para Investigadores:
- Análisis geográfico de parroquias específicas
- Estudios de cobertura de servicios por área
- Investigación en geografía y telecomunicaciones

## Ejemplos de Uso

### Parroquia BATAN:
```python
NOMBRE_PARROQUIA = "BATAN"
```
Resultado: `mapa_parroquia_batan_con_cobertura.html`

### Parroquia BAÑOS:
```python
NOMBRE_PARROQUIA = "BAÑOS"
```
Resultado: `mapa_parroquia_baños_con_cobertura.html`

### Parroquia YANUNCAY:
```python
NOMBRE_PARROQUIA = "YANUNCAY"
```
Resultado: `mapa_parroquia_yanuncay_con_cobertura.html`

## Estructura del Mapa Generado

El mapa HTML incluye:
1. **Capa de Parroquia**: Muestra solo la parroquia seleccionada en rojo
2. **Capa de Cobertura UMTS**: Muestra toda la cobertura de Azuay en azul transparente
3. **Controles de Capas**: Permite activar/desactivar cada capa
4. **Popups Informativos**: Muestra datos al hacer clic en cada elemento
5. **Zoom Automático**: Se centra automáticamente en la parroquia

## Licencia

Este proyecto está disponible para uso educativo y de investigación.

---

**Nota**: Este script está diseñado específicamente para trabajar con los archivos de límites parroquiales del CNE de Ecuador y datos de cobertura UMTS de Azuay. Para otros datasets, pueden ser necesarias modificaciones.
