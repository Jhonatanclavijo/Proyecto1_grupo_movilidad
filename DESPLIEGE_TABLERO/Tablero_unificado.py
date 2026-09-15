import os
import unicodedata
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from dash import Dash, Input, Output, dcc, html
# ===========================================================================
# 1. ESTILOS
# Paleta, plantilla de plotly y componentes que comparten las tres
# secciones. Antes era el módulo estilos.py.
# ===========================================================================
# ---------------------------------------------------------------------------
# Paleta
# ---------------------------------------------------------------------------
# Azul institucional como color de dato principal, naranja como contraste
# (solo cuando hay dos series que comparar) y rojo reservado para los cortes
# normativos y las alertas. El gris es texto secundario.
AZUL = "#2b6cb0"
AZUL_OSCURO = "#1a365d"
AZUL_CLARO = "#bee3f8"
NARANJA = "#dd6b20"
ROJO = "#c53030"
ROSA = "#e2a6a6"
VERDE = "#2f855a"
GRIS = "#718096"
GRIS_CLARO = "#e2e8f0"
TEXTO = "#2d3748"
FONDO = "#f7fafc"
# Secuencia para graficas categoricas (evolucion por modalidad / tipo).
SECUENCIA = [AZUL, NARANJA, VERDE, "#805ad5", "#d69e2e", GRIS]
 
TIPOGRAFIA = ('"Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, '
              '"Helvetica Neue", Arial, sans-serif')
# ---------------------------------------------------------------------------
# Plantilla de plotly
# ---------------------------------------------------------------------------
# Se registra una sola vez y se fija como plantilla por defecto, de modo que
# tanto las figuras hechas con plotly.express como las hechas con
# graph_objects salgan con la misma tipografia, margenes y grillas.
PLANTILLA = go.layout.Template()
PLANTILLA.layout = go.Layout(
    font=dict(family=TIPOGRAFIA, size=12, color=TEXTO),
    # El titulo se ancla al borde superior del contenedor para que nunca
    # compita con la leyenda, que va justo encima del area de dibujo.
    title=dict(font=dict(size=15, color=AZUL_OSCURO), x=0, xanchor="left",
               y=0.97, yanchor="top", yref="container"),
    paper_bgcolor="white",
    plot_bgcolor="white",
    colorway=SECUENCIA,
    # separators=",." hace que plotly escriba las cifras a la colombiana:
    # punto para los miles y coma para los decimales. Aplica a ejes,
    # etiquetas de barras y ventanas emergentes.
    separators=",.",
    # automargin deja que plotly agrande el margen segun lo que midan las
    # etiquetas. Sin esto los nombres largos (modalidades, contratistas)
    # salen cortados.
    xaxis=dict(showgrid=False, linecolor=GRIS_CLARO, ticks="outside",
               tickcolor=GRIS_CLARO, zeroline=False, automargin=True),
    yaxis=dict(gridcolor=GRIS_CLARO, linecolor=GRIS_CLARO, zeroline=False,
               automargin=True),
    legend=dict(font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
    margin=dict(l=60, r=30, t=80, b=55),
    hoverlabel=dict(font=dict(family=TIPOGRAFIA, size=12)),
)
pio.templates["tablero_sdm"] = PLANTILLA
pio.templates.default = "tablero_sdm"
# ---------------------------------------------------------------------------
# Estilos de bloque
# ---------------------------------------------------------------------------
# Posicion unica para las leyendas horizontales: pegadas al borde superior
# del area de dibujo, alineadas a la izquierda con el titulo. Se usa en todas
# las secciones para que las graficas no queden cada una con su criterio.
LEYENDA_SUPERIOR = dict(orientation="h", yanchor="bottom", y=1.0,
                        xanchor="left", x=0)
CAJA = {
    "backgroundColor": "white",
    "padding": "18px",
    "borderRadius": "8px",
    "border": f"1px solid {GRIS_CLARO}",
    "marginBottom": "16px",
}
 
CAJA_KPI = {**CAJA, "flex": "1", "minWidth": "150px", "textAlign": "center",
            "padding": "14px 10px", "marginBottom": "0"}
 
CAJA_NOTA = {**CAJA, "borderLeft": f"3px solid {AZUL}", "backgroundColor": "#f7fbff",
             "fontSize": "12.5px", "lineHeight": "1.6"}
 
FILA_KPI = {"display": "flex", "flexWrap": "wrap", "gap": "12px",
            "marginBottom": "16px"}
 
ETIQUETA = {"fontSize": "12px", "fontWeight": "600", "color": TEXTO,
            "display": "block", "marginBottom": "6px"}
 
NOTA = {"fontSize": "12px", "color": GRIS, "marginTop": "10px",
        "lineHeight": "1.6"}
 
PIE_DATOS = {**CAJA, "fontSize": "11.5px", "color": GRIS, "lineHeight": "1.6",
             "backgroundColor": "transparent", "border": "none",
             "borderTop": f"1px solid {GRIS_CLARO}", "borderRadius": "0",
             "padding": "14px 0 0 0"}
# ---------------------------------------------------------------------------
# Componentes reutilizables
# ---------------------------------------------------------------------------
def kpi(titulo, id_valor, id_nota=None, nota=None):
    """Tarjeta de indicador.
 
    El valor siempre lo llena un callback. La nota puede ser fija (texto que
    explica la unidad) o dinamica (se le pasa un id y la llena el callback).
    """
    pie = (html.Div(id=id_nota, style={"fontSize": "11px", "color": GRIS})
           if id_nota else
           html.Div(nota or "", style={"fontSize": "11px", "color": GRIS}))
    return html.Div([
        html.Div(titulo, style={"fontSize": "11.5px", "color": GRIS,
                                "minHeight": "30px"}),
        html.Div(id=id_valor, style={"fontSize": "25px", "fontWeight": "700",
                                     "color": AZUL, "margin": "6px 0 4px"}),
        pie,
    ], style=CAJA_KPI)
def tarjeta_grafica(id_grafica, pregunta, como_leer, alto=None, extra=None):
    """Envuelve una grafica con la pregunta que responde y como interpretarla.
 
    Es el patron que se repite en las tres secciones: el usuario final no es
    analista, asi que cada grafica viene con su pregunta arriba y su lectura
    abajo.
    """
    hijos = [html.Div(pregunta, style={"fontSize": "14px", "fontWeight": "600",
                                       "color": TEXTO, "marginBottom": "8px"})]
    if extra is not None:
        hijos.append(extra)
    hijos.append(dcc.Graph(id=id_grafica, config={"displayModeBar": False},
                           style={"height": f"{alto}px"} if alto else None))
    hijos.append(html.Div([html.B("Cómo leer esta gráfica. "), como_leer],
                          style=NOTA))
    return html.Div(hijos, style=CAJA)
def encabezado_seccion(titulo, pregunta):
    """Titulo de la seccion y la pregunta de negocio que resuelve."""
    return html.Div([
        html.H2(titulo, style={"fontSize": "21px", "fontWeight": "600",
                               "color": AZUL_OSCURO, "margin": "0 0 6px"}),
        html.P(pregunta, style={"color": GRIS, "fontSize": "13.5px",
                                "maxWidth": "78ch", "lineHeight": "1.6",
                                "margin": "0 0 18px"}),
    ])
def figura_vacia(mensaje, alto=340):
    """Estado vacio explicito: dice que pasó y que hacer, no una grafica en blanco."""
    fig = go.Figure()
    fig.add_annotation(text=mensaje, showarrow=False, x=0.5, y=0.5,
                       xref="paper", yref="paper",
                       font=dict(size=13, color=GRIS))
    fig.update_layout(height=alto, xaxis=dict(visible=False),
                      yaxis=dict(visible=False))
    return fig
def numero(valor, decimales=0):
    """Cifra escrita a la colombiana: punto para miles, coma para decimales.
 
    Python formatea al reves ("1,234.56"), asi que se intercambian los dos
    separadores usando un caracter intermedio para no pisar el resultado.
    """
    return (f"{valor:,.{decimales}f}"
            .replace(",", "\x00").replace(".", ",").replace("\x00", "."))
def miles(valor):
    """Cantidad entera con separador de miles."""
    return numero(valor, 0)
def pesos(valor):
    """Cifra de dinero en la escala mas legible segun su magnitud."""
    if valor >= 1e12:
        return f"${numero(valor / 1e12, 2)} B"
    if valor >= 1e9:
        return f"${numero(valor / 1e9, 0)} mil M"
    return f"${numero(valor / 1e6, 0)} M"
def porcentaje(valor, decimales=1):
    """Porcentaje con coma decimal."""
    return f"{numero(valor, decimales)}%"
# Plantilla HTML de la página. Reemplaza lo que antes estaba en
# assets/estilo.css: ancho de lectura, pestañas, foco del teclado y ajustes
# para pantallas pequeñas.
PLANTILLA_HTML = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
        /* Hoja de estilos global del tablero.
           Dash carga automáticamente todo lo que esté en la carpeta assets/.
           Aquí va lo que no se puede resolver con estilos en línea desde Python:
           el ancho de la página, el comportamiento de las pestañas, el foco del
           teclado y los ajustes para pantallas pequeñas. */
        
        html, body {
            margin: 0;
            padding: 0;
            background-color: #f7fafc;
            -webkit-font-smoothing: antialiased;
        }
        
        /* ---------- Navegación por pestañas ---------- */
        
        .navegacion {
            background-color: #ffffff;
            border-bottom: 1px solid #e2e8f0;
            padding: 0 28px;
            position: sticky;
            top: 0;
            z-index: 10;
            overflow-x: auto;
        }
        
        .navegacion .tab {
            cursor: pointer;
            white-space: nowrap;
            transition: color .12s ease;
        }
        
        .navegacion .tab:hover {
            color: #2b6cb0;
        }
        
        /* Contenido de cada pestaña: ancho de lectura acotado y centrado. */
        .contenido {
            max-width: 1280px;
            margin: 0 auto;
            padding: 26px 28px 60px;
        }
        
        /* ---------- Accesibilidad ---------- */
        
        /* El foco del teclado tiene que verse: el tablero se usa con lector de
           pantalla y navegación por tabulador en las auditorías de accesibilidad. */
        a:focus-visible,
        button:focus-visible,
        input:focus-visible,
        .tab:focus-visible,
        .rc-slider-handle:focus-visible {
            outline: 2px solid #2b6cb0;
            outline-offset: 2px;
        }
        
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: .01ms !important;
                transition-duration: .01ms !important;
            }
        }
        
        /* ---------- Controles ---------- */
        
        .rc-slider-track {
            background-color: #2b6cb0;
        }
        
        .rc-slider-handle {
            border-color: #2b6cb0;
        }
        
        .rc-slider-mark-text {
            font-size: 11px;
            color: #718096;
        }
        
        input[type="number"] {
            border: 1px solid #cbd5e0;
            border-radius: 5px;
        }
        
        /* ---------- Pantallas pequeñas ---------- */
        
        @media (max-width: 760px) {
            .contenido {
                padding: 18px 14px 48px;
            }
        
            .navegacion {
                padding: 0 14px;
            }
        }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""
