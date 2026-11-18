# PostSIMA

Sistema modular en Python basado en **Arquitectura Hexagonal (Ports and Adapters)** diseñado para la extracción, normalización, matching probabilístico, consolidación geográfica y persistencia de infraestructura de recarga de vehículos eléctricos (VE).

PostSIMA procesa registros provenientes de múltiples redes y proveedores (PlugShare, Tesla Destination Charger y Tesla Supercharger), resolviendo discrepancias sintácticas, unificando identidades físicas mediante reglas deterministas y métricas espaciales, enriqueciendo la ubicación con polígonos cartográficos oficiales del INEGI y exportando un padrón estandarizado en formato tabular para análisis y reportes.

---

## Características Principales

* **Arquitectura Hexagonal:** Desacoplamiento estricto entre el modelo de dominio, los casos de uso y los adaptadores de infraestructura (HTTP, persistencia relacional, geoespacial y formatos de exportación).
* **Fuentes Soportadas:**
  * **PlugShare:** Extracción de infraestructura multired y especificaciones de conectores.
  * **Tesla Destination Charger:** Red de carga en destino (Nivel 2 / AC).
  * **Tesla Supercharger:** Red de carga rápida en corriente continua (Nivel 3 / DC).
* **Pipeline de Normalización:**
  * **Coordenadas y Geografía:** Validación de rangos en WGS84 ($\text{EPSG:4326}$) y precisión decimal homogénea.
  * **Texto y Códigos Postales:** Homogeneización de caracteres, eliminación de diacríticos y formato estándar de código postal mexicano de 5 dígitos.
  * **Teléfonos:** Limpieza y estructuración homogénea de números de contacto.
  * **Conectores Eléctricos:** Mapeo de variantes de catálogo a una taxonomía técnica estandarizada (`CCS1`, `CCS2`, `CHAdeMO`, `GB/T (DC)`, `GB/T (AC)`, `J1772`, `NACS`, `Tesla Destination`, `Tesla Supercharger`, tomas industriales NEMA y Wall Outlets).
* **Motor de Matching y Consolidación:**
  * **Regla estricta de fuente única:** Dos registros con distinto identificador originados por el mismo proveedor nunca se consolidan entre sí.
  * **Indexación y Ponderación:** Generación de candidatos mediante rejilla espacial e índices de texto, con evaluación multicriterio basada en distancia geodésica ($85\%$), dirección ($10\%$), nombre ($5\%$) y código postal ($5\%$).
  * **Umbrales Deterministas:** Consolidación automática ante similitud $\ge 0.80$, detección de duplicados potenciales para revisión entre $0.55$ y $0.80$, y creación de nuevas identidades ante puntajes inferiores a $0.55$.
* **Resolución Cartográfica Oficial:** Enriquecimiento automático de municipio y estado mediante intersección espacial de puntos contra polígonos simplificados del marco geoestadístico del INEGI.
* **Persistencia Aislada y Conmutable:** Soporte nativo para tres motores de almacenamiento independientes seleccionables por consola: **PostgreSQL**, **SQLite** y repositorio volátil en **Memoria**.
* **Reporte Operativo Automatizado:** Generación obligatoria del reporte tabular `report-ss.xlsx` con estructura estandarizada y desglose de hasta 5 tipos de conectores simultáneos.

---

## Arquitectura del Sistema

El flujo de procesamiento sigue una dirección unidireccional de dependencias hacia el núcleo del dominio:

```
[ CLI / Presentation ]
         │
         ▼
[ Application Layer ] ──> (Normalización, Matching, Consolidación)
   │             │
   │             ▼
   │      [ Domain Model ] (Station [UUID], SourceRecord, Charger, Value Objects)
   │
   ▼ (Ports & Protocols)
[ Infrastructure Adapters ]
   ├─ Sources: PlugShareClient, TeslaClient (Destination & Supercharger)
   ├─ Persistence: SqlAlchemyStationRepository (PostgreSQL / SQLite) | InMemoryStationRepository
   ├─ Geographic: InegiGeographicResolver (GeoPackage / EPSG:4326)
   └─ Exporters: ExcelReportLayoutExporter
```

---

## Modelo de Dominio y Persistencia

