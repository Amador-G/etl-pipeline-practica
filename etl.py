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
engine_origen = create_engine(f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_ORIGEN}')
engine_destino = create_engine(f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_DESTINO}')


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
        (inversores["email"] != "") &
        (inversores["email"].notna()) &
        (inversores["id_fondo"].isin(ids_fondos_validos))
    ]
    inversores_invalidos = inversores[~inversores.index.isin(inversores_validos.index)]

    # --- TRANSACCIONES: monto > 0, fecha no nula, Y apuntar a un inversor válido ---
    ids_inversores_validos = inversores_validos["id_inversor"]
    transacciones_validas = transacciones[
        (transacciones["monto"] > 0) &
        (transacciones["fecha"].notna()) &
        (transacciones["id_inversor"].isin(ids_inversores_validos))
    ]
    transacciones_invalidas = transacciones[~transacciones.index.isin(transacciones_validas.index)]

    return (fondos_validos, inversores_validos, inversores_invalidos,
            transacciones_validas, transacciones_invalidas)


def cargar(fondos, inversores, transacciones):
    """Escribe las tres tablas limpias en la base de destino."""
    fondos.to_sql("fondos", con=engine_destino, if_exists="replace", index=False)
    inversores.to_sql("inversores", con=engine_destino, if_exists="replace", index=False)
    transacciones.to_sql("transacciones", con=engine_destino, if_exists="replace", index=False)


def reportar(fondos_v, inversores_v, inversores_i, transacciones_v, transacciones_i):
    """Reporte del proceso, tabla por tabla."""
    print("=" * 45)
    print("REPORTE ETL")
    print("=" * 45)
    print(f"Fondos cargados:        {len(fondos_v)}")
    print(f"Inversores cargados:    {len(inversores_v)}  (descartados: {len(inversores_i)})")
    print(f"Transacciones cargadas: {len(transacciones_v)}  (descartadas: {len(transacciones_i)})")
    print("-" * 45)

    if len(inversores_i) > 0:
        print("Inversores descartados:")
        for _, r in inversores_i.iterrows():
            motivo = "Email vacío" if (r["email"] == "" or pd.isna(r["email"])) else "Fondo inválido"
            print(f"  id {r['id_inversor']}: {motivo}")

    if len(transacciones_i) > 0:
        print("Transacciones descartadas:")
        for _, r in transacciones_i.iterrows():
            motivo = "Monto inválido" if r["monto"] <= 0 else "Fecha inválida" if pd.isna(r["fecha"]) else "Inversor inexistente"
            print(f"  id {r['id']}: {motivo}")
    print("=" * 45)


# def main():
#     """Orquesta el ETL completo: extraer -> transformar -> cargar -> reportar."""
#     fondos, inversores, transacciones = extraer()
#     (fondos_v, inversores_v, inversores_i,
#      transacciones_v, transacciones_i) = transformar(fondos, inversores, transacciones)
#     cargar(fondos_v, inversores_v, transacciones_v)
#     reportar(fondos_v, inversores_v, inversores_i, transacciones_v, transacciones_i)


# if __name__ == "__main__":
#     main()