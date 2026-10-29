import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import platform

# --------------------------------------------------------
# 0. 한글 폰트 설정 (그래프에서 한글 깨짐 방지)
# --------------------------------------------------------
if platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin':  # Mac
    plt.rc('font', family='AppleGothic')
plt.rcParams['axes.unicode_minus'] = False

# --------------------------------------------------------
# 1. 웹앱 제목 및 설명
# --------------------------------------------------------
st.title("🏫 캠퍼스 생활 설문조사 웹앱")
st.write("학생들의 생활 습관이 학교 생활 만족도에 미치는 영향을 분석합니다.")

# --------------------------------------------------------
# 2. CSV 파일 업로드
# --------------------------------------------------------
uploaded_file = st.file_uploader("분석할 CSV 파일을 업로드해주세요", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # --------------------------------------------------------
    # 3. 데이터 미리보기
    # --------------------------------------------------------
    st.subheader("👀 1. 데이터 미리보기")
    st.dataframe(df.head())

    # --------------------------------------------------------
    # 4. 데이터 전처리
    # --------------------------------------------------------
    st.subheader("🧹 2. 데이터 전처리 결과")

    total_rows = len(df)

    # '만족도' 열의 '모름' 등을 처리하기 위해 숫자로 강제 변환
    df['만족도'] = pd.to_numeric(df['만족도'], errors='coerce')

    # 빈 값이 있는 행 제거
    df_clean = df.dropna(subset=['학과', '공부시간', '수면시간', '스마트폰', '만족도'])

    # 24시간 초과 이상치 제거
    df_clean = df_clean[(df_clean['공부시간'] <= 24) &
                        (df_clean['수면시간'] <= 24) &
                        (df_clean['스마트폰'] <= 24)]

    valid_rows = len(df_clean)
    excluded_rows = total_rows - valid_rows

    st.write(f"총 **{total_rows}**개의 데이터 중, 잘못되거나 비어있는 데이터 **{excluded_rows}**건을 제외했습니다.")
    st.success(f"현재 **{valid_rows}**건의 유효한 데이터로 분석을 진행합니다.")

    # --------------------------------------------------------
    # 5. 학과 선택 (여기서 선택한 학과가 전체 결과에 연동됨)
    # --------------------------------------------------------
    st.subheader("🎯 3. 학과별 데이터 분석")

    departments = df_clean['학과'].unique()
    selected_dept = st.selectbox("결과를 확인할 학과를 선택하세요:", departments)

    # [중요] 선택한 학과 데이터만 필터링합니다.
    # 이후의 텍스트 분석(한줄 의견)도 모두 이 'dept_data'를 사용하므로 자동 연동됩니다.
    dept_data = df_clean[df_clean['학과'] == selected_dept]

    avg_satisfaction = dept_data['만족도'].mean()
    st.info(f"선택하신 **{selected_dept}** 학생들의 평균 만족도는 **{avg_satisfaction:.1f}점** 입니다.")

    # --------------------------------------------------------
    # 6. 그래프 시각화
    # --------------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**[{selected_dept}] 만족도 분포**")
        satisfaction_counts = dept_data['만족도'].value_counts().sort_index()
        fig_pie, ax_pie = plt.subplots()
        ax_pie.pie(satisfaction_counts, labels=satisfaction_counts.index, autopct='%1.1f%%', startangle=90)
        st.pyplot(fig_pie)

    with col2:
        st.markdown(f"**[{selected_dept}] 습관 - 만족도 상관관계**")
        corr_matrix = dept_data[['공부시간', '수면시간', '스마트폰', '만족도']].corr()
        fig_corr, ax_corr = plt.subplots()
        sns.heatmap(corr_matrix, annot=True, cmap='Blues', fmt='.2f', ax=ax_corr)
        st.pyplot(fig_corr)

    st.markdown("---")
    st.markdown(f"**[{selected_dept}] 만족도 점수에 따른 생활습관 변화**")
    habit_trend = dept_data.groupby('만족도')[['공부시간', '수면시간', '스마트폰']].mean()
    st.line_chart(habit_trend)

    # --------------------------------------------------------
    # 7. 텍스트 분석 (한 줄 의견 키워드 & 긍정/부정 분석)
    # --------------------------------------------------------
    st.subheader("💬 4. 한 줄 의견 키워드 및 감성 분석")

    if '한줄의견' in dept_data.columns:
        # 1. 단어 추출 및 빈도수 계산
        all_text = " ".join(dept_data['한줄의견'].dropna().astype(str).tolist())
        words = all_text.split()
        words = [w for w in words if len(w) > 1]  # 길이가 1인 단어 제외

        word_counts = Counter(words)

        # 2. 상위 10개 단어 막대그래프 (5개 -> 10개로 변경)
        top_10_words = word_counts.most_common(10)

        if top_10_words:
            top_words_df = pd.DataFrame(top_10_words, columns=['단어', '등장횟수']).set_index('단어')
            st.markdown(f"**[{selected_dept}] 자주 등장하는 단어 Top 10**")
            st.bar_chart(top_words_df)

            # 3. 긍정/부정 단어 분석 (간단한 사전 방식)
            st.markdown(f"**[{selected_dept}] 긍정/부정 반응 분석**")

            # 우리가 미리 정해둔 긍정/부정 키워드 리스트
            positive_keywords = ['좋아요', '좋아요.', '맛있어요', '맛있어요.', '재미있어요', '재미있어요.', '최고에요', '도움이', '예뻐서']
            negative_keywords = ['부족해요', '부족해요.', '피곤해요', '피곤해요.', '불편해요', '불편해요.', '힘듭니다', '많아요', '많아요.']

            # 리스트에 있는 단어들이 문서에서 몇 번 나왔는지 모두 더합니다.
            pos_count = sum(word_counts[word] for word in positive_keywords if word in word_counts)
            neg_count = sum(word_counts[word] for word in negative_keywords if word in word_counts)

            # 결과를 화면에 나란히 표시합니다.
            col3, col4 = st.columns(2)
            with col3:
                st.success(f"😊 긍정적인 단어 등장 횟수: **{pos_count}번**")
                st.caption(f"기준 단어: {', '.join(positive_keywords[:4])} 등")
            with col4:
                st.error(f"😢 부정적인 단어 등장 횟수: **{neg_count}번**")
                st.caption(f"기준 단어: {', '.join(negative_keywords[:4])} 등")

        else:
            st.write("분석할 의견이 부족합니다.")