from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# Ruta a la carpeta raíz del repositorio
RUTA_RAIZ = Path(__file__).resolve().parents[1]

# Ruta al archivo de datos
RUTA_DATOS = RUTA_RAIZ / "Datos_completos_SDM.csv"

# Cargar la base completa
df = pd.read_csv(RUTA_DATOS)

# Columnas necesarias para el análisis de Manuela
columnas_manuela = [
    "id_contrato",
    "estado_contrato",
    "tipo_de_contrato",
    "modalidad_de_contratacion",
    "fecha_de_firma",
    "valor_del_contrato"
]

df_manuela = df[columnas_manuela].copy()

# Estados que no corresponden a contratos formalizados
estados_excluir = [
    "Borrador",
    "Cancelado",
    "enviado Proveedor",
    "En aprobación"
]

df_limpio = df_manuela[
    ~df_manuela["estado_contrato"].isin(estados_excluir)
].copy()

# Convertir la fecha de firma a formato fecha
df_limpio["fecha_de_firma"] = pd.to_datetime(
    df_limpio["fecha_de_firma"]
)

# Crear variable de año
df_limpio["año"] = df_limpio["fecha_de_firma"].dt.year

#GRÁFICA 1 - Modalidad de contratación

# Resumen por modalidad de contratación
resumen_modalidad = (
    df_limpio
    .groupby("modalidad_de_contratacion")
    .agg(
        numero_contratos=("id_contrato", "count"),
        valor_total=("valor_del_contrato", "sum")
    )
    .reset_index()
)

# Participación en el número de contratos
resumen_modalidad["participacion_contratos_pct"] = (
    resumen_modalidad["numero_contratos"]
    / resumen_modalidad["numero_contratos"].sum()
    * 100
)

# Participación en el valor contratado
resumen_modalidad["participacion_valor_pct"] = (
    resumen_modalidad["valor_total"]
    / resumen_modalidad["valor_total"].sum()
    * 100
)

# Preparar datos para la gráfica
grafica_modalidad = resumen_modalidad[
    [
        "modalidad_de_contratacion",
        "participacion_contratos_pct",
        "participacion_valor_pct"
    ]
].melt(
    id_vars="modalidad_de_contratacion",
    var_name="indicador",
    value_name="participacion_pct"
)

grafica_modalidad["indicador"] = grafica_modalidad["indicador"].replace({
    "participacion_contratos_pct": "Participación en contratos",
    "participacion_valor_pct": "Participación en valor"
})

orden_modalidades = (
    resumen_modalidad
    .sort_values("participacion_valor_pct", ascending=False)
    ["modalidad_de_contratacion"]
    .tolist()
)

fig_modalidad = px.bar(
    grafica_modalidad,
    x="participacion_pct",
    y="modalidad_de_contratacion",
    color="indicador",
    barmode="group",
    orientation="h",
    category_orders={
        "modalidad_de_contratacion": orden_modalidades
    },
    labels={
        "participacion_pct": "Participación (%)",
        "modalidad_de_contratacion": "Modalidad de contratación",
        "indicador": ""
    },
    title="Concentración por modalidad: número de contratos vs. valor contratado"
)

fig_modalidad.update_traces(
    texttemplate="%{x:.1f}%",
    textposition="outside"
)

fig_modalidad.update_layout(
    height=600,
    xaxis_title="Participación (%)",
    yaxis_title="",
    legend_title_text="",
    margin=dict(l=220, r=120, t=80, b=60)
)

#fig_modalidad.show()

#GRAFICA 2 - Tipo de contrato

# Resumen por tipo de contrato
resumen_tipo = (
    df_limpio
    .groupby("tipo_de_contrato")
    .agg(
        numero_contratos=("id_contrato", "count"),
        valor_total=("valor_del_contrato", "sum")
    )
    .reset_index()
)

# Participación en el número de contratos
resumen_tipo["participacion_contratos_pct"] = (
    resumen_tipo["numero_contratos"]
    / resumen_tipo["numero_contratos"].sum()
    * 100
)

