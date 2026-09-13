
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

AZUL, NARANJA, GRIS = "#2b6cb0", "#dd6b20", "#718096"
VERDE, ROJO = "#2f855a", "#c53030"

FECHAS = ["fecha_de_firma", "fecha_de_inicio_del_contrato", "fecha_de_fin_del_contrato"]
base = pd.read_csv("datos_limpios.csv", low_memory=False, parse_dates=FECHAS)

# 2019 tiene un vacio de reporte en la fuente
df = base[base["anio_firma"] != 2019].copy()
df["anio_firma"] = df["anio_firma"].astype(int)

ANIOS = sorted(int(a) for a in df["anio_firma"].unique())
ANIO_MIN, ANIO_MAX = ANIOS[0], ANIOS[-1]

CAJA = {"backgroundColor": "white", "padding": "18px", "borderRadius": "10px",
        "boxShadow": "0 1px 3px rgba(0,0,0,.08)", "marginBottom": "16px"}
CAJA_KPI = {**CAJA, "flex": "1", "textAlign": "center", "margin": "0 6px",
            "padding": "14px"}
NOTA = {"fontSize": "12px", "color": GRIS, "marginTop": "8px", "lineHeight": "1.5"}


def kpi(titulo, id_valor, id_nota):
    return html.Div([
        html.Div(titulo, style={"fontSize": "12px", "color": GRIS}),
        html.Div(id=id_valor, style={"fontSize": "26px", "fontWeight": "700",
                                     "color": AZUL, "margin": "4px 0"}),
        html.Div(id=id_nota, style={"fontSize": "11px", "color": GRIS}),
    ], style=CAJA_KPI)


def tarjeta_grafica(id_grafica, pregunta, como_leer):
    """Envuelve cada grafica con la pregunta que responde y como interpretarla."""
    return html.Div([
        html.Div(pregunta, style={"fontSize": "14px", "fontWeight": "600",
                                  "color": "#2d3748", "marginBottom": "4px"}),
        dcc.Graph(id=id_grafica),
        html.Div([html.B("Cómo leer esta gráfica. "), como_leer], style=NOTA),
    ], style=CAJA)


