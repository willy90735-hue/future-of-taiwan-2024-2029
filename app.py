import streamlit as st
import pandas as pd
import numpy as np
import altair as alt



# ======================================
# 1. 模型參數（依照你提供的數據計算）
# ======================================

# 台灣自然路徑（1997–2024 平均）
TW_GDP_CAGR_BASE   = 0.03642405889760747   # 約 3.64% / 年
TW_FDI_CAGR_BASE   = 0.022877126440026485  # 約 2.29% / 年
TW_HOUSE_CAGR_BASE = 0.0409105229702702    # 約 4.09% / 年（2012–2021）

# 套用「香港回歸衝擊係數」後（中國模式）
TW_GDP_CAGR_CHINA   = 0.010086986828831218  # 約 1.01% / 年
TW_FDI_CAGR_CHINA   = 0.011270998331796981  # 約 1.13% / 年
TW_HOUSE_CAGR_CHINA = 0.007923277505180824  # 約 0.79% / 年

# 台灣 2024 年基準值（從台灣資料.xlsx 算出來）
BASE_GDP_2024 = 796_904_000_000     # USD
BASE_FDI_2024 = 7_858_117_000       # USD

BASE_YEAR = 2024
END_YEAR  = 2029


# ======================================
# 2. 預測運算函式
# ======================================

def project(base_value, cagr, years):
    """複利成長：base_value * (1+cagr)^years"""
    return base_value * ((1 + cagr) ** years)


def build_macro():
    """建立 2024–2029 台灣 GDP / FDI 兩種情境預測（單位：千萬美元）"""
    years = np.arange(BASE_YEAR, END_YEAR + 1)
    t = years - BASE_YEAR

    gdp_nat_usd   = project(BASE_GDP_2024, TW_GDP_CAGR_BASE, t)
    gdp_china_usd = project(BASE_GDP_2024, TW_GDP_CAGR_CHINA, t)
    fdi_nat_usd   = project(BASE_FDI_2024, TW_FDI_CAGR_BASE, t)
    fdi_china_usd = project(BASE_FDI_2024, TW_FDI_CAGR_CHINA, t)

    df = pd.DataFrame({
        "年份": years,
        "自然_GDP_美元": gdp_nat_usd,
        "中國模式_GDP_美元": gdp_china_usd,
        "自然_FDI_美元": fdi_nat_usd,
        "中國模式_FDI_美元": fdi_china_usd,
    })

    # 轉成「千萬美元」
    df["自然_GDP_千萬美元"]     = df["自然_GDP_美元"] / 10_000_000
    df["中國模式_GDP_千萬美元"] = df["中國模式_GDP_美元"] / 10_000_000
    df["自然_FDI_千萬美元"]     = df["自然_FDI_美元"] / 10_000_000
    df["中國模式_FDI_千萬美元"] = df["中國模式_FDI_美元"] / 10_000_000

    return df


def build_personal(income_2024_ntd, house_2024_ntd):
    """建立個人 2024–2029 收入 / 房價 / 房價所得比兩種情境"""
    years = np.arange(BASE_YEAR, END_YEAR + 1)
    t = years - BASE_YEAR

    income_nat   = project(income_2024_ntd, TW_GDP_CAGR_BASE, t)
    income_china = project(income_2024_ntd, TW_GDP_CAGR_CHINA, t)
    house_nat    = project(house_2024_ntd, TW_HOUSE_CAGR_BASE, t)
    house_china  = project(house_2024_ntd, TW_HOUSE_CAGR_CHINA, t)

    df = pd.DataFrame({
        "年份": years,
        "自然_收入_新台幣": income_nat,
        "中國模式_收入_新台幣": income_china,
        "自然_房價_新台幣": house_nat,
        "中國模式_房價_新台幣": house_china,
    })

    # 房價所得比（倍數）
    df["自然_房價所得比"]   = df["自然_房價_新台幣"] / df["自然_收入_新台幣"]
    df["中國模式_房價所得比"] = df["中國模式_房價_新台幣"] / df["中國模式_收入_新台幣"]

    # 顯示友善：四捨五入
    df["自然_收入_新台幣"]     = df["自然_收入_新台幣"].round(0)
    df["中國模式_收入_新台幣"] = df["中國模式_收入_新台幣"].round(0)
    df["自然_房價_新台幣"]     = df["自然_房價_新台幣"].round(0)
    df["中國模式_房價_新台幣"] = df["中國模式_房價_新台幣"].round(0)
    df["自然_房價所得比"]     = df["自然_房價所得比"].round(2)
    df["中國模式_房價所得比"] = df["中國模式_房價所得比"].round(2)

    return df


