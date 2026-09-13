
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

sns.set_theme(style="whitegrid")
os.makedirs("figuras", exist_ok=True)
AZUL, NARANJA = "#4c72b0", "#dd8452"


def guardar(nombre):
    plt.tight_layout()
    plt.savefig(os.path.join("figuras", nombre), dpi=150)
    plt.show()


FECHAS = ["fecha_de_firma", "fecha_de_inicio_del_contrato", "fecha_de_fin_del_contrato"]
datos = pd.read_csv("datos_limpios.csv", low_memory=False, parse_dates=FECHAS)


# Estadisticas descriptivas
print(datos[["valor_millones", "plazo_dias", "dias_adicionados",
             "n_contratos_proveedor"]].describe().round(2).to_string())


# Tabla a nivel de proveedor
proveedores = datos.groupby("documento_proveedor").agg(
    nombre=("proveedor_adjudicado", "first"),
    tipo_persona=("tipo_persona", "first"),
    n_contratos=("id_contrato", "count"),
    valor_total=("valor_del_contrato", "sum"),
).reset_index()
proveedores["valor_total_millones"] = proveedores["valor_total"] / 1e6


# Histograma: cuantos contratos acumula cada proveedor
fig, ax = plt.subplots(figsize=(9, 5))
sns.histplot(data=proveedores, x="n_contratos", hue="tipo_persona",
             bins=range(1, 15), multiple="stack", palette=[AZUL, NARANJA])
ax.set_xlabel("Numero de contratos por proveedor")
ax.set_ylabel("Cantidad de proveedores")
ax.set_title("Distribucion del numero de contratos por proveedor")
guardar("01_histograma_contratos_proveedor.png")


# Curva de Lorenz y coeficiente de Gini
# El Gini vale 0 si todos los proveedores reciben lo mismo y se acerca a 1
# cuando uno solo concentra todo el valor.
valores = np.sort(proveedores["valor_total"].values)
n = len(valores)
prop_proveedores = np.arange(1, n + 1) / n
prop_valor = np.cumsum(valores) / valores.sum()
gini = (n + 1 - 2 * np.sum(np.cumsum(valores)) / valores.sum()) / n

print(f"\nCoeficiente de Gini: {gini:.3f}")
for pct in [0.50, 0.80, 0.90, 0.95, 0.99]:
    idx = int(n * pct) - 1
    print(f"   El {int(pct * 100)}% con menor valor concentra {prop_valor[idx] * 100:5.1f}%")

fig, ax = plt.subplots(figsize=(7, 7))
ax.plot(prop_proveedores, prop_valor, color=AZUL,
        label=f"Curva de Lorenz (Gini = {gini:.3f})")
ax.plot([0, 1], [0, 1], color="gray", linestyle="dashed", label="Igualdad perfecta")
ax.fill_between(prop_proveedores, prop_valor, prop_proveedores, alpha=0.2, color=AZUL)
ax.set_xlabel("Proporcion acumulada de proveedores")
ax.set_ylabel("Proporcion acumulada del valor contratado")
ax.set_title("Curva de Lorenz del valor contratado por proveedor")
ax.legend()
guardar("02_curva_lorenz.png")


# Donas: participacion en numero de contratos vs participacion en valor
por_tipo = datos.groupby("tipo_persona").agg(
    n_contratos=("id_contrato", "count"),
    valor_total=("valor_del_contrato", "sum"))
por_tipo["pct_contratos"] = (por_tipo["n_contratos"] / por_tipo["n_contratos"].sum() * 100).round(1)
por_tipo["pct_valor"] = (por_tipo["valor_total"] / por_tipo["valor_total"].sum() * 100).round(1)
print("\n" + por_tipo[["n_contratos", "pct_contratos", "pct_valor"]].to_string())

fig, ax = plt.subplots(1, 2, figsize=(12, 5))
ax[0].pie(por_tipo["n_contratos"], labels=por_tipo.index, colors=[AZUL, NARANJA],
          autopct="%.1f%%", wedgeprops=dict(width=0.5))
ax[0].set_title("Participacion en numero de contratos")
ax[1].pie(por_tipo["valor_total"], labels=por_tipo.index, colors=[AZUL, NARANJA],
          autopct="%.1f%%", wedgeprops=dict(width=0.5))
ax[1].set_title("Participacion en valor contratado")
plt.suptitle("Personas naturales frente a personas juridicas")
guardar("03_donas_tipo_persona.png")