layout = html.Div([

    html.H3("¿De cuántos proveedores depende la Secretaría?",
            style={"marginBottom": "4px"}),
    html.P("Este tablero muestra cómo se reparte el presupuesto de contratación "
           "entre los contratistas de la entidad y con qué frecuencia se vuelve a "
           "contratar a los mismos de un año a otro. El propósito es identificar "
           "riesgos de dependencia y de continuidad en la operación.",
           style={"color": GRIS, "fontSize": "13px", "maxWidth": "900px"}),

    # ----- Lectura rapida: se actualiza con los filtros -----
    html.Div(id="p1-resumen",
             style={**CAJA, "borderLeft": f"4px solid {AZUL}",
                    "backgroundColor": "#f7fafc"}),

    # ----- Filtros -----
    html.Div([
        html.Div([
            html.Label("Periodo que desea revisar",
                       style={"fontSize": "12px", "fontWeight": "600"}),
            dcc.RangeSlider(id="p1-anios", min=ANIO_MIN, max=ANIO_MAX, step=1,
                            value=[ANIO_MIN, ANIO_MAX],
                            marks={a: str(a) for a in ANIOS}),
        ], style={"flex": "3"}),
        html.Div([
            html.Label("Tipo de contratista",
                       style={"fontSize": "12px", "fontWeight": "600"}),
            dcc.Checklist(id="p1-tipo",
                          options=[{"label": " Personas (contratos de prestación de servicios)",
                                    "value": "Natural"},
                                   {"label": " Empresas (personas jurídicas)",
                                    "value": "Juridica"}],
                          value=["Natural", "Juridica"],
                          labelStyle={"display": "block", "fontSize": "12px",
                                      "marginTop": "6px"}),
        ], style={"flex": "2", "paddingLeft": "40px"}),
    ], style={**CAJA, "display": "flex"}),

    # ----- Indicadores -----
    html.Div([
        kpi("Contratos firmados", "p1-kpi-contratos", "p1-nota-contratos"),
        kpi("Contratistas distintos", "p1-kpi-proveedores", "p1-nota-proveedores"),
        kpi("Presupuesto comprometido", "p1-kpi-valor", "p1-nota-valor"),
        kpi("Desigualdad del reparto", "p1-kpi-gini", "p1-nota-gini"),
        kpi("Nivel de concentración", "p1-kpi-hhi", "p1-nota-hhi"),
        kpi("Peso de los 10 mayores", "p1-kpi-top10", "p1-nota-top10"),
    ], style={"display": "flex", "marginBottom": "16px"}),

    # ----- Graficas -----
    html.Div([
        html.Div(tarjeta_grafica(
            "p1-lorenz",
            "¿Qué tan parejo es el reparto del presupuesto?",
            "La línea punteada es el reparto perfectamente igualitario: cada "
            "contratista recibiría lo mismo. Entre más se aleje la curva azul de "
            "esa línea, más desigual es el reparto real. El área sombreada es la "
            "brecha entre ambos."), style={"flex": "1"}),
        html.Div(tarjeta_grafica(
            "p1-participacion",
            "¿Quién firma más contratos y quién se lleva más dinero?",
            "Las dos barras de cada grupo deberían ser parecidas si el reparto "
            "fuera proporcional. Cuando la barra naranja supera ampliamente a la "
            "azul, ese grupo concentra mucho más dinero del que su número de "
            "contratos sugiere."), style={"flex": "1"}),
    ], style={"display": "flex", "gap": "16px"}),

    tarjeta_grafica(
        "p1-hhi",
        "¿La dependencia está aumentando o disminuyendo?",
        "La línea azul mide qué tan concentrado está el dinero cada año: sube "
        "cuando pocos contratistas acaparan más. Las barras grises muestran cuántos "
        "contratistas hubo ese año. Si las barras crecen pero la línea también, "
        "significa que entran más contratistas pequeños sin reducir la dependencia "
        "de los grandes."),

    tarjeta_grafica(
        "p1-top",
        "¿Cuáles son los contratistas de los que más depende la entidad?",
        "Cada barra es un contratista y su longitud es el dinero acumulado en el "
        "periodo seleccionado. El porcentaje al final indica qué parte del "
        "presupuesto total representa. Son los nombres cuya salida tendría mayor "
        "impacto sobre la operación."),

    tarjeta_grafica(
        "p1-retencion",
        "¿Qué tan estable es el equipo de contratistas?",
        "Mide qué porcentaje de los contratistas de cada año ya trabajaba con la "
        "entidad el año anterior. Un valor alto indica continuidad y conocimiento "
        "acumulado, pero también que la operación depende de personas sin vínculo "
        "laboral cuya permanencia se renueva año a año."),

    html.Div([
        html.B("Sobre los datos. "),
        "Contratos registrados en SECOP II entre julio de 2017 y agosto de 2026. "
        "Se excluyen los procesos que nunca se firmaron, los contratos sin valor y "
        "aquellos en los que la plataforma no identifica al contratista. El año 2019 "
        "se omite porque presenta un vacío de reporte en la fuente, y 2026 cubre "
        "solo hasta agosto.",
    ], style={**CAJA, "fontSize": "11px", "color": GRIS}),
])


def filtrar(rango, tipos):
    return df[(df["anio_firma"] >= rango[0]) &
              (df["anio_firma"] <= rango[1]) &
              (df["tipo_persona"].isin(tipos))]


def gini(valores):
    v = np.sort(np.asarray(valores, dtype=float))
    n = len(v)
    if n == 0 or v.sum() == 0:
        return np.nan
    return (n + 1 - 2 * np.sum(np.cumsum(v)) / v.sum()) / n


def hhi(datos):
    participacion = datos.groupby("documento_proveedor")["valor_del_contrato"].sum()
    if len(participacion) == 0 or participacion.sum() == 0:
        return np.nan
    proporcion = participacion / participacion.sum()
    return float((proporcion ** 2).sum() * 10000)


def nivel_gini(valor):
    if valor < 0.4:
        return "Reparto equilibrado"
    if valor < 0.6:
        return "Desigualdad moderada"
    if valor < 0.8:
        return "Desigualdad alta"
    return "Desigualdad muy alta"