# ===========================================================================
# 2. DATOS
# Carga única del archivo limpio y construcción de las dos variables
# derivadas. Antes era el módulo datos.py.
# ===========================================================================
# ---------------------------------------------------------------------------
# Ubicacion del archivo
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent
RUTA_DATOS = Path(os.environ.get("RUTA_DATOS",
                                 RAIZ / "datos_limpios_sdm.csv"))
COLUMNAS_FECHA = ["fecha_de_firma", "fecha_de_inicio_del_contrato",
                  "fecha_de_fin_del_contrato"]
ENTIDAD = "Secretaría Distrital de Movilidad"
CORTE_DATOS = "24 de agosto de 2026"
# Dependencias de la SDM y los patrones con que se reconocen en el objeto
# contractual. El orden importa: se asigna la primera que coincida.
PATRONES_DEPENDENCIA = {
    "Investigaciones Administrativas": "investigaciones administrativas",
    "Gestion en Via": "gestion en via",
    "Gestion de Cobro": "gestion de cobro",
    "Senalizacion": "senalizacion",
    "Semaforizacion": "semaforizacion",
    "Control de Transito": "control de transito",
    "Seguridad Vial": "seguridad vial",
    "Atencion al Ciudadano": "atencion al ciudadano|servicio al ciudadano",
}
def _sin_tildes(serie):
    """Normaliza texto a minusculas sin tildes para poder buscar patrones."""
    return (serie.astype(str)
            .apply(lambda s: unicodedata.normalize("NFKD", s)
                   .encode("ascii", "ignore").decode())
            .str.lower())
def cargar():
    """Lee el archivo limpio y agrega las variables derivadas."""
    if not RUTA_DATOS.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de datos en {RUTA_DATOS}. "
            "Déjelo en la misma carpeta que este script o defina la "
            "variable de entorno "
            "RUTA_DATOS con su ruta."
        )
    df = pd.read_csv(RUTA_DATOS, low_memory=False, parse_dates=COLUMNAS_FECHA)
    # Banderas booleanas: si el CSV se regenera desde Athena pueden llegar
    # como texto, asi que se normalizan.
    for col in ["vencido", "cerrado", "cerrado_amplio", "estado_incompatible"]:
        if col in df.columns and df[col].dtype != bool:
            df[col] = (df[col].astype(str).str.strip().str.lower()
                       .isin(["true", "1", "si", "sí"]))
 
    df["anio_firma"] = df["anio_firma"].astype(int)
    df["anio_fin"] = df["anio_fin"].astype(int)
 
    # Persona natural vs juridica. En SECOP II no hay una columna directa:
    # se deduce del tipo de documento del proveedor. Solo el NIT identifica
    # a una empresa; cedula, cedula de extranjeria y los residuales son
    # personas naturales (contratos de prestacion de servicios).
    df["tipo_persona"] = np.where(
        df["tipodocproveedor"].astype(str).str.strip().str.upper() == "NIT",
        "Juridica", "Natural")
 
    # Dependencia responsable. Tampoco existe como columna: se infiere del
    # objeto del contrato. Lo que no coincide con ningun patron queda en
    # "Otras", que es la categoria mas grande y debe leerse como tal.
    objeto = _sin_tildes(df["objeto_del_contrato"])
    df["dependencia"] = "Otras"
    for nombre, patron in PATRONES_DEPENDENCIA.items():
        sin_asignar = df["dependencia"].eq("Otras")
        df.loc[sin_asignar & objeto.str.contains(patron, na=False),
               "dependencia"] = nombre
 
    return df
 
 
# ---------------------------------------------------------------------------
# Objetos compartidos por las secciones
# ---------------------------------------------------------------------------
DF = cargar()
 
# Universo de la pregunta 3: solo contratos cuyo plazo ya vencio.
VENCIDOS = DF[DF["vencido"]].copy()
 
ANIOS = sorted(DF["anio_firma"].unique().tolist())
ANIO_MIN, ANIO_MAX = ANIOS[0], ANIOS[-1]
 
# 2019 tiene un vacio de reporte en la fuente y 2026 solo llega hasta agosto.
ANIOS_PARCIALES = [a for a in (2019, 2026) if a in ANIOS]
 
LISTA_DEPENDENCIAS = sorted(VENCIDOS["dependencia"].unique().tolist())
LISTA_TIPOS_CONTRATO = sorted(VENCIDOS["tipo_de_contrato"].dropna().unique().tolist())
 
TOTAL_CONTRATOS = len(DF)
TOTAL_VALOR = float(DF["valor_del_contrato"].sum())
TOTAL_PROVEEDORES = int(DF["documento_proveedor"].nunique())
 
 
 
# ===========================================================================
# 3. PREGUNTA DE NEGOCIO 1 — Concentración de proveedores
# ¿De cuántos proveedores depende la Secretaría y qué tan concentrado
# está el presupuesto? Antes era secciones/pregunta1.py.
# ===========================================================================
 
# El año 2019 se excluye de esta pregunta: la fuente reporta 460 contratos
# frente a ~2.000 de los años vecinos, lo que distorsiona cualquier medida de
# concentración anual. Las otras dos secciones sí lo conservan y lo advierten.
DF_P1 = DF[DF["anio_firma"] != 2019].copy()
 
ANIOS_P1 = sorted(DF_P1["anio_firma"].unique().tolist())
ANIO_MIN_P1, ANIO_MAX_P1 = ANIOS_P1[0], ANIOS_P1[-1]
 
 
# ---------------------------------------------------------------------------
# Métricas
# ---------------------------------------------------------------------------
def gini(valores):
    """Coeficiente de Gini sobre el valor contratado por proveedor.
 
    0 = todos los contratistas reciben lo mismo. 1 = uno solo se lo lleva todo.
    """
    v = np.sort(np.asarray(valores, dtype=float))
    n = len(v)
    if n == 0 or v.sum() == 0:
        return np.nan
    return (n + 1 - 2 * np.sum(np.cumsum(v)) / v.sum()) / n
 
 
def hhi(datos_filtrados):
    """Índice Herfindahl-Hirschman sobre la participación en valor.
 
    Es la medida estándar de concentración de mercado: suma de los cuadrados
    de las participaciones, escalada a 10.000.
    """
    participacion = (datos_filtrados.groupby("documento_proveedor")
                     ["valor_del_contrato"].sum())
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
    # Umbrales usados por las autoridades de competencia para medir
    # concentración de mercado.
    if valor < 1500:
        return "Mercado poco concentrado"
    if valor < 2500:
        return "Concentración moderada"
    return "Concentración elevada"
 
 
def escala_redonda(maximo, divisiones=4):
    """Límite superior y paso 'bonitos' para un eje.
 
    Se usa en la gráfica de dos ejes: si cada eje escoge sus marcas por su
    cuenta, plotly alinea las del eje derecho con la grilla del izquierdo y
    aparecen valores sin sentido (345, 1.183, 2.021…). Fijando en ambos el
    mismo número de divisiones sobre un paso redondo, las marcas coinciden y
    se pueden leer.
    """
    if maximo <= 0:
        return 1, 1 / divisiones
    crudo = maximo / divisiones
    magnitud = 10 ** np.floor(np.log10(crudo))
    for multiplo in (1, 2, 2.5, 5, 10):
        paso = multiplo * magnitud
        if paso >= crudo:
            break
    return paso * divisiones, paso
 
 
def filtrar_p1(rango, tipos):
    return DF_P1[(DF_P1["anio_firma"] >= rango[0]) &
              (DF_P1["anio_firma"] <= rango[1]) &
              (DF_P1["tipo_persona"].isin(tipos))]
 
 
# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
layout_p1 = html.Div([
 
    encabezado_seccion(
        "1. ¿De cuántos proveedores depende la Secretaría?",
        "Cómo se reparte el presupuesto de contratación entre los "
        "contratistas de la entidad y con qué frecuencia se vuelve a "
        "contratar a los mismos de un año a otro. El propósito es "
        "identificar riesgos de dependencia y de continuidad en la operación."),
 
    # Lectura en lenguaje corriente: se reescribe con cada cambio de filtro.
    html.Div(id="p1-resumen", style=CAJA_NOTA),
 
    # ----- Filtros -----
    html.Div([
        html.Div([
            html.Label("Periodo que desea revisar", style=ETIQUETA),
            dcc.RangeSlider(id="p1-anios", min=ANIO_MIN_P1, max=ANIO_MAX_P1, step=1,
                            value=[ANIO_MIN_P1, ANIO_MAX_P1],
                            marks={a: str(a) for a in ANIOS_P1}),
        ], style={"flex": "3", "minWidth": "320px"}),
        html.Div([
            html.Label("Tipo de contratista", style=ETIQUETA),
            dcc.Checklist(
                id="p1-tipo",
                options=[
                    {"label": " Personas (prestación de servicios)",
                     "value": "Natural"},
                    {"label": " Empresas (personas jurídicas)",
                     "value": "Juridica"},
                ],
                value=["Natural", "Juridica"],
                labelStyle={"display": "block", "fontSize": "12px",
                            "marginTop": "4px"}),
        ], style={"flex": "1", "minWidth": "230px", "paddingLeft": "24px"}),
    ], style={**CAJA, "display": "flex", "flexWrap": "wrap", "gap": "16px"}),
 
    # ----- Indicadores -----
    html.Div([
        kpi("Contratos firmados", "p1-kpi-contratos", "p1-nota-contratos"),
        kpi("Contratistas distintos", "p1-kpi-proveedores", "p1-nota-proveedores"),
        kpi("Presupuesto comprometido", "p1-kpi-valor", "p1-nota-valor"),
        kpi("Desigualdad del reparto", "p1-kpi-gini", "p1-nota-gini"),
        kpi("Nivel de concentración", "p1-kpi-hhi", "p1-nota-hhi"),
        kpi("Peso de los 10 mayores", "p1-kpi-top10", "p1-nota-top10"),
    ], style=FILA_KPI),
 
    # ----- Gráficas -----
    html.Div([
        html.Div(tarjeta_grafica(
            "p1-lorenz",
            "¿Qué tan parejo es el reparto del presupuesto?",
            "La línea punteada es el reparto perfectamente igualitario: cada "
            "contratista recibiría lo mismo. Entre más se aleje la curva azul "
            "de esa línea, más desigual es el reparto real. El área sombreada "
            "es la brecha entre ambos.", alto=420),
            style={"flex": "1", "minWidth": "380px"}),
        html.Div(tarjeta_grafica(
            "p1-participacion",
            "¿Quién firma más contratos y quién se lleva más dinero?",
            "Las dos barras de cada grupo deberían ser parecidas si el reparto "
            "fuera proporcional. Cuando la barra naranja supera ampliamente a "
            "la azul, ese grupo concentra mucho más dinero del que su número "
            "de contratos sugiere.", alto=420),
            style={"flex": "1", "minWidth": "380px"}),
    ], style={"display": "flex", "flexWrap": "wrap", "gap": "16px"}),
 
    tarjeta_grafica(
        "p1-hhi",
        "¿La dependencia está aumentando o disminuyendo?",
        "La línea azul mide qué tan concentrado está el dinero cada año: sube "
        "cuando pocos contratistas acaparan más. Las barras grises muestran "
        "cuántos contratistas hubo ese año. Si las barras crecen pero la línea "
        "también, entran más contratistas pequeños sin reducir la dependencia "
        "de los grandes.", alto=420),
 
    tarjeta_grafica(
        "p1-top",
        "¿Cuáles son los contratistas de los que más depende la entidad?",
        "Cada barra es un contratista y su longitud es el dinero acumulado en "
        "el periodo seleccionado. El porcentaje al final indica qué parte del "
        "presupuesto total representa. Son los nombres cuya salida tendría "
        "mayor impacto sobre la operación.", alto=540),
 
    tarjeta_grafica(
        "p1-retencion",
        "¿Qué tan estable es el equipo de contratistas?",
        "Mide qué porcentaje de los contratistas de cada año ya trabajaba con "
        "la entidad el año anterior. Un valor alto indica continuidad y "
        "conocimiento acumulado, pero también que la operación depende de "
        "personas sin vínculo laboral cuya permanencia se renueva año a año. "
        "Los años 2019 y 2020 no aparecen: como 2019 se excluye por el vacío "
        "de reporte, no hay con qué comparar esos dos años.",
        alto=420),
 
    html.Div([
        html.B("Alcance de esta sección. "),
        "Contratos firmados entre 2017 y agosto de 2026 registrados en "
        "SECOP II. Se excluye 2019 porque la fuente reporta un vacío "
        "(460 contratos frente a cerca de 2.000 en los años vecinos) que "
        "distorsiona las medidas de concentración anual. 2026 cubre solo "
        "hasta agosto. El contratista se identifica por su número de "
        "documento, no por el nombre, para no dividir a un mismo proveedor "
        "que aparezca escrito de varias formas.",
    ], style=PIE_DATOS),
])
 
 
# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------
def registrar_callbacks_p1(app):
 
    @app.callback(
        Output("p1-resumen", "children"),
        Input("p1-anios", "value"), Input("p1-tipo", "value"))
    def actualizar_resumen(rango, tipos):
        d = filtrar_p1(rango, tipos)
        if len(d) == 0:
            return html.Div("No hay contratos con los filtros seleccionados. "
                            "Amplíe el periodo o marque algún tipo de contratista.")
 
        por_proveedor = d.groupby("documento_proveedor")["valor_del_contrato"].sum()
        g = gini(por_proveedor.values)
 
        # Cuántos contratistas acumulan la mitad del presupuesto.
        ordenados = por_proveedor.sort_values(ascending=False)
        acumulado = ordenados.cumsum() / ordenados.sum()
        n_mitad = int((acumulado < 0.5).sum() + 1)
        pct_mitad = n_mitad / len(ordenados) * 100
 
        # Retención del último año disponible dentro de la selección.
        anios = sorted(d["anio_firma"].unique())
        texto_retencion = ""
        if len(anios) >= 2 and anios[-1] - anios[-2] == 1:
            previo = set(d.loc[d.anio_firma == anios[-2], "documento_proveedor"])
            actual = set(d.loc[d.anio_firma == anios[-1], "documento_proveedor"])
            pct = len(previo & actual) / len(actual) * 100
            texto_retencion = (f" En {anios[-1]}, {pct:.0f} de cada 100 "
                               f"contratistas ya trabajaban con la entidad el "
                               f"año anterior.")
 
        return html.Div([
            html.Div("Lectura rápida", style={"fontSize": "12px",
                                              "fontWeight": "700",
                                              "color": AZUL,
                                              "marginBottom": "6px"}),
            html.P([
                f"Entre {rango[0]} y {rango[1]} la Secretaría firmó ",
                html.B(f"{miles(len(d))} contratos"), " con ",
                html.B(f"{miles(d.documento_proveedor.nunique())} contratistas "
                       f"distintos"), ", por un total de ",
                html.B(f"${numero(d.valor_del_contrato.sum() / 1e12, 2)} billones"), ". ",
                html.B(f"{miles(n_mitad)} contratistas"),
                f" ({porcentaje(pct_mitad)} del total) concentran la mitad de ese "
                f"dinero, lo que corresponde a un reparto con ",
                html.B(nivel_gini(g).lower()), ".", texto_retencion,
            ], style={"fontSize": "13.5px", "lineHeight": "1.7", "margin": "0"}),
        ])
 
    @app.callback(
        [Output("p1-kpi-contratos", "children"), Output("p1-nota-contratos", "children"),
         Output("p1-kpi-proveedores", "children"), Output("p1-nota-proveedores", "children"),
         Output("p1-kpi-valor", "children"), Output("p1-nota-valor", "children"),
         Output("p1-kpi-gini", "children"), Output("p1-nota-gini", "children"),
         Output("p1-kpi-hhi", "children"), Output("p1-nota-hhi", "children"),
         Output("p1-kpi-top10", "children"), Output("p1-nota-top10", "children")],
        Input("p1-anios", "value"), Input("p1-tipo", "value"))
    def actualizar_kpis(rango, tipos):
        d = filtrar_p1(rango, tipos)
        if len(d) == 0:
            return ["–", "sin datos"] * 6
 
        por_proveedor = d.groupby("documento_proveedor")["valor_del_contrato"].sum()
        g = gini(por_proveedor.values)
        h = hhi(d)
        top10 = por_proveedor.nlargest(10).sum() / por_proveedor.sum() * 100
        contratos_por_proveedor = len(d) / d.documento_proveedor.nunique()
 
        return (
            miles(len(d)), f"entre {rango[0]} y {rango[1]}",
            miles(d.documento_proveedor.nunique()),
            f"{numero(contratos_por_proveedor, 1)} contratos cada uno en promedio",
            f"${numero(d.valor_del_contrato.sum() / 1e12, 2)} B", "billones de pesos",
            numero(g, 3), nivel_gini(g),
            miles(h), nivel_hhi(h),
            porcentaje(top10), "del presupuesto en 10 contratistas",
        )
 
    @app.callback(
        Output("p1-lorenz", "figure"),
        Input("p1-anios", "value"), Input("p1-tipo", "value"))
    def actualizar_lorenz(rango, tipos):
        d = filtrar_p1(rango, tipos)
        por_proveedor = d.groupby("documento_proveedor")["valor_del_contrato"].sum()
        valores = np.sort(por_proveedor.values)
        n = len(valores)
        if n == 0:
            return figura_vacia("Sin contratos con los filtros seleccionados", 420)
 
        x = np.arange(1, n + 1) / n
        y = np.cumsum(valores) / valores.sum()
 
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x, y=y, mode="lines", name="Reparto real",
            line=dict(color=AZUL, width=3), fill="tozeroy",
            fillcolor="rgba(43,108,176,.12)",
            hovertemplate="El %{x:.0%} de contratistas con menor valor<br>"
                          "recibe el %{y:.1%} del presupuesto<extra></extra>"))
        fig.add_trace(go.Scatter(
            x=[0, 1], y=[0, 1], mode="lines",
            name="Si todos recibieran lo mismo",
            line=dict(color=GRIS, dash="dash"), hoverinfo="skip"))
        fig.update_layout(
            title=f"Desigualdad del reparto: {nivel_gini(gini(valores)).lower()}",
            xaxis_title="Contratistas, del que menos recibe al que más",
            yaxis_title="Parte del presupuesto acumulada",
            xaxis_tickformat=".0%", yaxis_tickformat=".0%", height=420,
            legend=LEYENDA_SUPERIOR)
        return fig
 
    @app.callback(
        Output("p1-participacion", "figure"),
        Input("p1-anios", "value"), Input("p1-tipo", "value"))
    def actualizar_participacion(rango, tipos):
        d = filtrar_p1(rango, tipos)
        if len(d) == 0:
            return figura_vacia("Sin contratos con los filtros seleccionados", 420)
 
        resumen = d.groupby("tipo_persona").agg(
            contratos=("id_contrato", "count"),
            valor=("valor_del_contrato", "sum")).reset_index()
        resumen["etiqueta"] = resumen["tipo_persona"].map(
            {"Natural": "Personas", "Juridica": "Empresas"})
 
        pct_contratos = resumen["contratos"] / resumen["contratos"].sum() * 100
        pct_valor = resumen["valor"] / resumen["valor"].sum() * 100
 
        fig = go.Figure()
        fig.add_trace(go.Bar(x=resumen["etiqueta"], y=pct_contratos,
                             name="Cuántos contratos firman", marker_color=AZUL,
                             text=[porcentaje(v) for v in pct_contratos],
                             textposition="outside"))
        fig.add_trace(go.Bar(x=resumen["etiqueta"], y=pct_valor,
                             name="Cuánto dinero reciben", marker_color=NARANJA,
                             text=[porcentaje(v) for v in pct_valor],
                             textposition="outside"))
        fig.update_layout(title="Contratos firmados frente a dinero recibido",
                          yaxis_title="Porcentaje del total (%)",
                          yaxis_range=[0, 112], barmode="group", height=420,
                          legend=LEYENDA_SUPERIOR)
        return fig
 
    @app.callback(
        Output("p1-hhi", "figure"),
        Input("p1-anios", "value"), Input("p1-tipo", "value"))
    def actualizar_hhi(rango, tipos):
        d = filtrar_p1(rango, tipos)
        if len(d) == 0:
            return figura_vacia("Sin contratos con los filtros seleccionados", 420)
 
        # El año va como texto: con eje categórico no queda un hueco en
        # 2019, que esta sección excluye a propósito.
        filas = [{"anio": str(int(anio)), "hhi": hhi(grupo),
                  "proveedores": grupo["documento_proveedor"].nunique()}
                 for anio, grupo in d.groupby("anio_firma")]
        serie = pd.DataFrame(filas)
 
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=serie["anio"], y=serie["proveedores"], name="Contratistas activos",
            marker_color=GRIS, opacity=0.28, yaxis="y2",
            hovertemplate="%{y} contratistas en %{x}<extra></extra>"))
        fig.add_trace(go.Scatter(
            x=serie["anio"], y=serie["hhi"], mode="lines+markers",
            name="Nivel de concentración", line=dict(color=AZUL, width=3),
            hovertemplate="Concentración: %{y:.0f} en %{x}<extra></extra>"))
        tope_hhi, paso_hhi = escala_redonda(serie["hhi"].max())
        tope_prov, paso_prov = escala_redonda(serie["proveedores"].max())
 
        fig.update_layout(
            title="Evolución de la dependencia año por año",
            xaxis=dict(type="category", title="Año de firma del contrato"),
            yaxis=dict(title="Concentración del dinero", range=[0, tope_hhi],
                       dtick=paso_hhi),
            yaxis2=dict(title="Número de contratistas", overlaying="y",
                        side="right", showgrid=False, range=[0, tope_prov],
                        dtick=paso_prov),
            height=420, legend=LEYENDA_SUPERIOR)
        return fig
 
    @app.callback(
        Output("p1-top", "figure"),
        Input("p1-anios", "value"), Input("p1-tipo", "value"))
    def actualizar_top(rango, tipos):
        d = filtrar_p1(rango, tipos)
        if len(d) == 0:
            return figura_vacia("Sin contratos con los filtros seleccionados", 540)
 
        total = d["valor_del_contrato"].sum()
        top = (d.groupby(["documento_proveedor", "proveedor_adjudicado"])
               ["valor_del_contrato"].sum().nlargest(15).reset_index())
        top["valor_millones"] = top["valor_del_contrato"] / 1e6
        top["pct"] = top["valor_del_contrato"] / total * 100
        top["nombre"] = top["proveedor_adjudicado"].astype(str).str.slice(0, 45)
        top = top.sort_values("valor_millones")
 
        fig = go.Figure(go.Bar(
            x=top["valor_millones"], y=top["nombre"], orientation="h",
            marker_color=AZUL, text=[porcentaje(p) for p in top["pct"]],
            textposition="outside",
            hovertemplate="%{y}<br>$%{x:,.0f} millones<extra></extra>"))
        fig.update_layout(
            title=f"Los 15 mayores concentran {porcentaje(top['pct'].sum())} "
                  f"del presupuesto",
            xaxis_title="Dinero contratado (millones de pesos)",
            height=540, margin=dict(l=10, r=60))
        return fig
 
    @app.callback(
        Output("p1-retencion", "figure"),
        Input("p1-anios", "value"), Input("p1-tipo", "value"))
    def actualizar_retencion(rango, tipos):
        d = filtrar_p1(rango, tipos)
        anios = sorted(d["anio_firma"].unique())
        if len(anios) < 2:
            return figura_vacia("Amplíe el periodo a dos años o más "
                                "para ver la retención", 420)
 
        conjuntos = {a: set(d.loc[d.anio_firma == a, "documento_proveedor"])
                     for a in anios}
 
        filas = []
        for i in range(len(anios) - 1):
            a, b = anios[i], anios[i + 1]
            if b - a != 1:
                continue
            comunes = len(conjuntos[a] & conjuntos[b])
            filas.append({"anio": str(b),
                          "retencion": comunes / len(conjuntos[b]) * 100,
                          "nuevos": 100 - comunes / len(conjuntos[b]) * 100})
 
        if not filas:
            return figura_vacia("El periodo seleccionado no tiene años "
                                "consecutivos", 420)
 
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
            # Eje categórico: solo aparecen los años que sí se pueden
            # comparar con el anterior. Con eje numérico quedaban huecos
            # en 2019 y 2020 que se leían como datos faltantes.
            xaxis=dict(type="category", title="Año"),
            yaxis_title="Porcentaje de los contratistas (%)",
            barmode="stack", height=420,
            legend={**LEYENDA_SUPERIOR, "traceorder": "normal"})
        return fig
