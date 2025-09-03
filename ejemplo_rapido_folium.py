#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear mapas interactivos de parroquias específicas con cobertura UMTS usando Folium
"""

import geopandas as gpd
import folium

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
            
            print("Creando mapa interactivo...")
            
            # Crear mapa centrado en Ecuador
            mapa = folium.Map(
                location=[-2.0, -78.0],
                zoom_start=7,
                tiles='OpenStreetMap'
            )
            
            # Agregar la parroquia específica de la manera más simple
            folium.GeoJson(
                parroquia_encontrada,
                name=f'Parroquia {NOMBRE_PARROQUIA}'
            ).add_to(mapa)
            
            # Agregar cobertura UMTS de la manera más simple
            folium.GeoJson(
                gdf_umts,
                name='Cobertura UMTS Azuay'
            ).add_to(mapa)
            
            # Agregar controles de capas
            folium.LayerControl().add_to(mapa)
            
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
