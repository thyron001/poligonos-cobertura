import geopandas as gpd
import folium
import json
from shapely.geometry import mapping

def analizar_niveles_cobertura(gdf):
    """
    Analiza los niveles de cobertura en el GeoDataFrame
    """
    print("\n=== ANÁLISIS DE NIVELES DE COBERTURA ===")
    
    # Analizar cada columna relevante
    columnas_analizar = ['LEGEND', 'THRESHOLD', 'COLOR', 'Prediction']
    
    for columna in columnas_analizar:
        if columna in gdf.columns:
            print(f"\n--- Columna: {columna} ---")
            valores_unicos = gdf[columna].unique()
            print(f"Valores únicos: {valores_unicos}")
            
            conteo = gdf[columna].value_counts()
            for valor, count in conteo.items():
                print(f"  {valor}: {count} registros")
    
    return gdf

def obtener_color_por_nivel(feature):
    """
    Asigna colores según el nivel de cobertura usando los valores RGB del archivo SHP
    """
    # Obtener las propiedades del feature
    props = feature.get('properties', {})
    color_rgb = props.get('COLOR', '')
    threshold = props.get('THRESHOLD', '')
    
    # Convertir RGB string a color hexadecimal
    def rgb_to_hex(rgb_string):
        try:
            # El formato es "255 0 0" o similar
            rgb_values = rgb_string.strip().split()
            if len(rgb_values) == 3:
                r, g, b = [int(x) for x in rgb_values]
                return f"#{r:02x}{g:02x}{b:02x}"
        except:
            pass
        return '#3388ff'  # Color por defecto
    
    # Usar el color RGB del archivo
    color = rgb_to_hex(color_rgb)
    
    # Determinar el nivel basado en el threshold para el popup
    nivel_texto = ""
    if threshold == -85:
        nivel_texto = "Excelente (≥-85 dBm)"
    elif threshold == -95:
        nivel_texto = "Buena (≥-95 dBm)"
    elif threshold == -105:
        nivel_texto = "Básica (≥-105 dBm)"
    
    return {
        'fillColor': color,
        'color': '#000000',
        'weight': 2,
        'fillOpacity': 0.7,
    }

def crear_mapa_azuay_con_niveles():
    """
    Crea un mapa HTML que muestra los diferentes niveles de cobertura GSM de Azuay
    """
    # Ruta al archivo SHP
    shp_path = "AZUAY SHAPE/1. Azuay Cobertura GSM Semestre I 2025.shp"
    
    try:
        # Leer el archivo SHP
        print("Leyendo archivo SHP de Azuay...")
        gdf = gpd.read_file(shp_path)
        
        print(f"Archivo cargado exitosamente:")
        print(f"- Número de registros: {len(gdf)}")
        print(f"- Columnas: {list(gdf.columns)}")
        print(f"- Sistema de coordenadas: {gdf.crs}")
        
        # Analizar los niveles de cobertura
        gdf = analizar_niveles_cobertura(gdf)
        
        # Convertir a WGS84 si es necesario
        if gdf.crs != 'EPSG:4326':
            print("\nConvirtiendo coordenadas a WGS84...")
            gdf = gdf.to_crs('EPSG:4326')
        
        # Calcular el centro del mapa
        bounds = gdf.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        
        # Crear mapa base
        print("\nCreando mapa con niveles de cobertura...")
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=8,  # Zoom más amplio para ver mejor los polígonos
            tiles='OpenStreetMap'
        )
        
        # Función para crear popup informativo
        def crear_popup(feature):
            props = feature.get('properties', {})
            legend = props.get('LEGEND', 'N/A')
            threshold = props.get('THRESHOLD', 'N/A')
            color_rgb = props.get('COLOR', 'N/A')
            
            # Determinar nivel de cobertura
            if threshold == -85:
                nivel = "Excelente"
            elif threshold == -95:
                nivel = "Buena"
            elif threshold == -105:
                nivel = "Básica"
            else:
                nivel = "Desconocido"
            
            popup_html = f"""
            <b>Cobertura GSM Azuay</b><br>
            <b>Nivel:</b> {nivel}<br>
            <b>Umbral:</b> {threshold} dBm<br>
            <b>Leyenda:</b> {legend}<br>
            <b>Color RGB:</b> {color_rgb}<br>
            <b>Semestre I 2025</b>
            """
            return folium.Popup(popup_html, parse_html=True)
        
        # Agregar capa de cobertura GSM con colores diferenciados
        print("Agregando capa GeoJSON al mapa...")
        print(f"Número de features: {len(gdf)}")
        
        # Debug: imprimir información de cada feature
        for i, row in gdf.iterrows():
            print(f"Feature {i}: COLOR={row['COLOR']}, THRESHOLD={row['THRESHOLD']}")
        
        folium.GeoJson(
            gdf,
            style_function=obtener_color_por_nivel,
            popup=crear_popup,
            tooltip="Cobertura GSM - Haz clic para más detalles"
        ).add_to(m)
        
        # Ajustar los límites del mapa para mostrar todos los polígonos
        m.fit_bounds(gdf.total_bounds)
        
        # Agregar marcador en el centro
        folium.Marker(
            [center_lat, center_lon],
            popup="Centro de Azuay",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
        
        # Agregar leyenda con colores reales del archivo
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 250px; height: 140px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Niveles de Cobertura GSM</b></p>
        <p><i class="fa fa-square" style="color:#ff0000"></i> Excelente (≥-85 dBm)</p>
        <p><i class="fa fa-square" style="color:#0000ff"></i> Buena (≥-95 dBm)</p>
        <p><i class="fa fa-square" style="color:#00ff00"></i> Básica (≥-105 dBm)</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Guardar el mapa
        output_file = "mapa_azuay_niveles_cobertura.html"
        m.save(output_file)
        
        print(f"\nMapa guardado exitosamente como: {output_file}")
        print(f"Centro del mapa: Lat {center_lat:.4f}, Lon {center_lon:.4f}")
        
        return output_file
        
    except Exception as e:
        print(f"Error al procesar el archivo SHP: {str(e)}")
        return None

if __name__ == "__main__":
    archivo_html = crear_mapa_azuay_con_niveles()
    if archivo_html:
        print(f"\n¡Mapa creado exitosamente! Abre el archivo '{archivo_html}' en tu navegador para verlo.")
    else:
        print("Error al crear el mapa.")
