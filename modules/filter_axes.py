import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import datetime

def show(df):
    st.button("⬅️ Retour à l'accueil", on_click=lambda: st.session_state.update(page="accueil"))
    st.markdown("<h2 style='text-align:center; color:orange;'>Filtrer les Axes Crédit</h2>", unsafe_allow_html=True)

    df = df.copy()
    df["Maturity"] = pd.to_datetime(df["Maturity"], errors="coerce")

    st.markdown("### Filtres")
    col1, col2, col3 = st.columns(3)

    with col1:
        # Sector
        all_sectors = sorted(df["Sector"].dropna().unique())
        select_all_sectors = st.checkbox("Tous les secteurs", value=True)
        if select_all_sectors:
            selected_sectors = all_sectors
        else:
            selected_sectors = st.multiselect("Sector", all_sectors)

        # Currency
        all_currencies = sorted(df["Currency"].dropna().unique())
        select_all_currencies = st.checkbox("Toutes les devises", value=True)
        if select_all_currencies:
            selected_currencies = all_currencies
        else:
            selected_currencies = st.multiselect("Currency", all_currencies)

        # Coupon Type
        all_coupons = sorted(df["CouponType"].dropna().unique())
        select_all_coupons = st.checkbox("Tous les types de coupon", value=True)
        if select_all_coupons:
            selected_coupons = all_coupons
        else:
            selected_coupons = st.multiselect("Coupon Type", all_coupons)

        # Rating Category
        all_ratings = sorted(df["Rating_Category"].dropna().unique())
        select_all_ratings = st.checkbox("Toutes les notations", value=True)
        if select_all_ratings:
            selected_ratings = all_ratings
        else:
            selected_ratings = st.multiselect("Rating Category", all_ratings)
            
        issuers = sorted(df["IssuerName"].dropna().unique())
        issuer_selected = st.selectbox("Filtrer par émetteur (IssuerName)", [""] + issuers)

    with col2:
        yld_range = st.slider(
            "Yield (%)",
            min_value=0.0,
            max_value=50.0,
            value=(float(df["AXE_Offer_YLD"].min()), float(df["AXE_Offer_YLD"].max()))
        )

        bmk_spd_range = st.slider(
            "BMK Spread",
            min_value=float(df["AXE_Offer_BMK_SPD"].min()),
            max_value=float(df["AXE_Offer_BMK_SPD"].max()),
            value=(float(df["AXE_Offer_BMK_SPD"].min()), float(df["AXE_Offer_BMK_SPD"].max()))
        )

        qty_min = st.number_input("Quantité minimum", min_value=0.0, value=0.0)
        qty_max = st.number_input("Quantité maximum", min_value=0.0, value=float(df["AXE_Offer_QTY"].max()))

    with col3:
        nb_dealer_range = st.slider("Nb dealers axe", 1, int(df["Nb_Dealers_AXE"].max()), (1, int(df["Nb_Dealers_AXE"].max())))
        filter_composite = st.checkbox("Filtrer autour de la fourchette composite (Bid/Offer)")
        tol = None
        if filter_composite:
            tol = st.slider("Marge autour du Bid/Offer (± points)", min_value=0.0, max_value=5.0, value=0.05, step=0.01)
            axe_spread_range = st.slider("Axe vs Mid", float(df["Axe_Mid_Spread"].min()), float(df["Axe_Mid_Spread"].max()), (float(df["Axe_Mid_Spread"].min()), float(df["Axe_Mid_Spread"].max())))
        else:
            axe_spread_range = (float(df["Axe_Mid_Spread"].min()), float(df["Axe_Mid_Spread"].max()))

        exclude_144a = st.checkbox("Exclure les titres 144A")
        show_scraps = st.checkbox("Afficher uniquement les Scraps (quantité ne finissant pas par 0)")


    streamlit_min = datetime.date(1970, 1, 1)
    streamlit_max = datetime.date(2100, 12, 31)
    min_maturity = df["Maturity"].min()
    max_maturity = df["Maturity"].max()
    safe_min_date = max(min_maturity.date(), streamlit_min) if pd.notnull(min_maturity) else datetime.date.today()
    safe_max_date = min(max_maturity.date(), streamlit_max) if pd.notnull(max_maturity) else streamlit_max

    col4, col5 = st.columns(2)
    with col4:
        maturity_min = st.date_input("Maturité min", value=safe_min_date, min_value=streamlit_min, max_value=safe_max_date)
    with col5:
        maturity_max = st.date_input("Maturité max", value=safe_max_date, min_value=safe_min_date, max_value=streamlit_max)

    filtered_df = df.copy()
    filtered_df = filtered_df[filtered_df["Sector"].isin(selected_sectors)]
    filtered_df = filtered_df[filtered_df["Currency"].isin(selected_currencies)]
    filtered_df = filtered_df[filtered_df["CouponType"].isin(selected_coupons)]
    filtered_df = filtered_df[filtered_df["Rating_Category"].isin(selected_ratings)]

    if issuer_selected:
        filtered_df = filtered_df[filtered_df["IssuerName"] == issuer_selected]

    filtered_df = filtered_df[
        (filtered_df["AXE_Offer_YLD"] >= yld_range[0]) & (filtered_df["AXE_Offer_YLD"] <= yld_range[1]) &
        (filtered_df["AXE_Offer_QTY"] >= qty_min) & (filtered_df["AXE_Offer_QTY"] <= qty_max) &
        (filtered_df["Nb_Dealers_AXE"] >= nb_dealer_range[0]) & (filtered_df["Nb_Dealers_AXE"] <= nb_dealer_range[1]) &
        (filtered_df["Axe_Mid_Spread"] >= axe_spread_range[0]) & (filtered_df["Axe_Mid_Spread"] <= axe_spread_range[1]) &
        (filtered_df["AXE_Offer_BMK_SPD"] >= bmk_spd_range[0]) & (filtered_df["AXE_Offer_BMK_SPD"] <= bmk_spd_range[1])
    ]

    if maturity_min and maturity_max:
        maturity_min_dt = pd.to_datetime(maturity_min)
        maturity_max_dt = pd.to_datetime(maturity_max)
        filtered_df = filtered_df[
            (filtered_df["Maturity"] >= maturity_min_dt) &
            ((filtered_df["Maturity"] <= maturity_max_dt) | (filtered_df["Maturity"] > pd.to_datetime("2100-12-31")))
        ]

    if maturity_max < datetime.date(2100, 12, 31):
        filtered_df = filtered_df[filtered_df["Maturity"] <= pd.to_datetime(maturity_max)]

    if exclude_144a:
        filtered_df = filtered_df[~filtered_df["Bond ID"].astype(str).str.contains("144A", regex=False)]

    if show_scraps:
        filtered_df = filtered_df[~filtered_df["AXE_Offer_QTY"].astype(str).str.endswith("0")]

    if filter_composite and tol is not None:
        filtered_df = filtered_df[
            (filtered_df["AXE_Offer_Price"] >= filtered_df["Composite_Bid_Price"] - tol) &
            (filtered_df["AXE_Offer_Price"] <= filtered_df["Composite_Offer_Price"] + tol)
        ]

    st.markdown(f"### Résultats filtrés ({len(filtered_df)} lignes)")
    colonnes_affichees = [
        "IssuerName", "Bond ID", "Sector", "Sub_Sector", "Ticker", "ISIN", "Currency", "Coupon", "CouponType", "Maturity",
        "AXE_Offer_Price", "AXE_Offer_YLD", "AXE_Offer_QTY", "Nb_Dealers_AXE", "Best_Dealer",
        "Composite_Bid_Price", "Composite_Offer_Price", "Axe_Mid_Spread",
        "AXE_Offer_BMK_SPD", "AXE_Offer_Z-SPD", "AXE_Offer_I-SPD", "AXE_Offer_ASW",
        "FitchRating", "Moody's_rating", "Rating_Category"
    ]
    st.dataframe(filtered_df[colonnes_affichees], use_container_width=True)

    buffer = BytesIO()
    filtered_df[colonnes_affichees].to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button("📅 Exporter en Excel", data=buffer.getvalue(), file_name="axes_filtres.xlsx")


    # CLUSTERING
    st.markdown("### Clustering des résultats filtrés")
    filtered_df["Années avant maturité"] = (pd.to_datetime(filtered_df["Maturity"]) - pd.Timestamp.now()).dt.days / 365
    with st.expander("Paramétrage du graphique"):
        x_axis = st.selectbox("Axe X", ["Années avant maturité", "AXE_Offer_YLD", "AXE_Offer_Price"])
        y_axis = st.selectbox("Axe Y", ["AXE_Offer_BMK_SPD", "AXE_Offer_Z-SPD", "AXE_Offer_YLD", "AXE_Offer_Price"])
        color_by = st.selectbox("Couleur", ["Sector", "Currency", "Sub_Sector", "Rating_Category"])

    fig = px.scatter(
        filtered_df.dropna(subset=[x_axis, y_axis]),
        x=x_axis, y=y_axis, color=color_by,
        hover_data=["ISIN", "IssuerName", "AXE_Offer_YLD", "AXE_Offer_Price"],
        height=600
    )
    fig.update_traces(marker=dict(size=9, opacity=0.85, line=dict(width=0.5, color="white")))
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<p style='text-align:center; font-size:0.9em; color:gray;'>Vous pouvez zoomer sur le graphique et double-cliquer pour réinitialiser la vue.</p>", unsafe_allow_html=True)

    # RECHERCHE ISIN
    st.markdown("### Rechercher un ISIN ou un Émetteur")
    options = filtered_df[["IssuerName", "ISIN"]].dropna().astype(str)
    options["Label"] = options["IssuerName"] + " – " + options["ISIN"]
    combo_dict = dict(zip(options["Label"], options["ISIN"]))
    combo_list = [""] + sorted(combo_dict.keys())

    selected = st.selectbox("Commencez à taper le nom ou l'ISIN :", combo_list)

    if selected:
        selected_isin = combo_dict[selected]
        df_full = st.session_state.get("df_full", df)
        subset = df_full[df_full["ISIN"] == selected_isin]

        if not subset.empty:
            bond = subset.iloc[0]

            st.markdown("#### Infos du titre")
            infos = {
                "Bond ID": bond.get("Bond ID"),
                "Émetteur": bond.get("IssuerName"),
                "ISIN": bond.get("ISIN"),
                "Maturité": bond.get("Maturity"),
                "Devise": bond.get("Currency"),
                "Coupon": bond.get("Coupon"),
                "CouponType": bond.get("CouponType"),
                "Secteur": bond.get("Sector"),
                "Notation Moody's": bond.get("Moody's_rating")
            }
            st.table(pd.DataFrame.from_dict(infos, orient='index', columns=["Valeur"]))

        st.markdown("#### Dealers axés sur ce titre")
        dealer_col = "Dealer" if "Dealer" in subset.columns else "Best_Dealer"
        dealers_data = subset[[dealer_col, "AXE_Offer_Price", "AXE_Offer_YLD", "AXE_Offer_QTY",
            "Composite_Bid_Price", "Composite_Offer_Price", "Axe_Mid_Spread",
            "AXE_Offer_BMK_SPD", "AXE_Offer_Z-SPD", "AXE_Offer_I-SPD", "AXE_Offer_ASW"]].copy()
        dealers_data.rename(columns={dealer_col: "Dealer"}, inplace=True)
        st.dataframe(dealers_data, use_container_width=True)

        bid = bond.get("Composite_Bid_Price")
        offer = bond.get("Composite_Offer_Price")
        mid = bond.get("Mid_Price")

        fig2 = go.Figure()
        fig2.add_shape(type="line", x0=bid, x1=offer, y0=0, y1=0, line=dict(color="#FFA500", width=3))
        for val, label in zip([bid, mid, offer], ["Bid", "Mid", "Offer"]):
            fig2.add_shape(type="line", x0=val, x1=val, y0=-0.2, y1=0.2, line=dict(color="orange", width=2))
            fig2.add_annotation(x=val, y=-0.3, text=label, showarrow=False, font=dict(color="orange"), yanchor="top")

        for _, row in subset.iterrows():
            fig2.add_trace(go.Scatter(
                x=[row["AXE_Offer_Price"]],
                y=[0],
                mode="markers+text",
                text=row[dealer_col],
                textposition="top center",
                marker=dict(size=15)
            ))

        fig2.update_layout(height=250, template="plotly_dark", showlegend=False,
                           xaxis_title="Prix", xaxis=dict(showgrid=False), yaxis=dict(visible=False))
        st.plotly_chart(fig2, use_container_width=True)