# ===========================================================================
# 4. PREGUNTA DE NEGOCIO 2 — Composición del valor contratado
# ¿Qué modalidades y tipos de contrato concentran el valor y cómo ha
# cambiado? Antes era secciones/pregunta2.py.
# ===========================================================================
# Un contrato de un tipo que aparece menos de esta cantidad de veces se
# agrupa bajo "Otros": son categorías residuales que alargan el eje sin
# aportar lectura.
MINIMO_CONTRATOS_CATEGORIA = 5
# Cuántas categorías se muestran por separado en la evolución temporal.
TOP_EVOLUCION = 5
def filtrar_p2(rango):
    return DF[(DF["anio_firma"] >= rango[0]) & (DF["anio_firma"] <= rango[1])]
 
 
def etiqueta_anio(anio):
    """Marca con asterisco los años cuya cobertura no es completa."""
    return f"{anio}*" if anio in ANIOS_PARCIALES else str(anio)
 
 
def resumen_participacion(d, columna, agrupar_residuales=False):
    """Participación de cada categoría en número de contratos y en valor."""
    resumen = (d.groupby(columna)
               .agg(numero_contratos=("id_contrato", "count"),
                    valor_total=("valor_del_contrato", "sum"))
               .reset_index()
               .rename(columns={columna: "categoria"}))
 
    if agrupar_residuales:
        residuales = resumen["numero_contratos"] < MINIMO_CONTRATOS_CATEGORIA
        if residuales.sum() > 1:
            resumen.loc[residuales, "categoria"] = "Otros"
            resumen = (resumen.groupby("categoria", as_index=False)
                       .agg(numero_contratos=("numero_contratos", "sum"),
                            valor_total=("valor_total", "sum")))
 
    resumen["pct_contratos"] = (resumen["numero_contratos"] /
                                resumen["numero_contratos"].sum() * 100)
    resumen["pct_valor"] = (resumen["valor_total"] /
                            resumen["valor_total"].sum() * 100)
    return resumen.sort_values("pct_valor", ascending=False)
