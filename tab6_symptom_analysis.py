import streamlit as st
import pandas as pd

def render_symptom_analysis_tab():
    """증상조사 분석 탭 렌더링"""
    st.title("증상조사 분석")
    
    # 서브탭 생성
    sub_tabs = st.tabs(["기초현황", "작업기간", "육체적부담", "통증호소자"])
    
    # 6-1. 기초현황
    with sub_tabs[0]:
        st.subheader("기초현황")
        
        if "기초현황_data" not in st.session_state:
            st.session_state["기초현황_data"] = pd.DataFrame({
                "구분": ["남", "여", "계"],
                "20대": [0, 0, 0],
                "30대": [0, 0, 0],
                "40대": [0, 0, 0],
                "50대": [0, 0, 0],
                "60대 이상": [0, 0, 0],
                "계": [0, 0, 0]
            })
        
        기초현황_data = st.data_editor(
            st.session_state["기초현황_data"],
            use_container_width=True,
            hide_index=True,
            disabled=["구분"],
            column_config={
                "구분": st.column_config.TextColumn("구분", disabled=True),
                "20대": st.column_config.NumberColumn("20대", min_value=0, max_value=1000, step=1),
                "30대": st.column_config.NumberColumn("30대", min_value=0, max_value=1000, step=1),
                "40대": st.column_config.NumberColumn("40대", min_value=0, max_value=1000, step=1),
                "50대": st.column_config.NumberColumn("50대", min_value=0, max_value=1000, step=1),
                "60대 이상": st.column_config.NumberColumn("60대 이상", min_value=0, max_value=1000, step=1),
                "계": st.column_config.NumberColumn("계", min_value=0, max_value=1000, step=1)
            },
            key="기초현황_editor"
        )
        
        # 자동 계산
        for idx in range(2):  # 남, 여
            기초현황_data.at[idx, "계"] = sum(기초현황_data.iloc[idx, 1:6])
        
        # 계 행 자동 계산
        for col in ["20대", "30대", "40대", "50대", "60대 이상", "계"]:
            기초현황_data.at[2, col] = 기초현황_data.iloc[0:2][col].sum()
        
        st.session_state["기초현황_data"] = 기초현황_data
        st.session_state["기초현황_data_저장"] = 기초현황_data.copy()
        
        # 계산된 결과 표시
        st.markdown("##### 계산 결과")
        st.dataframe(기초현황_data, use_container_width=True, hide_index=True)
    
    # 6-2. 작업기간
    with sub_tabs[1]:
        st.subheader("작업기간별 인원현황")
        
        if "작업기간_data" not in st.session_state:
            st.session_state["작업기간_data"] = pd.DataFrame({
                "구분": ["남", "여", "계"],
                "1년 미만": [0, 0, 0],
                "1~5년": [0, 0, 0],
                "5~10년": [0, 0, 0],
                "10년 이상": [0, 0, 0],
                "계": [0, 0, 0]
            })
        
        작업기간_data = st.data_editor(
            st.session_state["작업기간_data"],
            use_container_width=True,
            hide_index=True,
            disabled=["구분"],
            column_config={
                "구분": st.column_config.TextColumn("구분", disabled=True),
                "1년 미만": st.column_config.NumberColumn("1년 미만", min_value=0, max_value=1000, step=1),
                "1~5년": st.column_config.NumberColumn("1~5년", min_value=0, max_value=1000, step=1),
                "5~10년": st.column_config.NumberColumn("5~10년", min_value=0, max_value=1000, step=1),
                "10년 이상": st.column_config.NumberColumn("10년 이상", min_value=0, max_value=1000, step=1),
                "계": st.column_config.NumberColumn("계", min_value=0, max_value=1000, step=1)
            },
            key="작업기간_editor"
        )
        
        # 자동 계산
        for idx in range(2):  # 남, 여
            작업기간_data.at[idx, "계"] = sum(작업기간_data.iloc[idx, 1:5])
        
        # 계 행 자동 계산
        for col in ["1년 미만", "1~5년", "5~10년", "10년 이상", "계"]:
            작업기간_data.at[2, col] = 작업기간_data.iloc[0:2][col].sum()
        
        st.session_state["작업기간_data"] = 작업기간_data
        st.session_state["작업기간_data_저장"] = 작업기간_data.copy()
        
        # 계산된 결과 표시
        st.markdown("##### 계산 결과")
        st.dataframe(작업기간_data, use_container_width=True, hide_index=True)
    
    # 6-3. 육체적부담
    with sub_tabs[2]:
        st.subheader("육체적 부담정도")
        
        if "육체적부담_data" not in st.session_state:
            st.session_state["육체적부담_data"] = pd.DataFrame({
                "구분": ["매우 쉬움", "쉬움", "약간 힘듦", "힘듦", "매우 힘듦", "계"],
                "남": [0, 0, 0, 0, 0, 0],
                "여": [0, 0, 0, 0, 0, 0],
                "계": [0, 0, 0, 0, 0, 0]
            })
        
        육체적부담_data = st.data_editor(
            st.session_state["육체적부담_data"],
            use_container_width=True,
            hide_index=True,
            disabled=["구분"],
            column_config={
                "구분": st.column_config.TextColumn("구분", disabled=True),
                "남": st.column_config.NumberColumn("남", min_value=0, max_value=1000, step=1),
                "여": st.column_config.NumberColumn("여", min_value=0, max_value=1000, step=1),
                "계": st.column_config.NumberColumn("계", min_value=0, max_value=1000, step=1)
            },
            key="육체적부담_editor"
        )
        
        # 자동 계산
        for idx in range(5):  # 각 부담 정도
            육체적부담_data.at[idx, "계"] = 육체적부담_data.iloc[idx, 1:3].sum()
        
        # 계 행 자동 계산
        for col in ["남", "여", "계"]:
            육체적부담_data.at[5, col] = 육체적부담_data.iloc[0:5][col].sum()
        
        st.session_state["육체적부담_data"] = 육체적부담_data
        st.session_state["육체적부담_data_저장"] = 육체적부담_data.copy()
        
        # 계산된 결과 표시
        st.markdown("##### 계산 결과")
        st.dataframe(육체적부담_data, use_container_width=True, hide_index=True)
    
    # 6-4. 통증호소자
    with sub_tabs[3]:
        st.subheader("통증호소자 현황")
        
        # 부위별 컬럼 정의
        부위_columns = ["목", "어깨", "등/허리", "팔/팔꿈치", "손/손목/손가락", "다리/발", "계"]
        
        if "통증호소자_data" not in st.session_state:
            st.session_state["통증호소자_data"] = pd.DataFrame({
                "부서/공정": [""],
                **{부위: [0] for 부위 in 부위_columns}
            })
        
        통증호소자_data = st.data_editor(
            st.session_state["통증호소자_data"],
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "부서/공정": st.column_config.TextColumn("부서/공정", width="medium"),
                **{부위: st.column_config.NumberColumn(부위, min_value=0, max_value=1000, step=1) 
                   for 부위 in 부위_columns}
            },
            key="통증호소자_editor"
        )
        
        # 계 열 자동 계산
        for idx in range(len(통증호소자_data)):
            통증호소자_data.at[idx, "계"] = sum(통증호소자_data.iloc[idx, 1:7])
        
        st.session_state["통증호소자_data"] = 통증호소자_data
        st.session_state["통증호소자_data_저장"] = 통증호소자_data.copy()
        
        # 합계 행 추가
        if len(통증호소자_data) > 0:
            합계_row = {"부서/공정": "합계"}
            for 부위 in 부위_columns:
                합계_row[부위] = 통증호소자_data[부위].sum()
            
            # 합계를 포함한 전체 데이터 표시
            display_data = pd.concat([통증호소자_data, pd.DataFrame([합계_row])], ignore_index=True)
            
            st.markdown("##### 계산 결과 (합계 포함)")
            st.dataframe(display_data, use_container_width=True, hide_index=True)