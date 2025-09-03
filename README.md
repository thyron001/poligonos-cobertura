# Visualizador de Mapas - Parroquias con Cobertura UMTS

Este proyecto contiene un script de Python para visualizar los límites de una parroquia específica junto con la cobertura UMTS de Azuay usando archivos shapefile del Consejo Nacional Electoral (CNE) de Ecuador y datos de cobertura móvil.

## Archivos del Proyecto

- `ejemplo_rapido_folium.py` - Script principal para crear mapas combinados
- `requirements.txt` - Dependencias de Python necesarias
- `LIMITE_PARROQUIAL_CONALI_CNE_2022/` - Carpeta con archivos shapefile de límites parroquiales
- `AZUAY SHAPE/` - Carpeta con archivos shapefile de cobertura UMTS de Azuay

## Instalación

1. **Instalar Python**: Asegúrate de tener Python 3.7 o superior instalado.

2. **Instalar dependencias**: Ejecuta el siguiente comando en tu terminal:
   ```bash
   pip install -r requirements.txt
   ```

## Uso del Script

### 1. Configurar la Parroquia

Abre el archivo `ejemplo_rapido_folium.py` y cambia la variable `NOMBRE_PARROQUIA`:

```python
NOMBRE_PARROQUIA = "YANUNCAY"  # Cambiar por el nombre de la parroquia deseada
```

### 2. Ejecutar el Script

En tu terminal, navega al directorio del proyecto y ejecuta:

```bash
py ejemplo_rapido_folium.py
```

### 3. Resultado

El script:
- Cargará los datos del shapefile de límites parroquiales
- Buscará la parroquia especificada
- Cargará los datos de cobertura UMTS de Azuay
- Calculará las intersecciones entre la parroquia y las zonas de cobertura alta
- Generará un mapa combinado con todas las capas
- Aplicará colores diferenciados según el nivel de cobertura UMTS
- Resaltará las intersecciones con color rojo intenso
- Guardará el archivo HTML automáticamente
- Mostrará información detallada en la consola

## Características del Script

- **Búsqueda específica**: Busca y grafica solo la parroquia especificada
- **Mapa combinado**: Siempre incluye la parroquia + cobertura UMTS
- **Colores diferenciados**: Cada nivel de cobertura UMTS tiene su color específico
- **Intersecciones resaltadas**: Las áreas donde la parroquia se superpone con cobertura alta se muestran en rojo intenso
- **Mapa interactivo**: Genera archivos HTML que puedes abrir en tu navegador web
- **Zoom automático**: Se centra automáticamente en la parroquia seleccionada
- **Popups informativos**: Muestra información detallada al hacer clic
- **Controles de capas**: Puedes activar/desactivar la parroquia, cada nivel de cobertura e intersecciones
- **Leyenda integrada**: Incluye una leyenda explicativa de todos los colores
- **Manejo de errores**: Proporciona mensajes claros si algo falla
- **Exportación web**: Guarda automáticamente el mapa como archivo HTML

## Esquema de Colores del Mapa

El script aplica automáticamente colores diferenciados según el nivel de cobertura y las intersecciones:

| Elemento | Color | Descripción |
|----------|-------|-------------|
| **Parroquia** | 🔵 Azul | Límites administrativos de la parroquia seleccionada |
| **Cobertura Alta** | 🟢 Verde intenso | Excelente señal (-85 dBm), máxima cobertura |
| **Cobertura Media** | 🟡 Amarillo pastel | Buena señal (-95 dBm), cobertura moderada |
| **Cobertura Baja** | 🔴 Rojo pastel | Señal débil (-105 dBm), cobertura limitada |
| **Intersección** | 🔴 Rojo intenso | Área donde la parroquia se superpone con cobertura alta |

### Colores Utilizados:
- **Azul** (`blue`): Para la parroquia seleccionada
- **Verde intenso** (`#00FF00`): Para cobertura alta (-85 dBm)
- **Amarillo pastel** (`#FFFF99`): Para cobertura media (-95 dBm)  
- **Rojo pastel** (`#FFB3B3`): Para cobertura baja (-105 dBm)
- **Rojo intenso** (`#FF0000`): Para intersecciones (parroquia + cobertura alta)

## Funcionalidad de Intersecciones

### ¿Qué son las Intersecciones?
Las intersecciones son las áreas geográficas donde la parroquia seleccionada se superpone con las zonas de cobertura alta (-85 dBm). Estas áreas son especialmente importantes porque:

- **Indican la mejor cobertura** dentro de la parroquia
- **Permiten identificar** dónde los habitantes tendrán mejor servicio móvil
- **Ayudan en la planificación** de infraestructura y servicios
- **Proporcionan información visual** clara sobre la calidad de cobertura