### Estructura de Entidades
* **`Station`:** Entidad raíz del agregado. Posee un identificador único global inmutable (`station_id: UUID`), atributos canónicos consolidados (`name`, `address`, `postal_code`, `telephone`, `coordinates`, `municipality`, `state`, `price`), la lista de registros de origen que la respaldan (`source_records`) y la relación consolidada de cargadores (`chargers`).
* **`SourceRecord`:** Evidencia histórica y técnica provista por un proveedor específico. Su identidad está determinada por la tupla compuesta `(source, external_id)`. Preserva los datos crudos extraídos de la fuente, incluyendo la cadena tarifaria (`price`).
* **`Charger`:** Especificación física del conector, conformada por `connector_type` (normalizado), `power_kw` (potencia en kilovatios) y `quantity` (número de puertos físicos idénticos).
* **Objetos de Valor:** `Coordinates` (latitud y longitud validadas) y `PostalCode` (cadena de 5 dígitos).

### Esquema Relacional de Base de Datos
Al seleccionar persistencia en base de datos (`postgres` o `sqlite`), el sistema inicializa automáticamente las siguientes tablas relacionales:

1. `stations`: Agregado principal indexado por `station_id` (UUID PK).
2. `source_records`: Registros fuente asociados vía FK a `stations`, con restricción única `UNIQUE(source, external_id)`.
3. `station_chargers`: Conectores consolidados pertenecientes a cada estación.
4. `source_record_chargers`: Conectores reportados por cada registro individual para trazabilidad y auditoría.

---

## Requisitos del Sistema

* **Python:** Versión 3.11 o superior.
* **Sistema Operativo:** Compatible con Linux (Debian, Ubuntu, Kali, RedHat) y Windows 10/11 (PowerShell).
* **Capa Cartográfica:** Archivo vectorial INEGI simplificado en formato GeoPackage (`Entidades_Estados_INEGI_Simplificado.gpkg`) ubicado en `data/reference/`.

### Instalación de Paquetes del Sistema

#### Linux (Debian / Ubuntu / Kali)
```bash
sudo apt update
sudo apt install -y python3-venv python3-pip

# Opcional si se utiliza el motor PostgreSQL local:
sudo apt install -y postgresql postgresql-contrib libpq-dev
```

