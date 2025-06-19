import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def show(df):
    st.button("⬅️ Retour à l'accueil", on_click=lambda: st.session_state.update(page="accueil"))
    st.markdown("<h2 style='text-align:center; color:orange;'>Chercher un Émetteur</h2>", unsafe_allow_html=True)

    df_full = st.session_state.get("df_full_axes", df)
    emetteurs = sorted(df["IssuerName"].dropna().unique())
    emetteurs = [""] + emetteurs 

    selected_issuer = st.selectbox("Rechercher un émetteur", emetteurs, index=0)

    if selected_issuer != "":
        df_issuer = df[df["IssuerName"] == selected_issuer].copy()
        df_issuer["Maturity"] = pd.to_datetime(df_issuer["Maturity"], errors="coerce")
        df_issuer["Années avant maturité"] = (df_issuer["Maturity"] - pd.Timestamp.now()).dt.days / 365

        st.markdown("### Courbe des meilleurs axes de l’émetteur")
        x_axis = st.selectbox("Axe X", ["Années avant maturité", "AXE_Offer_YLD", "AXE_Offer_Price"], key="x1")
        y_axis = st.selectbox("Axe Y", ["AXE_Offer_BMK_SPD", "AXE_Offer_Z-SPD", "AXE_Offer_YLD"], key="y1")

        df_issuer_sorted = df_issuer.dropna(subset=[x_axis, y_axis]).sort_values("Maturity")
        fig1 = px.line(
            df_issuer_sorted,
            x=x_axis,
            y=y_axis,
            color="Sub_Sector",
            text="ISIN",
            markers=True,
            title="Clustering – Meilleurs axes de l’émetteur",
            template="plotly_dark"
        )
        fig1.update_traces(mode='lines+markers+text', marker=dict(size=10), textposition="top center")
        st.plotly_chart(fig1, use_container_width=True)

        st.markdown("<p style='text-align:center; font-size:0.9em; color:gray;'>Vous pouvez zoomer sur le graphique et double-cliquer pour réinitialiser la vue.</p>", unsafe_allow_html=True)

        st.markdown("### Comparaison avec le secteur ou sous-secteur")
        compare_by = st.radio("Comparer à :", ["Sub_Sector", "Sector", "Rating_Category"], horizontal=True)

        if compare_by == "Rating_Category":
            if "Rating_Category" in df.columns and "Rating_Category" in df_issuer.columns:
                peer_group = df[df["Rating_Category"] == df_issuer["Rating_Category"].iloc[0]].copy()
            else:
                st.error("La colonne 'Rating_Category' est manquante dans le DataFrame")
                peer_group = pd.DataFrame()
        else:
            peer_group = df[df[compare_by] == df_issuer[compare_by].iloc[0]].copy()

        peer_group["Maturity"] = pd.to_datetime(peer_group["Maturity"], errors="coerce")
        peer_group["Années avant maturité"] = (peer_group["Maturity"] - pd.Timestamp.now()).dt.days / 365

        last_maturity_issuer = df_issuer["Maturity"].max()
        peer_group = peer_group[peer_group["Maturity"] <= last_maturity_issuer]

        x_axis2 = st.selectbox("Axe X (comparaison)", ["Années avant maturité", "AXE_Offer_YLD", "AXE_Offer_Price"], key="x2")
        y_axis2 = st.selectbox("Axe Y (comparaison)", ["AXE_Offer_BMK_SPD", "AXE_Offer_Z-SPD", "AXE_Offer_YLD"], key="y2")

        fig2 = go.Figure()
        color_col = "Rating_Category" if compare_by == "Rating_Category" else "Sub_Sector"
        peer_group_plot = peer_group.dropna(subset=[x_axis2, y_axis2, color_col])

        for cat in sorted(peer_group_plot[color_col].dropna().unique()):
            data_cat = peer_group_plot[peer_group_plot[color_col] == cat]
            customdata = np.stack([
                data_cat["IssuerName"],
                data_cat["ISIN"],
                data_cat["AXE_Offer_YLD"],
                data_cat["AXE_Offer_Price"]
            ], axis=-1)

            fig2.add_trace(go.Scatter(
                x=data_cat[x_axis2],
                y=data_cat[y_axis2],
                mode='markers',
                name=str(cat),
                marker=dict(size=8),
                customdata=customdata,
                hovertemplate=(
                    "Émetteur : %{customdata[0]}<br>" +
                    "ISIN : %{customdata[1]}<br>" +
                    "YLD : %{customdata[2]:.2f}%<br>" +
                    "Prix : %{customdata[3]:.2f}<extra></extra>"
                )
            ))

        df_issuer_plot = df_issuer.dropna(subset=[x_axis2, y_axis2])
        fig2.add_trace(go.Scatter(
            x=df_issuer_plot[x_axis2],
            y=df_issuer_plot[y_axis2],
            mode='markers+text',
            text=df_issuer_plot["ISIN"],
            textposition='top center',
            marker=dict(symbol='x', size=12, color='white', line=dict(width=2, color='black')),
            name='ISINs de l’émetteur'
        ))

        fig2.update_layout(
            title=f"Comparaison avec le {compare_by.lower()}",
            template="plotly_dark",
            showlegend=True
        )

        st.plotly_chart(fig2, use_container_width=True)

        st.markdown(
            "<p style='text-align:center; font-size:0.9em; color:gray;'>Vous pouvez zoomer sur le graphique et double-cliquer pour réinitialiser la vue.</p>",
            unsafe_allow_html=True
        )

        st.markdown("### Détail d’un ISIN")
        isin_df = df_issuer[["ISIN", "Maturity"]].dropna().drop_duplicates()
        isin_df["Maturity"] = pd.to_datetime(isin_df["Maturity"], errors="coerce").dt.date
        isin_df["Label"] = isin_df["ISIN"] + " – " + isin_df["Maturity"].astype(str)

        isin_options = [""] + isin_df["Label"].sort_values().tolist()
        selected_label = st.selectbox("Sélectionner un ISIN", isin_options, index=0)

        selected_isin = None
        if selected_label != "":
            selected_isin = selected_label.split(" – ")[0]

        if selected_isin:
            df_full_all = st.session_state.get("df_full", df)
            subset = df_full_all[df_full_all["ISIN"] == selected_isin]
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
                dealers_data = subset[[
                    dealer_col, "AXE_Offer_Price", "AXE_Offer_YLD", "AXE_Offer_QTY",
                    "Composite_Bid_Price", "Composite_Offer_Price", "Axe_Mid_Spread",
                    "AXE_Offer_BMK_SPD", "AXE_Offer_Z-SPD", "AXE_Offer_I-SPD", "AXE_Offer_ASW"
                ]].copy()
                dealers_data.rename(columns={dealer_col: "Dealer"}, inplace=True)
                st.dataframe(dealers_data, use_container_width=True)

                st.markdown("#### Visualisation fourchette composite")
                bid = bond.get("Composite_Bid_Price")
                offer = bond.get("Composite_Offer_Price")
                mid = bond.get("Mid_Price")

                fig = go.Figure()
                fig.add_shape(type="line", x0=bid, x1=offer, y0=0, y1=0,
                              line=dict(color="orange", width=3))

                for val, label in zip([bid, mid, offer], ["Bid", "Mid", "Offer"]):
                    fig.add_shape(type="line", x0=val, x1=val, y0=-0.2, y1=0.2,
                                  line=dict(color="orange", width=2))
                    fig.add_annotation(x=val, y=-0.3, text=label, showarrow=False,
                                       font=dict(color="orange"), yanchor="top")

                for _, row in subset.iterrows():
                    fig.add_trace(go.Scatter(
                        x=[row["AXE_Offer_Price"]],
                        y=[0],
                        mode="markers+text",
                        text=row["Dealer"],
                        textposition="top center",
                        marker=dict(size=15)
                    ))

                fig.update_layout(
                    height=250,
                    template="plotly_dark",
                    showlegend=False,
                    xaxis_title="Prix",
                    xaxis=dict(showgrid=False),
                    yaxis=dict(visible=False)
                )

                st.plotly_chart(fig, use_container_width=True)