### Cálculo Automático:
El script calcula automáticamente estas intersecciones usando operaciones geométricas:
1. Identifica las zonas de cobertura alta (-85 dBm)
2. Calcula la intersección geométrica con la parroquia
3. Visualiza el resultado en rojo intenso
4. Permite activar/desactivar esta capa independientemente

## Campos de Búsqueda Soportados

### Límites Parroquiales:
- `CODPRO`, `PROVINCIA`, `CANTON`, `CODPAR`, `PARROQUIA`, `ESTADO`

### Cobertura UMTS:
- `Float`: Nivel de señal en dBm (determina el color)
- `String`: Información adicional (si está disponible)

## Datos Disponibles

### Límites Parroquiales (CNE 2022):
- **Total de registros**: 1,236
- **Parroquias únicas**: 1,081
- **Cantones únicos**: 221
- **Provincias únicas**: 25

### Cobertura UMTS Azuay (Junio 2023):
- **Total de regiones**: 3
- **Niveles de cobertura**: Alta (-85 dBm), Media (-95 dBm), Baja (-105 dBm)
- **Información técnica**: Valores de señal en decibelios por miliwatt (dBm)
- **Útil para**: Análisis de infraestructura de telecomunicaciones

## Parroquias Disponibles

### Cantón Cuenca (Provincia Azuay):
- BAÑOS, CUMBE, CHAUCHA/ANGAS, CHECA JIDCAY, CHIQUINTAD
- LLACAO, MOLLETURO, MULTI/NULTI, OCTAVIO CORDERO PALACIOS
- PACCHA, QUINGEO, RICAURTE, SAN JOAQUIN, SANTA ANA
- SAYAUSI, SIDCAY, SININCAY, TARQUI, TURI, VALLE
- VICTORIA DEL PORTETE, YANUNCAY, EL BATAN, SUCRE
- HUAYNACAPAC, SAN SEBASTIAN, RAMIREZ DAVALOS, SAGRARIO
- SAN BLAS, CAÑARIBAMBA, MONAY, TOTORACOCHA, EL VECINO
- BELLAVISTA, HERMANO MIGUEL, MACHANGARA

## Personalización

### Cambiar Parroquia:
```python
NOMBRE_PARROQUIA = "TU_PARROQUIA_AQUI"
```

### Cambiar Rutas de Shapefiles:
```python
# Para límites parroquiales
RUTA_PARROQUIAS = "ruta/a/tu/archivo_parroquias.shp"

# Para cobertura UMTS
RUTA_UMTS = "ruta/a/tu/archivo_cobertura.shp"
```

### Cambiar Colores de Cobertura:
```python
# En la función get_color_by_coverage()
if coverage_level == -85.0:  # Nivel alto
    return '#00FF00'  # Verde intenso
elif coverage_level == -95.0:  # Nivel medio
    return '#FFFF99'  # Amarillo pastel
elif coverage_level == -105.0:  # Nivel bajo
    return '#FFB3B3'  # Rojo pastel
```

### Cambiar Color de Intersecciones:
```python
# En el estilo de la intersección
style_function=lambda feature: {
    'fillColor': '#FF0000',  # Rojo intenso para intersecciones
    'color': '#000000',      # Borde negro
    'weight': 3,             # Grosor del borde mayor
    'fillOpacity': 0.8       # Transparencia menor
}
```

### Cambiar Estilos de Visualización:
```python
# Estilo de la parroquia
style_function=lambda feature: {
    'fillColor': 'blue',     # Color de relleno (azul)
    'color': '#000000',      # Color del borde (negro)
    'weight': 2,             # Grosor del borde
    'fillOpacity': 0.7       # Transparencia
}

# Estilo de la cobertura UMTS
style_function=lambda feature, level=coverage_level: {
    'fillColor': get_color_by_coverage({'properties': {'Float': level}}),
    'color': '#000000',      # Color del borde (negro)
    'weight': 1,             # Grosor del borde
    'fillOpacity': 0.6       # Transparencia
}
```

## Solución de Problemas

### Error: "No se encontró la parroquia especificada"

1. Verifica que el nombre de la parroquia esté escrito correctamente
2. El script mostrará los campos disponibles para ayudarte
3. Puedes usar coincidencias parciales (el script las detectará automáticamente)

### Error: "No se pudo cargar el shapefile"

1. Verifica que las rutas a los archivos .shp sean correctas
2. Asegúrate de que todos los archivos del shapefile estén presentes (.shp, .shx, .dbf, .prj)
3. Verifica que tengas permisos de lectura en las carpetas

