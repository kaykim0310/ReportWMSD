import streamlit as st

def render_overview_tab():
    """사업장개요 탭 렌더링"""
    st.title("사업장 개요")
    
    사업장명 = st.text_input("사업장명", key="사업장명", value=st.session_state.get("workplace", ""))
    소재지 = st.text_input("소재지", key="소재지")
    업종 = st.text_input("업종", key="업종")
    
    col1, col2 = st.columns(2)
    with col1:
        예비조사 = st.text_input("예비조사일 (YYYY-MM-DD)", key="예비조사", placeholder="2024-01-01")
        수행기관 = st.text_input("수행기관", key="수행기관")
    with col2:
        본조사 = st.text_input("본조사일 (YYYY-MM-DD)", key="본조사", placeholder="2024-01-01")
        성명 = st.text_input("성명", key="성명")