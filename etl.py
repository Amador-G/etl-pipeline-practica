import logging
import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_ORIGEN = os.getenv("DB_ORIGEN")
DB_DESTINO = os.getenv("DB_DESTINO")

# Dos motores: uno para leer del origen, otro para escribir en el destino
engine_origen = create_engine(
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_ORIGEN}"
)
engine_destino = create_engine(
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_DESTINO}"
)


def extraer():
    """Lee las tres tablas crudas desde la base de origen."""
    fondos = pd.read_sql("SELECT * FROM fondos", engine_origen)
    inversores = pd.read_sql("SELECT * FROM inversores", engine_origen)
    transacciones = pd.read_sql("SELECT * FROM transacciones", engine_origen)
    return fondos, inversores, transacciones


def transformar(fondos, inversores, transacciones):
    """Valida cada tabla y propaga los descartes por la cadena de dependencias."""

    # --- FONDOS: no dependen de nadie, se validan solos ---
    fondos_validos = fondos[fondos["nombre"].notna() & (fondos["nombre"] != "")]

    # --- INVERSORES: deben tener email Y apuntar a un fondo válido ---
    ids_fondos_validos = fondos_validos["id_fondo"]
    inversores_validos = inversores[
        (inversores["email"] != "")
        & (inversores["email"].notna())
        & (inversores["id_fondo"].isin(ids_fondos_validos))
    ]
    inversores_invalidos = inversores[~inversores.index.isin(inversores_validos.index)]

    # --- TRANSACCIONES: monto > 0, fecha no nula, Y apuntar a un inversor válido ---
    ids_inversores_validos = inversores_validos["id_inversor"]
    transacciones_validas = transacciones[
        (transacciones["monto"] > 0)
        & (transacciones["fecha"].notna())
        & (transacciones["id_inversor"].isin(ids_inversores_validos))
    ]
    transacciones_invalidas = transacciones[
        ~transacciones.index.isin(transacciones_validas.index)
    ]

    return (
        fondos_validos,
        inversores_validos,
        inversores_invalidos,
        transacciones_validas,
        transacciones_invalidas,
    )


def cargar(fondos, inversores, transacciones):
    """Carga fondos e inversores por reemplazo; transacciones de forma incremental."""
    momento_carga = pd.Timestamp.now()

    # --- Fondos e inversores: reemplazo completo ---
    fondos = fondos.copy()
    inversores = inversores.copy()
    fondos["fecha_carga"] = momento_carga
    inversores["fecha_carga"] = momento_carga
    fondos.to_sql("fondos", con=engine_destino, if_exists="replace", index=False)
    inversores.to_sql(
        "inversores", con=engine_destino, if_exists="replace", index=False
    )

    # ---- transacciones cargar incremental (solo ids nuevos) -----
    transacciones = transacciones.copy()

    # Averiguar que ids ya existen en el destino
    try:
        ids_existentes = pd.read_sql("SELECT id FROM transacciones", engine_destino)[
            "id"
        ]
    except Exception:
        # La tabla no existe aún (primera corrida): no hay ids previos
        ids_existentes = pd.Series([], dtype="int64")

    # Quedarse solo con las transacciones cuyo id NO está en el destino
    transacciones_nuevas = transacciones[~transacciones["id"].isin(ids_existentes)]

    # Cargar solo las nuevas, agregando (append) a lo que ya haya
    if len(transacciones_nuevas) > 0:
        transacciones_nuevas = transacciones_nuevas.copy()
        transacciones_nuevas["fecha_carga"] = momento_carga
        transacciones_nuevas.to_sql(
            "transacciones", con=engine_destino, if_exists="append", index=False
        )

    # Devolver cuántas se cargaron realmente, para el reporte
    return len(transacciones_nuevas)


def reportar(fondos_v, inversores_v, inversores_i, transacciones_v, transacciones_i):
    """Registra el resultado del proceso: éxitos resumidos, descartes detallados."""
    logging.info("----- REPORTE DE CARGA -----")
    logging.info(f"Fondos cargados: {len(fondos_v)}")
    logging.info(f"Inversores cargados correctamente: {len(inversores_v)}")
    logging.info(f"Transacciones cargadas correctamente: {len(transacciones_v)}")

    # Descartes: se detallan uno por uno, como WARNING
    if len(inversores_i) > 0:
        logging.warning(f"Inversores descartados: {len(inversores_i)}")
        for _, r in inversores_i.iterrows():
            motivo = (
                "Email vacío o nulo"
                if (r["email"] == "" or pd.isna(r["email"]))
                else "Fondo inválido"
            )
            logging.warning(f" Inversion id {r['id_inversor']}: {motivo}")

    if len(transacciones_i) > 0:
        logging.warning(f"Transacciones descartadas: {len(transacciones_i)}")
        for _, r in transacciones_i.iterrows():
            motivo = (
                "Monto <= 0"
                if (r["monto"] <= 0)
                else "Fecha nula" if pd.isna(r["fecha"]) else "Inversor inválido"
            )
            logging.warning(f" Transacción id {r['id']}: {motivo}")

    logging.info("----- FIN DEL REPORTE -----")


# def main():
#     """Orquesta el ETL completo: extraer -> transformar -> cargar -> reportar."""
#     fondos, inversores, transacciones = extraer()
#     (fondos_v, inversores_v, inversores_i,
#      transacciones_v, transacciones_i) = transformar(fondos, inversores, transacciones)
#     cargar(fondos_v, inversores_v, transacciones_v)
#     reportar(fondos_v, inversores_v, inversores_i, transacciones_v, transacciones_i)


# if __name__ == "__main__":
#     main()
