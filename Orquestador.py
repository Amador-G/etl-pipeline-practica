import logging
import etl
#   configura el archivo de log y el formato de salida
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s",
                    # muestra por pantalla y en archivo de log
                        handlers=[logging.FileHandler("etl.log"), logging.StreamHandler()]
                    )

def ejecutar_etl():
    try:
        logging.info("Iniciando proceso ETL...")
        logging.info("Extrayendo datos de la base de origen...")
        fondos, inversores, transacciones = etl.extraer()
        logging.info(f"Datos extraídos: {len(fondos)} fondos, {len(inversores)} inversores, {len(transacciones)} transacciones.")
        logging.info("Transformando datos...")
        fondos_validos, inversores_validos, inversores_invalidos, transacciones_validas, transacciones_invalidas = etl.transformar(fondos, inversores, transacciones)
        logging.info(f"Datos transformados: {len(fondos_validos)} fondos válidos, {len(inversores_validos)} inversores válidos, {len(inversores_invalidos)} inversores inválidos, {len(transacciones_validas)} transacciones")
        logging.info("Cargando datos en la base de destino...")
        etl.cargar(fondos_validos, inversores_validos, transacciones_validas)
        logging.info(f"Datos cargados: {len(fondos_validos)} fondos, {len(inversores_validos)} inversores, {len(transacciones_validas)} transacciones.")
        logging.info("Generando reporte del proceso...")
        etl.reportar(fondos_validos, inversores_validos, inversores_invalidos, transacciones_validas, transacciones_invalidas)
        logging.info("Proceso ETL finalizado con éxito.")
    except Exception as e:
        logging.error(f"El proceso ETL falló: {e}")
        raise

if __name__ == "__main__":
        ejecutar_etl()