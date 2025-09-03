#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear mapas interactivos de parroquias específicas con cobertura UMTS usando Folium
"""

import geopandas as gpd
import folium
from shapely.geometry import Polygon, MultiPolygon

def crear_mapa_parroquia_con_cobertura():
    """Crear mapa de una parroquia específica con cobertura UMTS"""
    # Configuración
    NOMBRE_PARROQUIA = "YANUNCAY"  # Cambiar aquí el nombre de la parroquia
    RUTA_PARROQUIAS = "LIMITE_PARROQUIAL_CONALI_CNE_2022/LIMITE_PARROQUIAL_CONALI_CNE_2022.shp"
    RUTA_UMTS = "AZUAY SHAPE/AZUAY_UMTS_JUN2023_v4_region.shp"
    
    print(f"Buscando parroquia: {NOMBRE_PARROQUIA}")
    
    try:
        # Cargar datos de parroquias
        print("Cargando límites parroquiales...")
        gdf_parroquias = gpd.read_file(RUTA_PARROQUIAS)
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
            
            print("Calculando intersecciones...")
            
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
                            # Crear un GeoDataFrame con la intersección
                            interseccion_gdf = gpd.GeoDataFrame(
                                geometry=[interseccion],
                                crs=parroquia_encontrada.crs
                            )
                            
                            # Agregar la intersección al mapa con color rojo intenso
                            folium.GeoJson(
                                interseccion_gdf,
                                name=f'Intersección {NOMBRE_PARROQUIA} - Cobertura Alta',
                                style_function=lambda feature: {
                                    'fillColor': '#FF0000',  # Rojo intenso
                                    'color': '#000000',      # Borde negro
                                    'weight': 3,             # Grosor del borde mayor
                                    'fillOpacity': 0.8       # Transparencia menor
                                },
                                tooltip=f'Intersección: {NOMBRE_PARROQUIA} + Cobertura Alta'
                            ).add_to(mapa)
                            
                            intersecciones.append(interseccion)
                            print(f"✅ Intersección encontrada y agregada al mapa")
                        else:
                            print(f"ℹ️ No hay intersección entre {NOMBRE_PARROQUIA} y la zona de cobertura alta")
                            
                    except Exception as e:
                        print(f"⚠️ Error al calcular intersección: {e}")
            
            # Agregar controles de capas
            folium.LayerControl().add_to(mapa)
            
            # Agregar leyenda de colores actualizada
            legend_html = '''
            <div style="position: fixed; 
                        bottom: 50px; left: 50px; width: 220px; height: auto; 
                        background-color: white; border:2px solid grey; z-index:9999; 
                        font-size:14px; padding: 10px">
            <p><b>Leyenda del Mapa</b></p>
            <p><i class="fa fa-square" style="color:#00FF00"></i> Cobertura Alta (-85 dBm)</p>
            <p><i class="fa fa-square" style="color:#FFFF99"></i> Cobertura Media (-95 dBm)</p>
            <p><i class="fa fa-square" style="color:#FFB3B3"></i> Cobertura Baja (-105 dBm)</p>
            <p><i class="fa fa-square" style="color:blue"></i> Parroquia</p>
            <p><i class="fa fa-square" style="color:#FF0000"></i> Intersección (Parroquia + Cobertura Alta)</p>
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
                print(f"    * Parroquia + Cobertura Alta: Rojo intenso")
            else:
                print(f"  - No se encontraron intersecciones")
            
        else:
            print(f"No se encontró la parroquia '{NOMBRE_PARROQUIA}'")
            print("Verifica el nombre de la parroquia en la variable NOMBRE_PARROQUIA")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Verifica que:")
        print("1. Las dependencias estén instaladas: pip install -r requirements.txt")
        print("2. Las rutas a los shapefiles sean correctas")
        print("3. Los archivos .shp, .shx, .dbf, .prj estén presentes")

if __name__ == "__main__":
    crear_mapa_parroquia_con_cobertura()
