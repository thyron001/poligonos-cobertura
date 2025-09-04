# Aplicación Streamlit - Análisis de Cobertura de Telecomunicaciones

Esta aplicación permite analizar la cobertura de telecomunicaciones en parroquias específicas de Ecuador usando archivos shapefile de cobertura.

## Características

- **Interfaz web intuitiva** con Streamlit
- **Soporte para 6 provincias**: Azuay, Cañar, El Oro, Loja, Morona Santiago, Zamora Chinchipe
- **Carga de archivos**: ZIP o RAR con shapefiles de cobertura
- **Selectores configurables**: Provincia, Parroquia, Operadora, Año, Tecnología
- **Visualización interactiva**: Mapas de Folium con geometría unificada
- **Exportación automática**: Descarga de archivos KMZ con formato personalizado

## Formato de archivo de salida

Los archivos KMZ se generan con el siguiente formato:
```
parroquia_operadora_año_tecnologia.kmz
```

Ejemplo: `yanuncay_movistar_2024_4g.kmz`

## Configuración para Streamlit Cloud

### Archivo principal
```
streamlit_app.py
```

### Dependencias
```
requirements.txt
```

### Configuración
```
.streamlit/config.toml
```

## Uso

1. **Seleccionar provincia**: Elige una de las 6 provincias disponibles
2. **Seleccionar parroquia**: Se cargan automáticamente las parroquias de la provincia
3. **Configurar parámetros**: Operadora (Movistar, Claro, CNT), Año, Tecnología (2G, 3G, 4G)
4. **Subir archivo**: Archivo ZIP o RAR con shapefile de cobertura
5. **Convertir**: Procesar la cobertura y generar geometría unificada
6. **Descargar**: Obtener el archivo KMZ resultante

## Archivos necesarios

- `streamlit_app.py` - Aplicación principal
- `requirements.txt` - Dependencias de Python
- `.streamlit/config.toml` - Configuración de Streamlit
- `geojson_provincias/` - Archivos GeoJSON de las 6 provincias

## Tecnologías utilizadas

- **Streamlit**: Interfaz web
- **GeoPandas**: Procesamiento de datos geoespaciales
- **Folium**: Visualización de mapas interactivos
- **Shapely**: Operaciones geométricas
- **Py7zr**: Soporte para archivos RAR
