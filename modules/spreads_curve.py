import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Fonction de classification des maturités
def maturity_bucket(maturity_date):
    if pd.isna(maturity_date):
        return "PERP"
    
    delta = (maturity_date - pd.Timestamp.now()).days / 365

    if delta <= 1:
        return "0-1Y"
    elif delta <= 2:
        return "1-2Y"
    elif delta <= 3:
        return "2-3Y"
    elif delta <= 4:
        return "3-4Y"
    elif delta <= 5:
        return "4-5Y"
    elif delta <= 7:
        return "5-7Y"
    elif delta <= 8:
        return "7-8Y"
    elif delta <= 10:
        return "8-10Y"
    elif delta <= 15:
        return "10-15Y"
    elif delta <= 20:
        return "15-20Y"
    elif delta <= 25:
        return "20-25Y"
    elif delta <= 30:
        return "25-30Y"
    else:
        return "PERP"

def show(df):
    st.button("⬅️ Retour à l'accueil", on_click=lambda: st.session_state.update(page="accueil"))
    st.markdown(f"<h2 style='text-align:center; color:orange;'>Flux du {datetime.now().strftime('%d/%m/%Y')}</h2>", unsafe_allow_html=True)

    # Préparation des données
    df = df.copy()
    df["Maturity"] = pd.to_datetime(df["Maturity"], errors="coerce")
    df["MaturityBucket"] = df["Maturity"].apply(maturity_bucket)

    # Ordre défini pour les buckets de maturité
    ordered_buckets = [
        "0-1Y", "1-2Y", "2-3Y", "3-4Y", "4-5Y",
        "5-7Y", "7-8Y", "8-10Y", "10-15Y", "15-20Y",
        "20-25Y", "25-30Y", "PERP"
    ]
    df["MaturityBucket"] = pd.Categorical(df["MaturityBucket"], categories=ordered_buckets, ordered=True)

    # Moody's sorting
    moodys_order = [
        "Aaa", "Aa1", "Aa2", "Aa3", "A1", "A2", "A3",
        "Baa1", "Baa2", "Baa3", "Ba1", "Ba2", "Ba3",
        "B1", "B2", "B3", "Caa1", "Caa2", "Caa3", "Ca", "C", "WR"
    ]
    df["Moody's_rating"] = pd.Categorical(df["Moody's_rating"], categories=moodys_order, ordered=True)

    # Rating_Category sorting
    rating_order = ["Investment Grade", "Crossover", "High Yield", "Junk", "Not Rated"]
    df["Rating_Category"] = pd.Categorical(df["Rating_Category"], categories=rating_order, ordered=True)

    # --- HEATMAP ---
    st.markdown("### Heatmap des quantités proposées")
    heatmap_y = st.selectbox("Axe Y (heatmap)", ["Rating_Category", "Sector", "Sub_Sector"])

    qty_pivot = df.groupby([heatmap_y, "MaturityBucket"])["AXE_Offer_QTY"].sum().reset_index().pivot(
        index=heatmap_y, columns="MaturityBucket", values="AXE_Offer_QTY"
    )
    qty_pivot = qty_pivot.reindex(columns=ordered_buckets)

    if pd.api.types.is_categorical_dtype(df[heatmap_y]):
        qty_pivot = qty_pivot.reindex(index=df[heatmap_y].cat.categories)

    fig_qty = px.imshow(
        qty_pivot.fillna(0),
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Viridis",
        title=f"Quantité totale proposée par {heatmap_y} / MaturityBucket"
    )
    st.plotly_chart(fig_qty, use_container_width=True)

    # --- BAR CHART ---
    st.markdown("### Analyse des flux d'axes")
    x_flux = st.selectbox("Axe X (flux)", ["Sector", "Sub_Sector", "Moody's_rating", "MaturityBucket", "Rating_Category"])
    bar_mode = st.radio("Mode", ["Nombre d’axes", "Quantité totale"])

    if bar_mode == "Nombre d’axes":
        flux_data = df[x_flux].value_counts().reset_index()
        flux_data.columns = [x_flux, "Nombre d'axes"]
        y_col = "Nombre d'axes"
    else:
        flux_data = df.groupby(x_flux)["AXE_Offer_QTY"].sum().reset_index()
        y_col = "AXE_Offer_QTY"

    if x_flux in ["Moody's_rating", "MaturityBucket", "Rating_Category"]:
        flux_data[x_flux] = pd.Categorical(flux_data[x_flux], categories=df[x_flux].cat.categories, ordered=True)
        flux_data = flux_data.sort_values(by=x_flux)

    flux_data = flux_data[flux_data[y_col] > 0]

    fig_flux = px.bar(
        flux_data,
        x=x_flux,
        y=y_col,
        text_auto=True,
        title=f"{y_col} par {x_flux}",
        color_discrete_sequence=["#1f77b4"]
    )
    st.plotly_chart(fig_flux, use_container_width=True)







