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


layout = html.Div([
    # ----- ENCABEZADO Y TÍTULO PRINCIPAL -----
    html.H3("Cierre del expediente contractual", style={"marginBottom": "2px"}),
    html.P("¿Qué proporción de los contratos cuyo plazo ya venció sigue sin "
           "registrar su cierre, y cuánto tiempo llevan en esa situación?",
           style={"color": GRIS, "fontSize": "13px"}),
     # ----- CAJA DE INSTRUCCIONES Y MARCO LEGAL -----
    html.Div([
        html.B("Cómo usar este módulo. "),
        "Mueva el umbral para definir a partir de cuántos meses considera que un "
        "expediente está rezagado: las marcas de 4, 6 y 24 meses son los términos "
        "del artículo 11 de la Ley 1150 de 2007. Abajo, indique cuántos "
        "expedientes puede depurar por semana para estimar cuánto tardaría.",
        html.Br(),
        html.I("El indicador mide el estado del registro en SECOP II, no el "
               "estado jurídico del contrato."),
    ], style={**CAJA, "fontSize": "12px", "borderLeft": f"4px solid {AZUL}"}),
 
    # ----- PANEL DE FILTROS INTERACTIVOS -----

    html.Div([
        # Control deslizante (Slider) para definir el umbral en meses de rezago
        html.Div([
            html.Label("Umbral de rezago (meses desde la terminación)",
                       style={"fontSize": "12px", "fontWeight": "600"}),
            dcc.Slider(id="p3_umbral", min=0, max=36, step=1, value=4,
                       marks={0: "0", 4: "4 bilateral", 6: "6 unilateral",
                              12: "12", 24: "24 límite", 36: "36"},
                       tooltip={"placement": "bottom", "always_visible": True}),
        ], style={"flex": "2", "padding": "0 14px"}),
        # Menú desplegable para filtrar por Dependencia interna
        html.Div([
            html.Label("Dependencia", style={"fontSize": "12px", "fontWeight": "600"}),
            dcc.Dropdown(id="p3_dependencia", options=LISTA_DEPENDENCIAS,
                         multi=True, placeholder="Todas",
                         style={"fontSize": "12px"}),
        ], style={"flex": "1", "padding": "0 8px"}),
        # Menú desplegable para filtrar por Tipo de contrato
        html.Div([
            html.Label("Tipo de contrato",
                       style={"fontSize": "12px", "fontWeight": "600"}),
            dcc.Dropdown(id="p3_tipo", options=LISTA_TIPOS, multi=True,
                         placeholder="Todos", style={"fontSize": "12px"}),
        ], style={"flex": "1", "padding": "0 8px"}),
    ], style={**CAJA, "display": "flex", "alignItems": "flex-start"}),
 
    # ----- TARJETAS DE INDICADORES CLAVE (KPIs) -----
    html.Div([
        kpi("Expedientes rezagados", "p3_kpi_n", "según el umbral elegido"),
        kpi("Valor comprometido", "p3_kpi_valor", "suma del valor contratado"),
        kpi("Rezago mediano", "p3_kpi_mediana", "meses desde la terminación"),
        kpi("Más de 24 meses", "p3_kpi_criticos", "fuera del término para liquidar"),
    ], style={"display": "flex", "marginBottom": "6px"}),
 
    # ----- Respuesta micropreguntas 1 y 2
    html.Div([
        html.Div([dcc.Graph(id="p3_g1", config={"displayModeBar": False})],
                 style={**CAJA, "flex": "1", "marginRight": "10px"}),
        html.Div([dcc.Graph(id="p3_g2", config={"displayModeBar": False})],
                 style={**CAJA, "flex": "1"}),
    ], style={"display": "flex"}),
 
    # ----- Respuesta micropregunta 3
    html.Div([
        html.Label("Ver la concentración del rezago por:",
                   style={"fontSize": "12px", "fontWeight": "600"}),
        dcc.RadioItems(id="p3_agrupador",
                       options=[{"label": " Dependencia", "value": "dependencia"},
                                {"label": " Tipo de contrato", "value": "tipo_de_contrato"},
                                {"label": " Modalidad", "value": "modalidad_de_contratacion"}],
                       value="dependencia", inline=True,
                       style={"fontSize": "12px", "marginBottom": "6px"}),
        dcc.Graph(id="p3_g3", config={"displayModeBar": False}),
    ], style=CAJA),
 
    # ----- Simulador de Depuracion
    html.Div([
        html.H4("¿Cuánto tardaría en depurar el rezago?",
                style={"marginTop": "0", "marginBottom": "10px"}),
        html.Div([
            # Entrada numérica para definir la capacidad semanal de cierre de expedientes
            html.Div([
                html.Label("Expedientes que puede cerrar por semana",
                           style={"fontSize": "12px", "fontWeight": "600"}),
                html.Br(),
                dcc.Input(id="p3_capacidad", type="number", value=40, min=1,
                          max=2000, step=5, debounce=True,
                          style={"width": "110px", "marginTop": "6px"}),
            ], style={"marginRight": "30px"}),
            # Selector de estrategia o regla de priorización para la depuración
            html.Div([
                html.Label("¿Por dónde empezar?",
                           style={"fontSize": "12px", "fontWeight": "600"}),
                dcc.RadioItems(
                    id="p3_regla",
                    options=[{"label": " Los más antiguos", "value": "antiguedad"},
                             {"label": " Los de mayor valor", "value": "valor"},
                             {"label": " Combinación de ambos", "value": "mixta"}],
                    value="antiguedad", style={"fontSize": "12px"},
                    labelStyle={"display": "block"}),
            ]),
        ], style={"display": "flex", "alignItems": "flex-start"}),
        # Gráfica de proyección temporal del simulador
        dcc.Graph(id="p3_g4", config={"displayModeBar": False}),
        # Contenedor dinámico para mostrar el texto con los resultados de la simulación
        html.Div(id="p3_texto_sim", style={"fontSize": "13px", "marginTop": "4px"}),
    ], style=CAJA),
 
], style={"fontFamily": "Segoe UI, Arial", "backgroundColor": "#f7fafc",
          "padding": "18px"})

# funcion auxiliar

def filtrar(umbral, deps, tipos):
    """Devuelve el universo filtrado y el subconjunto que cuenta como rezagado."""
    datos = ven
    if deps:
        datos = datos[datos["dependencia"].isin(deps)]
    if tipos:
        datos = datos[datos["tipo_de_contrato"].isin(tipos)]
    rezago = datos[(~datos["cerrado"]) & (datos["meses_desde_fin"] >= umbral)]
    return datos, rezago



