import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
import time

# Parámetros para WACC realista
Rf = 0.0435  # Tasa libre de riesgo
Rm = 0.085   # Rentabilidad esperada del mercado
Tc = 0.21    # Tasa de impuestos

def calcular_wacc(info, balance_sheet):
    try:
        beta = info.get("beta")
        price = info.get("currentPrice")
        shares = info.get("sharesOutstanding")
        market_cap = price * shares if price and shares else None
        lt_debt = balance_sheet.loc["Long Term Debt", :].iloc[0] if "Long Term Debt" in balance_sheet.index else 0
        st_debt = balance_sheet.loc["Short Long Term Debt", :].iloc[0] if "Short Long Term Debt" in balance_sheet.index else 0
        total_debt = lt_debt + st_debt
        Re = Rf + beta * (Rm - Rf) if beta is not None else None
        Rd = 0.055 if total_debt > 0 else 0
        E = market_cap
        D = total_debt
        if not Re or not E or not D or E + D == 0:
            return None, total_debt
        wacc = (E / (E + D)) * Re + (D / (E + D)) * Rd * (1 - Tc)
        return wacc, total_debt
    except:
        return None, None

def get_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        bs = stock.balance_sheet
        fin = stock.financials
        cf = stock.cashflow

        price = info.get("currentPrice")
        name = info.get("longName")
        sector = info.get("sector")
        country = info.get("country")
        industry = info.get("industry")
        pe = info.get("trailingPE")
        pb = info.get("priceToBook")
        dividend = info.get("dividendRate")
        dividend_yield = info.get("dividendYield")
        payout = info.get("payoutRatio")
        roa = info.get("returnOnAssets")
        roe = info.get("returnOnEquity")
        current_ratio = info.get("currentRatio")
        ltde = info.get("longTermDebtEquity")
        de = info.get("debtToEquity")
        op_margin = info.get("operatingMargins")
        profit_margin = info.get("netMargins")

        fcf = cf.loc["Total Cash From Operating Activities", :].iloc[0] if "Total Cash From Operating Activities" in cf.index else None
        shares = info.get("sharesOutstanding")
        pfcf = price / (fcf / shares) if fcf and shares else None

        ebit = fin.loc["EBIT", :].iloc[0] if "EBIT" in fin.index else None
        equity = bs.loc["Total Stockholder Equity", :].iloc[0] if "Total Stockholder Equity" in bs.index else None
        wacc, total_debt = calcular_wacc(info, bs)
        capital_invertido = total_debt + equity if total_debt and equity else None
        roic = ebit / capital_invertido if ebit and capital_invertido else None
        eva = roic - wacc if roic and wacc else None

        return {
            "Ticker": ticker,
            "Nombre": name,
            "Sector": sector,
            "País": country,
            "Industria": industry,
            "Precio": price,
            "P/E": pe,
            "P/B": pb,
            "P/FCF": pfcf,
            "Dividend Year": dividend,
            "Dividend Yield %": dividend_yield,
            "Payout Ratio": payout,
            "ROA": roa,
            "ROE": roe,
            "Current Ratio": current_ratio,
            "LtDebt/Eq": ltde,
            "Debt/Eq": de,
            "Oper Margin": op_margin,
            "Profit Margin": profit_margin,
            "WACC": wacc,
            "ROIC": roic,
            "EVA": eva,
            "Deuda Total": total_debt,
            "Patrimonio Neto": equity,
        }
    except Exception as e:
        return {"Ticker": ticker, "Error": str(e)}

# Inicializar resultados persistentes
if "resultados" not in st.session_state:
    st.session_state["resultados"] = {}

st.set_page_config(page_title="Dashboard Financiero", layout="wide")
st.title("📊 Dashboard de Análisis Financiero")

# -------- Sección 1 --------
st.markdown("## 📋 Sección 1: Ratios Financieros Generales")
tickers_input = st.text_area("🔎 Ingresa hasta 50 tickers separados por coma", "AAPL,MSFT,GOOGL,TSLA,AMZN")
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
tickers = tickers[:50]

if st.button("🔍 Analizar"):
    nuevos = [t for t in tickers if t not in st.session_state["resultados"]]
    for i, t in enumerate(nuevos):
        st.write(f"⏳ Procesando {t} ({i+1}/{len(nuevos)})...")
        st.session_state["resultados"][t] = get_data(t)
        time.sleep(1.5)

if st.session_state["resultados"]:
    datos = list(st.session_state["resultados"].values())
    df = pd.DataFrame(datos).drop(columns=["Deuda Total", "Patrimonio Neto", "Error"], errors="ignore")
    st.dataframe(df, use_container_width=True)

# -------- Sección 2 --------
st.markdown("## 💳 Sección 2: Análisis de Solvencia de Deuda")