def nivel_hhi(valor):
    # Umbrales usados por las autoridades de competencia para medir concentracion
    if valor < 1500:
        return "Mercado poco concentrado"
    if valor < 2500:
        return "Concentración moderada"
    return "Concentración elevada"


def miles(numero):
    return f"{numero:,.0f}".replace(",", ".")


def figura_vacia(mensaje):
    fig = go.Figure()
    fig.update_layout(title=mensaje, template="simple_white")
    return fig


def registrar_callbacks(app):

    # ----- Lectura rapida en lenguaje corriente -----
    @app.callback(
        Output("p1-resumen", "children"),
        [Input("p1-anios", "value"), Input("p1-tipo", "value")]
    )
    def actualizar_resumen(rango, tipos):
        datos = filtrar(rango, tipos)
        if len(datos) == 0:
            return html.Div("No hay contratos con los filtros seleccionados.")

        por_proveedor = datos.groupby("documento_proveedor")["valor_del_contrato"].sum()
        g = gini(por_proveedor.values)

        # Cuantos contratistas acumulan la mitad del presupuesto
        ordenados = por_proveedor.sort_values(ascending=False)
        acumulado = ordenados.cumsum() / ordenados.sum()
        n_mitad = int((acumulado < 0.5).sum() + 1)
        pct_mitad = n_mitad / len(ordenados) * 100

        # Retencion del ultimo ano disponible en la seleccion
        anios = sorted(datos["anio_firma"].unique())
        texto_retencion = ""
        if len(anios) >= 2 and anios[-1] - anios[-2] == 1:
            previo = set(datos.loc[datos.anio_firma == anios[-2], "documento_proveedor"])
            actual = set(datos.loc[datos.anio_firma == anios[-1], "documento_proveedor"])
            pct = len(previo & actual) / len(actual) * 100
            texto_retencion = (f" En {anios[-1]}, {pct:.0f} de cada 100 contratistas "
                               f"ya trabajaban con la entidad el año anterior.")

        return html.Div([
            html.Div("Lectura rápida", style={"fontSize": "12px", "fontWeight": "700",
                                              "color": AZUL, "marginBottom": "6px"}),
            html.P([
                f"Entre {rango[0]} y {rango[1]} la Secretaría firmó ",
                html.B(f"{miles(len(datos))} contratos"),
                " con ",
                html.B(f"{miles(datos.documento_proveedor.nunique())} contratistas "
                       f"distintos"),
                f", por un total de ",
                html.B(f"${datos.valor_del_contrato.sum() / 1e12:,.2f} billones"),
                ". ",
                html.B(f"{miles(n_mitad)} contratistas"),
                f" ({pct_mitad:.1f}% del total) concentran la mitad de ese dinero, "
                f"lo que corresponde a un reparto con ",
                html.B(nivel_gini(g).lower()),
                ".", texto_retencion,
            ], style={"fontSize": "14px", "lineHeight": "1.7", "margin": "0"}),
        ])

    # ----- Indicadores -----
    @app.callback(
        [Output("p1-kpi-contratos", "children"),
         Output("p1-nota-contratos", "children"),
         Output("p1-kpi-proveedores", "children"),
         Output("p1-nota-proveedores", "children"),
         Output("p1-kpi-valor", "children"),
         Output("p1-nota-valor", "children"),
         Output("p1-kpi-gini", "children"),
         Output("p1-nota-gini", "children"),
         Output("p1-kpi-hhi", "children"),
         Output("p1-nota-hhi", "children"),
         Output("p1-kpi-top10", "children"),
         Output("p1-nota-top10", "children")],
        [Input("p1-anios", "value"), Input("p1-tipo", "value")]
    )
    def actualizar_kpis(rango, tipos):
        datos = filtrar(rango, tipos)
        if len(datos) == 0:
            return ["-", "sin datos"] * 6

        por_proveedor = datos.groupby("documento_proveedor")["valor_del_contrato"].sum()
        g = gini(por_proveedor.values)
        h = hhi(datos)
        top10 = por_proveedor.nlargest(10).sum() / por_proveedor.sum() * 100
        contratos_por_proveedor = len(datos) / datos.documento_proveedor.nunique()

        return (
            miles(len(datos)), f"entre {rango[0]} y {rango[1]}",
            miles(datos.documento_proveedor.nunique()),
            f"{contratos_por_proveedor:.1f} contratos cada uno en promedio",
            f"${datos.valor_del_contrato.sum() / 1e12:,.2f} B", "billones de pesos",
            f"{g:.3f}", nivel_gini(g),
            miles(h), nivel_hhi(h),
            f"{top10:.1f}%", "del presupuesto en 10 contratistas",
        )

    @app.callback(
        Output("p1-lorenz", "figure"),
        [Input("p1-anios", "value"), Input("p1-tipo", "value")]
    )
    def actualizar_lorenz(rango, tipos):
        datos = filtrar(rango, tipos)
        por_proveedor = datos.groupby("documento_proveedor")["valor_del_contrato"].sum()
        valores = np.sort(por_proveedor.values)
        n = len(valores)

        if n == 0:
            return figura_vacia("Sin datos para la selección")

        x = np.arange(1, n + 1) / n
        y = np.cumsum(valores) / valores.sum()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x, y=y, mode="lines", name="Reparto real",
            line=dict(color=AZUL, width=3), fill="tozeroy",
            hovertemplate="El %{x:.0%} de contratistas con menor valor<br>"
                          "recibe el %{y:.1%} del presupuesto<extra></extra>"))
        fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines",
                                 name="Si todos recibieran lo mismo",
                                 line=dict(color=GRIS, dash="dash"),
                                 hoverinfo="skip"))
        fig.update_layout(
            title=f"Desigualdad del reparto: {nivel_gini(gini(valores)).lower()}",
            xaxis_title="Contratistas, del que menos recibe al que más",
            yaxis_title="Parte del presupuesto acumulada",
            xaxis_tickformat=".0%", yaxis_tickformat=".0%",
            template="simple_white", height=430,
            legend=dict(orientation="h", y=1.1))
        return fig

    @app.callback(
        Output("p1-participacion", "figure"),
        [Input("p1-anios", "value"), Input("p1-tipo", "value")]
    )
    def actualizar_participacion(rango, tipos):
        datos = filtrar(rango, tipos)
        if len(datos) == 0:
            return figura_vacia("Sin datos para la selección")

        resumen = datos.groupby("tipo_persona").agg(
            contratos=("id_contrato", "count"),
            valor=("valor_del_contrato", "sum")).reset_index()
        resumen["etiqueta"] = resumen["tipo_persona"].map(
            {"Natural": "Personas", "Juridica": "Empresas"})

        pct_contratos = resumen["contratos"] / resumen["contratos"].sum() * 100
        pct_valor = resumen["valor"] / resumen["valor"].sum() * 100

        fig = go.Figure()
        fig.add_trace(go.Bar(x=resumen["etiqueta"], y=pct_contratos,
                             name="Cuántos contratos firman", marker_color=AZUL,
                             text=[f"{v:.1f}%" for v in pct_contratos],
                             textposition="outside"))
        fig.add_trace(go.Bar(x=resumen["etiqueta"], y=pct_valor,
                             name="Cuánto dinero reciben", marker_color=NARANJA,
                             text=[f"{v:.1f}%" for v in pct_valor],
                             textposition="outside"))
        fig.update_layout(title="Contratos firmados frente a dinero recibido",
                          yaxis_title="Porcentaje del total (%)",
                          yaxis_range=[0, 110], barmode="group",
                          template="simple_white", height=430,
                          legend=dict(orientation="h", y=1.1))
        return fig

    @app.callback(
        Output("p1-hhi", "figure"),
        [Input("p1-anios", "value"), Input("p1-tipo", "value")]
    )
    def actualizar_hhi(rango, tipos):
        datos = filtrar(rango, tipos)
        if len(datos) == 0:
            return figura_vacia("Sin datos para la selección")

        filas = []
        for anio, grupo in datos.groupby("anio_firma"):
            filas.append({"anio": int(anio), "hhi": hhi(grupo),
                          "proveedores": grupo["documento_proveedor"].nunique()})
        serie = pd.DataFrame(filas)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=serie["anio"], y=serie["proveedores"], name="Contratistas activos",
            marker_color=GRIS, opacity=0.3, yaxis="y2",
            hovertemplate="%{y} contratistas en %{x}<extra></extra>"))
        fig.add_trace(go.Scatter(
            x=serie["anio"], y=serie["hhi"], mode="lines+markers",
            name="Nivel de concentración", line=dict(color=AZUL, width=3),
            hovertemplate="Concentración: %{y:.0f} en %{x}<extra></extra>"))
        fig.update_layout(
            title="Evolución de la dependencia año por año",
            xaxis_title="Año de firma del contrato",
            yaxis=dict(title="Concentración del dinero (más alto = más dependencia)"),
            yaxis2=dict(title="Número de contratistas", overlaying="y",
                        side="right", showgrid=False),
            template="simple_white", height=430,
            legend=dict(orientation="h", y=1.12))
        return fig

    @app.callback(
        Output("p1-top", "figure"),
        [Input("p1-anios", "value"), Input("p1-tipo", "value")]
    )
    def actualizar_top(rango, tipos):
        datos = filtrar(rango, tipos)
        if len(datos) == 0:
            return figura_vacia("Sin datos para la selección")

        total = datos["valor_del_contrato"].sum()
        top = (datos.groupby(["documento_proveedor", "proveedor_adjudicado"])
               ["valor_del_contrato"].sum().nlargest(15).reset_index())
        top["valor_millones"] = top["valor_del_contrato"] / 1e6
        top["pct"] = top["valor_del_contrato"] / total * 100
        top["nombre"] = top["proveedor_adjudicado"].astype(str).str.slice(0, 45)
        top = top.sort_values("valor_millones")

        fig = go.Figure(go.Bar(
            x=top["valor_millones"], y=top["nombre"], orientation="h",
            marker_color=AZUL, text=[f"{p:.1f}%" for p in top["pct"]],
            textposition="outside",
            hovertemplate="%{y}<br>$%{x:,.0f} millones<extra></extra>"))
        fig.update_layout(
            title=f"Los 15 mayores concentran {top['pct'].sum():.1f}% del presupuesto",
            xaxis_title="Dinero contratado (millones de pesos)",
            template="simple_white", height=540, margin=dict(l=10))
        return fig

    @app.callback(
        Output("p1-retencion", "figure"),
        [Input("p1-anios", "value"), Input("p1-tipo", "value")]
    )
    def actualizar_retencion(rango, tipos):
        datos = filtrar(rango, tipos)
        anios = sorted(datos["anio_firma"].unique())

        if len(anios) < 2:
            return figura_vacia("Seleccione al menos dos años para ver la retención")

        conjuntos = {a: set(datos.loc[datos.anio_firma == a, "documento_proveedor"])
                     for a in anios}

        filas = []
        for i in range(len(anios) - 1):
            a, b = anios[i], anios[i + 1]
            if b - a != 1:
                continue
            comunes = len(conjuntos[a] & conjuntos[b])
            filas.append({"anio": b, "retencion": comunes / len(conjuntos[b]) * 100,
                          "nuevos": 100 - comunes / len(conjuntos[b]) * 100})

        if not filas:
            return figura_vacia("Sin años consecutivos en la selección")

        serie = pd.DataFrame(filas)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=serie["anio"], y=serie["retencion"], name="Ya trabajaban antes",
            marker_color=AZUL,
            hovertemplate="%{y:.0f}% ya trabajaban con la entidad<extra></extra>"))
        fig.add_trace(go.Bar(
            x=serie["anio"], y=serie["nuevos"], name="Contratistas nuevos",
            marker_color=NARANJA,
            hovertemplate="%{y:.0f}% son nuevos<extra></extra>"))
        fig.update_layout(
            title="Composición de los contratistas de cada año",
            xaxis_title="Año", yaxis_title="Porcentaje de los contratistas (%)",
            barmode="stack", template="simple_white", height=430,
            legend=dict(orientation="h", y=1.12))
        return fig


# Permite abrir el tablero directamente con: python tablero.py
if __name__ == "__main__":
    from dash import Dash

    app = Dash(__name__)
    app.layout = layout
    registrar_callbacks(app)
    app.run(debug=True)