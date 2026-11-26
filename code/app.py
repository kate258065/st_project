
import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import linregress

# =================================
# 1. 기본 설정
# =================================

st.set_page_config(
    page_title="지역별 의료 인프라와 건강검진",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 지역별 의료 인프라와 건강검진 수검률")
st.write(
    "우리나라 지역별 의료기관 수와 건강검진 수검률의 관계를 알아봅니다."
)

# =================================
# 2. CSV 파일 자동 불러오기
# =================================

def read_csv_file(path):
    for encoding in ["utf-8-sig", "cp949", "euc-kr", "utf-8"]:
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"{path} 파일의 인코딩을 확인해 주세요.")

try:
    population = read_csv_file("data/population.csv")
    health = read_csv_file("data/health.csv")
    hospital = read_csv_file("data/hospital.csv")

except Exception as e:
    st.error(f"데이터를 불러올 수 없습니다: {e}")
    st.stop()

# =================================
# 3. 지역명 통일
# =================================

REGION_MAP = {
    "서울": "서울특별시",
    "부산": "부산광역시",
    "대구": "대구광역시",
    "인천": "인천광역시",
    "광주": "광주광역시",
    "대전": "대전광역시",
    "울산": "울산광역시",
    "세종": "세종특별자치시",
    "경기": "경기도",
    "강원": "강원특별자치도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전북": "전북특별자치도",
    "전남": "전라남도",
    "경북": "경상북도",
    "경남": "경상남도",
    "제주": "제주특별자치도"
}

def normalize_region(value):
    value = str(value).strip()
    value = value.split()[0]
    value = value.split("(")[0].strip()
    return REGION_MAP.get(value, value)

# =================================
# 4. 인구 데이터 처리
# =================================

population_columns = [
    col for col in population.columns
    if str(col).startswith("20")
]

if not population_columns:
    st.error("인구 자료의 연도별 열을 찾을 수 없습니다.")
    st.stop()

population_year = population_columns[-1]

population = population[
    population["연령별"].astype(str).str.strip() == "계"
].copy()

population = population[
    ["행정구역(시군구)별", population_year]
].copy()

population.columns = ["지역", "인구수"]

population["지역"] = population["지역"].apply(normalize_region)
population["인구수"] = pd.to_numeric(
    population["인구수"], errors="coerce"
)

population = population[population["지역"] != "전국"]

# =================================
# 5. 건강검진 데이터 처리
# =================================

health = health[
    ["시도", "대상인원", "수검인원"]
].copy()

health.columns = ["지역", "대상인원", "수검인원"]

health["지역"] = health["지역"].apply(normalize_region)

health["대상인원"] = pd.to_numeric(
    health["대상인원"], errors="coerce"
)

health["수검인원"] = pd.to_numeric(
    health["수검인원"], errors="coerce"
)

health["수검률(%)"] = (
    health["수검인원"] / health["대상인원"] * 100
)

# =================================
# 6. 의료기관 데이터 처리
# =================================

years = sorted(hospital["연도"].dropna().unique())

selected_year = st.sidebar.selectbox(
    "의료기관 자료 연도 선택",
    years,
    index=len(years) - 1
)

hospital = hospital[hospital["연도"] == selected_year].copy()

hospital["지역"] = hospital["시도"].apply(normalize_region)

facility_columns = [
    "병의원_종합병원",
    "병의원_요양병원",
    "병의원_일반병원",
    "병의원_의원"
]

for col in facility_columns:
    hospital[col] = pd.to_numeric(
        hospital[col], errors="coerce"
    )

hospital["의료기관 수"] = hospital[facility_columns].sum(axis=1)

hospital = hospital[["지역", "의료기관 수"]]

# =================================
# 7. 데이터 결합
# =================================

df = pd.merge(
    health,
    hospital,
    on="지역",
    how="inner"
)

df = pd.merge(
    df,
    population,
    on="지역",
    how="inner"
)

df = df.dropna(
    subset=["대상인원", "수검인원", "의료기관 수", "인구수"]
)

df = df[
    (df["인구수"] > 0) &
    (df["대상인원"] > 0)
].copy()

df["인구 1만 명당 의료기관 수"] = (
    df["의료기관 수"] / df["인구수"] * 10000
)

if len(df) < 3:
    st.error("분석할 수 있는 지역이 3곳 미만입니다.")
    st.stop()

# =================================
# 8. 지역별 분석 데이터 표
# =================================

st.subheader("📊 1. 지역별 분석 데이터")

st.caption(
    f"의료기관 기준 연도: {selected_year}년 / "
    f"인구 기준: {population_year}"
)

display_df = df[
    [
        "지역",
        "인구수",
        "의료기관 수",
        "인구 1만 명당 의료기관 수",
        "대상인원",
        "수검인원",
        "수검률(%)"
    ]
].copy()

display_df = display_df.sort_values("지역")

st.dataframe(
    display_df.style.format({
        "인구수": "{:,.0f}",
        "의료기관 수": "{:,.0f}",
        "인구 1만 명당 의료기관 수": "{:.2f}",
        "대상인원": "{:,.0f}",
        "수검인원": "{:,.0f}",
        "수검률(%)": "{:.2f}%"
    }),
    use_container_width=True,
    hide_index=True
)

# =================================
# 9. 의료 인프라와 수검률 관계 그래프
# =================================

st.subheader("📈 2. 의료 인프라와 건강검진 수검률의 관계")

x_choice = st.radio(
    "가로축 기준 선택",
    [
        "의료기관 수",
        "인구 1만 명당 의료기관 수"
    ],
    horizontal=True
)

x = df[x_choice]
y = df["수검률(%)"]

result = linregress(x, y)

slope = result.slope
intercept = result.intercept
r_value = result.rvalue

# 산점도
fig = px.scatter(
    df,
    x=x_choice,
    y="수검률(%)",
    text="지역",
    hover_data=[
        "의료기관 수",
        "인구 1만 명당 의료기관 수",
        "수검률(%)"
    ],
    labels={
        x_choice: x_choice,
        "수검률(%)": "건강검진 수검률(%)"
    },
    title="지역별 의료 인프라와 건강검진 수검률"
)

# 회귀선
line_x = [x.min(), x.max()]
line_y = [
    slope * value + intercept
    for value in line_x
]

fig.add_trace(
    go.Scatter(
        x=line_x,
        y=line_y,
        mode="lines",
        name="회귀선"
    )
)

fig.update_traces(
    textposition="top center",
    selector=dict(mode="markers+text")
)

st.plotly_chart(fig, use_container_width=True)

# =================================
# 10. 그래프 간단한 해석
# =================================

st.markdown("### 그래프 해석")

st.write(f"- 분석 지역 수: {len(df)}개")
st.write(f"- 상관계수: {r_value:.3f}")

if r_value > 0:
    st.write(
        "의료 인프라 지표가 높은 지역일수록 "
        "건강검진 수검률도 높은 경향이 있습니다."
    )
elif r_value < 0:
    st.write(
        "의료 인프라 지표가 높은 지역일수록 "
        "건강검진 수검률이 낮은 경향이 있습니다."
    )
else:
    st.write("두 변수 사이에 뚜렷한 선형 관계가 없습니다.")

st.caption(
    "※ 지역별 자료의 상관관계를 보여주는 그래프이며, "
    "인과관계를 증명하는 것은 아닙니다."
)
