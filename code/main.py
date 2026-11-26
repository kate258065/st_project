
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="이상값 전처리",
    page_icon="🔎",
    layout="wide"
)

st.title("🔎 데이터 이상값 전처리")
st.caption("IQR 방식으로 이상값을 탐지하고 제거합니다.")

st.divider()

# 1. 데이터 업로드
uploaded_file = st.file_uploader(
    "CSV 파일을 업로드하세요",
    type=["csv"]
)

if uploaded_file is not None:

    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8")
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding="cp949")

    st.subheader("📄 원본 데이터")
    st.dataframe(df, use_container_width=True)

    st.write(f"원본 데이터 행 수: **{len(df)}개**")

    # 2. 숫자형 열 선택
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    if not numeric_cols:
        st.warning("이상값을 탐지할 숫자형 데이터가 없습니다.")

    else:
        st.divider()
        st.subheader("⚙️ 이상값 탐지 기준")

        selected_col = st.selectbox(
            "이상값을 탐지할 열 선택",
            numeric_cols
        )

        # 3. IQR 계산
        Q1 = df[selected_col].quantile(0.25)
        Q3 = df[selected_col].quantile(0.75)
        IQR = Q3 - Q1

        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR

        # 4. 이상값 판별
        outliers = df[
            (df[selected_col] < lower) |
            (df[selected_col] > upper)
        ]

        st.write("### 📊 이상값 탐지 결과")

        col1, col2, col3 = st.columns(3)

        col1.metric("Q1", round(Q1, 2))
        col2.metric("Q3", round(Q3, 2))
        col3.metric("IQR", round(IQR, 2))

        col4, col5 = st.columns(2)

        col4.metric("하한값", round(lower, 2))
        col5.metric("상한값", round(upper, 2))

        st.write(
            f"**이상값 기준:** {lower:.2f} 미만 또는 "
            f"{upper:.2f} 초과"
        )

        st.write(f"**발견된 이상값 수: {len(outliers)}개**")

        # 5. 이상값 표시
        st.subheader("🚨 발견된 이상값")

        if len(outliers) > 0:
            st.dataframe(outliers, use_container_width=True)
        else:
            st.success("이 기준에 해당하는 이상값이 없습니다.")

        # 6. 상자 그림
        st.subheader("📈 이상값 시각화")

        fig = px.box(
            df,
            y=selected_col,
            points="all",
            title=f"{selected_col}의 이상값 확인"
        )

        st.plotly_chart(fig, use_container_width=True)

        # 7. 이상값 제거
        st.divider()
        st.subheader("🧹 이상값 제거")

        st.caption(
            "선택한 열에서 IQR 기준을 벗어난 행만 제거합니다. "
            "다른 열의 값이나 결측값, 중복값은 별도로 처리하지 않습니다."
        )

        if st.button("이상값 제거하기", type="primary"):

            cleaned_df = df[
                (df[selected_col] >= lower) &
                (df[selected_col] <= upper)
            ].copy()

            st.session_state["cleaned_df"] = cleaned_df
            st.session_state["selected_col"] = selected_col
            st.session_state["original_df"] = df.copy()

        # 8. 결과 표시
        if "cleaned_df" in st.session_state:

            cleaned_df = st.session_state["cleaned_df"]

            st.subheader("✅ 전처리 결과")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "원본 데이터",
                f"{len(df)}행"
            )

            col2.metric(
                "전처리 후",
                f"{len(cleaned_df)}행"
            )

            col3.metric(
                "제거된 행",
                f"{len(df) - len(cleaned_df)}행"
            )

            st.dataframe(
                cleaned_df,
                use_container_width=True
            )

            # 9. 다운로드
            csv = cleaned_df.to_csv(
                index=False,
                encoding="utf-8-sig"
            )

            st.download_button(
                label="📥 전처리된 데이터 다운로드",
                data=csv,
                file_name="outlier_cleaned.csv",
                mime="text/csv"
            )

else:
    st.info("👆 먼저 분석할 CSV 파일을 업로드하세요.")
import pandas as pd
from pathlib import Path

# 원본 CSV 파일
input_file = Path(
    "보건복지부_병원 및 의원 수_의료기관 종류별_시도별_20241231 (1).csv"
)

# 수정된 CSV 파일
output_file = Path(
    "병의원_종합병원_요양병원_일반병원_의원만.csv"
)

# CSV 파일 읽기
df = pd.read_csv(input_file, encoding="cp949")

# 남길 열
keep_columns = [
    "연도",
    "시도",
    "병의원_종합병원",
    "병의원_요양병원",
    "병의원_일반병원",
    "병의원_의원"
]

# 필요한 열만 선택
df = df[keep_columns]

# CSV 파일 저장
df.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)

# 결과 확인
print("열 삭제 완료!")
print(f"행 개수: {len(df)}")
print(f"열 개수: {len(df.columns)}")
print(f"남은 열: {list(df.columns)}")
print(f"저장 파일: {output_file.resolve()}")

