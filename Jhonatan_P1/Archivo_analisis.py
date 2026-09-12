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