#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear mapas interactivos de parroquias o cobertura UMTS usando Folium
"""

import geopandas as gpd
import folium

def crear_mapa_parroquia():
    """Crear mapa de una parroquia específica"""
    # Configuración
    NOMBRE_PARROQUIA = "YANUNCAY"  # Cambiar aquí el nombre de la parroquia
    RUTA_SHAPEFILE = "LIMITE_PARROQUIAL_CONALI_CNE_2022/LIMITE_PARROQUIAL_CONALI_CNE_2022.shp"
    
    print(f"Buscando parroquia: {NOMBRE_PARROQUIA}")
    
    try:
        # Cargar datos
        print("Cargando shapefile de límites parroquiales...")
        gdf = gpd.read_file(RUTA_SHAPEFILE)
        print(f"Datos cargados. Total de registros: {len(gdf)}")
        
        # Buscar la parroquia
        parroquia_encontrada = None
        
        for campo in gdf.columns:
            if gdf[campo].dtype == 'object':
                print(f"Buscando en campo: {campo}")
                coincidencias = gdf[gdf[campo].str.upper().str.contains(NOMBRE_PARROQUIA.upper(), na=False)]
                if len(coincidencias) > 0:
                    parroquia_encontrada = coincidencias
                    print(f"¡Encontrada! {len(coincidencias)} coincidencias en '{campo}'")
                    break
        
        if parroquia_encontrada is not None:
            print("Creando mapa interactivo...")
            
            # Crear mapa centrado en Ecuador
            mapa = folium.Map(
                location=[-2.0, -78.0],
                zoom_start=7,
                tiles='OpenStreetMap'
            )
            
            # Agregar la parroquia de la manera más simple posible
            folium.GeoJson(
                parroquia_encontrada,
                name=f'Parroquia {NOMBRE_PARROQUIA}',
                popup=folium.GeoJsonPopup(
                    fields=['PARROQUIA', 'CANTON', 'PROVINCIA', 'ESTADO'],
                    aliases=['Parroquia', 'Cantón', 'Provincia', 'Estado'],
                    localize=True,
                    labels=True,
                    style="background-color: yellow;",
                )
            ).add_to(mapa)
            
            # Guardar mapa
            nombre_archivo = f"mapa_parroquia_{NOMBRE_PARROQUIA.lower().replace(' ', '_')}.html"
            mapa.save(nombre_archivo)
            print(f"✅ Mapa guardado: {nombre_archivo}")
            print("Abre el archivo HTML en tu navegador web para ver el mapa interactivo.")
            
        else:
            print(f"No se encontró la parroquia '{NOMBRE_PARROQUIA}'")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Verifica que:")
        print("1. Las dependencias estén instaladas: pip install -r requirements.txt")
        print("2. La ruta al shapefile sea correcta")
        print("3. Los archivos .shp, .shx, .dbf, .prj estén presentes")

def crear_mapa_cobertura_umts():
    """Crear mapa de cobertura UMTS de Azuay"""
    RUTA_SHAPEFILE = "AZUAY SHAPE/AZUAY_UMTS_JUN2023_v4_region.shp"
    
    print("Creando mapa de cobertura UMTS de Azuay...")
    
    try:
        # Cargar datos
        print("Cargando shapefile de cobertura UMTS...")
        gdf = gpd.read_file(RUTA_SHAPEFILE)
        print(f"Datos cargados. Total de registros: {len(gdf)}")
        print(f"Columnas disponibles: {list(gdf.columns)}")
        
        # Mostrar primeros registros para ver la estructura
        print("\nPrimeros registros:")
        print(gdf.head())
        
        # Crear mapa centrado en Azuay
        mapa = folium.Map(
            location=[-2.9, -79.0],  # Coordenadas aproximadas de Azuay
            zoom_start=9,
            tiles='OpenStreetMap'
        )
        
        # Agregar la cobertura UMTS
        folium.GeoJson(
            gdf,
            name='Cobertura UMTS Azuay',
            popup=folium.GeoJsonPopup(
                fields=[col for col in gdf.columns if col != 'geometry'],
                aliases=[col for col in gdf.columns if col != 'geometry'],
                localize=True,
                labels=True,
                style="background-color: orange;",
            )
        ).add_to(mapa)
        
        # Guardar mapa
        nombre_archivo = "mapa_cobertura_umts_azuay.html"
        mapa.save(nombre_archivo)
        print(f"✅ Mapa guardado: {nombre_archivo}")
        print("Abre el archivo HTML en tu navegador web para ver el mapa interactivo.")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Verifica que:")
        print("1. Las dependencias estén instaladas: pip install -r requirements.txt")
        print("2. La ruta al shapefile sea correcta")
        print("3. Los archivos .shp, .shx, .dbf, .prj estén presentes")

def crear_mapa_combinado():
    """Crear mapa combinado con parroquias y cobertura UMTS"""
    print("Creando mapa combinado...")
    
    try:
        # Cargar datos de parroquias
        print("Cargando límites parroquiales...")
        gdf_parroquias = gpd.read_file("LIMITE_PARROQUIAL_CONALI_CNE_2022/LIMITE_PARROQUIAL_CONALI_CNE_2022.shp")
        
        # Filtrar solo parroquias del cantón Cuenca
        parroquias_cuenca = gdf_parroquias[gdf_parroquias['CANTON'].str.upper() == 'CUENCA']
        print(f"Parroquias del cantón Cuenca: {len(parroquias_cuenca)}")
        
        # Cargar datos de cobertura UMTS
        print("Cargando cobertura UMTS...")
        gdf_umts = gpd.read_file("AZUAY SHAPE/AZUAY_UMTS_JUN2023_v4_region.shp")
        print(f"Regiones UMTS: {len(gdf_umts)}")
        
        # Crear mapa centrado en Cuenca
        mapa = folium.Map(
            location=[-2.9, -79.0],
            zoom_start=10,
            tiles='OpenStreetMap'
        )
        
        # Agregar parroquias de Cuenca
        folium.GeoJson(
            parroquias_cuenca,
            name='Parroquias Cuenca',
            popup=folium.GeoJsonPopup(
                fields=['PARROQUIA', 'ESTADO'],
                aliases=['Parroquia', 'Estado'],
                localize=True,
                labels=True,
                style="background-color: blue;",
            )
        ).add_to(mapa)
        
        # Agregar cobertura UMTS
        folium.GeoJson(
            gdf_umts,
            name='Cobertura UMTS',
            popup=folium.GeoJsonPopup(
                fields=[col for col in gdf_umts.columns if col != 'geometry'],
                aliases=[col for col in gdf_umts.columns if col != 'geometry'],
                localize=True,
                labels=True,
                style="background-color: red;",
            )
        ).add_to(mapa)
        
        # Agregar controles de capas
        folium.LayerControl().add_to(mapa)
        
        # Guardar mapa
        nombre_archivo = "mapa_combinado_cuenca_umts.html"
        mapa.save(nombre_archivo)
        print(f"✅ Mapa combinado guardado: {nombre_archivo}")
        print("Abre el archivo HTML en tu navegador web para ver el mapa interactivo.")
        
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Función principal con menú de opciones"""
    print("=" * 60)
    print("VISUALIZADOR DE MAPAS - PARROQUIAS Y COBERTURA UMTS")
    print("=" * 60)
    print("1. Crear mapa de parroquia específica")
    print("2. Crear mapa de cobertura UMTS de Azuay")
    print("3. Crear mapa combinado (parroquias + cobertura)")
    print("4. Salir")
    print("=" * 60)
    
    while True:
        try:
            opcion = input("\nElige una opción (1-4): ").strip()
            
            if opcion == "1":
                crear_mapa_parroquia()
                break
            elif opcion == "2":
                crear_mapa_cobertura_umts()
                break
            elif opcion == "3":
                crear_mapa_combinado()
                break
            elif opcion == "4":
                print("¡Hasta luego!")
                break
            else:
                print("Opción no válida. Por favor elige 1, 2, 3 o 4.")
                
        except KeyboardInterrupt:
            print("\n\n¡Hasta luego!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
