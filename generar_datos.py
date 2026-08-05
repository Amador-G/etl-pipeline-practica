import os
import random
import pandas as pd
from faker import Faker
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_ORIGEN = os.getenv("DB_ORIGEN")


engine_origen = create_engine(
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_ORIGEN}"
)

fake = Faker()

# parametros

CANT_FONDOS = 5
CANT_INVERSORES = 100
CANT_TRANSACCIONES = 10000
PROP_INVALIDOS = 0.20  # 20%


def GenerarFondos():
    """Genera los fondos base, la cima de la cadena"""
    tipos = ["Equity", "Bonds", "Real Estate", "Hedge", "Private Equity"]
    fondos = []
    for i in range(1, CANT_FONDOS + 1):
        fondos.append(
            {"id_fondo": i, "nombre": fake.company(), "tipo": random.choice(tipos)}
        )

    return pd.DataFrame(fondos)


def GenerarInversores(ids_fondos):
    """Genera los inversores que apuntan a fondos existentes"""
    inversores = []
    for i in range(101, 101 + CANT_INVERSORES):
        Invalido = random.random() < PROP_INVALIDOS
        inversores.append(
            {
                "id_inversor": i,
                "nombre": fake.name(),
                # inválido: apunta a un fondo inexistente (999)
                "id_fondo": 999 if Invalido else random.choice(ids_fondos),
                # invalido : email vacio
                "email": "" if Invalido else fake.email(),
            }
        )
    return pd.DataFrame(inversores)


def GenerarTransacciones(ids_inversores):
    """Genera transacciones que apuntan a un inversor existente, algunas seran invalidas"""
    transacciones = []
    for i in range(1, CANT_TRANSACCIONES + 1):
        invalido = random.random() < PROP_INVALIDOS
        transacciones.append(
            {
                "id": i,
                # inválido: fecha nula
                "fecha": None if invalido else fake.date_between(start_date="-1y"),
                "id_inversor": random.choice(ids_inversores),
                # inválido: monto 0
                "monto": 0 if invalido else round(random.uniform(100, 100000), 2),
                "moneda": random.choice(["USD", "EUR"]),
            }
        )
    return pd.DataFrame(transacciones)


def agregar_lote_nuevo(cantidad=50):
    """Agrega un lote nuevo de transacciones al origen, sin borrar las existentes.
    Los ids arrancan después del último existente para no chocar."""
    # Averiguar cuál es el id más alto que ya existe en el origen
    ultimo_id = pd.read_sql(
        "SELECT MAX(id) AS max_id FROM transacciones", engine_origen
    )["max_id"][0]
    inicio = int(ultimo_id) + 1

    # Traer los inversores que ya existen, para que las nuevas apunten a ellos
    ids_inversores = pd.read_sql("SELECT id_inversor FROM inversores", engine_origen)[
        "id_inversor"
    ].tolist()

    nuevas = []
    for i in range(inicio, inicio + cantidad):
        nuevas.append(
            {
                "id": i,
                "fecha": fake.date_between(start_date="-1y"),
                "id_inversor": random.choice(ids_inversores),
                "monto": round(random.uniform(100, 100000), 2),
                "moneda": random.choice(["USD", "EUR"]),
            }
        )

    df_nuevas = pd.DataFrame(nuevas)
    df_nuevas.to_sql(
        "transacciones", con=engine_origen, if_exists="append", index=False
    )
    print(
        f"Se agregaron {cantidad} transacciones nuevas (ids {inicio} a {inicio + cantidad - 1})."
    )


def main():
    print("generando datos"),
    fondos = GenerarFondos()
    inversores = GenerarInversores(fondos["id_fondo"].tolist())
    transacciones = GenerarTransacciones(inversores["id_inversor"].tolist())

    print(
        f"Cargando el origen: {len(fondos)} fondos, {len(inversores)} inversores, {len(transacciones)} transacciones..."
    )
    fondos.to_sql("fondos", con=engine_origen, if_exists="replace", index=False)
    inversores.to_sql("inversores", con=engine_origen, if_exists="replace", index=False)
    transacciones.to_sql(
        "transacciones", con=engine_origen, if_exists="replace", index=False
    )

    print("Datos generados y cargados en la base de origen")


if __name__ == "__main__":
    agregar_lote_nuevo(50)