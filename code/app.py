
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import linregress

st.set_page_config(
    page_title="지역별 의료 인프라와 건강검진 수검률",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 지역별 의료 인프라와 건강검진 수검률 분석")
st.markdown("""
우리나라 지역별 의료 인프라 차이가 건강검진 수검률에 어떤 관계가 있는지 분석합니다.
""")

# -----------------------------
# CSV 파일 읽기
# -----------------------------
def read_csv_file(file):
    for encoding in ["utf-8-sig", "cp949", "euc-kr", "utf-8"]:
        try:
            file.seek(0)
            return pd.read_csv(file, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("CSV 파일의 인코딩을 확인해 주세요.")

# -----------------------------
# 지역명 통일
# -----------------------------
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

    if value in REGION_MAP:
        return REGION_MAP[value]

    return value

# -----------------------------
# 파일 업로드
# -----------------------------
st.sidebar.header("📂 분석 자료 업로드")

population_file = st.sidebar.file_uploader(
    "① 지역별 주민등록인구 CSV",
    type=["csv"]
)

health_file = st.sidebar.file_uploader(
    "② 지역별 건강검진 수검 현황 CSV",
    type=["csv"]
)

hospital_file = st.sidebar.file_uploader(
    "③ 지역별 의료기관 현황 CSV",
    type=["csv"]
)

if not all([population_file, health_file, hospital_file]):
    st.info("왼쪽 메뉴에서 CSV 파일 3개를 모두 업로드해 주세요.")
    st.stop()

try:
    population = read_csv_file(population_file)
    health = read_csv_file(health_file)
    hospital = read_csv_file(hospital_file)

except Exception as e:
    st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
    st.stop()

# -----------------------------
# 의료기관 연도 선택
# -----------------------------
if "연도" not in hospital.columns:
    st.error("의료기관 파일에 '연도' 열이 없습니다.")
    st.stop()

years = sorted(hospital["연도"].dropna().unique())
selected_year = st.sidebar.selectbox(
    "의료기관 자료 연도",
    years,
    index=len(years) - 1
)

hospital = hospital[hospital["연도"] == selected_year].copy()

# -----------------------------
# 인구 데이터 처리
# -----------------------------
required_population_columns = ["행정구역(시군구)별", "연령별"]

if not all(col in population.columns for col in required_population_columns):
    st.error("인구 파일의 열 이름을 확인해 주세요.")
    st.stop()

population_columns = [
    col for col in population.columns
    if str(col).startswith("20")
]

if not population_columns:
    st.error("인구 파일에서 인구수 열을 찾을 수 없습니다.")
    st.stop()

population_year = st.sidebar.selectbox(
    "인구 자료 기준월",
    population_columns,
    index=len(population_columns) - 1
)

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

# -----------------------------
# 건강검진 데이터 처리
# -----------------------------
required_health_columns = ["시도", "대상인원", "수검인원"]

if not all(col in health.columns for col in required_health_columns):
    st.error("건강검진 파일의 열 이름을 확인해 주세요.")
    st.stop()

health = health[["시도", "대상인원", "수검인원"]].copy()

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

# -----------------------------
# 의료기관 데이터 처리
# -----------------------------
required_hospital_columns = [
    "시도",
    "병의원_종합병원",
    "병의원_요양병원",
    "병의원_일반병원",
    "병의원_의원"
]

if not all(col in hospital.columns for col in required_hospital_columns):
    st.error("의료기관 파일의 열 이름을 확인해 주세요.")
    st.stop()

hospital = hospital[
    required_hospital_columns
].copy()

hospital.columns = [
    "지역",
    "종합병원",
    "요양병원",
    "일반병원",
    "의원"
]

hospital["지역"] = hospital["지역"].apply(normalize_region)

facility_columns = [
    "종합병원",
    "요양병원",
    "일반병원",
    "의원"
]

for col in facility_columns:
    hospital[col] = pd.to_numeric(
        hospital[col], errors="coerce"
    )

hospital["의료기관 수"] = hospital[facility_columns].sum(axis=1)

# -----------------------------
# 세 데이터 결합
# -----------------------------
df = pd.merge(
    health,
    hospital[["지역", "의료기관 수"]],
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
    subset=["수검률(%)", "의료기관 수", "인구수"]
)

df = df[df["인구수"] > 0].copy()

df["인구 1만 명당 의료기관 수"] = (
    df["의료기관 수"] / df["인구수"] * 10000
)

if len(df) < 3:
    st.error("분석 가능한 지역이 3곳 미만입니다. CSV 파일과 지역명을 확인해 주세요.")
    st.stop()

# -----------------------------
# 분석 결과
# -----------------------------
st.subheader("📊 지역별 분석 데이터")

st.caption(
    f"의료기관 기준 연도: {selected_year}년 | "
    f"인구 기준월: {population_year}"
)

st.dataframe(
    df[
        [
            "지역",
            "인구수",
            "의료기관 수",
            "인구 1만 명당 의료기관 수",
            "대상인원",
            "수검인원",
            "수검률(%)"
        ]
    ].round(2),
    use_container_width=True
)

# -----------------------------
# 지역별 수검률 막대그래프
# -----------------------------
st.subheader("1. 지역별 건강검진 수검률")

bar_df = df.sort_values("수검률(%)", ascending=False)

fig_bar = px.bar(
    bar_df,
    x="지역",
    y="수검률(%)",
    text=bar_df["수검률(%)"].round(1),
    title="지역별 건강검진 수검률 비교",
    labels={
        "지역": "지역",
        "수검률(%)": "건강검진 수검률(%)"
    }
)

fig_bar.update_layout(
    xaxis_tickangle=-45,
    yaxis_range=[0, 100]
)

st.plotly_chart(fig_bar, use_container_width=True)

# -----------------------------
# 산점도 및 회귀분석
# -----------------------------
st.subheader("2. 의료 인프라와 건강검진 수검률의 관계")

x_choice = st.radio(
    "분석할 의료 인프라 지표 선택",
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
r_squared = r_value ** 2
p_value = result.pvalue

fig_scatter = px.scatter(
    df,
    x=x_choice,
    y="수검률(%)",
    text="지역",
    hover_data=[
        "의료기관 수",
        "인구 1만 명당 의료기관 수",
        "인구수"
    ],
    title=f"{x_choice}와 건강검진 수검률의 관계",
    labels={
        x_choice: x_choice,
        "수검률(%)": "건강검진 수검률(%)"
    }
)

line_x = [x.min(), x.max()]
line_y = [
    slope * value + intercept
    for value in line_x
]

fig_scatter.add_trace(
    go.Scatter(
        x=line_x,
        y=line_y,
        mode="lines",
        name="회귀선"
    )
)

fig_scatter.update_traces(
    textposition="top center",
    selector=dict(mode="markers+text")
)

st.plotly_chart(fig_scatter, use_container_width=True)

# -----------------------------
# 회귀분석 통계값
# -----------------------------
st.subheader("3. 선형회귀분석 결과")

col1, col2, col3, col4 = st.columns(4)

col1.metric("상관계수 (r)", f"{r_value:.3f}")
col2.metric("결정계수 (R²)", f"{r_squared:.3f}")
col3.metric("회귀계수", f"{slope:.4f}")
col4.metric("p-value", f"{p_value:.4f}")

st.markdown("**회귀식**")

st.latex(
    rf"\hat{{Y}} = {slope:.4f}X + {intercept:.4f}"
)

if p_value < 0.05:
    st.success(
        "p-value가 0.05보다 작으므로 통계적으로 유의한 선형 관계가 관찰됩니다."
    )
else:
    st.warning(
        "p-value가 0.05 이상이므로 통계적으로 유의한 선형 관계라고 보기 어렵습니다."
    )

if r_value > 0:
    st.write("양의 상관관계: 의료 인프라 지표가 높은 지역일수록 수검률도 높은 경향이 있습니다.")
elif r_value < 0:
    st.write("음의 상관관계: 의료 인프라 지표가 높은 지역일수록 수검률이 낮은 경향이 있습니다.")
else:
    st.write("선형 상관관계가 거의 없습니다.")

# -----------------------------
# 상관관계 분석
# -----------------------------
st.subheader("4. 변수 간 상관관계")

corr_columns = [
    "인구수",
    "의료기관 수",
    "인구 1만 명당 의료기관 수",
    "수검률(%)"
]

corr = df[corr_columns].corr()

fig_corr = px.imshow(
    corr,
    text_auto=".2f",
    color_continuous_scale="RdBu_r",
    zmin=-1,
    zmax=1,
    title="변수 간 상관관계 히트맵"
)

st.plotly_chart(fig_corr, use_container_width=True)

# -----------------------------
# 데이터 다운로드
# -----------------------------
st.subheader("5. 분석 데이터 다운로드")

csv = df.to_csv(
    index=False,
    encoding="utf-8-sig"
)

st.download_button(
    label="📥 분석 결과 CSV 다운로드",
    data=csv,
    file_name="지역별_의료인프라_건강검진_분석.csv",
    mime="text/csv"
)

# -----------------------------
# 분석 시 유의사항
# -----------------------------
st.divider()

st.subheader("⚠️ 분석 시 유의사항")

st.markdown("""
- 건강검진 수검률은 수검인원을 대상인원으로 나눈 값입니다.
- 의료기관 수는 종합병원, 요양병원, 일반병원, 의원의 합계입니다.
- 지역별 인구 규모 차이를 고려하기 위해 인구 1만 명당 의료기관 수도 분석합니다.
- 건강검진 자료에 연도가 표시되어 있지 않으므로 의료기관 및 인구 자료와 기준 시점이 다를 수 있습니다.
- 이 분석은 지역 단위의 상관관계를 확인하는 것이며, 의료기관 수가 수검률을 직접 높인다는 인과관계를 증명하지는 않습니다.
- 건강검진 자료에 서울과 경기도가 없어 해당 지역은 분석에서 제외될 수 있습니다.
""")