# Participación en el valor contratado
resumen_tipo["participacion_valor_pct"] = (
    resumen_tipo["valor_total"]
    / resumen_tipo["valor_total"].sum()
    * 100
)

# Agrupar tipos de contrato residuales para el dashboard
tipos_otros = [
    "Comisión",
    "Arrendamiento de muebles",
    "Servicios financieros",
    "Concesión",
    "Comodato"
]

# Crear una copia para no modificar el resumen original
resumen_tipo_dashboard = resumen_tipo.copy()

# Reemplazar únicamente esos cinco tipos por la categoría "Otros"
resumen_tipo_dashboard["tipo_dashboard"] = (
    resumen_tipo_dashboard["tipo_de_contrato"]
    .where(
        ~resumen_tipo_dashboard["tipo_de_contrato"].isin(tipos_otros),
        "Otros"
    )
)

# Agrupar las cinco categorías bajo "Otros"
resumen_tipo_dashboard = (
    resumen_tipo_dashboard
    .groupby("tipo_dashboard")
    .agg(
        numero_contratos=("numero_contratos", "sum"),
        valor_total=("valor_total", "sum")
    )
    .reset_index()
)

# Recalcular participaciones después de la agrupación
resumen_tipo_dashboard["participacion_contratos_pct"] = (
    resumen_tipo_dashboard["numero_contratos"]
    / resumen_tipo_dashboard["numero_contratos"].sum()
    * 100
)

resumen_tipo_dashboard["participacion_valor_pct"] = (
    resumen_tipo_dashboard["valor_total"]
    / resumen_tipo_dashboard["valor_total"].sum()
    * 100
)

# =========================================================
# KPI PRINCIPALES
# =========================================================

# Número total de contratos analizados
kpi_numero_contratos = df_limpio["id_contrato"].count()

# Valor total contratado
kpi_valor_total = df_limpio["valor_del_contrato"].sum()

# Formato legible del valor total para el dashboard
kpi_valor_total_billones = kpi_valor_total / 1_000_000_000_000

# Modalidad con mayor participación en el valor contratado
fila_modalidad_lider = resumen_modalidad.loc[
    resumen_modalidad["participacion_valor_pct"].idxmax()
]

kpi_modalidad_lider = fila_modalidad_lider["modalidad_de_contratacion"]
kpi_modalidad_pct = fila_modalidad_lider["participacion_valor_pct"]

# Tipo de contrato con mayor participación en el valor contratado
fila_tipo_lider = resumen_tipo.loc[
    resumen_tipo["participacion_valor_pct"].idxmax()
]

kpi_tipo_lider = fila_tipo_lider["tipo_de_contrato"]
kpi_tipo_pct = fila_tipo_lider["participacion_valor_pct"]


orden_tipos = (
    resumen_tipo_dashboard
    .sort_values("participacion_valor_pct", ascending=False)["tipo_dashboard"]
    .tolist()
)

fig_tipo = go.Figure()

fig_tipo.add_trace(
    go.Bar(
        y=resumen_tipo_dashboard["tipo_dashboard"],
        x=resumen_tipo_dashboard["participacion_contratos_pct"],
        name="Participación en contratos",
        orientation="h",
        text=[
            f"{x:.1f}%"
            for x in resumen_tipo_dashboard["participacion_contratos_pct"]
        ],
        textposition="outside"
    )
)

fig_tipo.add_trace(
    go.Bar(
        y=resumen_tipo_dashboard["tipo_dashboard"],
        x=resumen_tipo_dashboard["participacion_valor_pct"],
        name="Participación en valor",
        orientation="h",
        text=[
            f"{x:.1f}%"
            for x in resumen_tipo_dashboard["participacion_valor_pct"]
        ],
        textposition="outside"
    )
)

fig_tipo.update_layout(
    title="Concentración por tipo de contrato: número de contratos vs. valor contratado",
    xaxis_title="Participación (%)",
    yaxis_title="",
    barmode="group",
    template="plotly",
    height=700
)

fig_tipo.update_yaxes(
    categoryorder="array",
    categoryarray=orden_tipos,
    autorange="reversed"
)

