#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para generar intersecciones de 4 parroquias específicas con cobertura GSM
y crear archivos KMZ individuales + mapa HTML unificado
"""

import sys
import os
# Configurar codificación UTF-8 para Windows
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

import geopandas as gpd
import folium
from shapely.geometry import Polygon, MultiPolygon, LineString
from shapely.ops import unary_union
import numpy as np
import zipfile

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
        print(f"Error al exportar a KMZ: {e}")
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
            print(f"  La geometría unificada está vacía, usando solo las intersecciones")
            geometria_unificada = unary_union(intersecciones)
        
        print(f"  Geometría unificada creada exitosamente")
        return geometria_unificada, lineas_conexion
        
    except Exception as e:
        print(f"Error al crear geometría unificada: {e}")
        # Si falla, intentar unir solo las intersecciones
        try:
            print(f"  Intentando unir solo las intersecciones...")
            geometria_simple = unary_union(intersecciones)
            return geometria_simple, []
        except Exception as e2:
            print(f"  Error al unir intersecciones: {e2}")
            return None, []

def procesar_parroquia(nombre_parroquia, gdf_parroquias, gdf_umts, mapa):
    """Procesar una parroquia específica y generar su intersección"""
    print(f"\n{'='*60}")
    print(f"PROCESANDO: {nombre_parroquia}")
    print(f"{'='*60}")
    
    # Buscar la parroquia específica
    parroquia_encontrada = None
    
    for campo in gdf_parroquias.columns:
        if gdf_parroquias[campo].dtype == 'object':
            coincidencias = gdf_parroquias[gdf_parroquias[campo].str.upper().str.contains(nombre_parroquia.upper(), na=False)]
            if len(coincidencias) > 0:
                parroquia_encontrada = coincidencias
                print(f"Encontrada en campo '{campo}': {coincidencias[campo].iloc[0]}")
                break
    
    if parroquia_encontrada is None:
        print(f"❌ No se encontró la parroquia: {nombre_parroquia}")
        return None
    
    # Agregar la parroquia al mapa
    folium.GeoJson(
        parroquia_encontrada,
        name=f'Parroquia {nombre_parroquia}',
        style_function=lambda feature: {
            'fillColor': 'blue',
            'color': '#000000',
            'weight': 0.5,
            'fillOpacity': 0.3
        }
    ).add_to(mapa)
    
    # Función para determinar el color según el nivel de cobertura
    def get_color_by_coverage(feature):
        coverage_level = feature['properties']['THRESHOLD']
        if coverage_level == -85:  # Nivel alto
            return '#00FF00'  # Verde intenso
        elif coverage_level == -95:  # Nivel medio
            return '#FFFF99'  # Amarillo pastel
        elif coverage_level == -105:  # Nivel bajo
            return '#FFB3B3'  # Rojo pastel
        else:
            return '#808080'  # Gris por defecto
    
    # Lista para almacenar las intersecciones
    intersecciones = []
    
    # Procesar cada nivel de cobertura UMTS
    for idx, row in gdf_umts.iterrows():
        coverage_level = row['THRESHOLD']
        
        # Crear un GeoDataFrame con solo esta fila
        single_region = gdf_umts.iloc[[idx]]
        
        # Agregar la capa de cobertura al mapa
        folium.GeoJson(
            single_region,
            name=f'Cobertura {coverage_level} dBm',
            style_function=lambda feature, level=coverage_level: {
                'fillColor': get_color_by_coverage({'properties': {'THRESHOLD': level}}),
                'color': '#000000',
                'weight': 0.3,
                'fillOpacity': 0.4
            }
        ).add_to(mapa)
        
        # Si es cobertura alta, calcular intersección con la parroquia
        if coverage_level == -85:
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
                    print(f"ℹ️ No hay intersección entre {nombre_parroquia} y la zona de cobertura alta")
                    
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
                    print(f"  Geometría unificada creada exitosamente")
                except Exception as e:
                    print(f"  Error al crear geometría unificada: {e}")
                    geometria_unificada = None
            
            # Los caminos ahora forman parte de la geometría unificada, no se muestran por separado
            print(f"Los caminos se han integrado en la geometría unificada")
            
            # Mostrar cada intersección por separado (para visualización)
            for i, interseccion in enumerate(intersecciones):
                interseccion_gdf = gpd.GeoDataFrame(
                    geometry=[interseccion],
                    crs=parroquia_encontrada.crs
                )
                
                folium.GeoJson(
                    interseccion_gdf,
                    name=f'Intersección {nombre_parroquia} - Cobertura Alta',
                    style_function=lambda feature: {
                        'fillColor': '#FF0000',  # Rojo intenso
                        'color': '#000000',
                        'weight': 0.5,
                        'fillOpacity': 0.8
                    }
                ).add_to(mapa)
            
            # Agregar la geometría unificada como capa separada
            if geometria_unificada:
                geometria_unificada_gdf = gpd.GeoDataFrame(
                    geometry=[geometria_unificada],
                    crs=parroquia_encontrada.crs
                )
                
                # Crear nombre del archivo KMZ
                nombre_parroquia_limpio = nombre_parroquia.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '').upper()
                nombre_kmz = f"{nombre_parroquia_limpio}_MOVISTAR_2025_2G.kmz"
                
                # Exportar la geometría unificada a KMZ
                if exportar_a_kmz(geometria_unificada_gdf, nombre_kmz):
                    print(f"✅ Geometría unificada exportada: {nombre_kmz}")
                else:
                    print(f"❌ Error al exportar geometría unificada a KMZ")
                
                folium.GeoJson(
                    geometria_unificada_gdf,
                    name=f'Geometría Unificada {nombre_parroquia}',
                    style_function=lambda feature: {
                        'fillColor': '#FF6600',  # Naranja
                        'color': '#800080',      # Borde morado
                        'weight': 0.5,
                        'fillOpacity': 0.4
                    }
                ).add_to(mapa)
                
                print(f"✅ Geometría unificada creada y agregada al mapa")
                
                return {
                    'parroquia': nombre_parroquia,
                    'intersecciones': len(intersecciones),
                    'geometria_unificada': geometria_unificada,
                    'archivo_kmz': nombre_kmz
                }
        
        except Exception as e:
            print(f"⚠️ Error al procesar intersecciones: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"ℹ️ No se encontraron intersecciones para {nombre_parroquia}")
        return None

def crear_mapa_4_parroquias():
    """Crear mapa con las 4 parroquias específicas"""
    
    # Parroquias a procesar
    parroquias = [
        "BULAN / J. VICTOR IZQUIERDO",
        "TOMEBAMBA", 
        "ABDON CALDERON / LA UNION",
        "SEVILLA DE ORO"
    ]
    
    # Rutas de archivos
    ruta_geojson = "geojson_provincias/azuay.geojson"
    ruta_umts = "AZUAY SHAPE/1. Azuay Cobertura GSM Semestre I 2025.shp"
    
    print("Cargando datos...")
    
    try:
        # Cargar datos de parroquias
        gdf_parroquias = gpd.read_file(ruta_geojson)
        print(f"Datos de parroquias cargados. Total: {len(gdf_parroquias)}")
        
        # Cargar datos de cobertura UMTS
        gdf_umts = gpd.read_file(ruta_umts)
        print(f"Datos de cobertura UMTS cargados. Total: {len(gdf_umts)}")
        
        # Crear mapa centrado en Ecuador
        mapa = folium.Map(
            location=[-2.0, -78.0],
            zoom_start=8,
            tiles='OpenStreetMap'
        )
        
        # Procesar cada parroquia
        resultados = []
        for parroquia in parroquias:
            resultado = procesar_parroquia(parroquia, gdf_parroquias, gdf_umts, mapa)
            if resultado:
                resultados.append(resultado)
        
        # Agregar controles de capas
        folium.LayerControl().add_to(mapa)
        
        # Agregar leyenda
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 300px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Leyenda del Mapa - 4 Parroquias</b></p>
        <p><i class="fa fa-square" style="color:#00FF00"></i> Cobertura Alta (-85 dBm)</p>
        <p><i class="fa fa-square" style="color:#FFFF99"></i> Cobertura Media (-95 dBm)</p>
        <p><i class="fa fa-square" style="color:#FFB3B3"></i> Cobertura Baja (-105 dBm)</p>
        <p><i class="fa fa-square" style="color:blue"></i> Parroquias</p>
        <p><i class="fa fa-square" style="color:#FF0000"></i> Intersecciones (Parroquia + Cobertura Alta)</p>
        <p><i class="fa fa-square" style="color:#FF6600"></i> Geometría Unificada (Exportada a KMZ)</p>
        </div>
        '''
        mapa.get_root().html.add_child(folium.Element(legend_html))
        
        # Guardar mapa
        nombre_archivo = "mapa_4_parroquias_intersecciones.html"
        mapa.save(nombre_archivo)
        print(f"\n✅ Mapa guardado: {nombre_archivo}")
        
        # Resumen de resultados
        print(f"\n{'='*60}")
        print("RESUMEN DE RESULTADOS")
        print(f"{'='*60}")
        print(f"Parroquias procesadas: {len(resultados)}")
        for resultado in resultados:
            print(f"  - {resultado['parroquia']}: {resultado['intersecciones']} intersecciones → {resultado['archivo_kmz']}")
        
        print(f"\nArchivos generados:")
        print(f"  - {nombre_archivo} (mapa HTML unificado)")
        for resultado in resultados:
            print(f"  - {resultado['archivo_kmz']} (geometría unificada)")
        
        return resultados
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    resultados = crear_mapa_4_parroquias()
    if resultados:
        print(f"\n¡Proceso completado exitosamente!")
    else:
        print("Error en el proceso.")
