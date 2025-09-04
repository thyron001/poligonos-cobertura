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

def procesar_cobertura(archivo_shp, archivo_shx, archivo_dbf, archivo_prj, provincia, parroquia, operadora, año, tecnologia):
    """Procesar los archivos de cobertura y generar la geometría unificada"""
    
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
        
        # Procesar archivos de cobertura
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Guardar todos los archivos en el directorio temporal
            archivos_shapefile = {
                'shp': archivo_shp,
                'shx': archivo_shx,
                'dbf': archivo_dbf,
                'prj': archivo_prj
            }
            
            rutas_archivos = {}
            for extension, archivo in archivos_shapefile.items():
                if archivo:
                    ruta_archivo = os.path.join(tmp_dir, f"cobertura.{extension}")
                    with open(ruta_archivo, 'wb') as f:
                        f.write(archivo.getvalue())
                    rutas_archivos[extension] = ruta_archivo
            
            # Cargar el shapefile usando el archivo .shp
            if 'shp' in rutas_archivos:
                gdf_cobertura = gpd.read_file(rutas_archivos['shp'])
            else:
                st.error("No se pudo cargar el archivo .shp")
                return None, None, None
        
        # Calcular intersecciones solo con cobertura alta
        intersecciones = []
        parroquia_geom = parroquia_encontrada.geometry.iloc[0]
        
        # Buscar el campo que contiene el nivel de cobertura
        campo_cobertura = None
        for col in gdf_cobertura.columns:
            if gdf_cobertura[col].dtype in ['float64', 'int64']:
                # Verificar si contiene valores típicos de cobertura (-85, -95, -105)
                valores_unicos = gdf_cobertura[col].unique()
                if any(val in valores_unicos for val in [-85.0, -95.0, -105.0, -85, -95, -105]):
                    campo_cobertura = col
                    break
        
        if campo_cobertura is None:
            st.warning("No se encontró campo de nivel de cobertura, calculando intersección con todas las áreas")
            # Si no se encuentra el campo, calcular con todas las áreas
            for idx, row in gdf_cobertura.iterrows():
                cobertura_geom = row.geometry
                try:
                    interseccion = parroquia_geom.intersection(cobertura_geom)
                    if not interseccion.is_empty:
                        intersecciones.append(interseccion)
                except Exception as e:
                    st.warning(f"Error al calcular intersección: {e}")
        else:
            st.info(f"Campo de cobertura encontrado: {campo_cobertura}")
            
            # Calcular intersección solo con cobertura alta (-85 dBm)
            for idx, row in gdf_cobertura.iterrows():
                coverage_level = row[campo_cobertura]
                
                # Solo calcular intersección si es cobertura alta
                if coverage_level == -85.0 or coverage_level == -85:
                    st.info("Calculando intersección con cobertura alta...")
                    
                    cobertura_geom = row.geometry
                    try:
                        interseccion = parroquia_geom.intersection(cobertura_geom)
                        if not interseccion.is_empty:
                            intersecciones.append(interseccion)
                            st.success("✅ Intersección encontrada")
                        else:
                            st.info("ℹ️ No hay intersección entre la parroquia y la zona de cobertura alta")
                    except Exception as e:
                        st.warning(f"Error al calcular intersección: {e}")
                else:
                    st.info(f"Saltando cobertura {coverage_level} dBm (no es alta)")
        
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
            return None, None, None, None
        
        return geometria_unificada, parroquia_encontrada, intersecciones, gdf_cobertura
        
    except Exception as e:
        st.error(f"Error al procesar cobertura: {e}")
        return None, None, None, None

