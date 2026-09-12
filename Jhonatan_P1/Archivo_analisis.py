import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
import unicodedata

plt.rcParams.update({"figure.dpi": 130, "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25})
AZUL, ROJO, AMBAR = "#2b6cb0", "#c53030", "#dd6b20"


df = pd.read_csv(r"C:\Users\jhona\OneDrive - Universidad de los Andes\2026-2\Analítica Para la toma de Desiciones\Proyecto 1\Repositorio no Tocar\Jhonatan_P1\datos_limpios_sdm.csv", parse_dates=["fecha_de_firma","fecha_de_inicio_del_contrato","fecha_de_fin_del_contrato"])

objeto = (df["objeto_del_contrato"].astype(str)
          .apply(lambda s: unicodedata.normalize("NFKD", s)
                 .encode("ascii", "ignore").decode().lower())
          .str.replace(r"\s+", " ", regex=True))
 
patrones_dependencia = {
    "Dir. Investigaciones Administrativas": "investigaciones administrativas",
    "Subd. Gestion en Via": "gestion en via",
    "Dir. Gestion de Cobro": "gestion de cobro",
    "Subd. Senalizacion": "senalizacion",
    "Subd. Semaforizacion": "semaforizacion",
    "Subd. Control de Transito": "control de transito",
    "Dir. Seguridad Vial": "seguridad vial",
    "Dir. Gestion de Transito": "gestion de transito",
    "Subd. Transporte Publico": "transporte publico",
    "Ofic. Comunicaciones": "comunicaciones",
    "Dir. Atencion al Ciudadano": "atencion al ciudadano|servicio al ciudadano",
    "Subd. Administrativa": "subdireccion administrativa",
    "Subd. Financiera": "subdireccion financiera",
    "Dir. Contratacion": "direccion de contratacion|subdireccion de contratacion",
    "Dir. Talento Humano": "talento humano",
    "Dir. Inteligencia Movilidad": "inteligencia para la movilidad",
    "Ofic. TIC": "tecnologias de la informacion|oficina de tic",
}
 
df["dependencia"] = "No identificada"
for nombre, patron in patrones_dependencia.items():
    faltantes = df["dependencia"].eq("No identificada")
    df.loc[faltantes & objeto.str.contains(patron, regex=True, na=False),"dependencia"] = nombre

df["perfil"] = "Otro"
df.loc[objeto.str.contains("apoyo a la gestion", na=False), "perfil"] = "Apoyo a la gestion"
df.loc[objeto.str.contains("tecnico|tecnolog", na=False), "perfil"] = "Tecnico/Tecnologo"
df.loc[objeto.str.contains("asistencial", na=False), "perfil"] = "Asistencial"
df.loc[objeto.str.contains("profesional", na=False), "perfil"] = "Profesional"
df["tiene_adicion"] = df["dias_adicionados"].fillna(0) > 0
df["liquidacion_pactada"] = df["liquidaci_n"].eq("Si")
df["persona_natural"] = df["tipodocproveedor"].eq("Cédula de Ciudadanía")
#plazo vencido
ven = df[df["vencido"]].copy()
sin_cierre = ven[~ven["cerrado"]].copy()

# porcentaje de contratos cerrados vs numero de contratos
cohortes = (ven.groupby("anio_fin").agg(contratos=("cerrado", "size"),cerrados=("cerrado", "sum"),tasa_cierre=("cerrado", "mean")))
cohortes["tasa_cierre"] = (100 * cohortes["tasa_cierre"]).round(1)

print(cohortes.to_string())

# Tasa de cierre por ano de terminacion

rho, p_rho = stats.spearmanr(cohortes.index, cohortes["tasa_cierre"])

print(f"\nSpearman (año de terminacion vs tasa de cierre):rho={rho:.2f}, p={p_rho:.4f}")


tabla = pd.crosstab(ven["anio_fin"], ven["cerrado"])
chi2, p, gl, _ = stats.chi2_contingency(tabla)
v_cramer = np.sqrt(chi2 / (tabla.values.sum() * (min(tabla.shape) - 1)))
print(f"Chi-cuadrado (cohorte x cierre): chi2={chi2:,.1f}, gl={gl}, p={p:.3e}, "
      f"V de Cramer={v_cramer:.3f}")

estados = pd.crosstab(ven["anio_fin"], ven["estado_contrato"], normalize="index") * 100


fig, ax = plt.subplots(figsize=(8.4, 3.6))
estados.plot(kind="bar", stacked=True, ax=ax, width=0.8, colormap="tab20")

ax.set_xlabel("Año de terminación del contrato")
ax.set_ylabel("% de contratos")
ax.set_title("Estado del expediente según el año en que venció el contrato")
ax.legend(fontsize=7, loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False)

fig.tight_layout()
plt.show()

# segunda micropregunta 

# 1. Contar cuántos contratos hay en cada grupo de tiempo
cantidad_contratos = sin_cierre["tramo_rezago"].value_counts()
# 2. Sumar el valor del dinero de los contratos por grupo
# Dividimos entre 1,000 millones (1e9) para que la cifra sea más fácil de leer
suma_dinero = sin_cierre.groupby("tramo_rezago")["valor_del_contrato"].sum()
suma_dinero_en_mil_millones = suma_dinero/1000000000
suma_dinero_redondeado = suma_dinero_en_mil_millones.round(0)
# 3. Unir estos datos en una tabla resumen (un DataFrame nuevo)
resumen_tramos = pd.DataFrame({"expedientes": cantidad_contratos,"valor_mil_millones": suma_dinero_redondeado,})
# 4. Calcular el porcentaje que representa cada grupo frente al total
total_de_contratos = resumen_tramos["expedientes"].sum()
porcentaje = (resumen_tramos["expedientes"] / total_de_contratos) *100 # Sacar la regla de tres
resumen_tramos["% del rezago"] = porcentaje.round(1)  #Redondear a un decimal
orden_deseado = ["0-4 meses", "4-6 meses", "6-24 meses", "Mas de 24 meses"]
# 6. Ordenar la tabla con el orden anterior y mostrarla en texto limpio
tabla_final = resumen_tramos.reindex(orden_deseado)
print(tabla_final.to_string())
fig2, ax = plt.subplots(figsize=(7.4, 3.4))
ax.hist(sin_cierre["meses_desde_fin"], bins=60, color=AZUL, alpha=0.85)
for x, etiqueta in [(4, "4 m\nbilateral"), (6, "6 m\nunilateral"),(24, "24 m\nlímite")]:
    ax.axvline(x, color=ROJO, ls="--", lw=1)
    ax.text(x + 1, ax.get_ylim()[1] * 0.75, etiqueta, color=ROJO, fontsize=7)
ax.set_xlabel("Meses transcurridos desde la terminación del contrato")
ax.set_ylabel("Expedientes sin cierre registrado")
ax.set_title("Antigüedad del rezago frente a los términos del art. 11, Ley 1150 de 2007")
fig2.tight_layout()
plt.show()

# Recorremos cada una de las variables clave para analizar su relación con el cierre de contratos
for variable in ["tipo_de_contrato","modalidad_de_contratacion", "perfil","dependencia"]:
    # 1. Seleccionamos únicamente las 6 categorías más frecuentes de la variable actual
    categorias = ven[variable].value_counts().head(6).index
    # 2. Creamos un subconjunto de datos filtrando solo esas categorías principales
    sub = ven[ven[variable].isin(categorias)]
    # 3. Construimos una tabla cruzada entre la categoría y si el contrato está cerrado o no
    tabla = pd.crosstab(sub[variable], sub["cerrado"])
    # 4. Aplicamos la prueba estadística Chi-cuadrado para ver si hay una relación real
    chi2, p, gl, _ = stats.chi2_contingency(tabla)
    # 5. Calculamos la V de Cramer para medir qué tan fuerte es esa asociación (de 0 a 1)
    v = np.sqrt(chi2 / (tabla.values.sum() * (min(tabla.shape) - 1)))
    #6. Agrupamos los datos para armar un resumen de desempeño por cada categoría
    resumen = (sub.groupby(variable).agg(contratos=("cerrado", "size"),pct_cierre=("cerrado", lambda s: round(100 * s.mean(), 1)),rezago_mediano=("meses_desde_fin", "median")).sort_values("pct_cierre"))

    # 7. Imprimimos el encabezado con los estadísticos globales y la tabla resumen en
    print(f"\n--- {variable}  (chi2={chi2:,.1f}, gl={gl}, p={p:.2e}, V={v:.3f})")
    print(resumen.to_string())

#Prueba: el rezago difiere entre tipos de contrato?
# 1. Agrupamos los datos por tipo de contrato y filtramos los grupos con menos de 30 registros
# para evitar distorsiones estadísticas por muestras muy pequeñas.
grupos = [g["meses_desde_fin"].dropna().values for _, g in sin_cierre.groupby("tipo_de_contrato") if len(g) >= 30]

# 2. Aplicamos la prueba de Kruskal-Wallis (alternativa no paramétrica al ANOVA)
# para contrastar si las medianas de rezago difieren entre los tipos de contrato.
h, p_h = stats.kruskal(*grupos)
# 3. Imprimimos el estadístico H y el valor p con notación científica para análisis formal.
print(f"\nKruskal-Wallis (rezago entre tipos de contrato): H={h:,.1f}, p={p_h:.3e}")


# Prueba: persona natural vs juridica

# 1. Separamos el tiempo de rezago en dos grupos: personas naturales (a) y personas jurídicas (b)
a = sin_cierre.loc[sin_cierre["persona_natural"],"meses_desde_fin"].dropna()
b = sin_cierre.loc[~sin_cierre["persona_natural"],"meses_desde_fin"].dropna()
# 2. Aplicamos la prueba de Mann-Whitney U (prueba no paramétrica para comparar dos grupos independientes)
u, p_u = stats.mannwhitneyu(a, b)

# 3. Imprimimos el resultado comparando las medianas y mostrando el valor p científico
print(f"Mann-Whitney (persona natural vs juridica): medianas "f"{a.median():.1f} vs {b.median():.1f} meses, p={p_u:.3e}")


#mapa de calor dependencia x ano de terminacion (% de cierre)
principales = ven["dependencia"].value_counts().head(9).index
mapa = (ven[ven["dependencia"].isin(principales)]
        .pivot_table(index="dependencia", columns="anio_fin",
                     values="cerrado", aggfunc="mean") * 100)
fig, ax = plt.subplots(figsize=(8.6, 3.8))
imagen = ax.imshow(mapa.values, cmap="RdYlGn", vmin=0, vmax=100, aspect="auto")
ax.set_xticks(range(len(mapa.columns)))
ax.set_xticklabels([int(c) for c in mapa.columns], fontsize=8)
ax.set_yticks(range(len(mapa.index)))
ax.set_yticklabels(mapa.index, fontsize=7)
for i in range(mapa.shape[0]):
    for j in range(mapa.shape[1]):
        if not np.isnan(mapa.values[i, j]):
            ax.text(j, i, f"{mapa.values[i, j]:.0f}", ha="center", va="center",
                    fontsize=6.5)
ax.set_title("Porcentaje de cierre por dependencia y año de terminación")
ax.grid(False)
fig.colorbar(imagen, ax=ax, shrink=0.8, label="% cerrado")
fig.tight_layout()

plt.show()

# 1. Correlación de Spearman entre el valor del contrato y el tiempo de rezago
# Evaluamos si los contratos más costosos tardan más o menos tiempo en cerrarse comparados con los de menor valor.
rho_vr, p_vr = stats.spearmanr(sin_cierre["valor_del_contrato"],sin_cierre["meses_desde_fin"])
# Imprimimos el coeficiente de correlación (rho) y el valor p asociado
print(f"Spearman (valor del contrato vs meses de rezago): rho={rho_vr:.3f}, "f"p={p_vr:.3e}")
 # 2. Análisis de concentración financiera (Principio de Pareto / 80-20)
# Ordenamos los contratos del valor más alto al más bajo para identificar el peso económico del rezago.
valores = sin_cierre["valor_del_contrato"].sort_values(ascending=False).reset_index(drop=True)
# Calculamos la proporción acumulada del dinero frente al total global
acumulado = valores.cumsum() / valores.sum()
# Encontramos la cantidad exacta de expedientes que acumulan el 80% (0.8) del valor monetario total
n80 = int((acumulado <= 0.8).sum() + 1)
# Imprimimos cuántos expedientes y qué porcentaje del total representan ese 80% del valor concentrado
print(f"{n80:,} expedientes ({100*n80/len(valores):.1f}% del rezago) concentran "f"el 80% del valor sin cierre")

