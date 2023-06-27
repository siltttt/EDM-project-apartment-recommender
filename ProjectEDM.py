# -*- coding: utf-8 -*-

# LIBRARIES
##################################
import streamlit as st
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import folium
from streamlit_folium import folium_static
import gower
###################################

# DATOS
data_barrio = pd.read_csv('./df_v13.csv',sep=';',encoding='UTF-8')
X = pd.read_csv('./df_binario.csv',sep=';',encoding='UTF-8')
data_pisos = pd.read_csv('./pisosValencia.csv',sep=';',encoding='UTF-8')
data_pisos.drop('index',axis=1)
# PAGE CONFIG
st.set_page_config(
    page_title="Home recommender",
    page_icon="🏢",
    layout="wide")
# TITLE
st.title("Recomendador de hogar")

options = st.multiselect(
    'Elige 3 de tus prioridades:',
    ['Colegios', 'Restaurante', 'Museo','Cine','Gimnasio','Biblioteca','Bus', 'Metro'],
    ['Cine', 'Colegios'],max_selections=3)

# SIDEBAR
health = st.sidebar.radio('Tipo de sanidad',['Privada','Pública'])
max_price = int(st.sidebar.number_input('Precio aproximado', min_value=min(data_pisos['Precio']),step=500))
m2 = int(st.sidebar.number_input('m²', 60, 1000, 200, 50))
bath = st.sidebar.slider('Baños', 1, 3)
bed = st.sidebar.slider('Habitaciones', 0, 4)
verde = st.sidebar.checkbox('Zonas verdes')
elevator = st.sidebar.checkbox('Ascensor')

# Convertir las preferencias del usuario
user = np.zeros(len(X.columns))
user[1] = max_price/m2
user[13] = 1
if health == 'Privada': user[4],user[6]=1,1
elif health == 'Pública': user[3],user[5]=1,1

for i,x in enumerate(X):
    if x in options:
        user[i]=1

# Escalar los datos de características y las preferencias del usuario
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
user_scaled = scaler.transform(user.reshape(1, -1))

nn_index = gower.gower_topn(user_scaled,X_scaled,n=1)['index'][0]
pisos = data_pisos.loc[data_pisos['Barrio'] == data_barrio["Barrio"][nn_index]]

nn_index = gower.gower_topn(user_scaled,X_scaled,n=10)['index']
cont=0
while len(pisos)==0:
    pisos = data_pisos.loc[data_pisos['Barrio'] == data_barrio["Barrio"][cont]]
    cont+=1
nn_index = nn_index[cont]

# Características
ad=':orange[¡Reconsidera el precio!]' if user[1]+100<data_barrio['Venta_2022'][nn_index] else ''

st.subheader("El barrio recomendado")
st.markdown(f"#### :blue[{data_barrio['Barrio'][nn_index].lower().capitalize()}]")
st.write(f"🔹 Precio medio: {data_barrio['Venta_2022'][nn_index]}€/m²"+ad)
if data_barrio['Rate_Supermercado'][nn_index]>0: st.write(f"🔹 Valoración de supermercados: {round(data_barrio['Rate_Supermercado'][nn_index],2)}⭐")
for i,x in enumerate(X):
    if x in options and x not in ['Colegios','Bus','Metro'] and data_barrio['Rate_'+x][nn_index]>0:   
        st.write(f"🔹 Valoración de {x.lower()}s: {round(data_barrio['Rate_'+x][nn_index],2)}⭐")
        
if 'Bus' in options:
    st.write("🔹 Tiene paradas de autobús")
if 'Metro' in options:
    st.write("🔹 Tiene paradas de metro")
if 'Colegios' in options:
    if data_barrio['Colegios'][nn_index]>1:
        st.write(f"🔹 Tiene {data_barrio['Colegios'][nn_index]} colegios")
    elif data_barrio['Colegios'][nn_index]==1:
        st.write(f"🔹 Tiene {data_barrio['Colegios'][nn_index]} colegio")
        
if health == 'Privada':
    if data_barrio['Centro_salud_privado'][nn_index] > 0:
        st.write(f'🔹 Tiene {data_barrio["Centro_salud_privado"][nn_index]} centro de salud privado')
    if data_barrio['Hospital_privado'][nn_index] > 0:
        st.write('🔹 Tiene hospital privado')
else:
    if data_barrio['Centro_salud_publico'][nn_index] > 0:
        st.write(f'🔹 Tiene {data_barrio["Centro_salud_publico"][nn_index]} centro de salud público')
    if data_barrio['Hospital_publico'][nn_index] > 0:
        st.write('🔹 Tiene hospital público')
        
if data_barrio['Espacios_verdes'][nn_index]>0:
    st.write('Tiene', int(data_barrio['Espacios_verdes'][nn_index]), 'zonas verdes')
        

################################
#           PISOS              #
################################

# Recomendación
X = pisos.loc[:,['Precio','Habitaciones','m2','Ascensor','Baños']]
X.fillna(0, inplace=True)

scaled_features = scaler.fit_transform(X.values)

user2=np.array([max_price, bed, m2, int(elevator), bath])
user_features = scaler.transform(user2.reshape(1, -1))

recommended_pisos = gower.gower_topn(user_features,scaled_features,n=5)['index']

# Mapa
lat,lon = data_barrio['Coordenadas'][nn_index].split(', ')
valencia_map = folium.Map(location=[float(lat), float(lon)], zoom_start=15)

pisos = pisos.reset_index()

for i in recommended_pisos:
    coord = pisos['Coordenadas'][i]
    if type(coord)!=float:
        p_lat,p_lon=coord.split(', ')
        marker = folium.Marker(location=[float(p_lat), float(p_lon)])
        valencia_map.add_child(marker)

st.subheader("Ubicación de tus pisos ideales")
folium_static(valencia_map)

st.subheader('Características del mejor piso')
if pisos['Rebajado%'][recommended_pisos[0]]>0:
    st.write(f':green[Este piso ha sido rebajado un {pisos["Rebajado%"][recommended_pisos[0]]}%]')
st.write('🔹 Precio:', str(pisos['Precio'][recommended_pisos[0]]).replace(',','.'), '€')
st.write('🔹 Superficie:', str(pisos['m2'][recommended_pisos[0]]).replace(',','.'), 'm²')
st.write('🔹 Habitaciones:', str(pisos['Habitaciones'][recommended_pisos[0]]))
st.write('🔹 Baños:', str(pisos['Baños'][recommended_pisos[0]]))
if pisos['Baños'][recommended_pisos[0]]>0:
    st.write('🔹 Tiene ascensor')
else:
    st.write('🔹 Sin ascensor')

