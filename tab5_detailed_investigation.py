import streamlit as st
import pandas as pd

def render_detailed_investigation_tab():
    """정밀조사 탭 렌더링"""
    st.title("정밀조사")
    
    if "정밀조사_목록" not in st.session_state:
        st.session_state["정밀조사_목록"] = []
    
    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        st.subheader("정밀조사 항목 관리")
    with col2:
        if st.button("➕ 새 정밀조사 추가", use_container_width=True):
            조사명 = f"정밀조사_{len(st.session_state['정밀조사_목록'])+1}"
            st.session_state["정밀조사_목록"].append(조사명)
            st.rerun()
    
    if st.session_state["정밀조사_목록"]:
        for 조사명 in st.session_state["정밀조사_목록"]:
            with st.expander(f"📋 {조사명}", expanded=True):
                col1, col2, col3 = st.columns([0.3, 0.3, 0.4])
                with col1:
                    작업공정명 = st.text_input("작업공정명", key=f"정밀_작업공정명_{조사명}")
                with col2:
                    작업명 = st.text_input("작업명", key=f"정밀_작업명_{조사명}")
                with col3:
                    if st.button(f"🗑️ {조사명} 삭제", key=f"delete_{조사명}"):
                        st.session_state["정밀조사_목록"].remove(조사명)
                        # 관련 데이터도 삭제
                        keys_to_delete = [k for k in st.session_state.keys() if 조사명 in k]
                        for key in keys_to_delete:
                            del st.session_state[key]
                        st.rerun()
                
                # 원인분석 섹션
                원인분석_key = f"정밀_원인분석_data_{조사명}"
                if 원인분석_key not in st.session_state:
                    st.session_state[원인분석_key] = pd.DataFrame({
                        "작업내용": [""],
                        "유해요인": [""],
                        "개선방안": [""]
                    })
                
                st.markdown("#### 원인분석")
                
                원인분석_data = st.data_editor(
                    st.session_state[원인분석_key],
                    num_rows="dynamic",
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "작업내용": st.column_config.TextColumn("작업내용", width="medium"),
                        "유해요인": st.column_config.TextColumn("유해요인", width="medium"),
                        "개선방안": st.column_config.TextColumn("개선방안", width="medium"),
                    },
                    key=f"정밀_원인분석_editor_{조사명}"
                )
                
                st.session_state[원인분석_key] = 원인분석_data
    else:
        st.info("아직 정밀조사 항목이 없습니다. 위의 '새 정밀조사 추가' 버튼을 클릭하여 추가하세요.")