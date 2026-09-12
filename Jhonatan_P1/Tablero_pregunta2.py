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

CAPACIDAD_POR_DEFECTO = 40
CAPACIDAD_MAXIMA = 2000

#Callbacks
def registrar_callbacks(app):
 
    # --------------------------------------------------------------------------
    # Callback 1: indicadores y las tres graficas de diagnostico
    # --------------------------------------------------------------------------
    @app.callback(
        Output("p3_kpi_n", "children"), Output("p3_kpi_valor", "children"),
        Output("p3_kpi_mediana", "children"), Output("p3_kpi_criticos", "children"),
        Output("p3_g1", "figure"), Output("p3_g2", "figure"),
        Output("p3_g3", "figure"),
        Input("p3_umbral", "value"), Input("p3_dependencia", "value"),
        Input("p3_tipo", "value"), Input("p3_agrupador", "value"))
    def actualizar(umbral, deps, tipos, agrupador):
        datos, rezago = filtrar(umbral, deps, tipos)
 
        # ----- indicadores
        n = f"{len(rezago):,}".replace(",", ".")
        valor = f"${rezago['valor_del_contrato'].sum()/1e9:,.0f} mil M".replace(",", ".")
        mediana = f"{rezago['meses_desde_fin'].median():.0f}" if len(rezago) else "-"
        criticos = (f"{100*(rezago['meses_desde_fin'] > 24).mean():.0f}%"
                    if len(rezago) else "-")
 
        # ----- GRAFICA 1 (micropregunta 1)
        # Barras: cuantos cerrados y cuantos sin cerrar por ano de terminacion.
        # Linea sobre eje derecho: el porcentaje de cierre de cada cohorte.
        # Muestra que el cierre NO mejora con la antiguedad del contrato.
        coh = (datos.groupby("anio_fin")
               .agg(cerrados=("cerrado", "sum"), total=("cerrado", "size")))
        coh["sin_cerrar"] = coh["total"] - coh["cerrados"]
        coh["pct"] = (100 * coh["cerrados"] / coh["total"]).round(1)
 
        g1 = go.Figure()
        g1.add_bar(x=coh.index, y=coh["cerrados"], name="Cerrados",
                   marker_color=AZUL)
        g1.add_bar(x=coh.index, y=coh["sin_cerrar"], name="Sin cierre",
                   marker_color="#e2a6a6")
        g1.add_scatter(x=coh.index, y=coh["pct"], name="% de cierre", yaxis="y2",
                       mode="lines+markers", line=dict(color=ROJO, width=2))
        g1.update_layout(
            barmode="stack", title="1. El cierre no mejora con la antigüedad",
            xaxis_title="Año de terminación del contrato",
            yaxis_title="Contratos",
            yaxis2=dict(title="% cerrado", overlaying="y", side="right",
                        range=[0, 100]),
            height=340, margin=dict(l=10, r=10, t=45, b=10),
            plot_bgcolor="white", legend=dict(font=dict(size=10)))
 
        # ----- GRAFICA 2 (micropregunta 2)
        # Histograma del tiempo transcurrido, con los cortes legales marcados.
        g2 = px.histogram(rezago, x="meses_desde_fin", nbins=40,
                          color_discrete_sequence=[AZUL],
                          title="2. Cuánto llevan esperando los expedientes")
        for x, etiqueta in [(4, "4 m"), (6, "6 m"), (24, "24 m")]:
            g2.add_vline(x=x, line_dash="dash", line_color=ROJO,
                         annotation_text=etiqueta, annotation_font_size=10)
        g2.update_layout(height=340, margin=dict(l=10, r=10, t=45, b=10),
                         xaxis_title="Meses desde la terminación",
                         yaxis_title="Expedientes sin cierre",
                         plot_bgcolor="white", showlegend=False)
 
        # ----- GRAFICA 3 (micropregunta 3)
        # Ranking del grupo elegido, del que menos cierra al que mas.
        # El tamano de la burbuja es el valor comprometido sin cierre.
        resumen = (datos.groupby(agrupador)
                   .agg(contratos=("cerrado", "size"),
                        pct_cierre=("cerrado", "mean"))
                   .query("contratos >= 30"))
        resumen["pct_cierre"] = (100 * resumen["pct_cierre"]).round(1)
        valor_rezago = (rezago.groupby(agrupador)["valor_del_contrato"].sum() / 1e9)
        resumen["valor"] = valor_rezago.reindex(resumen.index).fillna(0).round(1)
        resumen = resumen.sort_values("pct_cierre")
 
        g3 = go.Figure(go.Bar(
            x=resumen["pct_cierre"], y=resumen.index, orientation="h",
            marker_color=AZUL, text=resumen["pct_cierre"].map(lambda v: f"{v:.0f}%"),
            textposition="outside",
            customdata=np.stack([resumen["contratos"], resumen["valor"]], axis=-1),
            hovertemplate="%{y}<br>%{x:.1f}% cerrado<br>"
                          "%{customdata[0]} contratos<br>"
                          "$%{customdata[1]} mil M sin cierre<extra></extra>"))
        g3.add_vline(x=100 * datos["cerrado"].mean(), line_dash="dash",
                     line_color=ROJO, annotation_text="promedio",
                     annotation_font_size=10)
        g3.update_layout(
            title="3. Dónde se concentra el rezago (grupos con 30 o más contratos)",
            xaxis_title="% de expedientes cerrados", height=380,
            margin=dict(l=10, r=40, t=45, b=10), plot_bgcolor="white")
 
        return n, valor, mediana, criticos, g1, g2, g3
 
    # --------------------------------------------------------------------------
    # Callback 2: simulador de depuracion
    # --------------------------------------------------------------------------
    @app.callback(
        Output("p3_g4", "figure"), Output("p3_texto_sim", "children"),
        Input("p3_umbral", "value"), Input("p3_dependencia", "value"),
        Input("p3_tipo", "value"), Input("p3_capacidad", "value"),
        Input("p3_regla", "value"))
    def simular(umbral, deps, tipos, capacidad, regla):
        _, rezago = filtrar(umbral, deps, tipos)
        total = len(rezago)
 
        # ----- validacion de la capacidad ingresada -------------------------
        # El campo puede llegar vacio, con texto, con cero o con un numero
        # absurdo. Se corrige el valor y se avisa al usuario en vez de fallar.
        aviso = ""
        try:
            capacidad = int(float(capacidad))
        except (TypeError, ValueError):
            capacidad = CAPACIDAD_POR_DEFECTO
            aviso = " (se usó el valor por defecto porque el campo estaba vacío)"
 
        if capacidad < 1:
            capacidad = 1
            aviso = " (mínimo 1 expediente por semana)"
        elif capacidad > CAPACIDAD_MAXIMA:
            capacidad = CAPACIDAD_MAXIMA
            aviso = f" (se limitó a {CAPACIDAD_MAXIMA} por semana)"
 
        # ----- caso sin expedientes ----------------------------------------
        if total == 0:
            vacia = go.Figure()
            vacia.add_annotation(text="No hay expedientes rezagados con estos filtros",
                                 showarrow=False, font=dict(size=13, color=GRIS),
                                 x=0.5, y=0.5, xref="paper", yref="paper")
            vacia.update_layout(height=260, plot_bgcolor="white",
                                margin=dict(l=10, r=10, t=45, b=10),
                                xaxis=dict(visible=False), yaxis=dict(visible=False),
                                title="Expedientes pendientes según avanza el trabajo")
            return vacia, "No hay expedientes rezagados con estos filtros."
 
        # ----- ordenar segun la regla que eligio el usuario -----------------
        if regla == "antiguedad":
            orden = rezago.sort_values("meses_desde_fin", ascending=False)
        elif regla == "valor":
            orden = rezago.sort_values("valor_del_contrato", ascending=False)
        else:
            r = rezago.copy()
            for col in ["meses_desde_fin", "valor_del_contrato"]:
                rango = r[col].max() - r[col].min()
                r["n_" + col] = 0.5 if rango == 0 else (r[col] - r[col].min()) / rango
            r["puntaje"] = 0.5 * r["n_meses_desde_fin"] + 0.5 * r["n_valor_del_contrato"]
            orden = r.sort_values("puntaje", ascending=False)
 
        # ----- curva de agotamiento ----------------------------------------
        # Si la capacidad alcanza para todo, el trabajo termina en la primera
        # semana y la curva tiene solo dos puntos: el inicio y el cero.
        semanas = int(np.ceil(total / capacidad))
        eje = np.arange(0, semanas + 1)
        pendientes = np.maximum(total - capacidad * eje, 0)
 
        fig = go.Figure(go.Scatter(x=eje, y=pendientes, mode="lines+markers"
                                   if semanas <= 12 else "lines",
                                   line=dict(color=AZUL, width=3), fill="tozeroy",
                                   fillcolor="rgba(43,108,176,.12)",
                                   hovertemplate="Semana %{x}<br>"
                                                 "%{y} expedientes pendientes"
                                                 "<extra></extra>"))
        fig.update_layout(title="Expedientes pendientes según avanza el trabajo",
                          xaxis_title="Semanas", yaxis_title="Expedientes pendientes",
                          height=260, margin=dict(l=10, r=10, t=45, b=10),
                          plot_bgcolor="white",
                          xaxis=dict(range=[0, max(semanas, 1)]),
                          yaxis=dict(range=[0, total * 1.08]))
 
        # ----- expedientes que cruzarian los 24 meses en el camino ----------
        orden = orden.reset_index(drop=True)
        semana_atencion = np.floor(orden.index / capacidad) + 1
        meses_al_atender = orden["meses_desde_fin"] + semana_atencion / 4.33
        cruzan = int(((orden["meses_desde_fin"] <= 24) & (meses_al_atender > 24)).sum())
 
        # ----- texto del resultado -----------------------------------------
        if capacidad >= total:
            duracion = "menos de una semana (0,0 meses)"
        else:
            duracion = f"{semanas} semanas ({semanas/4.33:.1f} meses)"
 
        texto = html.Span([
            f"Con {capacidad} expedientes por semana{aviso}, depurar los "
            f"{total:,} rezagados toma cerca de ".replace(",", "."),
            html.B(duracion),
            f". Con esta regla, {cruzan} expedientes que hoy están dentro del "
            f"término de 24 meses lo superarían antes de ser atendidos.",
        ])
        return fig, texto



