#adjusted from @wbjmattingly - https://www.youtube.com/watch?v=s86jz9qVeWA&t=158s

#imports
import streamlit as st


Dashboard = st.Page('Dashboard.py', title='Dashboard')
ChangeLog = st.Page('ChangeLog.py', title = 'Change Log')
Placeholder= st.Page('page_2.py', title = 'Placeholder')
Visualization = st.Page('VisTrans.py', title = 'Viz & Transform')


pg = st.navigation([Dashboard, Visualization, Placeholder, ChangeLog])

st.set_page_config(page_title='No-code EDA', page_icon=':blue:')
pg.run()