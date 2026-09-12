import numpy as np 
import pandas as pd 
from datetime import date

df = pd.read_csv(r"C:\Users\jhona\OneDrive - Universidad de los Andes\2026-2\Analítica Para la toma de Desiciones\Proyecto 1\Repositorio no Tocar\Datos_completos_SDM.csv",parse_dates=['fecha_de_firma', 'fecha_de_inicio_del_contrato', 'fecha_de_fin_del_contrato'])

print(df.head())
#columnas de interes para responder la pregunta
COLUMNAS_INTERES = {"nombre_entidad": "validar que la extraccion corresponde solo a la SDM", "id_contrato": "llave unica para detectar duplicados", "referencia_del_contrato": "numero visible del contrato, va en el plan de trabajo","estado_contrato": "estado del registro: base del indicador de cierre", "fecha_de_fin_del_contrato": "fecha contra la que se mide el rezago", "tipo_de_contrato": "segmenta el rezago (obra, interventoria, prestacion de servicios)", "modalidad_de_contratacion": "segmenta el rezago por forma de seleccion", "objeto_del_contrato": "de aqui se extraen la dependencia y el perfil", "liquidaci_n": "indica si se pacto liquidacion: analisis de sensibilidad", "valor_del_contrato": "prioriza los expedientes de mayor valor", "dias_adicionados": "identifica contratos modificados", "fecha_de_firma": "vigencia de origen del contrato", "fecha_de_inicio_del_contrato": "junto con la fecha de fin da el plazo real", "proveedor_adjudicado": "aparece en el plan de trabajo priorizado", "documento_proveedor": "identificador del contratista", "tipodocproveedor": "distingue persona natural de juridica"}
df2 = df[list(COLUMNAS_INTERES.keys())]
print(df2.head())
p_faltantes= ["no definido", "nan", "none", ""]
faltantes=pd.DataFrame({"columna": df2.columns,"pct_faltante": [round(100*df2[c].astype(str).str.strip().str.lower().isin(p_faltantes).mean(), 1)for c in df2.columns],}).sort_values("pct_faltante", ascending=False) # Calcula el porcentaje de faltantes de las columnas de interes
print(faltantes) #visualizar cuales tienen faltantes de interes en las columnas
#limpieza de datos 
estadsiticas=df2.describe(include='all')
print(df2['estado_contrato'].unique())
#remover las filas que contengan datos que no aportan a la pregunta
sinaporte=["Borrador","Cancelado","En aprobación","En aprobacion","enviado Proveedor"]

df3=df2[~df2["estado_contrato"].isin(sinaporte)]

print(df2.shape)
print(df3.shape)

valorcontratos = df3['valor_del_contrato'].describe()

print(valorcontratos)
fila_max = df3.loc[df3['valor_del_contrato'].idxmax()]
print(fila_max)
fila_min= df3.loc[df3['valor_del_contrato'].idxmin()]
print(fila_min)

#duplicados
n_antes = len(df3)
df4 = df3.drop_duplicates(subset=["id_contrato"])
print(f"Duplicados por id_contrato eliminados: {n_antes - len(df4):,}")
print(f"Base depurada: {len(df4):,} registros")

#calculo de filas auxiliares

df4["anio_firma"] = df4["fecha_de_firma"].dt.year
df4["anio_fin"] =  df4["fecha_de_fin_del_contrato"].dt.year
df4["plazo_dias"] = ( df4["fecha_de_fin_del_contrato"]
                    -  df4["fecha_de_inicio_del_contrato"]).dt.days
df4["plazo_meses"] = ( df4["plazo_dias"] / 30.44).round(1)

print(df4.shape)


FECHA_CORTE = pd.Timestamp("today").normalize()

df4["vencido"] = df4["fecha_de_fin_del_contrato"] < FECHA_CORTE
df4["meses_desde_fin"] = ((FECHA_CORTE - df4["fecha_de_fin_del_contrato"]).dt.days
                         / 30.44).round(1)
df4.loc[~df4["vencido"], "meses_desde_fin"] = np.nan
print(df4.shape)