# ======================================
# 3. 通用中文折線圖（Altair）- 暖色系
# ======================================

def line_chart(df, x_col, y_cols, title, unit=""):
    df2 = df.copy()
    df2[x_col] = df2[x_col].astype(str)

    melt_df = df2.melt(x_col, y_cols, var_name="指標", value_name="數值")

    chart = (
        alt.Chart(melt_df)
        .mark_line(point=alt.OverlayMarkDef(size=80), strokeWidth=4)
        .encode(
            x=alt.X(
                f"{x_col}:O",
                title="年份",
                axis=alt.Axis(
                    labelAngle=0,
                    labelColor="black",
                    titleColor="black"
                )
            ),
            y=alt.Y(
                "數值:Q",
                title=f"數值（{unit}）" if unit else "數值",
                axis=alt.Axis(
                    labelColor="black",
                    titleColor="black"
                )
            ),
            color=alt.Color(
                "指標:N",
                title="情境 / 指標",
                scale=alt.Scale(
                    range=[
                        "#FF3B30",
                        "#009DFF",
                        "#FFC300",
                        "#FF6F00"
                    ]
                ),
                legend=alt.Legend(labelColor="black", titleColor="black")
            ),
            tooltip=[
                alt.Tooltip(f"{x_col}:O", title="年份"),
                alt.Tooltip("指標:N", title="情境 / 指標"),
                alt.Tooltip("數值:Q", format=",.0f", title="數值")
            ]
        )
        .properties(
            title=alt.TitleParams(
                text=title,
                color="black"
            ),
            width=780,
            height=360,
            background="#FFFFFF"
        )
    )

    st.altair_chart(chart, use_container_width=True)



# ======================================
# 4. Streamlit 主畫面 UI
# ======================================

st.set_page_config(
    page_title="台灣 2024–2029 經濟互動預測",
    layout="wide"
    # dark theme 可在 .streamlit/config.toml 裡設定 theme="dark"
)

st.title("🇹🇼 台灣 2024–2029 經濟互動預測模型")
st.caption("情境比較：自然發展 vs. 中國模式（香港回歸衝擊係數）")

st.markdown("""
本互動模型使用：

- **台灣 1997–2024 歷史 GDP / 外資 / 房價成長率**
- **香港回歸前後的成長率變化 → 推出「中國模式衝擊係數」**

來模擬台灣在 **2024–2029**：

- 若維持自然發展（不受中國影響）
- 若遭遇類似香港回歸後的制度衝擊（中國模式）

對 **GDP、外資 FDI、個人收入、房價、房價所得比** 的可能路徑。
""")


# --------------------------------------
# 左側：個人參數輸入
# --------------------------------------

st.sidebar.header("🔧 你的個人數據（2024 年起點）")

income_2024 = st.sidebar.number_input(
    "你的年收入（新台幣）",
    min_value=0.0,
    value=1_000_000.0,
    step=50_000.0,
    format="%.0f"
)

house_2024 = st.sidebar.number_input(
    "你目前房屋市值（新台幣）",
    min_value=0.0,
    value=10_000_000.0,
    step=100_000.0,
    format="%.0f"
)

st.sidebar.markdown("---")
st.sidebar.write("📘 **模型內部假設（已由資料計算）**")
st.sidebar.write(f"- 台灣自然 GDP 成長率：約 **{TW_GDP_CAGR_BASE*100:.2f}% / 年**")
st.sidebar.write(f"- 中國模式 GDP 成長率：約 **{TW_GDP_CAGR_CHINA*100:.2f}% / 年**")
st.sidebar.write(f"- 台灣自然房價成長率：約 **{TW_HOUSE_CAGR_BASE*100:.2f}% / 年**")
st.sidebar.write(f"- 中國模式房價成長率：約 **{TW_HOUSE_CAGR_CHINA*100:.2f}% / 年**")