for detalle in st.session_state["resultados"].values():
    nombre = detalle.get("Nombre", detalle["Ticker"])
    deuda = detalle.get("Deuda Total", 0)
    patrimonio = detalle.get("Patrimonio Neto", 0)

    if deuda is None or patrimonio is None:
        conclusion = "❓ Datos insuficientes para determinar la solvencia."
    elif patrimonio >= deuda:
        conclusion = f"✅ **Solvente**: el patrimonio neto (${patrimonio:,.0f}) supera la deuda total (${deuda:,.0f})."
    else:
        conclusion = f"❌ **No solvente**: la deuda total (${deuda:,.0f}) supera el patrimonio neto (${patrimonio:,.0f})."

    st.markdown(f"### 📌 {nombre}")
    df_velas = pd.DataFrame({
        "Categoría": ["Deuda Total", "Patrimonio Neto"],
        "Valor (USD)": [deuda, patrimonio]
    })

    fig, ax = plt.subplots()
    ax.bar(df_velas["Categoría"], df_velas["Valor (USD)"], width=0.4)
    ax.set_ylabel("USD")
    ax.set_title("Comparativa: Deuda vs Patrimonio")
    st.pyplot(fig)

    st.dataframe(df_velas.set_index("Categoría"))
    st.markdown(f"**Conclusión:** {conclusion}")
    st.markdown("---")

# -------- Sección 3 --------
st.markdown("## 💡 Sección 3: Análisis de Creación de Valor (ROIC vs WACC)")

for detalle in st.session_state["resultados"].values():
    nombre = detalle.get("Nombre", detalle["Ticker"])
    roic = detalle.get("ROIC")
    wacc = detalle.get("WACC")

    if roic is None or wacc is None:
        conclusion = "❓ Datos insuficientes para calcular ROIC o WACC."
    elif roic > wacc:
        conclusion = f"✅ **Crea valor**: ROIC ({roic:.2%}) > WACC ({wacc:.2%})"
    elif roic == wacc:
        conclusion = f"⚠️ **Margen neutro**: ROIC ({roic:.2%}) = WACC ({wacc:.2%})"
    else:
        conclusion = f"❌ **Destruye valor**: ROIC ({roic:.2%}) < WACC ({wacc:.2%})"

    st.markdown(f"### 📌 {nombre}")
    df_valor = pd.DataFrame({
        "Ratio": ["ROIC", "WACC"],
        "Valor (%)": [roic * 100 if roic else 0, wacc * 100 if wacc else 0]
    })

    fig, ax = plt.subplots()
    ax.bar(df_valor["Ratio"], df_valor["Valor (%)"], color=["green" if roic and roic > wacc else "red", "gray"])
    ax.set_ylabel("%")
    ax.set_title("ROIC vs WACC")
    st.pyplot(fig)

    st.markdown(f"**Conclusión:** {conclusion}")
    st.markdown("---")

# -------- Sección 4 --------
st.markdown("## 🧭 Sección 4: Mapa de Calor Financiero")

df_mapa = pd.DataFrame(list(st.session_state["resultados"].values()))
columnas_heatmap = ["P/E", "P/B", "ROA", "ROE", "Current Ratio", "Debt/Eq"]
df_mapa_filtrado = df_mapa[["Ticker"] + columnas_heatmap].set_index("Ticker")

def colorize(val, col):
    try:
        if pd.isnull(val): return ""
        if col == "P/E":
            return "background-color: red" if val > 40 else ("background-color: orange" if val > 25 else "background-color: green")
        if col == "P/B":
            return "background-color: red" if val > 8 else ("background-color: orange" if val > 4 else "background-color: green")
        if col == "ROA":
            return "background-color: red" if val < 0.02 else ("background-color: orange" if val < 0.05 else "background-color: green")
        if col == "ROE":
            return "background-color: red" if val < 0.05 else ("background-color: orange" if val < 0.12 else "background-color: green")
        if col == "Current Ratio":
            return "background-color: red" if val < 1 else ("background-color: orange" if val < 1.5 else "background-color: green")
        if col == "Debt/Eq":
            return "background-color: red" if val > 2 else ("background-color: orange" if val > 1 else "background-color: green")
    except:
        return ""
    return ""

styled_df = df_mapa_filtrado.style\
    .applymap(lambda v: colorize(v, "P/E"), subset=["P/E"])\
    .applymap(lambda v: colorize(v, "P/B"), subset=["P/B"])\
    .applymap(lambda v: colorize(v, "ROA"), subset=["ROA"])\
    .applymap(lambda v: colorize(v, "ROE"), subset=["ROE"])\
    .applymap(lambda v: colorize(v, "Current Ratio"), subset=["Current Ratio"])\
    .applymap(lambda v: colorize(v, "Debt/Eq"), subset=["Debt/Eq"])

st.dataframe(styled_df, use_container_width=True)
