import matplotlib
matplotlib.use("Agg")
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