#fig_tipo.show()

#GRÁFICA 3 - Evolución de la composición

# =========================================================
# EVOLUCIÓN TEMPORAL - MODALIDAD
# =========================================================

evolucion_modalidad = (
    df_limpio
    .groupby(["año", "modalidad_de_contratacion"])
    .agg(
        valor_total=("valor_del_contrato", "sum")
    )
    .reset_index()
)

total_anual_modalidad = (
    evolucion_modalidad
    .groupby("año")["valor_total"]
    .sum()
    .reset_index(name="valor_total_anual")
)

evolucion_modalidad = evolucion_modalidad.merge(
    total_anual_modalidad,
    on="año",
    how="left"
)

evolucion_modalidad["participacion_valor_pct"] = (
    evolucion_modalidad["valor_total"]
    / evolucion_modalidad["valor_total_anual"]
    * 100
)

# Top 5 modalidades según participación acumulada en el valor contratado
modalidades_principales = [
    "Contratación directa",
    "Contratación Directa (con ofertas)",
    "Licitación pública Obra Publica",
    "Licitación pública",
    "Concurso de méritos abierto"
]

# Mantener las 5 principales y agrupar las demás
evolucion_modalidad["modalidad_dashboard"] = (
    evolucion_modalidad["modalidad_de_contratacion"]
    .where(
        evolucion_modalidad["modalidad_de_contratacion"].isin(
            modalidades_principales
        ),
        "Otras modalidades"
    )
)

# Sumar primero el valor contratado de las modalidades
# agrupadas dentro de cada año
evolucion_modalidad_dashboard = (
    evolucion_modalidad
    .groupby(["año", "modalidad_dashboard"])
    .agg(
        valor_total=("valor_total", "sum")
    )
    .reset_index()
)

# Calcular el valor total contratado de cada año
total_anual_dashboard = (
    evolucion_modalidad_dashboard
    .groupby("año")["valor_total"]
    .sum()
    .reset_index(name="valor_total_anual")
)

# Agregar el total anual a cada modalidad
evolucion_modalidad_dashboard = evolucion_modalidad_dashboard.merge(
    total_anual_dashboard,
    on="año",
    how="left"
)

# Calcular nuevamente la participación de cada modalidad
# dentro del valor total contratado de su año
evolucion_modalidad_dashboard["participacion_valor_pct"] = (
    evolucion_modalidad_dashboard["valor_total"]
    / evolucion_modalidad_dashboard["valor_total_anual"]
    * 100
)

# Etiqueta del año para identificar que 2026 es parcial
evolucion_modalidad_dashboard["año_etiqueta"] = (
    evolucion_modalidad_dashboard["año"].astype(str)
)

evolucion_modalidad_dashboard.loc[
    evolucion_modalidad_dashboard["año"] == 2026,
    "año_etiqueta"
] = "2026*"

# Orden de las categorías en la gráfica
orden_modalidad_temporal = [
    "Contratación directa",
    "Contratación Directa (con ofertas)",
    "Licitación pública Obra Publica",
    "Licitación pública",
    "Concurso de méritos abierto",
    "Otras modalidades"
]

# Crear gráfica de barras apiladas al 100 %
fig_evolucion_modalidad = px.bar(
    evolucion_modalidad_dashboard,
    x="año_etiqueta",
    y="participacion_valor_pct",
    color="modalidad_dashboard",
    barmode="stack",
    category_orders={
        "modalidad_dashboard": orden_modalidad_temporal,
        "año_etiqueta": [
            "2017", "2018", "2019", "2020", "2021",
            "2022", "2023", "2024", "2025", "2026*"
        ]
    },
    labels={
        "año_etiqueta": "Año",
        "participacion_valor_pct": "Participación en el valor contratado (%)",
        "modalidad_dashboard": "Modalidad"
    },
    title="Evolución de la composición del valor contratado por modalidad"
)

fig_evolucion_modalidad.update_traces(
    hovertemplate=(
        "<b>%{fullData.name}</b><br>"
        "Año: %{x}<br>"
        "Participación en valor: %{y:.1f}%"
        "<extra></extra>"
    )
)