# Barras horizontales: los 15 proveedores con mas valor acumulado
top15 = proveedores.nlargest(15, "valor_total").sort_values("valor_total")
top15["pct"] = top15["valor_total"] / proveedores["valor_total"].sum() * 100

fig, ax = plt.subplots(figsize=(10, 7))
barras = ax.barh(top15["nombre"].str.slice(0, 45), top15["valor_total_millones"], color=AZUL)
ax.set_xlabel("Valor total contratado (millones de pesos)")
ax.set_title("Quince proveedores con mayor valor acumulado")
for barra, pct in zip(barras, top15["pct"]):
    ax.text(barra.get_width(), barra.get_y() + barra.get_height() / 2,
            f" {pct:.1f}%", va="center", fontsize=9)
guardar("04_top15_proveedores.png")

print(f"\nLos quince primeros concentran {top15['pct'].sum():.1f}% del valor")


# Indice HHI por ano: suma de los cuadrados de las participaciones de cada
# proveedor. Valores altos = dependencia de pocos contratistas.
def calcular_hhi(grupo):
    participacion = grupo.groupby("documento_proveedor")["valor_del_contrato"].sum()
    proporcion = participacion / participacion.sum()
    return (proporcion ** 2).sum() * 10000


resumen = []
for anio, grupo in datos.groupby("anio_firma"):
    participacion = grupo.groupby("documento_proveedor")["valor_del_contrato"].sum()
    proporcion = (participacion / participacion.sum()).sort_values(ascending=False)
    resumen.append({"anio": int(anio),
                    "contratos": len(grupo),
                    "proveedores": grupo["documento_proveedor"].nunique(),
                    "hhi": round(calcular_hhi(grupo)),
                    "top10_pct": round(proporcion.head(10).sum() * 100, 1),
                    "top1_pct": round(proporcion.iloc[0] * 100, 1)})

resumen = pd.DataFrame(resumen)
print("\n" + resumen.to_string(index=False))

# 2019 tiene un vacio de reporte en la fuente, se saca de las series
serie = resumen[(resumen.anio != 2019) & (resumen.anio >= 2018)]

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(serie["anio"], serie["hhi"], color=AZUL, marker="o")
ax.set_xlabel("Ano de firma")
ax.set_ylabel("Indice HHI")
ax.set_title("Evolucion de la concentracion de proveedores")

maximo = serie.loc[serie["hhi"].idxmax()]
ax.annotate(f"Maximo: {int(maximo.hhi)}", xy=(maximo.anio, maximo.hhi),
            xytext=(maximo.anio - 2, maximo.hhi + 100),
            arrowprops=dict(arrowstyle="->", color="gray"))
ax.annotate("2026 parcial\n(hasta agosto)", xy=(serie.anio.max(), serie.hhi.iloc[-1]),
            xytext=(serie.anio.max() - 1.8, serie.hhi.iloc[-1] - 220),
            arrowprops=dict(arrowstyle="->", color="gray"))
guardar("05_serie_hhi.png")

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(serie["anio"], serie["top10_pct"], color=AZUL, marker="o",
        label="Diez proveedores principales")
ax.plot(serie["anio"], serie["top1_pct"], color=NARANJA, marker="s",
        label="Proveedor principal")
ax.set_xlabel("Ano de firma")
ax.set_ylabel("Participacion en el valor contratado (%)")
ax.set_title("Participacion de los principales proveedores")
ax.legend()
guardar("06_participacion_principales.png")


# Violin: distribucion del valor segun cuantos contratos tiene el proveedor
ORDEN = ["1 contrato", "2 contratos", "3 a 4 contratos", "5 o mas"]

fig, ax = plt.subplots(figsize=(11, 6))
sns.violinplot(data=datos, x="recurrencia", y="valor_millones", hue="tipo_persona",
               order=ORDEN, split=True, inner="quart",
               palette=[AZUL, NARANJA], log_scale=True)
ax.set_xlabel("Numero de contratos acumulados por el proveedor")
ax.set_ylabel("Valor del contrato (millones, escala logaritmica)")
ax.set_title("Distribucion del valor segun recurrencia del proveedor")
guardar("07_violin_recurrencia.png")

print("\n" + datos.groupby("recurrencia", observed=True).agg(
    contratos=("id_contrato", "count"),
    valor_mediano_millones=("valor_millones", "median"),
    pct_con_adicion=("tiene_adicion", lambda x: x.mean() * 100)).round(2).to_string())


