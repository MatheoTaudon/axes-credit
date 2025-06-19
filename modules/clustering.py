import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

def show(df):
    st.button("⬅️ Retour à l’accueil", on_click=lambda: st.session_state.update(page="accueil"))
    st.markdown("<h2 style='text-align: center; color: orange;'>Clustering des Axes Crédit</h2>", unsafe_allow_html=True)

    df = df.copy()
    df["Maturity"] = pd.to_datetime(df["Maturity"], errors="coerce")
    df["Jours avant maturité"] = (df["Maturity"] - pd.Timestamp.now()).dt.days
    df["Années avant maturité"] = df["Jours avant maturité"] / 365

    for col in ["AXE_Offer_YLD", "AXE_Offer_BMK_SPD", "AXE_Offer_Z-SPD", "AXE_Offer_ASW", 
                "AXE_Offer_I-SPD", "AXE_Offer_QTY", "AXE_Offer_Price",
                "Composite_Bid_Price", "Composite_Offer_Price", "Mid_Price", "Axe_Mid_Spread"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    numeric_cols = ["Années avant maturité", "AXE_Offer_YLD", "AXE_Offer_BMK_SPD", "AXE_Offer_Z-SPD",
                    "AXE_Offer_I-SPD", "AXE_Offer_ASW", "AXE_Offer_QTY", "AXE_Offer_Price"]

    color_options = ["Sector", "Currency", "Sub_Sector"]

    with st.expander("Paramétrage du graphique"):
        x_axis = st.selectbox("Axe des abscisses (X)", numeric_cols, index=0)
        y_axis = st.selectbox("Axe des ordonnées (Y)", numeric_cols, index=1)
        color_by = st.selectbox("Colorier par :", color_options, index=0)

    df_filtered = df.dropna(subset=[x_axis, y_axis, "ISIN"])

    fig = px.scatter(
        df_filtered,
        x=x_axis,
        y=y_axis,
        color=color_by,
        hover_data=["ISIN", "IssuerName", "AXE_Offer_YLD", "AXE_Offer_Price", "AXE_Offer_QTY"],
        height=600
    )
    fig.update_traces(marker=dict(size=8, opacity=0.8, line=dict(width=0.5, color='white')))
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("<p style='text-align:center; font-size:0.9em; color:gray;'>Vous pouvez zoomer sur le graphique et double-cliquer pour réinitialiser la vue.</p>", unsafe_allow_html=True)

   # RECHERCHE ISIN
    st.markdown("### Rechercher un ISIN ou un Émetteur")
    df_all_labels = st.session_state.get("df_full", df).copy()
    df_all_labels["Label"] = df_all_labels["IssuerName"].astype(str) + " – " + df_all_labels["ISIN"].astype(str)
    
    combo_list = [""] + sorted(df_all_labels["Label"].dropna().unique())
    selected_label = st.selectbox("Commencez à taper le nom ou l'ISIN :", combo_list)
    
    if selected_label:
        selected_isin = df_all_labels.loc[df_all_labels["Label"] == selected_label, "ISIN"].values[0]
    
        # Recharger tous les dealers pour cet ISIN
        try:
            path = sorted([f for f in os.listdir("data") if f.startswith("Axes_") and f.endswith(".xlsx")], reverse=True)[0]
            full_path = os.path.join("data", path)
            df_usd = pd.read_excel(full_path, sheet_name="Axes Offers USD")
            df_eur = pd.read_excel(full_path, sheet_name="Axes Offers EUR")
            df_all = pd.concat([df_usd, df_eur], ignore_index=True)
            df_all.columns = df_all.columns.str.strip()
            df_all = df_all[df_all["ISIN"] == selected_isin]
        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier source : {e}")
            df_all = pd.DataFrame()
    
        if not df_all.empty:
            st.markdown("### Informations sur le titre")
            bond = df_all.iloc[0]
            infos = {
                "Bond ID": bond.get("Bond ID"),
                "Émetteur": bond.get("IssuerName"),
                "ISIN": bond.get("ISIN"),
                "Maturité": pd.to_datetime(bond.get("Maturity")).strftime("%d/%m/%Y") if pd.notna(bond.get("Maturity")) else None,
                "Devise": bond.get("Currency"),
                "Coupon": bond.get("Coupon"),
                "CouponType": bond.get("CouponType"),
                "Secteur": bond.get("Sector"),
                "Notation Moody's": bond.get("Moody's_rating")
            }
            st.table(pd.DataFrame.from_dict(infos, orient='index', columns=["Valeur"]))
    
            st.markdown("### Dealers axés sur ce titre")
            df_all["AXE_Offer_YLD"] = pd.to_numeric(df_all["IA_Offer_YLD"], errors="coerce") * 100
            df_all["AXE_Offer_Price"] = pd.to_numeric(df_all["IA_Offer_Price"], errors="coerce")
            df_all["AXE_Offer_QTY"] = pd.to_numeric(df_all["IA_Offer_QTY"], errors="coerce")
            df_all["Composite_Bid_Price"] = pd.to_numeric(df_all["TW_Bid_Price"], errors="coerce")
            df_all["Composite_Offer_Price"] = pd.to_numeric(df_all["TW_Offer_Price"], errors="coerce")
            df_all["Mid_Price"] = (df_all["Composite_Bid_Price"] + df_all["Composite_Offer_Price"]) / 2
            df_all["Axe_Mid_Spread"] = df_all["AXE_Offer_Price"] - df_all["Mid_Price"]
    
            table_cols = [
                "Dealer", "AXE_Offer_Price", "AXE_Offer_YLD", "AXE_Offer_QTY",
                "Composite_Bid_Price", "Composite_Offer_Price", "Axe_Mid_Spread",
                "IA_Offer_BMK_SPD", "IA_Offer_Z-SPD", "IA_Offer_I-SPD", "IA_Offer_ASW"
            ]
            table_cols = [col for col in table_cols if col in df_all.columns]
            st.dataframe(df_all[table_cols], use_container_width=True)
    
            st.markdown("### Fourchette Composite et position des dealers")
            bid = df_all["Composite_Bid_Price"].mean()
            offer = df_all["Composite_Offer_Price"].mean()
            mid = (bid + offer) / 2
    
            fig_spread = go.Figure()
    
            # Barre principale (bid → offer)
            fig_spread.add_shape(type="line", x0=bid, x1=offer, y0=0, y1=0,
                                 line=dict(color="orange", width=3))
    
            # Barres et labels : Bid, Mid, Offer
            for val, label in zip([bid, mid, offer], ["Bid", "Mid", "Offer"]):
                fig_spread.add_shape(type="line", x0=val, x1=val, y0=-0.2, y1=0.2,
                                     line=dict(color="orange", width=2))
                fig_spread.add_annotation(x=val, y=-0.3, text=label, showarrow=False,
                                          font=dict(color="orange"), yanchor="top")
    
            # Points des dealers 
            unique_dealers = df_all["Dealer"].dropna().unique()
            color_map = px.colors.qualitative.Safe  
            dealer_colors = {dealer: color_map[i % len(color_map)] for i, dealer in enumerate(unique_dealers)}
    
            for _, row in df_all.iterrows():
                fig_spread.add_trace(go.Scatter(
                    x=[row["AXE_Offer_Price"]],
                    y=[0],
                    mode="markers+text",
                    text=row["Dealer"],
                    textposition="top center",
                    marker=dict(size=15),
                    name=row["Dealer"]
                ))
    
            fig_spread.update_layout(
                height=250,
                template="plotly_dark",
                showlegend=False,
                xaxis_title="Prix",
                xaxis=dict(showgrid=False),
                yaxis=dict(visible=False),
            )
    
            st.plotly_chart(fig_spread, use_container_width=True)