# ======================================
# 5. 建立預測資料
# ======================================

macro_df = build_macro()
personal_df = build_personal(income_2024, house_2024)

# 方便顯示：四捨五入
macro_df_round = macro_df.copy()
for col in ["自然_GDP_千萬美元", "中國模式_GDP_千萬美元",
            "自然_FDI_千萬美元", "中國模式_FDI_千萬美元"]:
    macro_df_round[col] = macro_df_round[col].round(0).astype(int)

personal_df_round = personal_df.copy()
for col in [
    "自然_收入_新台幣", "中國模式_收入_新台幣",
    "自然_房價_新台幣", "中國模式_房價_新台幣"
]:
    personal_df_round[col] = personal_df_round[col].round(0)

for col in ["自然_房價所得比", "中國模式_房價所得比"]:
    personal_df_round[col] = personal_df_round[col].round(2)


# ======================================
# 6. 顯示：國家層級 GDP / FDI 預測
# ======================================

st.subheader("📈 國家層級：台灣 GDP 與外資 FDI 預測（單位：千萬美元）")

# GDP 圖
line_chart(
    macro_df_round,
    x_col="年份",
    y_cols=["自然_GDP_千萬美元", "中國模式_GDP_千萬美元"],
    title="台灣 GDP 預測（千萬美元）",
    unit="千萬美元"
)

# FDI 圖
line_chart(
    macro_df_round,
    x_col="年份",
    y_cols=["自然_FDI_千萬美元", "中國模式_FDI_千萬美元"],
    title="台灣外資 FDI 預測（千萬美元）",
    unit="千萬美元"
)

st.markdown("**GDP / FDI 詳細數值（千萬美元）**")
macro_df_show = macro_df_round[[
    "年份",
    "自然_GDP_千萬美元", "中國模式_GDP_千萬美元",
    "自然_FDI_千萬美元", "中國模式_FDI_千萬美元"
]].reset_index(drop=True)

macro_df_show = macro_df_round[[ ... ]].reset_index(drop=True)
st.dataframe(macro_df_show, use_container_width=True)



# ======================================
# 7. 個人收入預測（新台幣原值）
# ======================================

st.subheader("👤 你的個人收入：在兩種情境下的變化（單位：新台幣）")

line_chart(
    personal_df_round,
    x_col="年份",
    y_cols=["自然_收入_新台幣", "中國模式_收入_新台幣"],
    title="你的收入預測（新台幣）",
    unit="新台幣"
)

st.dataframe(
    personal_df_round[["年份", "自然_收入_新台幣", "中國模式_收入_新台幣"]],
    use_container_width=True
)


# ======================================
# 8. 個人房價預測（新台幣原值）
# ======================================

st.subheader("🏠 你的房價：在兩種情境下的變化（單位：新台幣）")

line_chart(
    personal_df_round,
    x_col="年份",
    y_cols=["自然_房價_新台幣", "中國模式_房價_新台幣"],
    title="你的房價預測（新台幣）",
    unit="新台幣"
)

st.dataframe(
    personal_df_round[["年份", "自然_房價_新台幣", "中國模式_房價_新台幣"]],
    use_container_width=True
)


# ======================================
# 9. 房價負擔能力：房價所得比
# ======================================

st.subheader("💰 房價負擔能力：房價所得比變化（房價 ÷ 年收入，倍數）")

line_chart(
    personal_df_round,
    x_col="年份",
    y_cols=["自然_房價所得比", "中國模式_房價所得比"],
    title="房價所得比（倍數）",
    unit="倍"
)

st.dataframe(
    personal_df_round[["年份", "自然_房價所得比", "中國模式_房價所得比"]],
    use_container_width=True
)

st.markdown("""
> 🔎 說明：房價所得比 = 房價 ÷ 年收入  
> - 例如：房價 1,000 萬、年收入 100 萬 → 房價所得比 = 10 倍  
> - 數字越高，代表買房壓力越大。
""")

