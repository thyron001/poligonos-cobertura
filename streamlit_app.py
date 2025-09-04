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
    page_title="Análisis de Cobertura de Telecomunicaciones",
    page_icon="📡",
    layout="wide"
)

# Título principal
st.title("📡 Análisis de Cobertura de Telecomunicaciones")
st.markdown("---")

# Configuración de las 6 provincias disponibles
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
AÑOS = ["2020", "2021", "2022", "2023", "2024"]

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
        st.error(f"Error al exportar a KMZ: {e}")
        return None

def crear_geometria_unificada(intersecciones, parroquia_geom):
    """Crear una geometría unificada conectando las intersecciones con líneas delgadas"""
    if len(intersecciones) <= 1:
        return intersecciones[0] if intersecciones else None, []
    
    try:
        st.info(f"Creando geometría unificada para {len(intersecciones)} intersecciones...")
        
        # Obtener los centroides de cada intersección
        centroides = []
        for interseccion in intersecciones:
            if not interseccion.is_empty:
                centroide = interseccion.centroid
                centroides.append((centroide.x, centroide.y))
        
        st.info(f"Centroides calculados: {len(centroides)}")
        
        # Crear líneas de conexión entre centroides
        lineas_conexion = []
        for i in range(len(centroides)):
            for j in range(i + 1, len(centroides)):
                linea = LineString([centroides[i], centroides[j]])
                # Verificar que la línea esté dentro de la parroquia
                if linea.within(parroquia_geom) or linea.intersects(parroquia_geom):
                    lineas_conexion.append(linea)
        
        st.info(f"Líneas de conexión creadas: {len(lineas_conexion)}")
        
        # Crear buffer SÚPER ancho alrededor de las líneas de conexión para formar "puentes" sólidos
        buffer_width = 1  # Buffer EXTREMADAMENTE ancho para crear corredores muy visibles
        puentes = []
        for linea in lineas_conexion:
            puente = linea.buffer(buffer_width)
            puentes.append(puente)
        
        st.info(f"Puentes creados con buffer de {buffer_width}")
        
        # Combinar todas las intersecciones y puentes
        geometrias_combinadas = intersecciones + puentes
        
        # Unir todo en una sola geometría
        st.info(f"Uniendo {len(geometrias_combinadas)} geometrías...")
        geometria_unificada = unary_union(geometrias_combinadas)
        
        # Verificar que la unión fue exitosa
        if geometria_unificada.is_empty:
            st.warning("La geometría unificada está vacía, usando solo las intersecciones")
            geometria_unificada = unary_union(intersecciones)
        
        st.success("Geometría unificada creada exitosamente")
        return geometria_unificada, lineas_conexion
        
    except Exception as e:
        st.error(f"Error al crear geometría unificada: {e}")
        # Si falla, intentar unir solo las intersecciones
        try:
            st.info("Intentando unir solo las intersecciones...")
            geometria_simple = unary_union(intersecciones)
            return geometria_simple, []
        except Exception as e2:
            st.error(f"Error al unir intersecciones: {e2}")
            return None, []

