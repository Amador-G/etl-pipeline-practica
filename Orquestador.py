import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from sqlalchemy import text
import etl

# --- Configuración del logging con rotación diaria ---
file_handler = TimedRotatingFileHandler(
    "etl.log", when="midnight", interval=1, backupCount=7, encoding="utf-8"
)
formato = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
file_handler.setFormatter(formato)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formato)
logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])


def registrar_ejecucion(inicio, fin, estado, contadores, mensaje_error=""):
    """Inserta una fila en la tabla de control con el resultado de la corrida."""
    consulta = text("""
        INSERT INTO control_ejecuciones
        (inicio, fin, estado, fondos_cargados, inversores_cargados,
         inversores_descartados, transacciones_cargadas, transacciones_descartadas, mensaje_error)
        VALUES (:inicio, :fin, :estado, :fondos, :inv_ok, :inv_desc, :txn_cargadas, :txn_desc, :error)
    """)
    with etl.engine_destino.begin() as conn:
        conn.execute(
            consulta,
            {
                "inicio": inicio,
                "fin": fin,
                "estado": estado,
                "fondos": contadores.get("fondos", 0),
                "inv_ok": contadores.get("inv_ok", 0),
                "inv_desc": contadores.get("inv_desc", 0),
                "txn_cargadas": contadores.get("txn_cargadas", 0),
                "txn_desc": contadores.get("txn_desc", 0),
                "error": mensaje_error,
            },
        )


def ejecutar_etl():
    """Orquesta el proceso ETL completo, con control de pasos, logging y auditoría."""
    inicio = datetime.now()
    contadores = {}
    estado = "ÉXITO"
    mensaje_error = ""

    logging.info("Iniciando proceso ETL...")

    try:
        logging.info("Paso 1/4: extrayendo datos del origen...")
        fondos, inversores, transacciones = etl.extraer()
        logging.info("Paso 2/4: transformando datos...")
        (
            fondos_validos,
            inversores_validos,
            inversores_invalidos,
            transacciones_validas,
            transacciones_invalidas,
        ) = etl.transformar(fondos, inversores, transacciones)

        contadores = {
            "fondos": len(fondos_validos),
            "inv_ok": len(inversores_validos),
            "inv_desc": len(inversores_invalidos),
            "txn_ok": len(transacciones_validas),
            "txn_desc": len(transacciones_invalidas),
        }

        logging.info("Paso 3/4: cargando datos en la base de destino...")
        transacciones_cargadas = etl.cargar(
            fondos_validos, inversores_validos, transacciones_validas
        )
        contadores["txn_cargadas"] = transacciones_cargadas
        logging.info(f"Nuevas transacciones cargadas : {transacciones_cargadas}")
        logging.info("Paso 4/4: generando reporte del proceso...")
        etl.reportar(
            fondos_validos,
            inversores_validos,
            inversores_invalidos,
            transacciones_validas,
            transacciones_invalidas,
        )
        logging.info("Proceso ETL finalizado con éxito.")
    except Exception as e:
        estado = "FALLO"
        mensaje_error = str(e)
        logging.error(f"Proceso ETL fallido: {e}")
        raise

    finally:
        fin = datetime.now()
        registrar_ejecucion(inicio, fin, estado, contadores, mensaje_error)
        logging.info(
            f"Registro de ejecución insertado en la tabla de control: estado={estado}"
        )


if __name__ == "__main__":
    ejecutar_etl()