### Error al Calcular Intersecciones

Si hay problemas con el cálculo de intersecciones:

1. Verifica que las geometrías de los shapefiles sean válidas
2. Asegúrate de que ambos datasets tengan el mismo sistema de coordenadas
3. El script mostrará mensajes informativos sobre el proceso

### Error de Dependencias

Si tienes problemas con las bibliotecas:

```bash
# Actualizar pip
python -m pip install --upgrade pip

# Instalar dependencias una por una
pip install geopandas
pip install folium
pip install shapely
pip install fiona
pip install pyproj
```

## Formato de los Datos

Los archivos shapefile contienen:
- **Geometría**: Polígonos que definen los límites o regiones
- **Atributos**: Información descriptiva de cada elemento
- **Sistema de coordenadas**: Definido en el archivo .prj

## Casos de Uso

### Para Administradores Públicos:
- Visualizar límites administrativos de parroquias específicas
- Analizar cobertura de servicios en áreas específicas
- Planificar infraestructura y servicios por parroquia
- Identificar áreas con necesidades de mejora en telecomunicaciones
- **Priorizar inversiones** en zonas con mejor cobertura

### Para Analistas de Telecomunicaciones:
- Estudiar cobertura de red en parroquias específicas
- Comparar cobertura con límites administrativos
- Identificar áreas con necesidades de infraestructura
- Analizar la calidad de señal por región geográfica
- **Evaluar la eficiencia** de la cobertura en áreas específicas

### Para Investigadores:
- Análisis geográfico de parroquias específicas
- Estudios de cobertura de servicios por área
- Investigación en geografía y telecomunicaciones
- Análisis de patrones de cobertura móvil
- **Estudios de impacto** de la infraestructura de telecomunicaciones

## Ejemplos de Uso

### Parroquia YANUNCAY:
```python
NOMBRE_PARROQUIA = "YANUNCAY"
```
Resultado: `mapa_parroquia_yanuncay_con_cobertura.html`
- ✅ Intersección encontrada: Parroquia + Cobertura Alta

### Parroquia BAÑOS:
```python
NOMBRE_PARROQUIA = "BAÑOS"
```
Resultado: `mapa_parroquia_baños_con_cobertura.html`

### Parroquia BATAN:
```python
NOMBRE_PARROQUIA = "BATAN"
```
Resultado: `mapa_parroquia_batan_con_cobertura.html`

## Estructura del Mapa Generado

El mapa HTML incluye:
1. **Capa de Parroquia**: Muestra solo la parroquia seleccionada en azul
2. **Capa de Cobertura Alta**: Verde intenso para señal -85 dBm
3. **Capa de Cobertura Media**: Amarillo pastel para señal -95 dBm
4. **Capa de Cobertura Baja**: Rojo pastel para señal -105 dBm
5. **Capa de Intersección**: Rojo intenso para áreas de parroquia + cobertura alta
6. **Controles de Capas**: Permite activar/desactivar cada capa individualmente
7. **Leyenda Integrada**: Explica el significado de todos los colores
8. **Popups Informativos**: Muestra datos al hacer clic en cada elemento

## Interpretación de los Valores dBm

Los valores de cobertura UMTS se miden en decibelios por miliwatt (dBm):

- **-85 dBm**: Excelente señal, máxima velocidad de datos
- **-95 dBm**: Buena señal, velocidad de datos moderada
- **-105 dBm**: Señal débil, velocidad de datos limitada

**Nota**: Los valores más negativos indican señal más débil.

## Análisis de Intersecciones

### ¿Por qué son importantes las intersecciones?

1. **Calidad de Servicio**: Las áreas de intersección tienen la mejor cobertura posible
2. **Planificación Urbana**: Ayudan a identificar zonas con mejor infraestructura
3. **Desarrollo Económico**: Las áreas con mejor cobertura suelen ser más atractivas para inversiones
4. **Servicios Públicos**: Permiten optimizar la ubicación de servicios que requieren conectividad

### Interpretación Visual:
- **Rojo intenso**: Zonas con excelente cobertura dentro de la parroquia
- **Verde + Azul**: Zonas de cobertura alta fuera de la parroquia
- **Solo Azul**: Áreas de la parroquia sin cobertura alta

## Licencia

Este proyecto está disponible para uso educativo y de investigación.

---

**Nota**: Este script está diseñado específicamente para trabajar con los archivos de límites parroquiales del CNE de Ecuador y datos de cobertura UMTS de Azuay. Para otros datasets, pueden ser necesarias modificaciones.