def figura_participacion(resumen, titulo, alto):
    """Barras horizontales pareadas: participación en contratos vs. en valor.
 
    La comparación es el punto de la gráfica: cuando las dos barras de una
    categoría se separan mucho, esa categoría mueve mucho más (o mucho menos)
    dinero del que su número de contratos haría esperar.
    """
    orden = resumen["categoria"].tolist()[::-1]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=resumen["categoria"], x=resumen["pct_contratos"], orientation="h",
        name="Participación en número de contratos", marker_color=AZUL,
        text=[porcentaje(v) for v in resumen["pct_contratos"]],
        textposition="outside", textfont_size=10,
        hovertemplate="%{y}<br>%{x:.1f}% de los contratos<extra></extra>"))
    fig.add_trace(go.Bar(
        y=resumen["categoria"], x=resumen["pct_valor"], orientation="h",
        name="Participación en valor contratado", marker_color=NARANJA,
        text=[porcentaje(v) for v in resumen["pct_valor"]],
        textposition="outside", textfont_size=10,
        hovertemplate="%{y}<br>%{x:.1f}% del valor<extra></extra>"))
    fig.update_layout(
        title=titulo, barmode="group", height=alto,
        xaxis_title="Participación sobre el total (%)",
        xaxis_range=[0, 112],
        yaxis=dict(categoryorder="array", categoryarray=orden),
        legend=LEYENDA_SUPERIOR, margin=dict(r=70, t=80))
    return fig
def figura_evolucion(d, columna, titulo_leyenda):
    """Barras apiladas al 100%: cómo se reparte el valor de cada año."""
    if len(d) == 0:
        return figura_vacia("Sin contratos en el periodo seleccionado", 520)
 
    principales = (d.groupby(columna)["valor_del_contrato"].sum()
                   .nlargest(TOP_EVOLUCION).index.tolist())
 
    base = d.copy()
    base["categoria"] = base[columna].where(base[columna].isin(principales),
                                            "Resto de categorías")
 
    evolucion = (base.groupby(["anio_firma", "categoria"], as_index=False)
                 ["valor_del_contrato"].sum())
    total_anual = (evolucion.groupby("anio_firma", as_index=False)
                   ["valor_del_contrato"].sum()
                   .rename(columns={"valor_del_contrato": "total_anual"}))
    evolucion = evolucion.merge(total_anual, on="anio_firma")
    evolucion["pct"] = (evolucion["valor_del_contrato"] /
                        evolucion["total_anual"] * 100)
    evolucion["anio_etiqueta"] = evolucion["anio_firma"].map(etiqueta_anio)
 
    orden_categorias = principales + ["Resto de categorías"]
    orden_anios = [etiqueta_anio(a) for a in sorted(evolucion["anio_firma"].unique())]
 
    fig = px.bar(
        evolucion, x="anio_etiqueta", y="pct", color="categoria",
        barmode="stack",
        category_orders={"categoria": orden_categorias,
                         "anio_etiqueta": orden_anios},
        color_discrete_sequence=SECUENCIA,
        custom_data=["valor_del_contrato"])
    fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>"
                                    "Año: %{x}<br>"
                                    "Participación: %{y:.1f}%<br>"
                                    "Valor: $%{customdata[0]:,.0f}"
                                    "<extra></extra>")
    fig.update_layout(
        height=520,
        # Sin type="category" plotly.js interpreta "2017", "2018"… como
        # números y descarta las etiquetas con asterisco (2019*, 2026*),
        # que desaparecían de la gráfica.
        xaxis=dict(type="category", title="Año de firma"),
        yaxis=dict(title="Participación en el valor contratado (%)",
                   range=[0, 100], ticksuffix="%"),
        legend=dict(title=titulo_leyenda, orientation="h", yanchor="top",
                    y=-0.16, xanchor="left", x=0),
        margin=dict(r=30, t=30, b=130))
    return fig
# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
layout_p2 = html.Div([
 
    encabezado_seccion(
        "2. ¿En qué se concentra el valor contratado?",
        "Qué modalidades y qué tipos de contrato concentran la mayor parte "
        "del presupuesto de la Secretaría, y cómo ha cambiado esa composición "
        "año a año. Sirve para ver si el gasto se mueve por los mecanismos "
        "competitivos o por contratación directa."),
 
    html.Div(id="p2-resumen", style=CAJA_NOTA),
 
    # ----- Filtro -----
    html.Div([
        html.Label("Periodo que desea revisar", style=ETIQUETA),
        dcc.RangeSlider(id="p2-anios", min=ANIO_MIN, max=ANIO_MAX, step=1,
                        value=[ANIO_MIN, ANIO_MAX],
                        marks={a: str(a) for a in ANIOS}),
    ], style=CAJA),
 
    # ----- Indicadores -----
    html.Div([
        kpi("Contratos analizados", "p2-kpi-contratos", "p2-nota-contratos"),
        kpi("Valor contratado", "p2-kpi-valor", nota="billones de pesos"),
        kpi("Modalidad líder en valor", "p2-kpi-modalidad", "p2-nota-modalidad"),
        kpi("Tipo de contrato líder en valor", "p2-kpi-tipo", "p2-nota-tipo"),
    ], style=FILA_KPI),
 
    tarjeta_grafica(
        "p2-modalidad",
        "¿Por qué mecanismo se adjudica el dinero?",
        "Cada modalidad tiene dos barras. La azul es el porcentaje de "
        "contratos que se firmaron por ese mecanismo y la naranja el "
        "porcentaje del dinero que movió. Una modalidad con barra azul muy "
        "alta y naranja baja firma muchos contratos pequeños; al revés, pocos "
        "contratos muy grandes.", alto=560),
 
    tarjeta_grafica(
        "p2-tipo",
        "¿Qué se está contratando?",
        "Misma lectura que la gráfica anterior, pero por tipo de objeto "
        "contractual. Los tipos con menos de cinco contratos en el periodo se "
        "agrupan en «Otros» para no alargar el eje con categorías "
        "residuales.", alto=520),
 
    tarjeta_grafica(
        "p2-evolucion",
        "¿Ha cambiado la composición con el tiempo?",
        "Cada barra es un año y suma 100%: muestra cómo se repartió el valor "
        "contratado de ese año entre las cinco categorías principales y el "
        "resto. Compare la altura de un mismo color entre años para ver si "
        "esa categoría ganó o perdió peso. Los años marcados con asterisco "
        "tienen cobertura incompleta.", alto=520,
        extra=html.Div([
            html.Label("Ver la evolución por:", style=ETIQUETA),
            dcc.RadioItems(
                id="p2-dimension",
                options=[{"label": " Modalidad de contratación",
                          "value": "modalidad_de_contratacion"},
                         {"label": " Tipo de contrato",
                          "value": "tipo_de_contrato"}],
                value="modalidad_de_contratacion", inline=True,
                inputStyle={"marginRight": "5px"},
                labelStyle={"marginRight": "22px", "fontSize": "12.5px"},
                style={"marginBottom": "10px"}),
        ])),
 
    html.Div([
        html.B("Alcance de esta sección. "),
        "Contratos firmados entre 2017 y agosto de 2026. Se excluyeron los "
        "registros en estado borrador, cancelado, enviado a proveedor y en "
        "aprobación, porque no corresponden a contratos formalizados. Los "
        "años 2019 y 2026 se marcan con asterisco: el primero tiene un vacío "
        "de reporte en la fuente y el segundo solo llega hasta agosto, así "
        "que su composición se calcula sobre menos contratos que la de los "
        "demás años.",
    ], style=PIE_DATOS),
])
# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------
def registrar_callbacks_p2(app):
 
    @app.callback(
        [Output("p2-resumen", "children"),
         Output("p2-kpi-contratos", "children"), Output("p2-nota-contratos", "children"),
         Output("p2-kpi-valor", "children"),
         Output("p2-kpi-modalidad", "children"), Output("p2-nota-modalidad", "children"),
         Output("p2-kpi-tipo", "children"), Output("p2-nota-tipo", "children"),
         Output("p2-modalidad", "figure"), Output("p2-tipo", "figure")],
        Input("p2-anios", "value"))
    def actualizar_composicion(rango):
        d = filtrar_p2(rango)
        if len(d) == 0:
            vacio = figura_vacia("Sin contratos en el periodo seleccionado")
            return (html.Div("No hay contratos en el periodo seleccionado."),
                    "–", "", "–", "–", "", "–", "", vacio, vacio)
 
        modalidad = resumen_participacion(d, "modalidad_de_contratacion")
        tipo = resumen_participacion(d, "tipo_de_contrato",
                                     agrupar_residuales=True)
 
        lider_mod = modalidad.iloc[0]
        lider_tipo = tipo.iloc[0]
 
        # Brecha entre peso en contratos y peso en valor de la modalidad
        # líder: es el hallazgo que el usuario debe ver primero.
        texto = html.Div([
            html.Div("Lectura rápida", style={"fontSize": "12px",
                                              "fontWeight": "700",
                                              "color": AZUL,
                                              "marginBottom": "6px"}),
            html.P([
                f"Entre {rango[0]} y {rango[1]} la Secretaría firmó ",
                html.B(f"{miles(len(d))} contratos"), " por ",
                html.B(f"${numero(d.valor_del_contrato.sum() / 1e12, 2)} billones"),
                ". La modalidad ", html.B(str(lider_mod["categoria"])),
                f" representa el {porcentaje(lider_mod['pct_contratos'])} de los "
                f"contratos y el ",
                html.B(f"{porcentaje(lider_mod['pct_valor'])} del dinero"),
                f". El tipo de contrato que más valor concentra es ",
                html.B(str(lider_tipo["categoria"])),
                f", con {porcentaje(lider_tipo['pct_valor'])} del total.",
            ], style={"fontSize": "13.5px", "lineHeight": "1.7", "margin": "0"}),
        ])
 
        fig_mod = figura_participacion(
            modalidad, "Modalidad de contratación: contratos frente a dinero",
            560)
        fig_tipo = figura_participacion(
            tipo, "Tipo de contrato: contratos frente a dinero", 520)

        return (
            texto,
            miles(len(d)), f"entre {rango[0]} y {rango[1]}",
            f"${numero(d.valor_del_contrato.sum() / 1e12, 2)} B",
            str(lider_mod["categoria"]), f"{porcentaje(lider_mod['pct_valor'])} del valor",
            str(lider_tipo["categoria"]), f"{porcentaje(lider_tipo['pct_valor'])} del valor",
            fig_mod, fig_tipo,
        )
    @app.callback(
        Output("p2-evolucion", "figure"),
        Input("p2-anios", "value"), Input("p2-dimension", "value"))
    def actualizar_evolucion(rango, dimension):
        d = filtrar_p2(rango)
        titulo = ("Modalidad" if dimension == "modalidad_de_contratacion"
                  else "Tipo de contrato")
        return figura_evolucion(d, dimension, titulo)