fig_evolucion_modalidad.update_layout(
    height=650,
    yaxis=dict(
        range=[0, 100],
        ticksuffix="%"
    ),
    xaxis_title="Año",
    yaxis_title="Participación en el valor contratado (%)",
    legend=dict(
        title="Modalidad",
        orientation="h",
        yanchor="top",
        y=-0.18,
        xanchor="center",
        x=0.5
    ),
    margin=dict(
        l=80,
        r=40,
        t=80,
        b=160
    )
)

#fig_evolucion_modalidad.show()

# =========================================================
# EVOLUCIÓN TEMPORAL - TIPO DE CONTRATO
# =========================================================

# Calcular el valor contratado por tipo y año
evolucion_tipo = (
    df_limpio
    .groupby(["año", "tipo_de_contrato"])
    .agg(
        valor_total=("valor_del_contrato", "sum")
    )
    .reset_index()
)

# Top 5 tipos de contrato según participación global en valor
tipos_principales = [
    "Prestación de servicios",
    "Otro",
    "Obra",
    "Interventoría",
    "Seguros"
]

# Conservar el Top 5 y agrupar los demás
evolucion_tipo["tipo_dashboard"] = (
    evolucion_tipo["tipo_de_contrato"]
    .where(
        evolucion_tipo["tipo_de_contrato"].isin(
            tipos_principales
        ),
        "Resto de tipos"
    )
)

# Sumar primero el valor contratado de los tipos agrupados por año
evolucion_tipo_dashboard = (
    evolucion_tipo
    .groupby(["año", "tipo_dashboard"])
    .agg(
        valor_total=("valor_total", "sum")
    )
    .reset_index()
)

# Calcular el valor total contratado de cada año
total_anual_tipo = (
    evolucion_tipo_dashboard
    .groupby("año")["valor_total"]
    .sum()
    .reset_index(name="valor_total_anual")
)

# Agregar el total anual a cada categoría
evolucion_tipo_dashboard = evolucion_tipo_dashboard.merge(
    total_anual_tipo,
    on="año",
    how="left"
)

# Calcular la participación anual
evolucion_tipo_dashboard["participacion_valor_pct"] = (
    evolucion_tipo_dashboard["valor_total"]
    / evolucion_tipo_dashboard["valor_total_anual"]
    * 100
)

# Etiqueta para identificar que 2026 es parcial
evolucion_tipo_dashboard["año_etiqueta"] = (
    evolucion_tipo_dashboard["año"].astype(str)
)

evolucion_tipo_dashboard.loc[
    evolucion_tipo_dashboard["año"] == 2026,
    "año_etiqueta"
] = "2026*"

# Orden de categorías
orden_tipo_temporal = [
    "Prestación de servicios",
    "Otro",
    "Obra",
    "Interventoría",
    "Seguros",
    "Resto de tipos"
]

# Crear gráfica
fig_evolucion_tipo = px.bar(
    evolucion_tipo_dashboard,
    x="año_etiqueta",
    y="participacion_valor_pct",
    color="tipo_dashboard",
    barmode="stack",
    category_orders={
        "tipo_dashboard": orden_tipo_temporal,
        "año_etiqueta": [
            "2017", "2018", "2019", "2020", "2021",
            "2022", "2023", "2024", "2025", "2026*"
        ]
    },
    labels={
        "año_etiqueta": "Año",
        "participacion_valor_pct": "Participación en el valor contratado (%)",
        "tipo_dashboard": "Tipo de contrato"
    },
    title="Evolución de la composición del valor contratado por tipo de contrato"
)

fig_evolucion_tipo.update_traces(
    hovertemplate=(
        "<b>%{fullData.name}</b><br>"
        "Año: %{x}<br>"
        "Participación en valor: %{y:.1f}%"
        "<extra></extra>"
    )
)

