import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

plt.rcParams.update({"figure.dpi": 130, "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25})
AZUL, ROJO, AMBAR = "#2b6cb0", "#c53030", "#dd6b20"


df = pd.read_csv(r"C:\Users\jhona\OneDrive - Universidad de los Andes\2026-2\Analítica Para la toma de Desiciones\Proyecto 1\Repositorio no Tocar\Jhonatan_P1\datos_limpios_sdm.csv", parse_dates=["fecha_de_firma","fecha_de_inicio_del_contrato","fecha_de_fin_del_contrato"])