def crear_mapa_folium(geometria_unificada, parroquia_encontrada, provincia, parroquia, intersecciones=None, gdf_cobertura=None):
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
    
    # Agregar capas de cobertura si están disponibles
    if gdf_cobertura is not None:
        # Buscar el campo de cobertura
        campo_cobertura = None
        for col in gdf_cobertura.columns:
            if gdf_cobertura[col].dtype in ['float64', 'int64']:
                valores_unicos = gdf_cobertura[col].unique()
                if any(val in valores_unicos for val in [-85.0, -95.0, -105.0, -85, -95, -105]):
                    campo_cobertura = col
                    break
        
        if campo_cobertura:
            # Función para determinar el color según el nivel de cobertura
            def get_color_by_coverage(level):
                if level == -85.0 or level == -85:  # Nivel alto
                    return '#00FF00'  # Verde intenso
                elif level == -95.0 or level == -95:  # Nivel medio
                    return '#FFFF99'  # Amarillo pastel
                elif level == -105.0 or level == -105:  # Nivel bajo
                    return '#FFB3B3'  # Rojo pastel
                else:
                    return '#808080'  # Gris por defecto
            
            # Función para obtener el nombre del nivel de cobertura
            def get_coverage_name(level):
                if level == -85.0 or level == -85:
                    return 'Cobertura Alta (-85 dBm)'
                elif level == -95.0 or level == -95:
                    return 'Cobertura Media (-95 dBm)'
                elif level == -105.0 or level == -105:
                    return 'Cobertura Baja (-105 dBm)'
                else:
                    return f'Cobertura ({level} dBm)'
            
            # Agregar cada nivel de cobertura con su color correspondiente
            for idx, row in gdf_cobertura.iterrows():
                coverage_level = row[campo_cobertura]
                coverage_name = get_coverage_name(coverage_level)
                
                # Crear un GeoDataFrame con solo esta fila
                single_region = gdf_cobertura.iloc[[idx]]
                
                # Agregar la capa de cobertura
                folium.GeoJson(
                    single_region,
                    name=coverage_name,
                    style_function=lambda feature, level=coverage_level: {
                        'fillColor': get_color_by_coverage(level),
                        'color': '#000000',      # Borde negro
                        'weight': 1,             # Grosor del borde
                        'fillOpacity': 0.6       # Transparencia
                    },
                    tooltip=coverage_name
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
    
    # Carga de archivos shapefile
    st.markdown("---")
    st.subheader("📁 Archivos de Cobertura")
    st.markdown("**Sube los 4 archivos del shapefile (drag & drop):**")
    
    # Información sobre los archivos requeridos
    with st.expander("ℹ️ Información sobre los archivos shapefile"):
        st.markdown("""
        Un shapefile completo requiere 4 archivos:
        - **.shp** - Archivo principal con la geometría
        - **.shx** - Archivo de índice
        - **.dbf** - Archivo de atributos
        - **.prj** - Archivo de proyección
        
        Todos los archivos deben tener el mismo nombre base.
        """)
    
    col_shp, col_shx = st.columns(2)
    with col_shp:
        archivo_shp = st.file_uploader(
            "Archivo .shp (principal):",
            type=['shp'],
            key="shp_file"
        )
    with col_shx:
        archivo_shx = st.file_uploader(
            "Archivo .shx (índice):",
            type=['shx'],
            key="shx_file"
        )
    
    col_dbf, col_prj = st.columns(2)
    with col_dbf:
        archivo_dbf = st.file_uploader(
            "Archivo .dbf (atributos):",
            type=['dbf'],
            key="dbf_file"
        )
    with col_prj:
        archivo_prj = st.file_uploader(
            "Archivo .prj (proyección):",
            type=['prj'],
            key="prj_file"
        )
    
    # Verificar que todos los archivos estén subidos
    archivos_completos = all([archivo_shp, archivo_shx, archivo_dbf, archivo_prj])
    
    if archivos_completos:
        # Verificar que los archivos tengan el mismo nombre base
        nombres_base = []
        for archivo in [archivo_shp, archivo_shx, archivo_dbf, archivo_prj]:
            if archivo:
                nombre_base = archivo.name.rsplit('.', 1)[0]  # Remover extensión
                nombres_base.append(nombre_base)
        
        if len(set(nombres_base)) == 1:
            st.success("✅ Todos los archivos del shapefile están listos")
        else:
            st.error("❌ Los archivos deben tener el mismo nombre base")
            st.warning("Ejemplo: cobertura.shp, cobertura.shx, cobertura.dbf, cobertura.prj")
    else:
        archivos_faltantes = []
        if not archivo_shp: archivos_faltantes.append(".shp")
        if not archivo_shx: archivos_faltantes.append(".shx")
        if not archivo_dbf: archivos_faltantes.append(".dbf")
        if not archivo_prj: archivos_faltantes.append(".prj")
        st.warning(f"⚠️ Faltan archivos: {', '.join(archivos_faltantes)}")
    
    # Botón de conversión
    st.markdown("---")
    convertir = st.button("🔄 Convertir", type="primary", use_container_width=True)

with col2:
    st.header("🗺️ Mapa de Resultados")
    
    if convertir and archivos_completos and parroquia:
        with st.spinner("Procesando cobertura..."):
            geometria_unificada, parroquia_encontrada, intersecciones, gdf_cobertura = procesar_cobertura(
                archivo_shp, archivo_shx, archivo_dbf, archivo_prj, provincia, parroquia, operadora, año, tecnologia
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
            mapa = crear_mapa_folium(geometria_unificada, parroquia_encontrada, provincia, parroquia, intersecciones, gdf_cobertura)
            
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
3. Sube los 4 archivos del shapefile (.shp, .shx, .dbf, .prj)
4. Haz clic en "Convertir" para procesar
5. Descarga el resultado en formato KMZ

**Provincias disponibles:** Azuay, Cañar, El Oro, Loja, Morona Santiago, Zamora Chinchipe
""")