fig_evolucion_tipo.update_layout(
    height=650,
    yaxis=dict(
        range=[0, 100],
        ticksuffix="%"
    ),
    xaxis_title="Año",
    yaxis_title="Participación en el valor contratado (%)",
    legend=dict(
        title="Tipo de contrato",
        orientation="h",
        yanchor="top",
        y=-0.18,
        xanchor="center",
        x=0.5
    ),
    margin=dict(
        l=80,
        r=40,
        t=80,
        b=160
    )
)

#fig_evolucion_tipo.show()

# =========================================================
# DASHBOARD
# =========================================================

# Estilo común para las tarjetas KPI
estilo_tarjeta = {
    "backgroundColor": "white",
    "borderRadius": "10px",
    "padding": "20px",
    "boxShadow": "0 2px 8px rgba(0,0,0,0.10)",
    "textAlign": "center",
    "flex": "1"
}


layout_manuela= html.Div(
    [

        # Título
        html.H1(
            "Composición de la contratación de la SDM",
            style={"textAlign": "center"}
        ),

        # Pregunta de negocio
        html.P(
            "¿Qué modalidades y tipos de contratación concentran la mayor parte "
            "del valor contratado por la Secretaría Distrital de Movilidad, "
            "y cómo ha cambiado esta composición a lo largo del tiempo?",
            style={
                "textAlign": "center",
                "fontSize": "18px"
            }
        ),

        # Tarjetas KPI
        html.Div(
            [

                html.Div(
                    [
                        html.H2(f"{kpi_numero_contratos:,}"),
                        html.P("Contratos analizados")
                    ],
                    style=estilo_tarjeta
                ),

                html.Div(
                    [
                        html.H2(
                            f"${kpi_valor_total_billones:.2f} billones"
                        ),
                        html.P("Valor contratado (COP)")
                    ],
                    style=estilo_tarjeta
                ),

                html.Div(
                    [
                        html.H3(kpi_modalidad_lider),
                        html.H2(f"{kpi_modalidad_pct:.1f}%"),
                        html.P("Modalidad líder en valor")
                    ],
                    style=estilo_tarjeta
                ),

                html.Div(
                    [
                        html.H3(kpi_tipo_lider),
                        html.H2(f"{kpi_tipo_pct:.1f}%"),
                        html.P("Tipo de contrato líder en valor")
                    ],
                    style=estilo_tarjeta
                )

            ],
            style={
                "display": "flex",
                "gap": "15px",
                "margin": "25px 0"
            }
        ),

        # Gráfica 1
        dcc.Graph(
            id="grafica-modalidad",
            figure=fig_modalidad
        ),

        # Gráfica 2
        dcc.Graph(
            id="grafica-tipo",
            figure=fig_tipo
        ),

        # Selector para la evolución temporal
html.Div(
    [
        html.H2(
            "Evolución de la composición del valor contratado",
            style={"textAlign": "center"}
        ),

        dcc.RadioItems(
            id="manuela-selector-temporal",
            options=[
                {
                    "label": "Modalidad",
                    "value": "modalidad"
                },
                {
                    "label": "Tipo de contrato",
                    "value": "tipo"
                }
            ],
            value="modalidad",
            inline=True,
            style={
                "textAlign": "center",
                "marginBottom": "20px"
            },
            labelStyle={
                "marginRight": "25px"
            }
        ),

        dcc.Graph(
            id="manuela-grafica-temporal",
            figure=fig_evolucion_modalidad
        )
    ]
)

    ],
    style={
        "padding": "30px",
        "backgroundColor": "#f5f6fa",
        "fontFamily": "Arial"
    }
)


# =========================================================
# CALLBACKS DE MANUELA
# =========================================================

def registrar_callbacks_manuela(app):

    @app.callback(
        Output("manuela-grafica-temporal", "figure"),
        Input("manuela-selector-temporal", "value")
    )
    def actualizar_grafica_temporal(dimension):

        if dimension == "tipo":
            return fig_evolucion_tipo

        return fig_evolucion_modalidad

# =========================================================
# EJECUCIÓN INDIVIDUAL
# =========================================================

if __name__ == "__main__":

    app = Dash(__name__)

    app.layout = layout_manuela

    registrar_callbacks_manuela(app)

    app.run(debug=True)