
import streamlit as st
import pandas as pd
import plotly.express as px

# ==================================================
# 페이지 설정
# ==================================================
st.set_page_config(
    page_title="데이터 전처리 및 분석",
    page_icon="📊",
    layout="wide"
)

st.title("📊 데이터 전처리 및 분석")
st.caption("이상값 전처리, 지역별 남녀 통합 및 다양한 그래프 분석")

# ==================================================
# 페이지 선택
# ==================================================
page = st.sidebar.radio(
    "📑 페이지 이동",
    [
        "🔎 이상값 전처리",
        "📊 그래프 및 표 분석",
        "🏙️ 지역별 남녀 통합 분석"
    ]
)

# ==================================================
# 데이터 업로드
# ==================================================
st.sidebar.divider()
st.sidebar.header("📁 데이터 업로드")

uploaded_file = st.sidebar.file_uploader(
    "CSV 파일 업로드",
    type=["csv"]
)

if uploaded_file is not None:

    try:
        df = pd.read_csv(
            uploaded_file,
            encoding="utf-8"
        )

    except UnicodeDecodeError:
        uploaded_file.seek(0)

        df = pd.read_csv(
            uploaded_file,
            encoding="cp949"
        )

    # 새로운 파일 업로드 시 데이터 초기화
    if st.session_state.get("uploaded_name") != uploaded_file.name:

        st.session_state["uploaded_name"] = uploaded_file.name
        st.session_state["original_df"] = df.copy()
        st.session_state["cleaned_df"] = df.copy()
        st.session_state["cleaned_col"] = None

        # 이전 지역 통합 결과 초기화
        st.session_state.pop("region_df", None)

else:
    df = None

# ==================================================
# 데이터 업로드 확인
# ==================================================
if "original_df" not in st.session_state:

    st.info("👈 왼쪽 메뉴에서 CSV 파일을 먼저 업로드해주세요.")