def procesar_cobertura(archivo_subido, provincia, parroquia, operadora, año, tecnologia):
    """Procesar el archivo de cobertura y generar la geometría unificada"""
    
    # Cargar datos de parroquias desde GeoJSON
    ruta_geojson = obtener_ruta_geojson_provincia(provincia)
    if not ruta_geojson or not os.path.exists(ruta_geojson):
        st.error(f"No se encontró el archivo GeoJSON para la provincia: {provincia}")
        return None, None
    
    try:
        gdf_parroquias = gpd.read_file(ruta_geojson)
        
        # Buscar la parroquia específica
        parroquia_encontrada = None
        for campo in gdf_parroquias.columns:
            if gdf_parroquias[campo].dtype == 'object':
                coincidencias = gdf_parroquias[gdf_parroquias[campo].str.upper().str.contains(parroquia.upper(), na=False)]
                if len(coincidencias) > 0:
                    parroquia_encontrada = coincidencias
                    break
        
        if parroquia_encontrada is None:
            st.error(f"No se encontró la parroquia '{parroquia}' en la provincia '{provincia}'")
            return None, None
        
        # Procesar archivo de cobertura
        file_extension = archivo_subido.name.split('.')[-1].lower()
        
        with tempfile.NamedTemporaryFile(suffix=f'.{file_extension}', delete=False) as tmp_file:
            tmp_file.write(archivo_subido.getvalue())
            tmp_file.flush()
            
            # Extraer y cargar shapefile
            with tempfile.TemporaryDirectory() as tmp_dir:
                if file_extension == 'zip':
                    import zipfile
                    with zipfile.ZipFile(tmp_file.name, 'r') as zip_ref:
                        zip_ref.extractall(tmp_dir)
                elif file_extension == 'rar':
                    try:
                        import py7zr
                        with py7zr.SevenZipFile(tmp_file.name, mode='r') as rar_ref:
                            rar_ref.extractall(tmp_dir)
                    except ImportError:
                        st.error("Para archivos RAR se requiere la biblioteca py7zr. Por favor, usa archivos ZIP.")
                        return None, None
                else:
                    st.error("Formato de archivo no soportado. Use ZIP o RAR.")
                    return None, None
                
                # Buscar archivo .shp
                shp_files = list(Path(tmp_dir).glob('*.shp'))
                if not shp_files:
                    st.error("No se encontró archivo .shp en el archivo subido")
                    return None, None
                
                gdf_cobertura = gpd.read_file(shp_files[0])
        
        # Limpiar archivo temporal
        os.unlink(tmp_file.name)
        
        # Calcular intersecciones
        intersecciones = []
        parroquia_geom = parroquia_encontrada.geometry.iloc[0]
        
        for idx, row in gdf_cobertura.iterrows():
            cobertura_geom = row.geometry
            try:
                interseccion = parroquia_geom.intersection(cobertura_geom)
                if not interseccion.is_empty:
                    intersecciones.append(interseccion)
            except Exception as e:
                st.warning(f"Error al calcular intersección: {e}")
        
        if not intersecciones:
            st.warning("No se encontraron intersecciones entre la parroquia y la cobertura")
            return None, None
        
        # Crear geometría unificada
        geometria_unificada, lineas_conexion = crear_geometria_unificada(intersecciones, parroquia_geom)
        
        # Crear líneas de conexión manuales si no se crearon automáticamente
        if not lineas_conexion:
            st.info("Creando líneas de conexión manuales...")
            
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
            
            st.info(f"Total de áreas sueltas encontradas: {len(todas_las_areas)}")
            
            # Crear líneas de conexión secuenciales (una con la siguiente)
            lineas_conexion = []
            
            # Ordenar las áreas por su posición (de izquierda a derecha usando el centroide X)
            areas_ordenadas = sorted(enumerate(todas_las_areas), key=lambda x: x[1].centroid.x)
            indices_ordenados = [idx for idx, _ in areas_ordenadas]
            
            st.info(f"Áreas ordenadas de izquierda a derecha: {[i+1 for i in indices_ordenados]}")
            
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
                    st.info(f"Conectando Área {idx_actual + 1} con Área {idx_siguiente + 1}")
            
            st.info(f"Líneas de conexión secuenciales creadas: {len(lineas_conexion)}")
            
            # Crear caminos anchos (corredores) en lugar de líneas delgadas
            caminos_conexion = []
            for linea in lineas_conexion:
                # Crear un camino EXTREMADAMENTE ancho usando buffer súper grande
                camino_ancho = linea.buffer(1)  # Buffer SÚPER ancho para crear corredor muy visible
                caminos_conexion.append(camino_ancho)
            
            st.info(f"Caminos de conexión creados: {len(caminos_conexion)}")
            
            # Combinar todas las áreas sueltas con los caminos para formar un solo polígono
            st.info(f"Combinando {len(todas_las_areas)} áreas sueltas con {len(caminos_conexion)} caminos...")
            elementos_para_unificar = todas_las_areas + caminos_conexion
            
            try:
                geometria_unificada = unary_union(elementos_para_unificar)
                st.success("Geometría unificada creada exitosamente")
            except Exception as e:
                st.error(f"Error al crear geometría unificada: {e}")
                geometria_unificada = None
        
        if geometria_unificada is None:
            st.error("No se pudo crear la geometría unificada")
            return None, None, None
        
        return geometria_unificada, parroquia_encontrada, intersecciones
        
    except Exception as e:
        st.error(f"Error al procesar cobertura: {e}")
        return None, None, None

