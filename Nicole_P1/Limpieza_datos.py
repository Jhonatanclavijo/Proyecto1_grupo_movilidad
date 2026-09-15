

import numpy as np
import pandas as pd

#RUTA_ENTRADA = r"C:\Users\castr\Desktop\Andes\Semestres\8\Analítica\Proyecto\Datos_completos_SDM.csv"
RUTA_ENTRADA="Datos_completos_SDM.csv"
RUTA_SALIDA = "datos_limpios.csv"
FECHAS = ["fecha_de_firma", "fecha_de_inicio_del_contrato", "fecha_de_fin_del_contrato"]

df = pd.read_csv(RUTA_ENTRADA, low_memory=False, parse_dates=FECHAS)


# Columnas que se necesitan para la pregunta de proveedores
COLUMNAS = [
    "id_contrato", "referencia_del_contrato", "urlproceso",
    "fecha_de_firma", "fecha_de_inicio_del_contrato", "fecha_de_fin_del_contrato",
    "documento_proveedor", "proveedor_adjudicado", "tipodocproveedor",
    "es_pyme", "g_nero_representante_legal",
    "estado_contrato", "tipo_de_contrato", "modalidad_de_contratacion",
    "valor_del_contrato", "dias_adicionados", "objeto_del_contrato",
]
df = df[COLUMNAS].copy()


# Quitar los procesos que nunca se firmaron (son los que no tienen fecha de firma)
SIN_APORTE = ["Borrador", "Cancelado", "En aprobación", "En aprobacion",
              "enviado Proveedor"]
df = df[~df["estado_contrato"].isin(SIN_APORTE)].copy()

# Quitar duplicados y contratos sin valor
df = df.drop_duplicates(subset="id_contrato")
df["valor_del_contrato"] = pd.to_numeric(df["valor_del_contrato"], errors="coerce")
df = df[df["valor_del_contrato"] > 0].copy()


# Sacar los null: SECOP II escribe "No definido" en vez de dejar el campo vacio,
# asi que isna() no los ve. Se comparan en minusculas porque la fuente escribe
# "No Definido" en documento_proveedor y "No definido" en el resto.
MARCADORES = ["no definido", "", "nan", "n/a", "none", "null", "-"]

for c in df.columns:
    if str(df[c].dtype) in ("object", "string", "str"):
        texto = df[c].astype("object").astype(str).str.strip().str.lower()
        df[c] = df[c].astype("object").mask(texto.isin(MARCADORES))

# Sin documento del proveedor no se puede agrupar, esas filas se van
df = df[df["documento_proveedor"].notna()].copy()

# El genero se deja como categoria, no se borra
df["g_nero_representante_legal"] = df["g_nero_representante_legal"].fillna("No reportado")


# Variables nuevas de fecha y valor
df["anio_firma"] = df["fecha_de_firma"].dt.year
df["mes_firma"] = df["fecha_de_firma"].dt.month
df["trimestre_firma"] = df["fecha_de_firma"].dt.quarter

df["plazo_dias"] = (df["fecha_de_fin_del_contrato"]
                    - df["fecha_de_inicio_del_contrato"]).dt.days
df.loc[df["plazo_dias"] < 0, "plazo_dias"] = np.nan

df["valor_millones"] = df["valor_del_contrato"] / 1e6
df["dias_adicionados"] = pd.to_numeric(df["dias_adicionados"], errors="coerce")
df["tiene_adicion"] = df["dias_adicionados"] > 0


# Variables nuevas del proveedor
df["tipo_persona"] = np.where(df["tipodocproveedor"] == "NIT", "Juridica", "Natural")

conteo = df["documento_proveedor"].value_counts()
df["n_contratos_proveedor"] = df["documento_proveedor"].map(conteo)

df["recurrencia"] = pd.cut(df["n_contratos_proveedor"],
                           bins=[0, 1, 2, 4, np.inf],
                           labels=["1 contrato", "2 contratos",
                                   "3 a 4 contratos", "5 o mas"])

valor_proveedor = df.groupby("documento_proveedor")["valor_del_contrato"].sum()
df["valor_total_proveedor"] = df["documento_proveedor"].map(valor_proveedor)


df.to_csv(RUTA_SALIDA, index=False, encoding="utf-8")
print(f"{len(df):,} registros y {df.shape[1]} columnas guardados en {RUTA_SALIDA}")