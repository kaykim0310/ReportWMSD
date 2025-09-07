import streamlit as st  # <-- 이 라인이 누락되어 오류가 발생했습니다.
from datetime import datetime
import time
import pandas as pd
import os

# 페이지 설정 (반드시 코드의 맨 처음에 위치해야 합니다)
st.set_page_config(layout="wide", page_title="근골격계 유해요인조사")

# 모듈 임포트
from utils import auto_save, get_saved_sessions, SAVE_DIR
from data_manager import save_to_excel, load_from_excel
from tab1_overview import render_overview_tab
from tab2_checklist import render_checklist_tab
from tab3_hazard_investigation import render_hazard_investigation_tab
from tab4_work_conditions import render_work_conditions_tab
from tab5_detailed_investigation import render_detailed_investigation_tab
from tab6_symptom_analysis import render_symptom_analysis_tab
from tab7_improvement_plan import render_improvement_plan_tab

# 세션 상태 초기화
if "checklist_df" not in st.session_state:
    st.session_state["checklist_df"] = pd.DataFrame()

if "workplace" not in st.session_state:
    st.session_state["workplace"] = None

if "session_id" not in st.session_state:
    st.session_state["session_id"] = None

# 사이드바 - 데이터 관리
with st.sidebar:
    st.title("📊 데이터 관리")
    
    # 작업현장 선택/입력
    st.markdown("### 🏭 작업현장 선택")
    # 예시 현장 목록 (필요시 수정 또는 데이터베이스 연동)
    작업현장_옵션 = ["현장 선택...", "A사업장", "B사업장", "C사업장", "신규 현장 추가"]
    선택된_현장 = st.selectbox("작업현장", 작업현장_옵션)
    
    if 선택된_현장 == "신규 현장 추가":
        새현장명 = st.text_input("새 현장명 입력")
        if 새현장명:
            st.session_state["workplace"] = 새현장명
            st.session_state["session_id"] = f"{새현장명}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.rerun() # 새 현장명 적용을 위해 새로고침
    elif 선택된_현장 != "현장 선택...":
        st.session_state["workplace"] = 선택된_현장
        if not st.session_state.get("session_id") or 선택된_현장 not in st.session_state.get("session_id", ""):
            st.session_state["session_id"] = f"{선택된_현장}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 세션 정보 표시
    if st.session_state.get("session_id"):
        st.info(f"📄 세션 ID: {st.session_state['session_id']}")
    
    # 자동 저장 상태
    if "last_successful_save" in st.session_state:
        last_save = st.session_state["last_successful_save"]
        save_count = st.session_state.get("save_count", 0)
        st.success(f"✅ 마지막 자동저장: {last_save.strftime('%H:%M:%S')} (총 {save_count}회)")
    
    st.markdown("---")
    st.markdown("### 📥 데이터 내보내기")

    # 수동 저장 버튼
    if st.button("💾 현재 상태 저장", use_container_width=True):
        if st.session_state.get("session_id") and st.session_state.get("workplace"):
            success, result = save_to_excel(st.session_state["session_id"], st.session_state.get("workplace"))
            if success:
                st.success(f"✅ 현재 상태가 서버에 저장되었습니다!")
                st.session_state["last_successful_save"] = datetime.now()
            else:
                st.error(f"저장 중 오류 발생: {result}")
        else:
            st.warning("먼저 작업현장을 선택해주세요!")

    # 다운로드 버튼
    if st.session_state.get("session_id") and st.session_state.get("workplace"):
        success, filepath = save_to_excel(st.session_state["session_id"], st.session_state.get("workplace"))
        if success:
            with open(filepath, "rb") as fp:
                st.download_button(
                    label="📋 전체 결과 다운로드",
                    data=fp,
                    file_name=f"{st.session_state.get('workplace', '결과')}_유해요인조사.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            st.error("다운로드 파일 생성에 실패했습니다.")
    
    # 저장된 세션 목록
    st.markdown("---")
    st.markdown("### 📂 저장된 세션 불러오기")
    
    saved_sessions = get_saved_sessions()
    if saved_sessions:
        selected_session = st.selectbox(
            "불러올 세션 선택",
            options=["선택..."] + [f"{s['workplace']} - {s['saved_at']}" for s in saved_sessions],
            key="session_selector"
        )
        
        if selected_session != "선택..." and st.button("📤 세션 불러오기", use_container_width=True):
            session_idx = [f"{s['workplace']} - {s['saved_at']}" for s in saved_sessions].index(selected_session)
            session_info = saved_sessions[session_idx]
            filepath = os.path.join(SAVE_DIR, session_info["filename"])
            
            if load_from_excel(filepath):
                st.success("✅ 세션을 성공적으로 불러왔습니다!")
                st.rerun()
            else:
                st.error("세션을 불러오는 중 오류가 발생했습니다.")
    else:
        st.info("저장된 세션이 없습니다.")

# 자동 저장 실행
if st.session_state.get("session_id") and st.session_state.get("workplace"):
    auto_save()

# 작업현장 선택 확인
if not st.session_state.get("workplace"):
    st.warning("⚠️ 먼저 사이드바에서 작업현장을 선택하거나 입력해주세요!")
    st.stop()

# 메인 화면 시작
st.title(f"근골격계 유해요인조사 - {st.session_state.get('workplace', '')}")

# 탭 정의
tabs = st.tabs([
    "사업장개요",
    "근골격계 부담작업 체크리스트",
    "유해요인조사표",
    "작업조건조사",
    "정밀조사",
    "증상조사 분석",
    "작업환경개선계획서"
])

# 각 탭 렌더링
with tabs[0]:
    render_overview_tab()

with tabs[1]:
    render_checklist_tab()

with tabs[2]:
    render_hazard_investigation_tab()

with tabs[3]:
    render_work_conditions_tab()

with tabs[4]:
    render_detailed_investigation_tab()

with tabs[5]:
    render_symptom_analysis_tab()

with tabs[6]:
    render_improvement_plan_tab()

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888;'>
        <p>근골격계 유해요인조사 시스템 v2.0 | 개발: 안전보건팀</p>
    </div>
    """,
    unsafe_allow_html=True
)