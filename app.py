import streamlit as st
from modules import accueil, clustering, filter_axes, detail_isin, spreads_curve

# Configuration initiale
st.set_page_config(layout="wide", page_title="Credit Dashboard")

# Initialisation de la navigation
if "page" not in st.session_state:
    st.session_state.page = "accueil"

# Affichage dynamique basé sur la page sélectionnée
pages = {
    "accueil": accueil,
    "clustering": clustering,
    "filter_axes": filter_axes,
    "detail_isin": detail_isin,
    "spreads_curve": spreads_curve
}

if st.session_state.page == "accueil":
    accueil.show()
elif st.session_state.page == "clustering":
    clustering.show(st.session_state.df)
elif st.session_state.page == "filter_axes":
    filter_axes.show(st.session_state.df)
elif st.session_state.page == "detail_isin":
    detail_isin.show(st.session_state.df)
elif st.session_state.page == "spreads_curve":
    spreads_curve.show(st.session_state.df)