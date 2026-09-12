import io
import os
import unicodedata
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dash_table, dcc, html
df = pd.read_csv(r"C:\Users\jhona\OneDrive - Universidad de los Andes\2026-2\Analítica Para la toma de Desiciones\Proyecto 1\Repositorio no Tocar\Jhonatan_P1\datos_limpios_sdm.csv", parse_dates=["fecha_de_firma","fecha_de_inicio_del_contrato","fecha_de_fin_del_contrato"])

AZUL, ROJO, GRIS = "#2b6cb0", "#c53030", "#718096"

# La dependencia no existe como columna en SECOP II: se extrae del objeto.

objeto = (df["objeto_del_contrato"].astype(str).apply(lambda s: unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()))
dependencias = {
    "Investigaciones Administrativas": "investigaciones administrativas",
    "Gestion en Via": "gestion en via",
    "Gestion de Cobro": "gestion de cobro",
    "Senalizacion": "senalizacion",
    "Semaforizacion": "semaforizacion",
    "Control de Transito": "control de transito",
    "Seguridad Vial": "seguridad vial",
    "Atencion al Ciudadano": "atencion al ciudadano|servicio al ciudadano",
}
df["dependencia"] = "Otras"
for nombre, patron in dependencias.items():
    sin_asignar = df["dependencia"].eq("Otras")
    df.loc[sin_asignar & objeto.str.contains(patron, na=False), "dependencia"] = nombre
# El tablero solo mira contratos cuyo plazo ya vencio.
ven = df[df["vencido"]].copy()
ven["anio_fin"] = ven["anio_fin"].astype(int)
LISTA_DEPENDENCIAS = sorted(ven["dependencia"].unique())
LISTA_TIPOS = sorted(ven["tipo_de_contrato"].dropna().unique())

# Caja de kpis superiores
CAJA = {"backgroundColor": "white", "padding": "16px", "borderRadius": "10px","boxShadow": "0 1px 3px rgba(0,0,0,.08)","marginBottom":"14px"}

CAJA_KPI = {**CAJA, "flex": "1", "textAlign": "center", "margin": "0 6px"}
 
 
def kpi(titulo, id_valor, nota):
    """Crea una tarjeta de indicador. El valor lo llena el callback."""
    return html.Div([
        html.Div(titulo, style={"fontSize": "12px", "color": GRIS}),
        html.Div(id=id_valor, style={"fontSize": "26px", "fontWeight": "700","color": AZUL, "margin": "4px 0"}),html.Div(nota, style={"fontSize": "11px","color": GRIS}),], style=CAJA_KPI)