# ===========================================================================
# 5. PREGUNTA DE NEGOCIO 3 — Cierre de expedientes
# ¿Cuántos contratos vencidos siguen sin cierre y dónde se concentra
# el rezago? Antes era secciones/pregunta3.py.
# ===========================================================================
# Solo se miran contratos cuyo plazo ya venció: un contrato en ejecución no
# puede estar rezagado en su cierre.
LISTA_TIPOS = LISTA_TIPOS_CONTRATO
CAPACIDAD_POR_DEFECTO = 40
CAPACIDAD_MAXIMA = 2000
# Artículo 11 de la Ley 1150 de 2007: 4 meses para la liquidación bilateral,
# 2 meses más para la unilateral, y 24 meses como término máximo.
# Las marcas de 4 y 6 meses caen tan juntas que dos etiquetas se pisan;
# se rotula solo la primera y la nota de la gráfica explica el par.
CORTES_LEGALES = [(4, "4 y 6 m · liquidación", "top left"),
                  (6, "", "top right"),
                  (24, "24 m · término máximo", "top right")]
def filtrar_p3(umbral, deps, tipos):
    """Devuelve el universo filtrado y el subconjunto que cuenta como rezagado."""
    d = VENCIDOS
    if deps:
        d = d[d["dependencia"].isin(deps)]
    if tipos:
        d = d[d["tipo_de_contrato"].isin(tipos)]
    rezago = d[(~d["cerrado"]) & (d["meses_desde_fin"] >= umbral)]
    return d, rezago
# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
layout_p3 = html.Div([
 
    encabezado_seccion(
        "3. ¿Cuántos expedientes siguen sin cerrar?",
        "Qué proporción de los contratos cuyo plazo ya venció sigue sin "
        "registrar su cierre en SECOP II, cuánto tiempo llevan esperando y "
        "en qué áreas se concentra el rezago. Incluye un simulador para "
        "estimar cuánto tardaría depurarlo."),
 
    html.Div([
        html.B("Cómo usar esta sección. "),
        "Mueva el umbral para definir a partir de cuántos meses considera que "
        "un expediente está rezagado: las marcas de 4, 6 y 24 meses son los "
        "términos del artículo 11 de la Ley 1150 de 2007. Al final de la "
        "sección puede indicar cuántos expedientes alcanza a depurar por "
        "semana para estimar cuánto tardaría en ponerse al día.",
        html.Br(),
        html.I("El indicador mide el estado del registro en SECOP II, no el "
               "estado jurídico del contrato."),
    ], style=CAJA_NOTA),
 
    # ----- Filtros -----
    html.Div([
        html.Div([
            html.Label("Umbral de rezago (meses desde la terminación)",
                       style=ETIQUETA),
            # El globo del valor va arriba (abajo se montaba sobre las marcas
            # de los cortes legales), y el margen superior del contenedor del
            # slider le deja el espacio para que no tape la etiqueta.
            html.Div(
                dcc.Slider(id="p3-umbral", min=0, max=36, step=1, value=4,
                           marks={0: "0", 4: "4", 6: "6", 12: "12", 24: "24",
                                  36: "36"},
                           tooltip={"placement": "top",
                                    "always_visible": True}),
                style={"marginTop": "52px"}),
        ], style={"flex": "2", "minWidth": "300px", "padding": "0 10px"}),
        html.Div([
            html.Label("Dependencia", style=ETIQUETA),
            dcc.Dropdown(id="p3-dependencia", options=LISTA_DEPENDENCIAS,
                         multi=True, placeholder="Todas",
                         style={"fontSize": "12px"}),
        ], style={"flex": "1", "minWidth": "200px"}),
        html.Div([
            html.Label("Tipo de contrato", style=ETIQUETA),
            dcc.Dropdown(id="p3-tipo", options=LISTA_TIPOS, multi=True,
                         placeholder="Todos", style={"fontSize": "12px"}),
        ], style={"flex": "1", "minWidth": "200px"}),
    ], style={**CAJA, "display": "flex", "flexWrap": "wrap", "gap": "16px",
              "alignItems": "flex-start"}),
 
    # ----- Indicadores -----
    html.Div([
        kpi("Expedientes rezagados", "p3-kpi-n", "p3-nota-n"),
        kpi("Valor comprometido", "p3-kpi-valor", nota="suma del valor contratado"),
        kpi("Rezago mediano", "p3-kpi-mediana", nota="meses desde la terminación"),
        kpi("Más de 24 meses", "p3-kpi-criticos",
            nota="fuera del término para liquidar"),
    ], style=FILA_KPI),
 
    # ----- Diagnóstico -----
    html.Div([
        html.Div(tarjeta_grafica(
            "p3-cohortes",
            "¿El rezago se resuelve con el tiempo?",
            "Cada barra es el año en que terminaron los contratos, dividida "
            "entre los que ya tienen cierre y los que no. La línea roja es el "
            "porcentaje cerrado de esa cohorte. Si el cierre fuera solo cosa "
            "de tiempo, la línea bajaría de izquierda a derecha; que no lo "
            "haga indica un problema de registro y no de trámite pendiente.",
            alto=360), style={"flex": "1", "minWidth": "380px"}),
        html.Div(tarjeta_grafica(
            "p3-espera",
            "¿Cuánto llevan esperando?",
            "Cuenta los expedientes sin cierre según los meses transcurridos "
            "desde que terminó el contrato. Las dos primeras líneas rojas son "
            "los plazos de liquidación bilateral y unilateral (4 y 6 meses). "
            "Todo lo que quede a la derecha de la tercera está fuera del "
            "término máximo de 24 meses para liquidar.",
            alto=360), style={"flex": "1", "minWidth": "380px"}),
    ], style={"display": "flex", "flexWrap": "wrap", "gap": "16px"}),
 
    tarjeta_grafica(
        "p3-concentracion",
        "¿Dónde se concentra el rezago?",
        "Los grupos están ordenados de arriba abajo, del que peor cierra al que "
        "mejor. La línea punteada es el promedio de la entidad: todo lo que "
        "esté a su izquierda cierra peor que el promedio. Al pasar el cursor "
        "se ve cuánto dinero sin "
        "cierre acumula cada grupo. Solo se muestran grupos con 30 o más "
        "contratos, para que un grupo de tres contratos no aparezca como el "
        "peor de la entidad.", alto=400,
        extra=html.Div([
            html.Label("Agrupar por:", style=ETIQUETA),
            dcc.RadioItems(
                id="p3-agrupador",
                options=[{"label": " Dependencia", "value": "dependencia"},
                         {"label": " Tipo de contrato", "value": "tipo_de_contrato"},
                         {"label": " Modalidad", "value": "modalidad_de_contratacion"}],
                value="dependencia", inline=True,
                inputStyle={"marginRight": "5px"},
                labelStyle={"marginRight": "22px", "fontSize": "12.5px"},
                style={"marginBottom": "10px"}),
        ])),
 
    # ----- Simulador -----
    html.Div([
        html.H3("¿Cuánto tardaría en depurar el rezago?",
                style={"fontSize": "16px", "fontWeight": "600",
                       "margin": "0 0 4px"}),
        html.P("Estime el tiempo de depuración según su capacidad de trabajo "
               "y el orden en que decida atender los expedientes.",
               style={"fontSize": "12.5px", "color": GRIS, "margin": "0 0 14px"}),
        html.Div([
            html.Div([
                html.Label("Expedientes que puede cerrar por semana",
                           style=ETIQUETA),
                dcc.Input(id="p3-capacidad", type="number", min=1,
                          max=CAPACIDAD_MAXIMA, step=1,
                          value=CAPACIDAD_POR_DEFECTO, debounce=True,
                          style={"width": "120px", "padding": "6px",
                                 "fontSize": "13px"}),
            ], style={"marginRight": "40px", "minWidth": "230px"}),
            html.Div([
                html.Label("¿Por dónde empezar?", style=ETIQUETA),
                dcc.RadioItems(
                    id="p3-regla",
                    options=[{"label": " Los más antiguos", "value": "antiguedad"},
                             {"label": " Los de mayor valor", "value": "valor"},
                             {"label": " Combinación de ambos", "value": "mixta"}],
                    value="antiguedad", inputStyle={"marginRight": "5px"},
                    labelStyle={"display": "block", "fontSize": "12.5px",
                                "marginBottom": "3px"}),
            ]),
        ], style={"display": "flex", "flexWrap": "wrap",
                  "alignItems": "flex-start", "marginBottom": "10px"}),
        dcc.Graph(id="p3-simulacion", config={"displayModeBar": False},
                  style={"height": "280px"}),
        html.Div(id="p3-texto-simulacion",
                 style={"fontSize": "13px", "lineHeight": "1.6",
                        "marginTop": "6px"}),
    ], style=CAJA),
 
    html.Div([
        html.B("Alcance de esta sección. "),
        "Solo contratos cuya fecha de terminación ya pasó "
        f"({miles(len(VENCIDOS))} de {miles(TOTAL_CONTRATOS)} registros). "
        "Un expediente se considera cerrado cuando su estado en SECOP II es "
        "«Cerrado». La dependencia no existe como campo en SECOP II: se "
        "infiere del objeto del contrato mediante palabras clave, y los "
        "contratos que no coinciden con ninguna quedan en «Otras», que por "
        "eso es la categoría más numerosa.",
    ], style=PIE_DATOS),
])
# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------
def registrar_callbacks_p3(app):
 
    @app.callback(
        [Output("p3-kpi-n", "children"), Output("p3-nota-n", "children"),
         Output("p3-kpi-valor", "children"), Output("p3-kpi-mediana", "children"),
         Output("p3-kpi-criticos", "children"),
         Output("p3-cohortes", "figure"), Output("p3-espera", "figure"),
         Output("p3-concentracion", "figure")],
        Input("p3-umbral", "value"), Input("p3-dependencia", "value"),
        Input("p3-tipo", "value"), Input("p3-agrupador", "value"))
    def actualizar_diagnostico(umbral, deps, tipos, agrupador):
        d, rezago = filtrar_p3(umbral, deps, tipos)
 
        if len(d) == 0:
            vacio = figura_vacia("Sin contratos vencidos con estos filtros")
            return ("–", "", "–", "–", "–", vacio, vacio, vacio)
 
        # ----- Indicadores -----
        n = miles(len(rezago))
        nota_n = f"de {miles(len(d))} contratos ya vencidos"
        valor = pesos(rezago["valor_del_contrato"].sum()) if len(rezago) else "–"
        mediana = (f"{rezago['meses_desde_fin'].median():.0f}"
                   if len(rezago) else "–")
        criticos = (f"{100 * (rezago['meses_desde_fin'] > 24).mean():.0f}%"
                    if len(rezago) else "–")
 
        # ----- Cohortes por año de terminación -----
        coh = (d.groupby("anio_fin")
               .agg(cerrados=("cerrado", "sum"), total=("cerrado", "size")))
        coh["sin_cerrar"] = coh["total"] - coh["cerrados"]
        coh["pct"] = (100 * coh["cerrados"] / coh["total"]).round(1)
 
        g1 = go.Figure()
        g1.add_bar(x=coh.index, y=coh["cerrados"], name="Con cierre registrado",
                   marker_color=AZUL)
        g1.add_bar(x=coh.index, y=coh["sin_cerrar"], name="Sin cierre",
                   marker_color=ROSA)
        g1.add_scatter(x=coh.index, y=coh["pct"], name="% con cierre",
                       yaxis="y2", mode="lines+markers",
                       line=dict(color=ROJO, width=2))
        g1.update_layout(
            barmode="stack", title="El cierre no mejora con la antigüedad",
            xaxis_title="Año de terminación del contrato",
            yaxis_title="Contratos",
            # tickvals explícitos: al superponer dos ejes plotly alinea las
            # marcas del secundario con la grilla del primario y salen
            # valores como 29,2 u 87,6 que no significan nada.
            yaxis2=dict(title="% con cierre", overlaying="y", side="right",
                        range=[0, 100], showgrid=False, tickmode="array",
                        tickvals=[0, 25, 50, 75, 100],
                        ticktext=["0%", "25%", "50%", "75%", "100%"]),
            height=360, legend=LEYENDA_SUPERIOR)
 
        # ----- Distribución de la espera -----
        if len(rezago) == 0:
            g2 = figura_vacia("Ningún expediente supera el umbral elegido", 360)
        else:
            g2 = px.histogram(rezago, x="meses_desde_fin", nbins=40,
                              color_discrete_sequence=[AZUL])
            for x, etiqueta, posicion in CORTES_LEGALES:
                g2.add_vline(x=x, line_dash="dash", line_color=ROJO,
                             annotation_text=etiqueta,
                             annotation_position=posicion,
                             annotation_font_size=9,
                             annotation_font_color=ROJO)
            g2.update_layout(
                title="Meses que llevan esperando los expedientes",
                xaxis_title="Meses desde la terminación",
                yaxis_title="Expedientes sin cierre",
                height=360, showlegend=False)
 
        # ----- Concentración por grupo -----
        resumen = (d.groupby(agrupador)
                   .agg(contratos=("cerrado", "size"),
                        pct_cierre=("cerrado", "mean"))
                   .query("contratos >= 30"))
 
        if len(resumen) == 0:
            g3 = figura_vacia("Ningún grupo alcanza los 30 contratos "
                              "con estos filtros", 400)
        else:
            resumen["pct_cierre"] = (100 * resumen["pct_cierre"]).round(1)
            valor_rezago = (rezago.groupby(agrupador)["valor_del_contrato"]
                            .sum() / 1e9)
            resumen["valor"] = (valor_rezago.reindex(resumen.index)
                                .fillna(0).round(1))
            resumen = resumen.sort_values("pct_cierre", ascending=False)

            g3 = go.Figure(go.Bar(
                x=resumen["pct_cierre"], y=resumen.index, orientation="h",
                marker_color=AZUL,
                text=resumen["pct_cierre"].map(lambda v: f"{v:.0f}%"),  # entero
                textposition="outside",
                customdata=np.stack([resumen["contratos"], resumen["valor"]],
                                    axis=-1),
                hovertemplate="%{y}<br>%{x:.1f}% con cierre<br>"
                              "%{customdata[0]} contratos<br>"
                              "$%{customdata[1]} mil M sin cierre<extra></extra>"))
            g3.add_vline(x=100 * d["cerrado"].mean(), line_dash="dash",
                         line_color=ROJO, annotation_text="promedio",
                         annotation_font_size=10, annotation_font_color=ROJO)
            g3.update_layout(
                title="Porcentaje de expedientes con cierre registrado",
                xaxis_title="% de expedientes cerrados",
                xaxis_range=[0, 112], height=400, margin=dict(r=70))
 
        return n, nota_n, valor, mediana, criticos, g1, g2, g3
    @app.callback(
        Output("p3-simulacion", "figure"),
        Output("p3-texto-simulacion", "children"),
        Input("p3-umbral", "value"), Input("p3-dependencia", "value"),
        Input("p3-tipo", "value"), Input("p3-capacidad", "value"),
        Input("p3-regla", "value"))
    def simular(umbral, deps, tipos, capacidad, regla):
        _, rezago = filtrar_p3(umbral, deps, tipos)
        total = len(rezago)
        # El campo puede llegar vacío o fuera de rango si el usuario escribe
        # directamente. Se corrige el valor y se le avisa, en vez de fallar.
        aviso = ""
        try:
            capacidad = int(float(capacidad))
        except (TypeError, ValueError):
            capacidad = CAPACIDAD_POR_DEFECTO
            aviso = f" (no se entendió el valor, se usaron {CAPACIDAD_POR_DEFECTO})"
        if capacidad < 1:
            capacidad, aviso = 1, " (el mínimo es 1 por semana)"
        elif capacidad > CAPACIDAD_MAXIMA:
            capacidad, aviso = (CAPACIDAD_MAXIMA,
                                f" (se limitó a {CAPACIDAD_MAXIMA} por semana)")
        if total == 0:
            return (figura_vacia("No hay expedientes rezagados con estos "
                                 "filtros. Baje el umbral para incluir más.",
                                 280),
                    "No hay expedientes rezagados con estos filtros.")
        # ----- Orden de atención según la regla elegida -----
        if regla == "antiguedad":
            orden = rezago.sort_values("meses_desde_fin", ascending=False)
        elif regla == "valor":
            orden = rezago.sort_values("valor_del_contrato", ascending=False)
        else:
            # Puntaje mixto: se normalizan antigüedad y valor a una escala
            # 0-1 y se promedian con el mismo peso.
            r = rezago.copy()
            for col in ["meses_desde_fin", "valor_del_contrato"]:
                rango = r[col].max() - r[col].min()
                r["n_" + col] = 0.5 if rango == 0 else (r[col] - r[col].min()) / rango
            r["puntaje"] = (0.5 * r["n_meses_desde_fin"] +
                            0.5 * r["n_valor_del_contrato"])
            orden = r.sort_values("puntaje", ascending=False)
        # ----- Curva de agotamiento -----
        semanas = int(np.ceil(total / capacidad))
        eje = np.arange(0, semanas + 1)
        pendientes = np.maximum(total - capacidad * eje, 0)
        fig = go.Figure(go.Scatter(
            x=eje, y=pendientes,
            mode="lines+markers" if semanas <= 12 else "lines",
            line=dict(color=AZUL, width=3), fill="tozeroy",
            fillcolor="rgba(43,108,176,.12)",
            hovertemplate="Semana %{x}<br>%{y} expedientes pendientes"
                          "<extra></extra>"))
        fig.update_layout(
            title="Expedientes pendientes según avanza el trabajo",
            xaxis_title="Semanas de trabajo",
            yaxis_title="Expedientes pendientes", height=280,
            xaxis=dict(range=[0, max(semanas, 1)]),
            yaxis=dict(range=[0, total * 1.08]))
        # ----- Expedientes que cruzarían los 24 meses en el camino -----
        orden = orden.reset_index(drop=True)
        semana_atencion = np.floor(orden.index / capacidad) + 1
        meses_al_atender = orden["meses_desde_fin"] + semana_atencion / 4.33
        cruzan = int(((orden["meses_desde_fin"] <= 24) &
                      (meses_al_atender > 24)).sum())
        duracion = ("menos de una semana" if capacidad >= total
                    else f"{miles(semanas)} semanas ({numero(semanas / 4.33, 1)} meses)")
        texto = html.Span([
            f"Con {capacidad} expedientes por semana{aviso}, depurar los "
            f"{miles(total)} rezagados toma cerca de ",
            html.B(duracion),
            f". Con esta regla de priorización, {miles(cruzan)} expedientes "
            f"que hoy están dentro del término de 24 meses lo superarían "
            f"antes de ser atendidos.",
        ])
        return fig, texto
