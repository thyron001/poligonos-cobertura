#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicación Streamlit para análisis de cobertura de telecomunicaciones
"""

import streamlit as st
import geopandas as gpd
import folium
from shapely.geometry import Polygon, MultiPolygon, LineString
from shapely.ops import unary_union
import numpy as np
import os
import zipfile
import tempfile
import io
from pathlib import Path
import streamlit.components.v1 as components

# Configuración de la página
st.set_page_config(
    page_title="Análisis de Cobertura",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración de provincias disponibles (solo 6)
PROVINCIAS_DISPONIBLES = {
    "AZUAY": "azuay.geojson",
    "CAÑAR": "cañar.geojson", 
    "EL ORO": "el_oro.geojson",
    "LOJA": "loja.geojson",
    "MORONA SANTIAGO": "morona_santiago.geojson",
    "ZAMORA CHINCHIPE": "zamora_chinchipe.geojson"
}

OPERADORAS = ["MOVISTAR", "CLARO", "CNT"]
TECNOLOGIAS = ["2G", "3G", "4G"]
AÑOS = ["2020", "2021", "2022", "2023", "2024", "2025"]

def obtener_ruta_geojson_provincia(nombre_provincia):
    """Obtener la ruta del archivo GeoJSON de la provincia especificada"""
    if nombre_provincia in PROVINCIAS_DISPONIBLES:
        return f"geojson_provincias/{PROVINCIAS_DISPONIBLES[nombre_provincia]}"
    return None

def exportar_a_kmz(geodataframe, nombre_archivo):
    """Exportar GeoDataFrame a archivo KMZ"""
    try:
        # Crear archivo temporal KML
        with tempfile.NamedTemporaryFile(suffix='.kml', delete=False) as tmp_kml:
            geodataframe.to_file(tmp_kml.name, driver='KML')
            
            # Crear archivo KMZ en memoria
            kmz_buffer = io.BytesIO()
            with zipfile.ZipFile(kmz_buffer, 'w', zipfile.ZIP_DEFLATED) as kmz_file:
                kmz_file.write(tmp_kml.name, os.path.basename(tmp_kml.name))
            
            # Limpiar archivo temporal
            os.unlink(tmp_kml.name)
            
            kmz_buffer.seek(0)
            return kmz_buffer.getvalue()
    except Exception as e:
        return None

def crear_geometria_unificada(intersecciones, parroquia_geom):
    """Crear una geometría unificada conectando las intersecciones con líneas delgadas - EXACTO del ejemplo_rapido_folium.py"""
    if len(intersecciones) <= 1:
        return intersecciones[0] if intersecciones else None, []
    
    try:
        # Obtener los centroides de cada intersección
        centroides = []
        for interseccion in intersecciones:
            if not interseccion.is_empty:
                centroide = interseccion.centroid
                centroides.append((centroide.x, centroide.y))
        
        # Crear líneas de conexión entre centroides
        lineas_conexion = []
        for i in range(len(centroides)):
            for j in range(i + 1, len(centroides)):
                linea = LineString([centroides[i], centroides[j]])
                # Verificar que la línea esté dentro de la parroquia
                if linea.within(parroquia_geom) or linea.intersects(parroquia_geom):
                    lineas_conexion.append(linea)
        
        # Crear buffer SÚPER ancho alrededor de las líneas de conexión para formar "puentes" sólidos
        buffer_width = 1  # Buffer EXTREMADAMENTE ancho para crear corredores muy visibles
        puentes = []
        for linea in lineas_conexion:
            puente = linea.buffer(buffer_width)
            puentes.append(puente)
        
        # Combinar todas las intersecciones y puentes
        geometrias_combinadas = intersecciones + puentes
        
        # Unir todo en una sola geometría
        geometria_unificada = unary_union(geometrias_combinadas)
        
        # Verificar que la unión fue exitosa
        if geometria_unificada.is_empty:
            geometria_unificada = unary_union(intersecciones)
        
        return geometria_unificada, lineas_conexion
        
    except Exception as e:
        # Si falla, intentar unir solo las intersecciones
        try:
            geometria_simple = unary_union(intersecciones)
            return geometria_simple, []
        except Exception as e2:
            return None, []

def procesar_cobertura(archivo_shp, archivo_shx, archivo_dbf, archivo_prj, provincia, parroquia, operadora, año, tecnologia):
    """Procesar la cobertura y crear geometría unificada - EXACTO del ejemplo_rapido_folium.py"""
    try:
        # Cargar datos de parroquias desde el GeoJSON de la provincia
        ruta_geojson_provincia = obtener_ruta_geojson_provincia(provincia)
        if not ruta_geojson_provincia:
            return None, None, None, None
        
        gdf_parroquias = gpd.read_file(ruta_geojson_provincia)
        
        # Buscar la parroquia específica
        parroquia_encontrada = None
        for campo in gdf_parroquias.columns:
            if gdf_parroquias[campo].dtype == 'object':
                coincidencias = gdf_parroquias[gdf_parroquias[campo].str.upper().str.contains(parroquia.upper(), na=False)]
                if len(coincidencias) > 0:
                    parroquia_encontrada = coincidencias
                    break
        
        if parroquia_encontrada is None:
            return None, None, None, None
        
        # Crear directorio temporal para los archivos shapefile
        with tempfile.TemporaryDirectory() as temp_dir:
            # Guardar archivos en el directorio temporal
            shp_path = os.path.join(temp_dir, archivo_shp.name)
            shx_path = os.path.join(temp_dir, archivo_shx.name)
            dbf_path = os.path.join(temp_dir, archivo_dbf.name)
            prj_path = os.path.join(temp_dir, archivo_prj.name)
            
            with open(shp_path, 'wb') as f:
                f.write(archivo_shp.getbuffer())
            with open(shx_path, 'wb') as f:
                f.write(archivo_shx.getbuffer())
            with open(dbf_path, 'wb') as f:
                f.write(archivo_dbf.getbuffer())
            with open(prj_path, 'wb') as f:
                f.write(archivo_prj.getbuffer())
            
            # Cargar datos de cobertura
            gdf_cobertura = gpd.read_file(shp_path)
        
        # Lista para almacenar las intersecciones
        intersecciones = []
        
        # Detectar automáticamente la columna de cobertura
        columna_cobertura = None
        for col in ['THRESHOLD', 'Float', 'LEVEL', 'COVERAGE']:
            if col in gdf_cobertura.columns:
                columna_cobertura = col
                break
        
        if columna_cobertura is None:
            st.error("❌ No se encontró columna de cobertura en el archivo SHP")
            return None, None, None, None
        
        st.write(f"✅ Usando columna de cobertura: {columna_cobertura}")
        st.write(f"📊 Columnas disponibles en el SHP: {list(gdf_cobertura.columns)}")
        st.write(f"📊 Niveles de cobertura encontrados: {sorted(gdf_cobertura[columna_cobertura].unique())}")
        
        # Procesar cada nivel de cobertura
        for idx, row in gdf_cobertura.iterrows():
            coverage_level = row[columna_cobertura]
            
            # Si es cobertura alta, calcular intersección con la parroquia
            if coverage_level == -85 or coverage_level == -85.0:
                # Obtener la geometría de la parroquia y la zona de cobertura alta
                parroquia_geom = parroquia_encontrada.geometry.iloc[0]
                cobertura_geom = row.geometry
                
                # Calcular la intersección
                try:
                    interseccion = parroquia_geom.intersection(cobertura_geom)
                    
                    if not interseccion.is_empty:
                        intersecciones.append(interseccion)
                        
                except Exception as e:
                    continue
        
        # Si hay intersecciones, procesarlas
        geometria_unificada = None
        if intersecciones:
            try:
                # Obtener la geometría de la parroquia
                parroquia_geom = parroquia_encontrada.geometry.iloc[0]
                
                # Crear geometría unificada
                geometria_unificada, caminos_conexion = crear_geometria_unificada(intersecciones, parroquia_geom)
                
                # Si no se crearon caminos automáticamente, crear líneas de conexión manuales
                if not caminos_conexion:
                    # Obtener todas las áreas sueltas de todas las intersecciones
                    todas_las_areas = []
                    for interseccion in intersecciones:
                        if hasattr(interseccion, 'geoms'):
                            # Si es MultiPolygon, agregar cada polígono individual
                            for geom in interseccion.geoms:
                                todas_las_areas.append(geom)
                        else:
                            # Si es Polygon simple, agregarlo directamente
                            todas_las_areas.append(interseccion)
                    
                    # Crear líneas de conexión secuenciales (una con la siguiente)
                    lineas_conexion = []
                    
                    # Ordenar las áreas por su posición (de izquierda a derecha usando el centroide X)
                    areas_ordenadas = sorted(enumerate(todas_las_areas), key=lambda x: x[1].centroid.x)
                    indices_ordenados = [idx for idx, _ in areas_ordenadas]
                    
                    # Conectar cada área con la siguiente (cadena secuencial)
                    for i in range(len(indices_ordenados) - 1):
                        idx_actual = indices_ordenados[i]
                        idx_siguiente = indices_ordenados[i + 1]
                        
                        # Obtener centroides de las dos áreas consecutivas
                        centroide_actual = todas_las_areas[idx_actual].centroid
                        centroide_siguiente = todas_las_areas[idx_siguiente].centroid
                        
                        # Crear línea entre centroides consecutivos
                        linea = LineString([(centroide_actual.x, centroide_actual.y), (centroide_siguiente.x, centroide_siguiente.y)])
                        
                        # Verificar que la línea esté dentro de la parroquia
                        if linea.within(parroquia_geom) or linea.intersects(parroquia_geom):
                            lineas_conexion.append(linea)
                    
                    # Crear caminos anchos (corredores) en lugar de líneas delgadas
                    caminos_conexion = []
                    for linea in lineas_conexion:
                        # Crear un camino EXTREMADAMENTE ancho usando buffer súper grande
                        camino_ancho = linea.buffer(1)  # Buffer SÚPER ancho para crear corredor muy visible
                        caminos_conexion.append(camino_ancho)
                    
                    # Combinar todas las áreas sueltas con los caminos para formar un solo polígono
                    elementos_para_unificar = todas_las_areas + caminos_conexion
                    
                    try:
                        geometria_unificada = unary_union(elementos_para_unificar)
                    except Exception as e:
                        geometria_unificada = None
                
            except Exception as e:
                geometria_unificada = None
        
        return geometria_unificada, parroquia_encontrada, intersecciones, gdf_cobertura
        
    except Exception as e:
        return None, None, None, None

def crear_mapa_folium(geometria_unificada, parroquia_encontrada, provincia, parroquia, intersecciones, gdf_cobertura):
    """Crear mapa de Folium - EXACTO del ejemplo_rapido_folium.py"""
    try:
        # Convertir a WGS84 si es necesario para el centrado del mapa
        if parroquia_encontrada.crs != 'EPSG:4326':
            parroquia_wgs84 = parroquia_encontrada.to_crs('EPSG:4326')
            if geometria_unificada:
                geometria_wgs84 = gpd.GeoDataFrame(geometry=[geometria_unificada], crs=parroquia_encontrada.crs).to_crs('EPSG:4326')
            else:
                geometria_wgs84 = None
        else:
            parroquia_wgs84 = parroquia_encontrada
            geometria_wgs84 = gpd.GeoDataFrame(geometry=[geometria_unificada], crs=parroquia_encontrada.crs) if geometria_unificada else None
        
        # Calcular el centro de la geometría unificada para centrar el mapa
        if geometria_wgs84 and not geometria_wgs84.geometry.iloc[0].is_empty:
            bounds = geometria_wgs84.geometry.iloc[0].bounds
            center_lat = (bounds[1] + bounds[3]) / 2
            center_lon = (bounds[0] + bounds[2]) / 2
        else:
            # Si no hay geometría unificada, usar el centro de la parroquia
            bounds = parroquia_wgs84.geometry.iloc[0].bounds
            center_lat = (bounds[1] + bounds[3]) / 2
            center_lon = (bounds[0] + bounds[2]) / 2
        
        # Debug temporal para ver las coordenadas
        st.write(f"Debug - Centro del mapa: lat={center_lat}, lon={center_lon}")
        st.write(f"Debug - Bounds: {bounds}")
        st.write(f"Debug - CRS original: {parroquia_encontrada.crs}")
        
        # Verificar que las coordenadas sean válidas (Ecuador está en lat -2 a 1, lon -92 a -75)
        if not (-5 < center_lat < 5) or not (-95 < center_lon < -70):
            st.write("⚠️ Coordenadas fuera de Ecuador, usando coordenadas por defecto")
            center_lat, center_lon = -2.0, -78.0  # Centro de Ecuador
        
        # Crear mapa centrado en la geometría unificada
        mapa = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles='OpenStreetMap'
        )
        
        # Convertir datos de cobertura a WGS84 si es necesario
        if gdf_cobertura.crs != 'EPSG:4326':
            gdf_cobertura_wgs84 = gdf_cobertura.to_crs('EPSG:4326')
        else:
            gdf_cobertura_wgs84 = gdf_cobertura
        
        # Agregar la parroquia específica
        st.write(f"Debug - Agregando parroquia: {len(parroquia_wgs84)} registros")
        folium.GeoJson(
            parroquia_wgs84,
            name=f'Parroquia {parroquia}',
            style_function=lambda feature: {
                'fillColor': 'blue',  # Azul para la parroquia
                'color': '#000000',      # Borde negro
                'weight': 0.5,           # Grosor del borde muy delgado
                'fillOpacity': 0.7       # Transparencia
            }
        ).add_to(mapa)
        
        # Detectar automáticamente la columna de cobertura para el mapa
        columna_cobertura_mapa = None
        for col in ['THRESHOLD', 'Float', 'LEVEL', 'COVERAGE']:
            if col in gdf_cobertura_wgs84.columns:
                columna_cobertura_mapa = col
                break
        
        # Función para determinar el color según el nivel de cobertura
        def get_color_by_coverage(feature):
            coverage_level = feature['properties'][columna_cobertura_mapa]
            if coverage_level == -85 or coverage_level == -85.0:  # Nivel alto
                return '#00FF00'  # Verde intenso
            elif coverage_level == -95 or coverage_level == -95.0:  # Nivel medio
                return '#FFFF99'  # Amarillo pastel
            elif coverage_level == -105 or coverage_level == -105.0:  # Nivel bajo
                return '#FFB3B3'  # Rojo pastel
            else:
                return '#808080'  # Gris por defecto
        
        # Función para obtener el nombre del nivel de cobertura
        def get_coverage_name(feature):
            coverage_level = feature['properties'][columna_cobertura_mapa]
            if coverage_level == -85 or coverage_level == -85.0:
                return 'Cobertura Alta (-85 dBm)'
            elif coverage_level == -95 or coverage_level == -95.0:
                return 'Cobertura Media (-95 dBm)'
            elif coverage_level == -105 or coverage_level == -105.0:
                return 'Cobertura Baja (-105 dBm)'
            else:
                return f'Cobertura ({coverage_level} dBm)'
        
        # Agregar cada nivel de cobertura UMTS con su color correspondiente
        st.write(f"Debug - Agregando {len(gdf_cobertura_wgs84)} regiones de cobertura")
        for idx, row in gdf_cobertura_wgs84.iterrows():
            coverage_level = row[columna_cobertura_mapa]
            coverage_name = get_coverage_name({'properties': {columna_cobertura_mapa: coverage_level}})
            
            # Crear un GeoDataFrame con solo esta fila
            single_region = gdf_cobertura_wgs84.iloc[[idx]]
            
            # Agregar la capa de cobertura
            folium.GeoJson(
                single_region,
                name=coverage_name,
                style_function=lambda feature, level=coverage_level: {
                    'fillColor': get_color_by_coverage({'properties': {columna_cobertura_mapa: level}}),
                    'color': '#000000',      # Borde negro
                    'weight': 0.3,           # Grosor del borde muy delgado
                    'fillOpacity': 0.6       # Transparencia
                },
                tooltip=coverage_name
            ).add_to(mapa)
        
        # Mostrar cada intersección por separado (para visualización)
        for i, interseccion in enumerate(intersecciones):
            interseccion_gdf = gpd.GeoDataFrame(
                geometry=[interseccion],
                crs=parroquia_encontrada.crs
            )
            # Convertir a WGS84 si es necesario
            if interseccion_gdf.crs != 'EPSG:4326':
                interseccion_gdf = interseccion_gdf.to_crs('EPSG:4326')
            
            folium.GeoJson(
                interseccion_gdf,
                name=f'Intersección {i+1} {parroquia} - Cobertura Alta',
                style_function=lambda feature: {
                    'fillColor': '#FF0000',  # Rojo intenso
                    'color': '#000000',      # Borde negro
                    'weight': 0.5,           # Grosor del borde muy delgado
                    'fillOpacity': 0.8       # Transparencia menor
                },
                tooltip=f'Intersección {i+1}: {parroquia} + Cobertura Alta'
            ).add_to(mapa)
        
        # Agregar la geometría unificada como capa separada
        if geometria_wgs84:
            geometria_unificada_gdf = geometria_wgs84
            
            folium.GeoJson(
                geometria_unificada_gdf,
                name=f'Geometría Unificada {parroquia} - Cobertura Alta',
                style_function=lambda feature: {
                    'fillColor': '#FF6600',  # Naranja para diferenciar
                    'color': '#800080',      # Borde morado
                    'weight': 0.5,           # Borde muy delgado
                    'fillOpacity': 0.4       # Menos transparente para mejor visibilidad
                },
                tooltip=f'Geometría Unificada: {parroquia} + Cobertura Alta (Exportada a KMZ)'
            ).add_to(mapa)
        
        # Agregar controles de capas
        folium.LayerControl().add_to(mapa)
        
        # Agregar leyenda de colores actualizada
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 280px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Leyenda del Mapa</b></p>
        <p><i class="fa fa-square" style="color:#00FF00"></i> Cobertura Alta (-85 dBm)</p>
        <p><i class="fa fa-square" style="color:#FFFF99"></i> Cobertura Media (-95 dBm)</p>
        <p><i class="fa fa-square" style="color:#FFB3B3"></i> Cobertura Baja (-105 dBm)</p>
        <p><i class="fa fa-square" style="color:blue"></i> Parroquia</p>
        <p><i class="fa fa-square" style="color:#FF0000"></i> Intersecciones Separadas (Parroquia + Cobertura Alta)</p>
        <p><i class="fa fa-square" style="color:#FF6600"></i> Geometría Unificada (Exportada a KMZ)</p>
        </div>
        '''
        mapa.get_root().html.add_child(folium.Element(legend_html))
        
        return mapa
        
    except Exception as e:
        return None

# Barra lateral
with st.sidebar:
    st.title("📡 Análisis de Cobertura")
    
    # Drag & Drop más grande (primero)
    st.subheader("📁 Archivos de Cobertura")
    archivos_subidos = st.file_uploader(
        "Arrastra y suelta los 4 archivos del shapefile:",
        type=['shp', 'shx', 'dbf', 'prj'],
        accept_multiple_files=True,
        help="Selecciona o arrastra los 4 archivos: .shp, .shx, .dbf, .prj"
    )
    
    # Procesar los archivos subidos
    archivos_completos = False
    archivo_shp = None
    archivo_shx = None
    archivo_dbf = None
    archivo_prj = None
    
    if archivos_subidos:
        # Verificar que se subieron exactamente 4 archivos
        if len(archivos_subidos) != 4:
            st.error(f"❌ Se requieren exactamente 4 archivos. Subiste {len(archivos_subidos)} archivos.")
        else:
            # Organizar los archivos por extensión
            archivos_por_extension = {}
            for archivo in archivos_subidos:
                extension = archivo.name.split('.')[-1].lower()
                archivos_por_extension[extension] = archivo
            
            # Verificar que estén todos los tipos requeridos
            extensiones_requeridas = {'shp', 'shx', 'dbf', 'prj'}
            extensiones_subidas = set(archivos_por_extension.keys())
            
            if extensiones_requeridas == extensiones_subidas:
                # Asignar los archivos
                archivo_shp = archivos_por_extension['shp']
                archivo_shx = archivos_por_extension['shx']
                archivo_dbf = archivos_por_extension['dbf']
                archivo_prj = archivos_por_extension['prj']
                
                # Verificar que los archivos tengan el mismo nombre base
                nombres_base = []
                for archivo in [archivo_shp, archivo_shx, archivo_dbf, archivo_prj]:
                    nombre_base = archivo.name.rsplit('.', 1)[0]  # Remover extensión
                    nombres_base.append(nombre_base)
                
                if len(set(nombres_base)) == 1:
                    st.success("✅ Archivos listos")
                    archivos_completos = True
                else:
                    st.error("❌ Los archivos deben tener el mismo nombre base")
            else:
                extensiones_faltantes = extensiones_requeridas - extensiones_subidas
                if extensiones_faltantes:
                    st.error(f"❌ Faltan archivos: {', '.join(extensiones_faltantes)}")
    
    st.markdown("---")
    
    # Selectores (después del drag & drop)
    st.subheader("⚙️ Configuración")
    
    # Selector de provincia
    provincia = st.selectbox(
        "Provincia:",
        options=list(PROVINCIAS_DISPONIBLES.keys()),
        index=0
    )
    
    # Cargar parroquias de la provincia seleccionada
    ruta_geojson = obtener_ruta_geojson_provincia(provincia)
    parroquias_disponibles = []
    
    if ruta_geojson:
        try:
            gdf_parroquias = gpd.read_file(ruta_geojson)
            parroquias_disponibles = sorted(gdf_parroquias['PARROQUIA'].unique().tolist())
        except Exception as e:
            st.error(f"Error al cargar parroquias: {e}")
    
    # Selector de parroquia
    parroquia = st.selectbox(
        "Parroquia:",
        options=parroquias_disponibles,
        index=0 if parroquias_disponibles else None,
        disabled=not parroquias_disponibles
    )
    
    # Selectores adicionales
    operadora = st.selectbox(
        "Operadora:",
        options=OPERADORAS,
        index=0
    )
    
    año = st.selectbox(
        "Año:",
        options=AÑOS,
        index=5  # 2025 por defecto
    )
    
    tecnologia = st.selectbox(
        "Tecnología:",
        options=TECNOLOGIAS,
        index=0
    )
    
    # Botón de conversión
    st.markdown("---")
    convertir = st.button("🔄 Convertir", type="primary", use_container_width=True)

# Área principal del mapa
st.title("📡 Mapa de Resultados")

# Procesar cuando se presiona el botón
if convertir and archivos_completos and parroquia:
    with st.spinner("Procesando cobertura..."):
        # Procesar la cobertura
        geometria_unificada, parroquia_encontrada, intersecciones, gdf_cobertura = procesar_cobertura(
            archivo_shp, archivo_shx, archivo_dbf, archivo_prj, 
            provincia, parroquia, operadora, año, tecnologia
        )
        
        # Debug temporal
        st.write(f"Debug - geometria_unificada: {geometria_unificada is not None}")
        st.write(f"Debug - parroquia_encontrada: {parroquia_encontrada is not None}")
        st.write(f"Debug - intersecciones: {len(intersecciones) if intersecciones else 0}")
        st.write(f"Debug - gdf_cobertura: {gdf_cobertura is not None}")
        
        if geometria_unificada is not None:
            # Crear el mapa
            mapa = crear_mapa_folium(geometria_unificada, parroquia_encontrada, provincia, parroquia, intersecciones, gdf_cobertura)
            
            st.write(f"Debug - mapa creado: {mapa is not None}")
            
            if mapa:
                # Mostrar el mapa
                components.html(mapa._repr_html_(), height=600)
                
                # Crear y mostrar botón de descarga
                nombre_archivo = f"{parroquia.upper()}_{operadora.upper()}_{año}_{tecnologia}.kmz"
                
                # Crear GeoDataFrame para exportar
                geometria_unificada_gdf = gpd.GeoDataFrame(
                    geometry=[geometria_unificada],
                    crs=parroquia_encontrada.crs
                )
                
                # Exportar a KMZ
                kmz_data = exportar_a_kmz(geometria_unificada_gdf, nombre_archivo)
                
                if kmz_data:
                    st.download_button(
                        label="📥 Descargar KMZ",
                        data=kmz_data,
                        file_name=nombre_archivo,
                        mime="application/vnd.google-earth.kmz",
                        use_container_width=True
                    )
                else:
                    st.error("❌ Error al generar el archivo KMZ")
            else:
                st.error("❌ Error al crear el mapa")
        else:
            st.error("❌ No se pudo procesar la cobertura")
else:
    if not archivos_completos:
        st.info("👆 Arrastra los 4 archivos del shapefile")
    elif not parroquia:
        st.info("👆 Selecciona una parroquia")
    else:
        st.info("👆 Presiona el botón Convertir")