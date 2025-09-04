#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear mapas interactivos de parroquias específicas con cobertura UMTS usando Folium
Ahora usa archivos GeoJSON por provincia para mejor rendimiento y organización
"""

import geopandas as gpd
import folium
from shapely.geometry import Polygon, MultiPolygon, LineString
from shapely.ops import unary_union
import numpy as np
import os
import zipfile

def obtener_ruta_geojson_provincia(nombre_provincia):
    """Obtener la ruta del archivo GeoJSON de la provincia especificada"""
    # Normalizar el nombre de la provincia para el archivo
    nombre_archivo = nombre_provincia.lower().replace(' ', '_').replace('ñ', 'n').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    ruta_geojson = f"geojson_provincias/{nombre_archivo}.geojson"
    
    # Verificar que el archivo existe
    if os.path.exists(ruta_geojson):
        return ruta_geojson
    else:
        print(f"⚠️ No se encontró el archivo GeoJSON para la provincia: {nombre_provincia}")
        print(f"   Ruta buscada: {ruta_geojson}")
        print(f"   Archivos disponibles en geojson_provincias/:")
        
        if os.path.exists("geojson_provincias"):
            archivos = [f for f in os.listdir("geojson_provincias") if f.endswith('.geojson')]
            for archivo in sorted(archivos):
                print(f"     - {archivo}")
        else:
            print(f"     - El directorio geojson_provincias no existe")
        
        return None

def exportar_a_kmz(geodataframe, nombre_archivo):
    """Exportar GeoDataFrame a archivo KMZ"""
    try:
        # Primero exportar a KML
        nombre_kml = nombre_archivo.replace('.kmz', '.kml')
        geodataframe.to_file(nombre_kml, driver='KML')
        
        # Crear archivo KMZ (que es un ZIP con el KML)
        with zipfile.ZipFile(nombre_archivo, 'w', zipfile.ZIP_DEFLATED) as kmz_file:
            kmz_file.write(nombre_kml, os.path.basename(nombre_kml))
        
        # Eliminar el archivo KML temporal
        os.remove(nombre_kml)
        
        return True
    except Exception as e:
        print(f"⚠️ Error al exportar a KMZ: {e}")
        return False

def crear_geometria_unificada(intersecciones, parroquia_geom):
    """Crear una geometría unificada conectando las intersecciones con líneas delgadas"""
    if len(intersecciones) <= 1:
        return intersecciones[0] if intersecciones else None, []
    
    try:
        print(f"  Creando geometría unificada para {len(intersecciones)} intersecciones...")
        
        # Obtener los centroides de cada intersección
        centroides = []
        for interseccion in intersecciones:
            if not interseccion.is_empty:
                centroide = interseccion.centroid
                centroides.append((centroide.x, centroide.y))
        
        print(f"  Centroides calculados: {len(centroides)}")
        
        # Crear líneas de conexión entre centroides
        lineas_conexion = []
        for i in range(len(centroides)):
            for j in range(i + 1, len(centroides)):
                linea = LineString([centroides[i], centroides[j]])
                # Verificar que la línea esté dentro de la parroquia
                if linea.within(parroquia_geom) or linea.intersects(parroquia_geom):
                    lineas_conexion.append(linea)
        
        print(f"  Líneas de conexión creadas: {len(lineas_conexion)}")
        
        # Crear buffer SÚPER ancho alrededor de las líneas de conexión para formar "puentes" sólidos
        buffer_width = 1  # Buffer EXTREMADAMENTE ancho para crear corredores muy visibles
        puentes = []
        for linea in lineas_conexion:
            puente = linea.buffer(buffer_width)
            puentes.append(puente)
        
        print(f"  Puentes creados con buffer de {buffer_width}")
        
        # Combinar todas las intersecciones y puentes
        geometrias_combinadas = intersecciones + puentes
        
        # Unir todo en una sola geometría
        print(f"  Uniendo {len(geometrias_combinadas)} geometrías...")
        geometria_unificada = unary_union(geometrias_combinadas)
        
        # Verificar que la unión fue exitosa
        if geometria_unificada.is_empty:
            print(f"  ⚠️ La geometría unificada está vacía, usando solo las intersecciones")
            geometria_unificada = unary_union(intersecciones)
        
        print(f"  ✅ Geometría unificada creada exitosamente")
        return geometria_unificada, lineas_conexion
        
    except Exception as e:
        print(f"⚠️ Error al crear geometría unificada: {e}")
        # Si falla, intentar unir solo las intersecciones
        try:
            print(f"  Intentando unir solo las intersecciones...")
            geometria_simple = unary_union(intersecciones)
            return geometria_simple, []
        except Exception as e2:
            print(f"  ❌ Error al unir intersecciones: {e2}")
            return None, []

def crear_mapa_parroquia_con_cobertura():
    """Crear mapa de una parroquia específica con cobertura UMTS"""
    # Configuración
    NOMBRE_PARROQUIA = "BATAN"  # Cambiar aquí el nombre de la parroquia
    NOMBRE_PROVINCIA = "AZUAY"  # Cambiar aquí el nombre de la provincia
    RUTA_UMTS = "AZUAY SHAPE/AZUAY_UMTS_JUN2023_v4_region.shp"
    
    print(f"Buscando parroquia: {NOMBRE_PARROQUIA} en provincia: {NOMBRE_PROVINCIA}")
    
    try:
        # Obtener ruta del GeoJSON de la provincia
        ruta_geojson_provincia = obtener_ruta_geojson_provincia(NOMBRE_PROVINCIA)
        
        if ruta_geojson_provincia is None:
            print(f"❌ No se pudo encontrar el archivo GeoJSON para la provincia: {NOMBRE_PROVINCIA}")
            return
        
        # Cargar datos de parroquias desde el GeoJSON de la provincia
        print(f"Cargando límites parroquiales desde: {ruta_geojson_provincia}")
        gdf_parroquias = gpd.read_file(ruta_geojson_provincia)
        print(f"Datos de parroquias cargados. Total de registros: {len(gdf_parroquias)}")
        
        # Buscar la parroquia específica
        parroquia_encontrada = None
        
        for campo in gdf_parroquias.columns:
            if gdf_parroquias[campo].dtype == 'object':
                print(f"Buscando en campo: {campo}")
                coincidencias = gdf_parroquias[gdf_parroquias[campo].str.upper().str.contains(NOMBRE_PARROQUIA.upper(), na=False)]
                if len(coincidencias) > 0:
                    parroquia_encontrada = coincidencias
                    print(f"¡Encontrada! {len(coincidencias)} coincidencias en '{campo}'")
                    break
        
        if parroquia_encontrada is not None:
            # Cargar datos de cobertura UMTS
            print("Cargando cobertura UMTS de Azuay...")
            gdf_umts = gpd.read_file(RUTA_UMTS)
            print(f"Datos de cobertura UMTS cargados. Total de registros: {len(gdf_umts)}")
            
            print("Calculando intersecciones y creando geometría unificada...")
            
            # Crear mapa centrado en Ecuador
            mapa = folium.Map(
                location=[-2.0, -78.0],
                zoom_start=7,
                tiles='OpenStreetMap'
            )
            
            # Agregar la parroquia específica
            folium.GeoJson(
                parroquia_encontrada,
                name=f'Parroquia {NOMBRE_PARROQUIA}',
                style_function=lambda feature: {
                    'fillColor': 'blue',  # Azul para la parroquia
                    'color': '#000000',      # Borde negro
                    'weight': 2,             # Grosor del borde
                    'fillOpacity': 0.7       # Transparencia
                }
            ).add_to(mapa)
            
            # Función para determinar el color según el nivel de cobertura
            def get_color_by_coverage(feature):
                coverage_level = feature['properties']['Float']
                if coverage_level == -85.0:  # Nivel alto
                    return '#00FF00'  # Verde intenso
                elif coverage_level == -95.0:  # Nivel medio
                    return '#FFFF99'  # Amarillo pastel
                elif coverage_level == -105.0:  # Nivel bajo
                    return '#FFB3B3'  # Rojo pastel
                else:
                    return '#808080'  # Gris por defecto
            
            # Función para obtener el nombre del nivel de cobertura
            def get_coverage_name(feature):
                coverage_level = feature['properties']['Float']
                if coverage_level == -85.0:
                    return 'Cobertura Alta (-85 dBm)'
                elif coverage_level == -95.0:
                    return 'Cobertura Media (-95 dBm)'
                elif coverage_level == -105.0:
                    return 'Cobertura Baja (-105 dBm)'
                else:
                    return f'Cobertura ({coverage_level} dBm)'
            
            # Lista para almacenar las intersecciones
            intersecciones = []
            
            # Agregar cada nivel de cobertura UMTS con su color correspondiente
            for idx, row in gdf_umts.iterrows():
                coverage_level = row['Float']
                coverage_name = get_coverage_name({'properties': {'Float': coverage_level}})
                
                # Crear un GeoDataFrame con solo esta fila
                single_region = gdf_umts.iloc[[idx]]
                
                # Agregar la capa de cobertura
                folium.GeoJson(
                    single_region,
                    name=coverage_name,
                    style_function=lambda feature, level=coverage_level: {
                        'fillColor': get_color_by_coverage({'properties': {'Float': level}}),
                        'color': '#000000',      # Borde negro
                        'weight': 1,             # Grosor del borde
                        'fillOpacity': 0.6       # Transparencia
                    },
                    tooltip=coverage_name
                ).add_to(mapa)
                
                # Si es cobertura alta, calcular intersección con la parroquia
                if coverage_level == -85.0:
                    print(f"Calculando intersección con cobertura alta...")
                    
                    # Obtener la geometría de la parroquia y la zona de cobertura alta
                    parroquia_geom = parroquia_encontrada.geometry.iloc[0]
                    cobertura_geom = row.geometry
                    
                    # Calcular la intersección
                    try:
                        interseccion = parroquia_geom.intersection(cobertura_geom)
                        
                        if not interseccion.is_empty:
                            intersecciones.append(interseccion)
                            print(f"✅ Intersección encontrada")
                        else:
                            print(f"ℹ️ No hay intersección entre {NOMBRE_PARROQUIA} y la zona de cobertura alta")
                            
                    except Exception as e:
                        print(f"⚠️ Error al calcular intersección: {e}")
            
            # Si hay intersecciones, procesarlas
            if intersecciones:
                print(f"Procesando {len(intersecciones)} intersecciones...")
                
                try:
                    # Obtener la geometría de la parroquia
                    parroquia_geom = parroquia_encontrada.geometry.iloc[0]
                    
                    # Crear geometría unificada
                    geometria_unificada, caminos_conexion = crear_geometria_unificada(intersecciones, parroquia_geom)
                    
                    # Mostrar cada intersección por separado (para visualización)
                    for i, interseccion in enumerate(intersecciones):
                        interseccion_gdf = gpd.GeoDataFrame(
                            geometry=[interseccion],
                            crs=parroquia_encontrada.crs
                        )
                        
                        folium.GeoJson(
                            interseccion_gdf,
                            name=f'Intersección {i+1} {NOMBRE_PARROQUIA} - Cobertura Alta',
                            style_function=lambda feature: {
                                'fillColor': '#FF0000',  # Rojo intenso
                                'color': '#000000',      # Borde negro
                                'weight': 3,             # Grosor del borde mayor
                                'fillOpacity': 0.8       # Transparencia menor
                            },
                            tooltip=f'Intersección {i+1}: {NOMBRE_PARROQUIA} + Cobertura Alta'
                        ).add_to(mapa)
                    
                    # Crear líneas de conexión manuales si no se crearon automáticamente
                    if not caminos_conexion:
                        print(f"Creando líneas de conexión manuales...")
                        
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
                        
                        print(f"  Total de áreas sueltas encontradas: {len(todas_las_areas)}")
                        
                        # Crear líneas de conexión secuenciales (una con la siguiente)
                        lineas_conexion = []
                        
                        # Ordenar las áreas por su posición (de izquierda a derecha usando el centroide X)
                        areas_ordenadas = sorted(enumerate(todas_las_areas), key=lambda x: x[1].centroid.x)
                        indices_ordenados = [idx for idx, _ in areas_ordenadas]
                        
                        print(f"  Áreas ordenadas de izquierda a derecha: {[i+1 for i in indices_ordenados]}")
                        
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
                                print(f"    Conectando Área {idx_actual + 1} con Área {idx_siguiente + 1}")
                        
                        print(f"  Líneas de conexión secuenciales creadas: {len(lineas_conexion)}")
                        
                        # Crear caminos anchos (corredores) en lugar de líneas delgadas
                        caminos_conexion = []
                        for linea in lineas_conexion:
                            # Crear un camino EXTREMADAMENTE ancho usando buffer súper grande
                            camino_ancho = linea.buffer(1)  # Buffer SÚPER ancho para crear corredor muy visible
                            caminos_conexion.append(camino_ancho)
                        
                        print(f"  Caminos de conexión creados: {len(caminos_conexion)}")
                        
                        # Combinar todas las áreas sueltas con los caminos para formar un solo polígono
                        print(f"  Combinando {len(todas_las_areas)} áreas sueltas con {len(caminos_conexion)} caminos...")
                        elementos_para_unificar = todas_las_areas + caminos_conexion
                        
                        try:
                            geometria_unificada = unary_union(elementos_para_unificar)
                            print(f"  ✅ Geometría unificada creada exitosamente")
                        except Exception as e:
                            print(f"  ⚠️ Error al crear geometría unificada: {e}")
                            geometria_unificada = None
                    
                    # Los caminos ahora forman parte de la geometría unificada, no se muestran por separado
                    print(f"✅ Los caminos se han integrado en la geometría unificada")
                    
                    # Agregar la geometría unificada como capa separada
                    if geometria_unificada:
                        geometria_unificada_gdf = gpd.GeoDataFrame(
                            geometry=[geometria_unificada],
                            crs=parroquia_encontrada.crs
                        )
                        
                        # Exportar la geometría unificada a KMZ
                        nombre_kmz = f"geometria_unificada_{NOMBRE_PARROQUIA.lower()}.kmz"
                        if exportar_a_kmz(geometria_unificada_gdf, nombre_kmz):
                            print(f"  ✅ Geometría unificada exportada: {nombre_kmz}")
                        else:
                            print(f"  ❌ Error al exportar geometría unificada a KMZ")
                        
                        folium.GeoJson(
                            geometria_unificada_gdf,
                            name=f'Geometría Unificada {NOMBRE_PARROQUIA} - Cobertura Alta',
                            style_function=lambda feature: {
                                'fillColor': '#FF6600',  # Naranja para diferenciar
                                'color': '#800080',      # Borde morado
                                'weight': 3,             # Borde más grueso
                                'fillOpacity': 0.4       # Menos transparente para mejor visibilidad
                            },
                            tooltip=f'Geometría Unificada: {NOMBRE_PARROQUIA} + Cobertura Alta (Exportada a KMZ)'
                        ).add_to(mapa)
                        
                        print(f"✅ Geometría unificada creada y agregada al mapa")
                        
                        print(f"   Los caminos se han combinado con las áreas para formar un solo polígono")
                    
                except Exception as e:
                    print(f"⚠️ Error al procesar intersecciones: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Contar áreas sueltas después de la intersección
            if intersecciones:
                print(f"\n" + "="*60)
                print("ANÁLISIS DE ÁREAS SUELTAS DESPUÉS DE LA INTERSECCIÓN")
                print("="*60)
                
                # Contar el número total de áreas sueltas
                total_areas_sueltas = 0
                
                for i, interseccion in enumerate(intersecciones):
                    if hasattr(interseccion, 'geoms'):
                        # Si es MultiPolygon, contar cada polígono individual
                        num_areas = len(interseccion.geoms)
                        total_areas_sueltas += num_areas
                        print(f"  Intersección {i+1}: {num_areas} área(s) suelta(s)")
                    else:
                        # Si es Polygon simple, es 1 área
                        total_areas_sueltas += 1
                        print(f"  Intersección {i+1}: 1 área suelta")
                
                print(f"\n📊 RESUMEN:")
                print(f"  Total de intersecciones encontradas: {len(intersecciones)}")
                print(f"  Total de áreas sueltas: {total_areas_sueltas}")
                
                if total_areas_sueltas > 1:
                    print(f"  🎯 Las intersecciones generan {total_areas_sueltas} áreas separadas")
                    if lineas_conexion:
                        print(f"  🔗 Conectadas con {len(lineas_conexion)} líneas de conexión")
                    if geometria_unificada:
                        print(f"  ✅ Unificadas en una sola geometría continua")
                else:
                    print(f"  🎯 Las intersecciones forman una sola área continua")
                
                print("="*60)
            
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
            <p><i class="fa fa-square" style="color:#FF6600"></i> Caminos de Conexión (Tomate + Borde Morado)</p>
            <p><i class="fa fa-square" style="color:#FF6600"></i> Geometría Unificada (Exportada a KMZ)</p>
            </div>
            '''
            mapa.get_root().html.add_child(folium.Element(legend_html))
            
            # Guardar mapa
            nombre_archivo = f"mapa_parroquia_{NOMBRE_PARROQUIA.lower().replace(' ', '_')}_con_cobertura.html"
            mapa.save(nombre_archivo)
            print(f"✅ Mapa guardado: {nombre_archivo}")
            print("Abre el archivo HTML en tu navegador web para ver el mapa interactivo.")
            
            # Mostrar información
            print(f"\nInformación del mapa:")
            print(f"  - Parroquia: {NOMBRE_PARROQUIA}")
            print(f"  - Provincia: {NOMBRE_PROVINCIA}")
            print(f"  - Archivo GeoJSON usado: {ruta_geojson_provincia}")
            print(f"  - Número de polígonos de parroquia: {len(parroquia_encontrada)}")
            print(f"  - Número de regiones UMTS: {len(gdf_umts)}")
            print(f"  - Niveles de cobertura:")
            for idx, row in gdf_umts.iterrows():
                level = row['Float']
                if level == -85.0:
                    print(f"    * Alta (-85 dBm): Verde intenso")
                elif level == -95.0:
                    print(f"    * Media (-95 dBm): Amarillo pastel")
                elif level == -105.0:
                    print(f"    * Baja (-105 dBm): Rojo pastel")
            
            if intersecciones:
                print(f"  - Intersecciones encontradas: {len(intersecciones)}")
                print(f"    * Mostradas por separado: Rojo intenso")
                if lineas_conexion:
                    print(f"    * Líneas de conexión: {len(lineas_conexion)} (moradas)")
                    print(f"    * Geometría unificada: Naranja (exportada a KMZ)")
                else:
                    print(f"    * No se pudieron crear líneas de conexión")
            else:
                print(f"  - No se encontraron intersecciones")
            
        else:
            print(f"No se encontró la parroquia '{NOMBRE_PARROQUIA}' en la provincia '{NOMBRE_PROVINCIA}'")
            print("Verifica:")
            print(f"  - El nombre de la parroquia en la variable NOMBRE_PARROQUIA")
            print(f"  - El nombre de la provincia en la variable NOMBRE_PROVINCIA")
            print(f"  - Que el archivo GeoJSON existe: {ruta_geojson_provincia}")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Verifica que:")
        print("1. Las dependencias estén instaladas: pip install -r requirements.txt")
        print("2. Los archivos GeoJSON de provincias estén creados (ejecuta crear_geojson_provincias.py)")
        print("3. El archivo GeoJSON de la provincia especificada exista")
        print("4. Las rutas a los archivos UMTS sean correctas")
        print("5. Los archivos .shp, .shx, .dbf, .prj estén presentes")

if __name__ == "__main__":
    crear_mapa_parroquia_con_cobertura()
