import streamlit as st
import pandas as pd
import os
from datetime import datetime
import numpy as np

def classify_rating_cat(fitch, moodys):
    rating = fitch if pd.notna(fitch) and str(fitch).strip().lower() != "nan" else moodys
    if pd.isna(rating) or str(rating).strip() == "":
        return "Not Rated"

    rating = str(rating).upper().strip()

    ig_ratings = {
        "AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "Aaa", "Aa1", "Aa2", "Aa3",
        "A1", "A2", "A3"
    }

    crossover_ratings = {
        "BBB+", "BBB", "BBB-", "Baa1", "Baa2", "Baa3", "BB+", "BB", "BB-"
    }

    hy_ratings = {
        "B+", "B", "B-", "B1", "B2", "B3"
    }

    junk_ratings = {
        "CCC+", "CCC", "CCC-", "CC", "C", "Ca", "Caa1", "Caa2", "Caa3"
    }

    if rating in ig_ratings:
        return "Investment Grade"
    elif rating in crossover_ratings:
        return "Crossover"
    elif rating in hy_ratings:
        return "High Yield"
    elif rating in junk_ratings:
        return "Junk"
    else:
        return "Not Rated"

def show():
    st.markdown("<h1 style='text-align:center; color:orange;'>AXES Crédit</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Bienvenue, sélectionnez une analyse :</p>", unsafe_allow_html=True)

    if "df" not in st.session_state:
        data_dir = "data"
        axes_files = [f for f in os.listdir(data_dir) if f.startswith("Axes_") and f.endswith(".xlsx")]
        if not axes_files:
            st.warning("⚠️ Aucun fichier Axes_*.xlsx trouvé dans le dossier 'data'.")
            return

        latest_file = sorted(axes_files, reverse=True)[0]
        path = os.path.join(data_dir, latest_file)

        df_usd = pd.read_excel(path, sheet_name="Axes Offers USD")
        df_eur = pd.read_excel(path, sheet_name="Axes Offers EUR")
        df = pd.concat([df_usd, df_eur], ignore_index=True)
        df.columns = df.columns.str.strip()

        df.rename(columns={
            "IA_Offer_Price": "AXE_Offer_Price",
            "IA_Offer_YLD": "AXE_Offer_YLD",
            "IA_Offer_QTY": "AXE_Offer_QTY",
            "IA_Offer_BMK_SPD": "AXE_Offer_BMK_SPD",
            "IA_Offer_I-SPD": "AXE_Offer_I-SPD",
            "IA_Offer_Z-SPD": "AXE_Offer_Z-SPD",
            "IA_Offer_ASW": "AXE_Offer_ASW"
        }, inplace=True)

        df.drop(columns=[
            "IA_Offer_BMK_SPD_zscore", "IA_Offer_BMK_SPD_percentile",
            "CompositeRating", "TW_Offer_YLD", "TW_Bid_YLD"
        ], errors="ignore", inplace=True)

        df = df[df["AXE_Offer_Price"].notna()]

        # Corriger les inversions yield/price
        if "Stream_Offer_Price" in df.columns:
            prix = pd.to_numeric(df["AXE_Offer_Price"], errors="coerce")
            stream = pd.to_numeric(df["Stream_Offer_Price"], errors="coerce")
            yld = pd.to_numeric(df["AXE_Offer_YLD"], errors="coerce")
            mask = (prix - stream).abs() > 10
            valid = mask & prix.notna() & yld.notna()
            temp_price = prix[valid]
            temp_yld = yld[valid]
            df.loc[valid, "AXE_Offer_Price"] = temp_yld * 100
            df.loc[valid, "AXE_Offer_YLD"] = temp_price / 100

        df.drop(columns=["Stream_Offer_Price"], errors="ignore", inplace=True)
        
        df["AXE_Offer_YLD"] = pd.to_numeric(df["AXE_Offer_YLD"], errors="coerce").abs() * 100
        df["AXE_Offer_Price"] = pd.to_numeric(df["AXE_Offer_Price"], errors="coerce")

        # Nettoyage YLD aberrants
        df["AXE_Offer_YLD"] = df["AXE_Offer_YLD"].where(~(
            ((df["AXE_Offer_Price"].between(95, 105)) & ((df["AXE_Offer_YLD"] < -5) | (df["AXE_Offer_YLD"] > 15))) |
            ((df["AXE_Offer_Price"] < 50) & (df["AXE_Offer_YLD"] > 60)) |
            ((df["AXE_Offer_Price"] > 150) & (df["AXE_Offer_YLD"] < -20))
        ))

        df["AXE_Offer_QTY"] = pd.to_numeric(df["AXE_Offer_QTY"], errors="coerce")

        # Calcul Mid et spread
        df["Composite_Offer_Price"] = df["TW_Offer_Price"]
        df["Composite_Bid_Price"] = df["TW_Bid_Price"]
        df["Mid_Price"] = (df["Composite_Offer_Price"] + df["Composite_Bid_Price"]) / 2
        df["Axe_Mid_Spread"] = df["AXE_Offer_Price"] - df["Mid_Price"]
        df.drop(columns=["TW_Offer_Price", "TW_Bid_Price"], inplace=True, errors="ignore")

        df["Maturity"] = pd.to_datetime(df["Maturity"], errors="coerce").dt.date

       # Calcul secteur et sous-secteur
        df["Sub_Sector"] = df["Sector"]
        df["Sector"] = df["Sub_Sector"].str.extract(r'^([^ -]+)')
        df["Sector"] = df.apply(lambda row: "IG FIN" if (
            row["Sub_Sector"].startswith("IG") and
            any(x in str(row["Sub_Sector"]) for x in ["CoCo", "Lower Tier 2", "Lower T2", "SnBnk/Fin", "Upper T2/T1"])
        ) else ("IG CORPO" if str(row["Sub_Sector"]).startswith("IG") else row["Sector"]), axis=1)

        # Rating Category
        df["Rating_Category"] = df.apply(lambda row: classify_rating_cat(row.get("FitchRating"), row.get("Moody's_rating")), axis=1)
        st.session_state.df_full = df.copy()
        
        # Sélection du best dealer
        df["Nb_Dealers_AXE"] = df.groupby("ISIN")["Dealer"].transform("count")
        df["AXE_Offer_YLD_clean"] = df["AXE_Offer_YLD"].fillna(-9999)
        idx = df.groupby("ISIN")["AXE_Offer_YLD_clean"].idxmax()
        df = df.loc[idx].copy()
        df.rename(columns={"Dealer": "Best_Dealer"}, inplace=True)

        # Arrondis
        for col in df.columns:
            if col.startswith("AXE_Offer_") and "SPD" in col:
                df[col] = np.ceil(pd.to_numeric(df[col], errors="coerce"))
            elif col in ["AXE_Offer_Price", "AXE_Offer_YLD", "AXE_Offer_QTY", "Composite_Offer_Price", "Composite_Bid_Price", "Mid_Price", "Axe_Mid_Spread"]:
                df[col] = pd.to_numeric(df[col], errors="coerce").round(2)

        st.session_state.df = df

    df = st.session_state.df

    # Navigation
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Clustering des axes"):
            st.session_state.page = "clustering"
            st.rerun()
    with col2:
        if st.button("Filtrer les axes"):
            st.session_state.page = "filter_axes"
            st.rerun()
    with col3:
        if st.button("Chercher un Émetteur"):
            st.session_state.page = "detail_isin"
            st.rerun()
    with col4:
        if st.button("Flux"):
            st.session_state.page = "spreads_curve"
            st.rerun()

    st.markdown(f"### Axes du {datetime.now().strftime('%d/%m/%Y')} ({len(df)} lignes)")

    colonnes_affichees = [
        "IssuerName", "Bond ID", "Sector", "Sub_Sector", "Ticker", "ISIN", "Currency", "Coupon", "CouponType", "Maturity",
        "AXE_Offer_Price", "AXE_Offer_YLD", "AXE_Offer_QTY", "Nb_Dealers_AXE", "Best_Dealer",
        "Composite_Bid_Price", "Composite_Offer_Price", "Axe_Mid_Spread",
        "AXE_Offer_BMK_SPD", "AXE_Offer_Z-SPD", "AXE_Offer_I-SPD", "AXE_Offer_ASW",
        "FitchRating", "Moody's_rating", "Rating_Category"
    ]
    colonnes_affichees = [col for col in colonnes_affichees if col in df.columns]

    st.dataframe(df[colonnes_affichees], use_container_width=True)