#### Windows
* Python 3.11+ instalado desde [python.org](https://www.python.org/) marcando la casilla **"Add python.exe to PATH"**.
* Opcional: Servidor PostgreSQL local o remoto accesible por red.

---

## Instalación y Configuración

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/tu-usuario/postsima.git
   cd postsima
   ```

2. **Crear y activar el entorno virtual:**

   * En Linux/macOS:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

   * En Windows (PowerShell):
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```

3. **Instalar el paquete y dependencias:**
   ```bash
   pip install --upgrade pip
   pip install -e ".[test]"
   ```

4. **Variables de Entorno:**
   Cree un archivo `.env` en la raíz del proyecto basándose en las necesidades de autenticación de las APIs y de la base de datos:

   ```dotenv
    # Claves necesarias para acceso a información de las páginas
    PLUGSHARE_TOKEN="TOKEN"
    PLUGSHARE_AUTH="TOKEN"
    TESLA_COOKIE="TOKEN"

    # Credenciales para la base de datos
    POSTGRES_USER="postsima_user"
    POSTGRES_PASSWORD="tu_password_seguro"
    POSTGRES_HOST="localhost/192.168.0.1"
    POSTGRES_PORT="5432"
    POSTGRES_DB="postsima"

   # O alternativamente mediante URL directa:
   # POSTGRES_URL=postgresql+psycopg://postsima_user:password@localhost:5432/postsima
   ```
5. **Paso extra para creación de la base de datos en PostgreSQL:**
    Crea la base de datos, este es un ejemplo para Linux.
    ```bash
    sudo -u postgres psql -c "CREATE USER postsima_user WITH PASSWORD 'tu_password';"
    sudo -u postgres psql -c "CREATE DATABASE postsima OWNER postsima_user;"
   ```

---

## Uso de la Interfaz de Línea de Comandos (CLI)

El comando principal `postsima` ejecuta el ciclo completo: extracción de las fuentes, normalización, matching contra los registros existentes en el repositorio seleccionado, resolución municipal/estatal con INEGI y generación del reporte final.

### Sintaxis
```bash
postsima --source <fuente> --ids-file <ruta_al_archivo> [--repository <motor>]
```

### Argumentos
* `--source`: Proveedor a consultar. Opciones: `plugshare`, `destination_charger`, `supercharger` *(Requerido)*.
* `--ids-file`: Ruta al archivo `.txt` que contiene un identificador externo por línea *(Requerido)*.
* `--repository` (o `--repo`): Motor de almacenamiento a utilizar. Opciones:
  * `postgres`: Conecta al servidor PostgreSQL configurado en el archivo `.env` *(Opción predeterminada)*.
  * `sqlite`: Persiste y consulta localmente en el archivo `data/postsima.db`.
  * `memory`: Ejecución en memoria RAM volátil. No requiere servicios externos ni genera archivos de base de datos.

### Ejemplos de Ejecución

**Extracción desde PlugShare persistiendo en PostgreSQL:**
```bash
postsima --source plugshare --ids-file data/ids_plugshare.txt --repository postgres
```

**Extracción de Superchargers de Tesla utilizando SQLite local:**
```bash
postsima --source supercharger --ids-file data/ids_tesla_sc.txt --repository sqlite
```

**Ejecución de prueba en memoria (sin afectar bases de datos persistentes):**
```bash
postsima --source destination_charger --ids-file data/ids_tesla_dc.txt --repository memory
```

---

## Estructura del Reporte de Salida (`report-ss.xlsx`)

Independientemente del motor de persistencia utilizado, el sistema genera de forma predeterminada el archivo `output/report-ss.xlsx` con la totalidad de estaciones registradas en la base de datos seleccionada.

El reporte contiene una única hoja denominada `Estaciones` con exactamente 27 columnas ordenadas:

| Índice | Columna | Descripción |
| :---: | :--- | :--- |
| **1** | `id` | Identificador único de la estación consolidada (UUID v4). |
| **2** | `source` | Identificador numérico de la fuente primaria determinista (`1`: Tesla DC, `2`: Tesla SC, `4`: PlugShare). |
| **3** | `web_page` | Identificador externo del registro principal en la fuente original. |
| **4** | `station_name` | Nombre consolidado y normalizado de la estación. |
| **5** | `address` | Dirección física normalizada. |
| **6** | `cp` | Código postal estandarizado a 5 dígitos. |
| **7** | `town` | Municipio determinado por el resolvedor cartográfico de INEGI. |
| **8** | `state` | Estado determinado por el resolvedor cartográfico de INEGI. |
| **9** | `telephone` | Teléfono de contacto normalizado. |
| **10** | `latitude` | Latitud geográfica decimal en EPSG:4326. |
| **11** | `longitude` | Longitud geográfica decimal en EPSG:4326. |
| **12** | `price` | Precio de carga de estación. |
| **13** | `electrolineras_totales` | Sumatoria total de cargadores/conectores físicos disponibles. |
| **14–16** | `cargadores_1`, `tipo_1`, `potencia_1` | Cantidad, conector estandarizado y potencia en kW del primer tipo. |
| **17–19** | `cargadores_2`, `tipo_2`, `potencia_2` | Cantidad, conector estandarizado y potencia en kW del segundo tipo. |
| **20–22** | `cargadores_3`, `tipo_3`, `potencia_3` | Cantidad, conector estandarizado y potencia en kW del tercer tipo. |
| **23–25** | `cargadores_4`, `tipo_4`, `potencia_4` | Cantidad, conector estandarizado y potencia en kW del cuarto tipo. |
| **26–28** | `cargadores_5`, `tipo_5`, `potencia_5` | Cantidad, conector estandarizado y potencia en kW del quinto tipo. |

*Nota:* Si una estación física dispone de más de 5 tipos de conectores distintos, las columnas 13 a 28 exponen los 5 principales ordenados por tipo y potencia, manteniendo en `electrolineras_totales` la sumatoria íntegra y emitiendo una advertencia explícita en consola.

---

## Verificación y Pruebas Automatizadas

El proyecto cuenta con cobertura de pruebas unitarias automatizadas para los componentes de normalización, matching, consolidación, repositorios de base de datos y exportadores de reporte.

Para ejecutar toda la suite de pruebas:

```bash
pytest
```

Para ejecutar pruebas con detalle de cobertura y diagnósticos extendidos:

```bash
pytest -v -ra
```

## Origen de datos

El origen del archivo `Entidades_Estados_INEGI_Simplificado.gpkg` se obtuvo de la página oficial del INEGI, puede consultar:
https://www.inegi.org.mx/app/ageeml/

Donde se asignarón ciertas modificaciones a nombres de columnas y eliminación de columnas innecesarias.

## Licencia

El código de PostSIMA se distribuye bajo la Licencia Pública General
de GNU, versión 3. Consulta el archivo [LICENSE](LICENSE).

El GeoPackage de INEGI y los datos de terceros se rigen por los
términos de sus respectivas fuentes.