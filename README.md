# Pipeline ETL — Migración de datos entre bases con validación e integridad referencial

Proceso ETL en Python que extrae datos de una base de origen, los valida y transforma, y los carga en una base de destino distinta. Simula el patrón de un conector de migración de datos: extracción, validación por reglas de negocio, control de integridad referencial entre tablas relacionadas, carga en destino, registro (logging) y ejecución automatizada mediante un job programado.

## Problema que resuelve

Mover datos entre dos sistemas rara vez es una copia directa. Los datos de origen suelen traer registros inválidos (campos vacíos, montos incorrectos) y referencias rotas (un registro que apunta a otro que no existe). Este pipeline procesa tres tablas relacionadas —**fondos → inversores → transacciones**— respetando sus dependencias: valida cada nivel, descarta lo inválido, y propaga esos descartes hacia abajo en la cadena. Si un fondo es inválido, sus inversores se descartan; si un inversor se descarta, sus transacciones también.

## Arquitectura

El proceso está compuesto por cinco piezas encadenadas, separando el "motor" (que coordina) de las "piezas de trabajo" (que ejecutan):

```
Job programado  →  correr_etl.bat  →  orquestador.py  →  etl.py  →  Bases de datos
   (disparador)      (traductor)        (director)       (piezas)     (origen/destino)
```

1. **`etl.py`** — Biblioteca de funciones ETL: `extraer`, `transformar`, `cargar`, `reportar`. No se ejecuta sola; ofrece las herramientas.
2. **`orquestador.py`** — Coordina el flujo: llama a las funciones en orden, controla errores con `try/except`, y registra cada paso en un log con marca de tiempo.
3. **`correr_etl.bat`** — Envuelve la ejecución para que Windows pueda dispararla sin conocer Python.
4. **Programador de tareas de Windows** — Dispara el `.bat` de forma automática a una hora fija (equivalente casero de un SQL Agent job).
5. **Bases MySQL de origen y destino** — Dos bases separadas: los datos crudos entran de una y los datos limpios salen a la otra.

## Validaciones implementadas

- **Fondos:** nombre no vacío.
- **Inversores:** email no vacío **y** debe apuntar a un fondo válido (integridad referencial).
- **Transacciones:** monto mayor a cero, fecha no nula **y** debe apuntar a un inversor válido.
- **Propagación en cascada:** los descartes de un nivel arrastran a los registros dependientes de los niveles inferiores.

## Tecnologías

- **Python** — lenguaje del proceso.
- **pandas** — transformación y validación de datos en memoria (DataFrames).
- **SQLAlchemy + mysql-connector** — conexión a las bases MySQL de origen y destino.
- **python-dotenv** — configuración y credenciales fuera del código, en un archivo `.env`.
- **logging** — registro persistente de la ejecución en `etl.log`.
- **MySQL** — bases de datos de origen y destino.

## Cómo ejecutarlo

1. Cloná el repo.
2. Instalá las dependencias:
   ```
   pip install pandas sqlalchemy mysql-connector-python pymysql python-dotenv
   ```
3. Creá las bases `etl_origen` (con las tablas y datos crudos) y `etl_destino` (vacía) en MySQL.
4. Copiá `.env.example` a `.env` y completá tus credenciales de MySQL.
5. Ejecutá el orquestador:
   ```
   python orquestador.py
   ```
6. (Opcional) Para automatizarlo, copiá `correr_etl.bat.example` a `correr_etl.bat`, ajustá las rutas a tu máquina, y programalo con el Programador de tareas de Windows.

## Notas

- `.env` y `correr_etl.bat` contienen datos específicos de cada máquina y no se versionan. Sus plantillas (`.env.example`, `correr_etl.bat.example`) sí están incluidas como referencia.
- `etl.log` se regenera en cada corrida y no se versiona.