else:

    original_df = st.session_state["original_df"]
    cleaned_df = st.session_state["cleaned_df"]

    # ==================================================
    # 1페이지: 이상값 전처리
    # ==================================================
    if page == "🔎 이상값 전처리":

        st.header("🔎 이상값 전처리")
        st.write("IQR 방식을 이용하여 이상값을 탐지하고 제거합니다.")

        st.divider()

        st.subheader("📄 원본 데이터")

        st.dataframe(
            original_df,
            use_container_width=True
        )

        st.write(f"원본 데이터 행 수: **{len(original_df)}개**")

        # 숫자형 열 선택
        numeric_cols = original_df.select_dtypes(
            include="number"
        ).columns.tolist()

        if not numeric_cols:

            st.warning("이상값을 탐지할 숫자형 데이터가 없습니다.")

        else:

            st.divider()
            st.subheader("⚙️ 이상값 탐지")

            selected_col = st.selectbox(
                "이상값을 탐지할 열 선택",
                numeric_cols
            )

            # IQR 계산
            Q1 = original_df[selected_col].quantile(0.25)
            Q3 = original_df[selected_col].quantile(0.75)
            IQR = Q3 - Q1

            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR

            # 이상값 탐지
            outliers = original_df[
                (original_df[selected_col] < lower) |
                (original_df[selected_col] > upper)
            ]

            st.subheader("📊 이상값 기준")

            col1, col2, col3 = st.columns(3)

            col1.metric("Q1", round(Q1, 2))
            col2.metric("Q3", round(Q3, 2))
            col3.metric("IQR", round(IQR, 2))

            col4, col5 = st.columns(2)

            col4.metric("하한값", round(lower, 2))
            col5.metric("상한값", round(upper, 2))

            st.write(
                f"이상값 기준: **{lower:.2f} 미만 또는 "
                f"{upper:.2f} 초과**"
            )

            st.write(f"발견된 이상값: **{len(outliers)}개**")

            st.subheader("🚨 발견된 이상값")

            if len(outliers) > 0:

                st.dataframe(
                    outliers,
                    use_container_width=True
                )

            else:

                st.success("이 기준에 해당하는 이상값이 없습니다.")

            # 상자 그림
            st.subheader("📈 이상값 시각화")

            fig = px.box(
                original_df,
                y=selected_col,
                points="all",
                title=f"{selected_col}의 상자 그림"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            # 이상값 제거
            st.divider()
            st.subheader("🧹 이상값 제거")

            st.caption(
                "선택한 열의 IQR 기준을 벗어난 행을 제거합니다. "
                "결측값과 중복값은 별도로 처리하지 않습니다."
            )

            if st.button("이상값 제거하기", type="primary"):

                cleaned_df = original_df[
                    (original_df[selected_col] >= lower) &
                    (original_df[selected_col] <= upper)
                ].copy()

                st.session_state["cleaned_df"] = cleaned_df
                st.session_state["cleaned_col"] = selected_col

                st.success("이상값 전처리가 완료되었습니다!")

            # 전처리 결과
            cleaned_df = st.session_state["cleaned_df"]

            st.subheader("✅ 전처리 결과")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "원본 데이터",
                f"{len(original_df)}행"
            )

            col2.metric(
                "전처리 후",
                f"{len(cleaned_df)}행"
            )

            col3.metric(
                "제거된 행",
                f"{len(original_df) - len(cleaned_df)}행"
            )

            st.dataframe(
                cleaned_df,
                use_container_width=True
            )

            # 다운로드
            csv = cleaned_df.to_csv(
                index=False,
                encoding="utf-8-sig"
            )

            st.download_button(
                label="📥 전처리 데이터 다운로드",
                data=csv,
                file_name="outlier_cleaned.csv",
                mime="text/csv"
            )

    # ==================================================
    # 2페이지: 그래프 및 표 분석
    # ==================================================
    elif page == "📊 그래프 및 표 분석":

        st.header("📊 그래프 및 표 분석")
        st.write("원본 데이터와 전처리 데이터를 다양한 방법으로 분석합니다.")

        st.divider()

        original_df = st.session_state["original_df"]
        cleaned_df = st.session_state["cleaned_df"]

        numeric_cols = original_df.select_dtypes(
            include="number"
        ).columns.tolist()

        if not numeric_cols:

            st.warning("숫자형 데이터가 없습니다.")

        else:

            selected_col = st.selectbox(
                "분석할 숫자형 열 선택",
                numeric_cols,
                key="analysis_col"
            )

            # ------------------------------------------
            # 기초 통계표
            # ------------------------------------------
            st.subheader("1️⃣ 기초 통계표")

            st.write("원본 데이터")

            st.dataframe(
                original_df[numeric_cols].describe().T,
                use_container_width=True
            )

            st.write("전처리 데이터")

            st.dataframe(
                cleaned_df[numeric_cols].describe().T,
                use_container_width=True
            )

            # ------------------------------------------
            # 전처리 전후 비교표
            # ------------------------------------------
            st.divider()
            st.subheader("2️⃣ 전처리 전후 비교표")

            comparison = pd.DataFrame({
                "원본 평균": original_df[numeric_cols].mean(),
                "전처리 평균": cleaned_df[numeric_cols].mean(),
                "원본 중앙값": original_df[numeric_cols].median(),
                "전처리 중앙값": cleaned_df[numeric_cols].median()
            })

            st.dataframe(
                comparison.round(2),
                use_container_width=True
            )

            # ------------------------------------------
            # 히스토그램
            # ------------------------------------------
            st.divider()
            st.subheader("3️⃣ 히스토그램")

            fig1 = px.histogram(
                original_df,
                x=selected_col,
                nbins=20,
                title=f"{selected_col} 원본 데이터 분포"
            )

            st.plotly_chart(
                fig1,
                use_container_width=True
            )

            fig2 = px.histogram(
                cleaned_df,
                x=selected_col,
                nbins=20,
                title=f"{selected_col} 전처리 데이터 분포"
            )

            st.plotly_chart(
                fig2,
                use_container_width=True
            )

            # ------------------------------------------
            # 상자 그림
            # ------------------------------------------
            st.divider()
            st.subheader("4️⃣ 상자 그림")

            fig3 = px.box(
                original_df,
                y=selected_col,
                points="all",
                title=f"{selected_col} 원본 상자 그림"
            )

            st.plotly_chart(
                fig3,
                use_container_width=True
            )

            fig4 = px.box(
                cleaned_df,
                y=selected_col,
                points="all",
                title=f"{selected_col} 전처리 상자 그림"
            )

            st.plotly_chart(
                fig4,
                use_container_width=True
            )

            # ------------------------------------------
            # 범주별 막대그래프
            # ------------------------------------------
            st.divider()
            st.subheader("5️⃣ 범주별 막대그래프")

            category_cols = [
                c for c in original_df.columns
                if c not in numeric_cols
            ]

            if category_cols:

                category_col = st.selectbox(
                    "범주형 열 선택",
                    category_cols,
                    key="bar_col"
                )

                fig5 = px.bar(
                    original_df,
                    x=category_col,
                    y=selected_col,
                    title=f"{category_col}별 {selected_col}"
                )

                st.plotly_chart(
                    fig5,
                    use_container_width=True
                )

            else:

                st.info("범주형 데이터가 없습니다.")

            # ------------------------------------------
            # 산점도
            # ------------------------------------------
            st.divider()
            st.subheader("6️⃣ 산점도")

            if len(numeric_cols) >= 2:

                x_col = st.selectbox(
                    "X축 변수",
                    numeric_cols,
                    key="scatter_x"
                )

                y_col = st.selectbox(
                    "Y축 변수",
                    numeric_cols,
                    index=1,
                    key="scatter_y"
                )

                fig6 = px.scatter(
                    original_df,
                    x=x_col,
                    y=y_col,
                    title=f"{x_col}과 {y_col}의 관계"
                )

                st.plotly_chart(
                    fig6,
                    use_container_width=True
                )

            else:

                st.info("산점도에는 숫자형 열이 2개 이상 필요합니다.")

            # ------------------------------------------
            # 데이터 확인
            # ------------------------------------------
            st.divider()
            st.subheader("7️⃣ 데이터 미리보기")

            tab1, tab2 = st.tabs(
                ["원본 데이터", "전처리 데이터"]
            )

            with tab1:

                st.dataframe(
                    original_df,
                    use_container_width=True
                )

            with tab2:

                st.dataframe(
                    cleaned_df,
                    use_container_width=True
                )

    # ==================================================
    # 3페이지: 지역별 남녀 통합 분석
    # ==================================================
    elif page == "🏙️ 지역별 남녀 통합 분석":

        st.header("🏙️ 지역별 남녀 통합 분석")

        st.write(
            "같은 지역에 속한 남성과 여성의 데이터를 합산하여 "
            "성별 구분 없이 지역별 전체 데이터를 분석합니다."
        )

        st.divider()

        original_df = st.session_state["original_df"]

        st.subheader("📄 원본 데이터")

        st.dataframe(
            original_df,
            use_container_width=True
        )

        # ------------------------------------------
        # 지역 및 성별 열 선택
        # ------------------------------------------
        st.divider()
        st.subheader("⚙️ 데이터 통합 설정")

        all_cols = original_df.columns.tolist()

        if len(all_cols) < 2:

            st.warning("지역 열과 성별 열을 선택하려면 열이 2개 이상 필요합니다.")

        else:

            col1, col2 = st.columns(2)

            with col1:

                region_col = st.selectbox(
                    "지역 열 선택",
                    all_cols,
                    key="region_select"
                )

            gender_options = [
                col for col in all_cols
                if col != region_col
            ]

            with col2:

                gender_col = st.selectbox(
                    "성별 열 선택",
                    gender_options,
                    key="gender_select"
                )

            # ------------------------------------------
            # 합산할 숫자형 열 선택
            # ------------------------------------------
            numeric_cols = original_df.select_dtypes(
                include="number"
            ).columns.tolist()

            value_cols = [
                col for col in numeric_cols
                if col not in [region_col, gender_col]
            ]

            if not value_cols:

                st.warning(
                    "지역별로 합산할 숫자형 열이 없습니다. "
                    "CSV 파일의 데이터 형식을 확인해주세요."
                )

            else:

                st.write("지역별로 합산할 숫자형 항목을 선택하세요.")

                selected_values = st.multiselect(
                    "합산 항목 선택",
                    value_cols,
                    default=value_cols,
                    key="region_values"
                )

                st.caption(
                    "예: 서울 남성 인구수 + 서울 여성 인구수 "
                    "= 서울 전체 인구수"
                )

                # ------------------------------------------
                # 지역별 남녀 통합 실행
                # ------------------------------------------
                if st.button(
                    "🏙️ 지역별 남녀 합산하기",
                    type="primary"
                ):

                    if not selected_values:

                        st.warning("합산할 항목을 하나 이상 선택해주세요.")

                    else:

                        region_df = (
                            original_df
                            .groupby(
                                region_col,
                                as_index=False,
                                dropna=False
                            )[selected_values]
                            .sum()
                        )

                        st.session_state["region_df"] = region_df

                        st.success(
                            "지역별 남녀 데이터 통합이 완료되었습니다!"
                        )

                # ------------------------------------------
                # 통합 결과 출력
                # ------------------------------------------
                if "region_df" in st.session_state:

                    region_df = st.session_state["region_df"]

                    st.divider()
                    st.subheader("✅ 지역별 통합 결과")

                    col1, col2 = st.columns(2)

                    col1.metric(
                        "통합 전 데이터",
                        f"{len(original_df)}행"
                    )

                    col2.metric(
                        "통합 후 지역 수",
                        f"{len(region_df)}개"
                    )

                    st.dataframe(
                        region_df,
                        use_container_width=True
                    )

                    # ------------------------------------------
                    # 지역별 막대그래프
                    # ------------------------------------------
                    st.divider()
                    st.subheader("📊 지역별 통합 데이터 그래프")

                    graph_cols = [
                        col for col in selected_values
                        if col in region_df.columns
                    ]

                    if graph_cols:

                        graph_col = st.selectbox(
                            "그래프로 확인할 항목 선택",
                            graph_cols,
                            key="region_graph_col"
                        )

                        fig_region = px.bar(
                            region_df,
                            x=region_col,
                            y=graph_col,
                            title=f"지역별 {graph_col} 비교",
                            text=graph_col
                        )

                        st.plotly_chart(
                            fig_region,
                            use_container_width=True
                        )

                    # ------------------------------------------
                    # 통합 데이터 다운로드
                    # ------------------------------------------
                    st.divider()
                    st.subheader("📥 지역별 통합 데이터 다운로드")

                    csv = region_df.to_csv(
                        index=False,
                        encoding="utf-8-sig"
                    )

                    st.download_button(
                        label="📥 지역별 통합 데이터 CSV 다운로드",
                        data=csv,
                        file_name="region_gender_combined.csv",
                        mime="text/csv"
                    )

# ==================================================
# 사이드바 안내
# ==================================================
st.sidebar.divider()

st.sidebar.caption(
    "1️⃣ 이상값 전처리\n\n"
    "2️⃣ 그래프 및 표 분석\n\n"
    "3️⃣ 지역별 남녀 통합 분석"
)
