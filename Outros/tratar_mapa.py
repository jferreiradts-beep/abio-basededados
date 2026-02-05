import pandas as pd
import geopandas as gpd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mapa_path = os.path.join(BASE_DIR, 'mapa', 'RJeAdjacencias_100km_otimizado.geojson')

mapa = gpd.read_file(mapa_path)

df = mapa[['NM_MUN', 'SIGLA_UF']]
df.to_csv('RJeAdjacencias.csv')