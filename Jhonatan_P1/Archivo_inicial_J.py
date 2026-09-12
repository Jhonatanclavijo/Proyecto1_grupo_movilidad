import numpy as np 
import pandas as pd 

df = pd.read_csv(r"C:\Users\jhona\OneDrive - Universidad de los Andes\2026-2\Analítica Para la toma de Desiciones\Proyecto 1\Repositorio no Tocar\Datos_completos_SDM.csv")

print(df.head())
#columnas de interes para responder la pregunta
COLUMNAS_INTERES = {"nombre_entidad": "validar que la extraccion corresponde solo a la SDM", "id_contrato": "llave unica para detectar duplicados", "referencia_del_contrato": "numero visible del contrato, va en el plan de trabajo","estado_contrato": "estado del registro: base del indicador de cierre", "fecha_de_fin_del_contrato": "fecha contra la que se mide el rezago", "tipo_de_contrato": "segmenta el rezago (obra, interventoria, prestacion de servicios)", "modalidad_de_contratacion": "segmenta el rezago por forma de seleccion", "objeto_del_contrato": "de aqui se extraen la dependencia y el perfil", "liquidaci_n": "indica si se pacto liquidacion: analisis de sensibilidad", "valor_del_contrato": "prioriza los expedientes de mayor valor", "dias_adicionados": "identifica contratos modificados", "fecha_de_firma": "vigencia de origen del contrato", "fecha_de_inicio_del_contrato": "junto con la fecha de fin da el plazo real", "proveedor_adjudicado": "aparece en el plan de trabajo priorizado", "documento_proveedor": "identificador del contratista", "tipodocproveedor": "distingue persona natural de juridica"}
df2 = df[list(COLUMNAS_INTERES.keys())]
print(df2.head())
p_faltantes= ["no definido", "nan", "none", ""]
faltantes=pd.DataFrame({"columna": df2.columns,"pct_faltante": [round(100*df2[c].astype(str).str.strip().str.lower().isin(p_faltantes).mean(), 1)for c in df2.columns],}).sort_values("pct_faltante", ascending=False) # Calcula el porcentaje de faltantes de las columnas de interes
print(faltantes) #visualizar cuales tienen faltantes de interes en las columnas