def crear_mapa_folium(geometria_unificada, parroquia_encontrada, provincia, parroquia, intersecciones=None):
    """Crear mapa de Folium con la geometría unificada"""
    
    # Crear mapa centrado en Ecuador
    mapa = folium.Map(
        location=[-2.0, -78.0],
        zoom_start=7,
        tiles='OpenStreetMap'
    )
    
    # Agregar la parroquia
    folium.GeoJson(
        parroquia_encontrada,
        name=f'Parroquia {parroquia}',
        style_function=lambda feature: {
            'fillColor': 'blue',
            'color': '#000000',
            'weight': 2,
            'fillOpacity': 0.7
        }
    ).add_to(mapa)
    
    # Mostrar cada intersección por separado (para visualización)
    if intersecciones:
        for i, interseccion in enumerate(intersecciones):
            interseccion_gdf = gpd.GeoDataFrame(
                geometry=[interseccion],
                crs=parroquia_encontrada.crs
            )
            
            folium.GeoJson(
                interseccion_gdf,
                name=f'Intersección {i+1} {parroquia} - Cobertura Alta',
                style_function=lambda feature: {
                    'fillColor': '#FF0000',  # Rojo intenso
                    'color': '#000000',      # Borde negro
                    'weight': 3,             # Grosor del borde mayor
                    'fillOpacity': 0.8       # Transparencia menor
                },
                tooltip=f'Intersección {i+1}: {parroquia} + Cobertura Alta'
            ).add_to(mapa)
    
    # Agregar la geometría unificada
    geometria_unificada_gdf = gpd.GeoDataFrame(
        geometry=[geometria_unificada],
        crs=parroquia_encontrada.crs
    )
    
    folium.GeoJson(
        geometria_unificada_gdf,
        name=f'Geometría Unificada {parroquia}',
        style_function=lambda feature: {
            'fillColor': '#FF6600',  # Naranja para diferenciar
            'color': '#800080',      # Borde morado
            'weight': 3,             # Borde más grueso
            'fillOpacity': 0.4       # Menos transparente para mejor visibilidad
        },
        tooltip=f'Geometría Unificada: {parroquia} + Cobertura Alta (Exportada a KMZ)'
    ).add_to(mapa)
    
    # Agregar controles de capas
    folium.LayerControl().add_to(mapa)
    
    # Agregar leyenda de colores
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 280px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <p><b>Leyenda del Mapa</b></p>
    <p><i class="fa fa-square" style="color:blue"></i> Parroquia</p>
    <p><i class="fa fa-square" style="color:#FF0000"></i> Intersecciones Separadas (Parroquia + Cobertura Alta)</p>
    <p><i class="fa fa-square" style="color:#FF6600"></i> Geometría Unificada (Exportada a KMZ)</p>
    </div>
    '''
    mapa.get_root().html.add_child(folium.Element(legend_html))
    
    return mapa

# Interfaz principal
col1, col2 = st.columns([1, 2])

with col1:
    st.header("📋 Configuración")
    
    # Selector de provincia
    provincia = st.selectbox(
        "Selecciona la provincia:",
        options=list(PROVINCIAS_DISPONIBLES.keys()),
        index=0
    )
    
    # Cargar parroquias de la provincia seleccionada
    ruta_geojson = obtener_ruta_geojson_provincia(provincia)
    if ruta_geojson and os.path.exists(ruta_geojson):
        try:
            gdf_parroquias = gpd.read_file(ruta_geojson)
            parroquias_disponibles = sorted(gdf_parroquias['PARROQUIA'].unique().tolist())
            
            parroquia = st.selectbox(
                "Selecciona la parroquia:",
                options=parroquias_disponibles,
                index=0
            )
        except Exception as e:
            st.error(f"Error al cargar parroquias de {provincia}: {e}")
            parroquia = None
    else:
        st.error(f"No se encontró el archivo GeoJSON para {provincia}")
        parroquia = None
    
    # Selectores adicionales
    operadora = st.selectbox(
        "Selecciona la operadora:",
        options=OPERADORAS,
        index=0
    )
    
    año = st.selectbox(
        "Selecciona el año:",
        options=AÑOS,
        index=len(AÑOS)-1  # Último año por defecto
    )
    
    tecnologia = st.selectbox(
        "Selecciona la tecnología:",
        options=TECNOLOGIAS,
        index=0
    )
    
    # Carga de archivo
    st.markdown("---")
    st.subheader("📁 Archivo de Cobertura")
    archivo_subido = st.file_uploader(
        "Sube el archivo de cobertura (ZIP o RAR):",
        type=['zip', 'rar'],
        help="El archivo debe contener un shapefile (.shp, .shx, .dbf, .prj)"
    )
    
    # Botón de conversión
    st.markdown("---")
    convertir = st.button("🔄 Convertir", type="primary", use_container_width=True)

with col2:
    st.header("🗺️ Mapa de Resultados")
    
    if convertir and archivo_subido and parroquia:
        with st.spinner("Procesando cobertura..."):
            geometria_unificada, parroquia_encontrada, intersecciones = procesar_cobertura(
                archivo_subido, provincia, parroquia, operadora, año, tecnologia
            )
        
        if geometria_unificada is not None:
            # Mostrar información sobre las áreas sueltas
            if intersecciones:
                st.markdown("---")
                st.subheader("📊 Análisis de Áreas Sueltas")
                
                # Contar el número total de áreas sueltas
                total_areas_sueltas = 0
                for i, interseccion in enumerate(intersecciones):
                    if hasattr(interseccion, 'geoms'):
                        # Si es MultiPolygon, contar cada polígono individual
                        num_areas = len(interseccion.geoms)
                        total_areas_sueltas += num_areas
                        st.info(f"Intersección {i+1}: {num_areas} área(s) suelta(s)")
                    else:
                        # Si es Polygon simple, es 1 área
                        total_areas_sueltas += 1
                        st.info(f"Intersección {i+1}: 1 área suelta")
                
                st.success(f"**Total de intersecciones encontradas:** {len(intersecciones)}")
                st.success(f"**Total de áreas sueltas:** {total_areas_sueltas}")
                
                if total_areas_sueltas > 1:
                    st.info(f"🎯 Las intersecciones generan {total_areas_sueltas} áreas separadas")
                    st.success("✅ Unificadas en una sola geometría continua")
                else:
                    st.info(f"🎯 Las intersecciones forman una sola área continua")
            
            # Crear mapa
            mapa = crear_mapa_folium(geometria_unificada, parroquia_encontrada, provincia, parroquia, intersecciones)
            
            # Mostrar mapa
            st_folium = components.html(
                mapa._repr_html_(),
                height=600
            )
            
            # Botón de descarga
            st.markdown("---")
            st.subheader("💾 Descargar Resultado")
            
            # Crear GeoDataFrame para exportación
            geometria_unificada_gdf = gpd.GeoDataFrame(
                geometry=[geometria_unificada],
                crs=parroquia_encontrada.crs
            )
            
            # Generar nombre del archivo
            nombre_archivo = f"{parroquia.lower()}_{operadora.lower()}_{año}_{tecnologia}.kmz"
            
            # Exportar a KMZ
            kmz_data = exportar_a_kmz(geometria_unificada_gdf, nombre_archivo)
            
            if kmz_data:
                st.download_button(
                    label="📥 Descargar KMZ",
                    data=kmz_data,
                    file_name=nombre_archivo,
                    mime="application/zip",
                    use_container_width=True
                )
                
                st.success(f"✅ Geometría unificada generada exitosamente")
                st.info(f"📄 Archivo: {nombre_archivo}")
            else:
                st.error("❌ Error al generar el archivo KMZ")
        else:
            st.error("❌ No se pudo procesar la cobertura")
    else:
        st.info("👆 Configura los parámetros y sube un archivo de cobertura para comenzar")

# Información adicional
st.markdown("---")
st.markdown("### ℹ️ Información")
st.markdown("""
Esta aplicación permite analizar la cobertura de telecomunicaciones en parroquias específicas de Ecuador.

**Proceso:**
1. Selecciona la provincia y parroquia
2. Configura la operadora, año y tecnología
3. Sube el archivo de cobertura (ZIP/RAR con shapefile)
4. Haz clic en "Convertir" para procesar
5. Descarga el resultado en formato KMZ

**Provincias disponibles:** Azuay, Cañar, El Oro, Loja, Morona Santiago, Zamora Chinchipe
""")
