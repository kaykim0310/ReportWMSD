import streamlit as st
import pandas as pd
from utils import get_사업장명_목록, get_팀_목록, get_작업명_목록, get_단위작업명_목록

def render_hazard_investigation_tab():
    """유해요인조사표 탭 렌더링"""
    st.title("유해요인조사표")
    
    # 계층적 선택 구조
    col1, col2, col3 = st.columns(3)
    
    with col1:
        회사명_목록 = get_사업장명_목록()
        if not 회사명_목록:
            st.warning("먼저 체크리스트에 데이터를 입력하세요.")
            selected_회사명 = None
        else:
            selected_회사명 = st.selectbox(
                "회사명 선택",
                ["선택하세요"] + 회사명_목록,
                key="유해요인_회사명"
            )
            if selected_회사명 == "선택하세요":
                selected_회사명 = None
    
    with col2:
        if selected_회사명:
            소속_목록 = get_팀_목록(selected_회사명)
            selected_소속 = st.selectbox(
                "소속 선택",
                ["전체"] + 소속_목록,
                key="유해요인_소속"
            )
            if selected_소속 == "전체":
                selected_소속 = None
        else:
            st.selectbox("소속 선택", ["회사명을 먼저 선택하세요"], disabled=True, key="유해요인_소속_disabled")
            selected_소속 = None
    
    with col3:
        if selected_회사명:
            작업명_목록 = get_작업명_목록(selected_회사명, selected_소속, None)
            if 작업명_목록:
                selected_작업명_유해 = st.selectbox(
                    "작업명 선택",
                    작업명_목록,
                    key="유해요인_작업명"
                )
            else:
                st.warning("해당 조건에 맞는 작업이 없습니다.")
                selected_작업명_유해 = None
        else:
            st.selectbox("작업명 선택", ["회사명을 먼저 선택하세요"], disabled=True, key="유해요인_작업명_disabled")
            selected_작업명_유해 = None
    
    if selected_작업명_유해:
        st.info(f"📋 선택된 작업: {selected_회사명} > {selected_소속 or '전체'} > {selected_작업명_유해}")
        
        # 해당 작업의 단위작업명 가져오기
        단위작업명_목록 = get_단위작업명_목록(selected_작업명_유해, selected_회사명, selected_소속, None)
        
        with st.expander(f"📌 {selected_작업명_유해} - 유해요인조사표", expanded=True):
            st.markdown("#### 가. 조사개요")
            col1, col2 = st.columns(2)
            with col1:
                조사일시 = st.text_input("조사일시", key=f"조사일시_{selected_작업명_유해}")
                부서명 = st.text_input("부서명", key=f"부서명_{selected_작업명_유해}")
            with col2:
                조사자 = st.text_input("조사자", key=f"조사자_{selected_작업명_유해}")
                작업공정명 = st.text_input("작업공정명", value=selected_작업명_유해, key=f"작업공정명_{selected_작업명_유해}")
            작업명_유해 = st.text_input("작업명", value=selected_작업명_유해, key=f"작업명_{selected_작업명_유해}")
            
            # 단위작업명 표시
            if 단위작업명_목록:
                st.markdown("##### 단위작업명 목록")
                st.write(", ".join(단위작업명_목록))

            st.markdown("#### 나. 작업장 상황조사")

            def 상황조사행(항목명, 작업명):
                cols = st.columns([2, 5, 3])
                with cols[0]:
                    st.markdown(f"<div style='text-align:center; font-weight:bold; padding-top:0.7em;'>{항목명}</div>", unsafe_allow_html=True)
                with cols[1]:
                    상태 = st.radio(
                        label="",
                        options=["변화없음", "감소", "증가", "기타"],
                        key=f"{항목명}_상태_{작업명}",
                        horizontal=True,
                        label_visibility="collapsed"
                    )
                with cols[2]:
                    if 상태 == "감소":
                        st.text_input("감소 - 언제부터", key=f"{항목명}_감소_시작_{작업명}", placeholder="언제부터", label_visibility="collapsed")
                    elif 상태 == "증가":
                        st.text_input("증가 - 언제부터", key=f"{항목명}_증가_시작_{작업명}", placeholder="언제부터", label_visibility="collapsed")
                    elif 상태 == "기타":
                        st.text_input("기타 - 내용", key=f"{항목명}_기타_내용_{작업명}", placeholder="내용", label_visibility="collapsed")
                    else:
                        st.markdown("&nbsp;", unsafe_allow_html=True)

            for 항목 in ["작업설비", "작업량", "작업속도", "업무변화"]:
                상황조사행(항목, selected_작업명_유해)
                st.markdown("<hr style='margin:0.5em 0;'>", unsafe_allow_html=True)
            
            st.markdown("---")