# ===========================================================================
# 6. APLICACIÓN
# Portada, pestañas y arranque. Antes era app.py.
# ===========================================================================
# ---------------------------------------------------------------------------
# Aplicación
# ---------------------------------------------------------------------------
app = Dash(__name__, title="Contratación SDM",
           update_title="Actualizando…",
           meta_tags=[{"name": "viewport",
                       "content": "width=device-width, initial-scale=1"}])
# Gunicorn necesita el servidor Flask subyacente.
server = app.server
# Sin carpeta assets/, la hoja de estilos se inyecta en la plantilla HTML.
app.index_string = PLANTILLA_HTML
# ---------------------------------------------------------------------------
# Portada
# ---------------------------------------------------------------------------
def tarjeta_pregunta(numero, titulo, descripcion, hallazgo):
    return html.Div([
        html.Div(f"Pregunta {numero}", style={"fontSize": "11.5px",
                                              "color": AZUL,
                                              "fontWeight": "700"}),
        html.H3(titulo, style={"fontSize": "16px", "fontWeight": "600",
                               "color": AZUL_OSCURO, "margin": "6px 0 8px"}),
        html.P(descripcion, style={"fontSize": "13px", "color": TEXTO,
                                   "lineHeight": "1.6", "margin": "0 0 10px"}),
        html.P(hallazgo, style={"fontSize": "12.5px", "color": GRIS,
                                "lineHeight": "1.6", "margin": "0",
                                "paddingTop": "10px",
                                "borderTop": f"1px solid {GRIS_CLARO}"}),
    ], style={**CAJA, "flex": "1", "minWidth": "280px", "marginBottom": "0"})
def cifra_global(valor, etiqueta):
    return html.Div([
        html.Div(valor, style={"fontSize": "27px", "fontWeight": "700",
                               "color": AZUL}),
        html.Div(etiqueta, style={"fontSize": "12px", "color": GRIS,
                                  "marginTop": "2px"}),
    ], style={"flex": "1", "minWidth": "160px"})
inicio = html.Div([
    html.H2("Contratación de la Secretaría Distrital de Movilidad",
            style={"fontSize": "22px", "fontWeight": "600",
                   "color": AZUL_OSCURO, "margin": "0 0 8px"}),
    html.P([
        "Este tablero está dirigido a la ",
        html.B("Dirección de Contratación de la Secretaría"),
        ", responsable de planear la contratación del año, vigilar de quién "
        "depende la operación y responder por el estado de los expedientes "
        "ante los entes de control. Reúne en un solo lugar las tres preguntas "
        "que esa área necesita responder con los datos de SECOP II.",
    ], style={"fontSize": "13.5px", "lineHeight": "1.7", "color": TEXTO,
              "maxWidth": "78ch", "margin": "0 0 20px"}),
    html.Div([
        cifra_global(miles(TOTAL_CONTRATOS), "contratos registrados"),
        cifra_global(f"${numero(TOTAL_VALOR / 1e12, 2)} B",
                     "valor total contratado"),
        cifra_global(miles(TOTAL_PROVEEDORES), "contratistas distintos"),
        cifra_global(f"{ANIO_MIN}–{ANIO_MAX}", "periodo cubierto"),
    ], style={**CAJA, "display": "flex", "flexWrap": "wrap", "gap": "20px",
              "padding": "22px"}),
    html.Div([
        tarjeta_pregunta(
            1, "Concentración de proveedores",
            "De cuántos contratistas depende la entidad, qué tan desigual es "
            "el reparto del presupuesto entre ellos y qué tan estable es ese "
            "grupo de un año a otro.",
            "Se responde con curva de Lorenz, coeficiente de Gini, índice de "
            "concentración HHI, ranking de contratistas y tasa de retención."),
        tarjeta_pregunta(
            2, "Composición del valor contratado",
            "Qué modalidades y qué tipos de contrato mueven el dinero, y cómo "
            "ha cambiado ese reparto año a año.",
            "Se responde comparando la participación de cada categoría en "
            "número de contratos frente a su participación en valor, y con la "
            "evolución anual de esa composición."),
        tarjeta_pregunta(
            3, "Cierre de expedientes",
            "Cuántos contratos ya vencidos siguen sin registrar cierre, "
            "cuánto llevan esperando y dónde se concentra el rezago.",
            "Se responde con el análisis por cohortes de terminación, la "
            "distribución del tiempo de espera y un simulador de depuración "
            "según la capacidad del área."),
    ], style={"display": "flex", "flexWrap": "wrap", "gap": "16px",
              "marginBottom": "18px"}),
 
    html.Div([
        html.B("Cómo usar el tablero. "),
        "Cada pestaña responde una pregunta y es independiente de las demás. "
        "Dentro de cada una, los filtros de la parte superior afectan todos "
        "los indicadores y todas las gráficas de esa pestaña. El recuadro "
        "azul resume en una frase lo que muestran los datos con la selección "
        "activa, y debajo de cada gráfica hay una nota que explica cómo "
        "leerla.",
        html.Br(), html.Br(),
        html.B("Origen de los  "),
        "SECOP II, conjunto de contratos electrónicos del portal de Datos "
        f"Abiertos, actualizado al {CORTE_DATOS}. Los registros de la "
        "entidad se extrajeron con AWS Glue y AWS Athena, y se limpiaron y "
        "prepararon en Python. El archivo que alimenta este tablero tiene "
        f"{miles(TOTAL_CONTRATOS)} contratos y 26 variables.",
        html.Br(), html.Br(),
        html.B("Advertencia sobre dos años. "),
        "2019 presenta un vacío de reporte en la fuente y 2026 solo cubre "
        "hasta agosto. La pregunta 1 excluye 2019 porque distorsiona las "
        "medidas de concentración anual; las preguntas 2 y 3 lo conservan y "
        "lo señalan. Cada sección indica su alcance al final.",
    ], style={**CAJA, "fontSize": "12.5px", "lineHeight": "1.7",
              "color": TEXTO, "maxWidth": "82ch"}),
])
# ---------------------------------------------------------------------------
# Estructura del tablero
# ---------------------------------------------------------------------------
ESTILO_TAB = {"padding": "12px 20px", "fontSize": "13.5px",
              "border": "none", "borderBottom": f"2px solid transparent",
              "backgroundColor": "transparent", "color": GRIS}
ESTILO_TAB_ACTIVO = {**ESTILO_TAB, "color": AZUL_OSCURO,
                     "fontWeight": "600",
                     "borderBottom": f"2px solid {AZUL}"}
app.layout = html.Div([
    # Encabezado fijo del producto
    html.Header([
        html.Div([
            html.Div(ENTIDAD,
                     style={"fontSize": "11.5px", "color": "#a3c4e8"}),
            html.H1("Analítica de contratación pública",
                    style={"fontSize": "19px", "fontWeight": "600",
                           "color": "white", "margin": "2px 0 0"}),
        ]),
        html.Div(f"SECOP II · datos al {CORTE_DATOS}",
                 style={"fontSize": "11.5px", "color": "#a3c4e8",
                        "textAlign": "right"}),
    ], style={"backgroundColor": AZUL_OSCURO, "padding": "16px 28px",
              "display": "flex", "justifyContent": "space-between",
              "alignItems": "center", "flexWrap": "wrap", "gap": "10px"}),
    # Navegación por pregunta de negocio
    html.Div([
        dcc.Tabs(id="navegacion", value="inicio", children=[
            dcc.Tab(label="Inicio", value="inicio", children=inicio,
                    style=ESTILO_TAB, selected_style=ESTILO_TAB_ACTIVO),
            dcc.Tab(label="1 · Concentración de proveedores", value="p1",
                    children=layout_p1,
                    style=ESTILO_TAB, selected_style=ESTILO_TAB_ACTIVO),
            dcc.Tab(label="2 · Composición del valor", value="p2",
                    children=layout_p2,
                    style=ESTILO_TAB, selected_style=ESTILO_TAB_ACTIVO),
            dcc.Tab(label="3 · Cierre de expedientes", value="p3",
                    children=layout_p3,
                    style=ESTILO_TAB, selected_style=ESTILO_TAB_ACTIVO),
        ], parent_className="navegacion", content_className="contenido"),
    ]),
], style={"fontFamily": TIPOGRAFIA, "backgroundColor": FONDO,
          "color": TEXTO, "minHeight": "100vh"})
# ---------------------------------------------------------------------------
# Callbacks de cada sección
# ---------------------------------------------------------------------------
registrar_callbacks_p1(app)
registrar_callbacks_p2(app)
registrar_callbacks_p3(app)
if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "0.0.0.0"),
            port=int(os.environ.get("PORT", 8050)),
            debug=os.environ.get("DEBUG", "0") == "1")
 