# Diagrama de caja por ano y tipo de proveedor
fig, ax = plt.subplots(figsize=(11, 6))
sns.boxplot(data=datos[datos.anio_firma >= 2020], x="anio_firma", y="valor_millones",
            hue="tipo_persona", palette=[AZUL, NARANJA], showfliers=False)
ax.set_yscale("log")
ax.set_xlabel("Ano de firma")
ax.set_ylabel("Valor del contrato (millones, escala logaritmica)")
ax.set_title("Valor del contrato por ano y tipo de proveedor")
guardar("08_boxplot_valor_anio.png")


# Dispersion: numero de contratos contra valor acumulado
fig, ax = plt.subplots(figsize=(10, 6))
for tipo, color in zip(["Natural", "Juridica"], [AZUL, NARANJA]):
    sub = proveedores[proveedores["tipo_persona"] == tipo]
    ax.scatter(sub["n_contratos"], sub["valor_total_millones"],
               alpha=0.5, s=25, color=color, label=tipo)
ax.set_yscale("log")
ax.set_xlabel("Numero de contratos acumulados")
ax.set_ylabel("Valor total contratado (millones, escala logaritmica)")
ax.set_title("Numero de contratos frente a valor acumulado por proveedor")
ax.legend(title="Tipo de persona")
guardar("09_dispersion_proveedores.png")


# Retencion: que porcentaje de los proveedores de un ano ya estaba el ano anterior
anios = sorted([int(a) for a in datos["anio_firma"].dropna().unique() if a != 2019])
conjuntos = {a: set(datos.loc[datos.anio_firma == a, "documento_proveedor"]) for a in anios}

matriz = pd.DataFrame(index=anios, columns=anios, dtype=float)
for a in anios:
    for b in anios:
        matriz.loc[a, b] = len(conjuntos[a] & conjuntos[b]) / len(conjuntos[a]) * 100

fig, ax = plt.subplots(figsize=(9, 7))
sns.heatmap(matriz.astype(float), annot=True, fmt=".0f", cmap="Blues",
            cbar_kws={"label": "Porcentaje de proveedores que continuan"})
ax.set_xlabel("Ano de destino")
ax.set_ylabel("Ano de origen")
ax.set_title("Matriz de permanencia de proveedores entre anos")
guardar("10_heatmap_retencion.png")

# La serie arranca en 2021 porque 2017 solo cubre medio ano
anios_completos = [a for a in anios if a >= 2020]
retencion = []
for i in range(len(anios_completos) - 1):
    a, b = anios_completos[i], anios_completos[i + 1]
    comunes = len(conjuntos[a] & conjuntos[b])
    retencion.append({"anio": b, "proveedores": len(conjuntos[b]),
                      "ya_estaban": comunes,
                      "pct_retencion": round(comunes / len(conjuntos[b]) * 100, 1)})

retencion = pd.DataFrame(retencion)
print("\n" + retencion.to_string(index=False))

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(retencion["anio"], retencion["pct_retencion"], color=AZUL, marker="o")
ax.set_xlabel("Ano")
ax.set_ylabel("Proveedores que ya contrataban el ano anterior (%)")
ax.set_title("Retencion de proveedores")
ax.set_ylim(0, 100)
guardar("11_serie_retencion.png")


# Pruebas estadisticas
# Kruskal-Wallis y Mann-Whitney son no parametricas: se usan porque el valor
# del contrato tiene una distribucion muy asimetrica y no es normal.
grupos = [g["valor_del_contrato"].dropna().values
          for _, g in datos.groupby("recurrencia", observed=True)]
h, p_h = stats.kruskal(*grupos)
print(f"\nKruskal-Wallis (valor segun recurrencia): H={h:.2f}, p={p_h:.3e}")

naturales = datos.loc[datos.tipo_persona == "Natural", "valor_del_contrato"].dropna()
juridicas = datos.loc[datos.tipo_persona == "Juridica", "valor_del_contrato"].dropna()
u, p_u = stats.mannwhitneyu(juridicas, naturales, alternative="two-sided")
print(f"Mann-Whitney (valor segun tipo de persona): U={u:,.0f}, p={p_u:.3e}")
print(f"   Medianas: naturales {naturales.median():,.0f} | "
      f"juridicas {juridicas.median():,.0f}")

tabla = pd.crosstab(datos["recurrencia"], datos["tiene_adicion"])
chi2, p_chi, gl, _ = stats.chi2_contingency(tabla)
print(f"Chi-cuadrado (recurrencia vs adicion): chi2={chi2:.2f}, gl={gl}, p={p_chi:.3e}")