import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import json
import os
import time

# PDF 관련 imports (선택사항)
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.enums import TA_CENTER
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

st.set_page_config(layout="wide", page_title="근골격계 유해요인조사")

# Excel 파일 저장 디렉토리 생성
SAVE_DIR = "saved_sessions"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# Excel 파일로 데이터 저장 함수
def save_to_excel(session_id, workplace=None):
    """세션 데이터를 Excel 파일로 저장"""
    try:
        filename = os.path.join(SAVE_DIR, f"{session_id}.xlsx")
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # 메타데이터 저장
            metadata = {
                "session_id": session_id,
                "workplace": workplace or st.session_state.get("workplace", ""),
                "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "사업장명": st.session_state.get("사업장명", ""),
                "소재지": st.session_state.get("소재지", ""),
                "업종": st.session_state.get("업종", ""),
                "예비조사": str(st.session_state.get("예비조사", "")),
                "본조사": str(st.session_state.get("본조사", "")),
                "수행기관": st.session_state.get("수행기관", ""),
                "성명": st.session_state.get("성명", "")
            }
            
            # 메타데이터를 DataFrame으로 변환
            metadata_df = pd.DataFrame([metadata])
            metadata_df.to_excel(writer, sheet_name='메타데이터', index=False)
            
            # 체크리스트 저장
            if "checklist_df" in st.session_state and not st.session_state["checklist_df"].empty:
                st.session_state["checklist_df"].to_excel(writer, sheet_name='체크리스트', index=False)
            
            # 작업명 목록 가져오기
            작업명_목록 = []
            if not st.session_state.get("checklist_df", pd.DataFrame()).empty:
                작업명_목록 = st.session_state["checklist_df"]["작업명"].dropna().unique().tolist()
            
            # 각 작업별 데이터 저장
            for 작업명 in 작업명_목록:
                # 유해요인조사표 데이터
                조사표_data = {
                    "조사일시": st.session_state.get(f"조사일시_{작업명}", ""),
                    "부서명": st.session_state.get(f"부서명_{작업명}", ""),
                    "조사자": st.session_state.get(f"조사자_{작업명}", ""),
                    "작업공정명": st.session_state.get(f"작업공정명_{작업명}", ""),
                    "작업명": st.session_state.get(f"작업명_{작업명}", "")
                }
                
                # 작업장 상황조사
                for 항목 in ["작업설비", "작업량", "작업속도", "업무변화"]:
                    조사표_data[f"{항목}_상태"] = st.session_state.get(f"{항목}_상태_{작업명}", "")
                    조사표_data[f"{항목}_세부사항"] = st.session_state.get(f"{항목}_감소_시작_{작업명}", "") or \
                                                     st.session_state.get(f"{항목}_증가_시작_{작업명}", "") or \
                                                     st.session_state.get(f"{항목}_기타_내용_{작업명}", "")
                
                조사표_df = pd.DataFrame([조사표_data])
                sheet_name = f'조사표_{작업명}'.replace('/', '_').replace('\\', '_')[:31]
                조사표_df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # 작업조건조사 데이터
                작업조건_key = f"작업조건_data_{작업명}"
                if 작업조건_key in st.session_state and isinstance(st.session_state[작업조건_key], pd.DataFrame):
                    sheet_name = f'작업조건_{작업명}'.replace('/', '_').replace('\\', '_')[:31]
                    st.session_state[작업조건_key].to_excel(writer, sheet_name=sheet_name, index=False)
                
                # 3단계 데이터
                단계3_data = {
                    "작업명": st.session_state.get(f"3단계_작업명_{작업명}", ""),
                    "근로자수": st.session_state.get(f"3단계_근로자수_{작업명}", "")
                }
                
                사진개수 = st.session_state.get(f"사진개수_{작업명}", 3)
                for i in range(사진개수):
                    단계3_data[f"사진{i+1}_설명"] = st.session_state.get(f"사진_{i+1}_설명_{작업명}", "")
                
                # 원인분석 데이터
                원인분석_key = f"원인분석_항목_{작업명}"
                if 원인분석_key in st.session_state:
                    원인분석_df = pd.DataFrame(st.session_state[원인분석_key])
                    sheet_name = f'원인분석_{작업명}'.replace('/', '_').replace('\\', '_')[:31]
                    원인분석_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # 정밀조사 데이터
            if "정밀조사_목록" in st.session_state:
                for 조사명 in st.session_state["정밀조사_목록"]:
                    정밀_data = {
                        "작업공정명": st.session_state.get(f"정밀_작업공정명_{조사명}", ""),
                        "작업명": st.session_state.get(f"정밀_작업명_{조사명}", "")
                    }
                    
                    원인분석_key = f"정밀_원인분석_data_{조사명}"
                    if 원인분석_key in st.session_state and isinstance(st.session_state[원인분석_key], pd.DataFrame):
                        sheet_name = f'정밀_{조사명}'.replace('/', '_').replace('\\', '_')[:31]
                        정밀_df = pd.DataFrame([정밀_data])
                        정밀_df.to_excel(writer, sheet_name=sheet_name, index=False)
                        
                        # 원인분석 데이터도 같은 시트에 추가
                        st.session_state[원인분석_key].to_excel(
                            writer, 
                            sheet_name=sheet_name, 
                            startrow=3, 
                            index=False
                        )
            
            # 증상조사 분석 데이터
            증상조사_시트 = {
                "기초현황": "기초현황_data_저장",
                "작업기간": "작업기간_data_저장",
                "육체적부담": "육체적부담_data_저장",
                "통증호소자": "통증호소자_data_저장"
            }
            
            for 시트명, 키 in 증상조사_시트.items():
                if 키 in st.session_state and isinstance(st.session_state[키], pd.DataFrame):
                    if not st.session_state[키].empty:
                        st.session_state[키].to_excel(writer, sheet_name=f'증상_{시트명}', index=False)
            
            # 작업환경개선계획서
            if "개선계획_data_저장" in st.session_state and isinstance(st.session_state["개선계획_data_저장"], pd.DataFrame):
                if not st.session_state["개선계획_data_저장"].empty:
                    st.session_state["개선계획_data_저장"].to_excel(writer, sheet_name='개선계획서', index=False)
        
        return True, filename
    except Exception as e:
        return False, str(e)

# Excel 파일에서 데이터 불러오기 함수
def load_from_excel(filename):
    """Excel 파일에서 세션 데이터 불러오기"""
    try:
        # 전체 시트 읽기
        excel_file = pd.ExcelFile(filename)
        
        # 메타데이터 읽기
        if '메타데이터' in excel_file.sheet_names:
            metadata_df = pd.read_excel(excel_file, sheet_name='메타데이터')
            if not metadata_df.empty:
                metadata = metadata_df.iloc[0].to_dict()
                
                # 세션 상태에 메타데이터 복원
                for key in ["session_id", "workplace", "사업장명", "소재지", "업종", "예비조사", "본조사", "수행기관", "성명"]:
                    if key in metadata:
                        st.session_state[key] = metadata[key]
        
        # 체크리스트 읽기
        if '체크리스트' in excel_file.sheet_names:
            st.session_state["checklist_df"] = pd.read_excel(excel_file, sheet_name='체크리스트')
        
        # 각 시트별로 데이터 읽기
        for sheet_name in excel_file.sheet_names:
            if sheet_name.startswith('조사표_'):
                작업명 = sheet_name.replace('조사표_', '')
                조사표_df = pd.read_excel(excel_file, sheet_name=sheet_name)
                if not 조사표_df.empty:
                    data = 조사표_df.iloc[0].to_dict()
                    for key, value in data.items():
                        if pd.notna(value):
                            st.session_state[f"{key}_{작업명}"] = value
            
            elif sheet_name.startswith('작업조건_'):
                작업명 = sheet_name.replace('작업조건_', '')
                st.session_state[f"작업조건_data_{작업명}"] = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            elif sheet_name.startswith('원인분석_'):
                작업명 = sheet_name.replace('원인분석_', '')
                원인분석_df = pd.read_excel(excel_file, sheet_name=sheet_name)
                st.session_state[f"원인분석_항목_{작업명}"] = 원인분석_df.to_dict('records')
            
            elif sheet_name.startswith('정밀_'):
                조사명 = sheet_name.replace('정밀_', '')
                if 조사명 not in st.session_state.get("정밀조사_목록", []):
                    if "정밀조사_목록" not in st.session_state:
                        st.session_state["정밀조사_목록"] = []
                    st.session_state["정밀조사_목록"].append(조사명)
                
                정밀_df = pd.read_excel(excel_file, sheet_name=sheet_name)
                # 구현 계속...
            
            elif sheet_name.startswith('증상_'):
                증상_키 = sheet_name.replace('증상_', '') + "_data_저장"
                st.session_state[증상_키] = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            elif sheet_name == '개선계획서':
                st.session_state["개선계획_data_저장"] = pd.read_excel(excel_file, sheet_name=sheet_name)
        
        return True
    except Exception as e:
        return False

# 자동 저장 기능 (Excel 버전)
def auto_save():
    if "last_save_time" not in st.session_state:
        st.session_state["last_save_time"] = time.time()
    
    current_time = time.time()
    if current_time - st.session_state["last_save_time"] > 30:  # 30초마다 자동 저장
        if st.session_state.get("session_id") and st.session_state.get("workplace"):
            success, _ = save_to_excel(st.session_state["session_id"], st.session_state.get("workplace"))
            if success:
                st.session_state["last_save_time"] = current_time
                st.session_state["last_successful_save"] = datetime.now()

# 저장된 세션 목록 가져오기
def get_saved_sessions():
    """저장된 Excel 세션 파일 목록 반환"""
    sessions = []
    if os.path.exists(SAVE_DIR):
        for filename in os.listdir(SAVE_DIR):
            if filename.endswith('.xlsx'):
                filepath = os.path.join(SAVE_DIR, filename)
                try:
                    # 메타데이터 읽기
                    metadata_df = pd.read_excel(filepath, sheet_name='메타데이터')
                    if not metadata_df.empty:
                        metadata = metadata_df.iloc[0].to_dict()
                        sessions.append({
                            "filename": filename,
                            "session_id": metadata.get("session_id", ""),
                            "workplace": metadata.get("workplace", ""),
                            "saved_at": metadata.get("saved_at", "")
                        })
                except:
                    continue
    return sorted(sessions, key=lambda x: x["saved_at"], reverse=True)

# 값 파싱 함수
def parse_value(value, val_type=float):
    """문자열 값을 숫자로 변환"""
    try:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return 0
            value = value.replace(",", "")
            return val_type(value)
        return val_type(value) if value else 0
    except:
        return 0

# 세션 상태 초기화
if "checklist_df" not in st.session_state:
    st.session_state["checklist_df"] = pd.DataFrame()

# 작업현장별 세션 관리
if "workplace" not in st.session_state:
    st.session_state["workplace"] = None

if "session_id" not in st.session_state:
    st.session_state["session_id"] = None

# 작업명 목록을 가져오는 함수
def get_작업명_목록(사업장명=None, 팀=None, 반=None):
    if st.session_state["checklist_df"].empty:
        return []
    
    df = st.session_state["checklist_df"]
    
    # 필터링
    if 사업장명:
        df = df[df["사업장명"] == 사업장명]
    if 팀:
        df = df[df["팀"] == 팀]
    if 반:
        df = df[df["반"] == 반]
    
    return df["작업명"].dropna().unique().tolist()

# 단위작업명 목록을 가져오는 함수
def get_단위작업명_목록(작업명=None, 사업장명=None, 팀=None, 반=None):
    if st.session_state["checklist_df"].empty:
        return []
    
    df = st.session_state["checklist_df"]
    
    # 필터링
    if 사업장명:
        df = df[df["사업장명"] == 사업장명]
    if 팀:
        df = df[df["팀"] == 팀]
    if 반:
        df = df[df["반"] == 반]
    if 작업명:
        df = df[df["작업명"] == 작업명]
    
    return df["단위작업명"].dropna().unique().tolist()

# 사업장명 목록을 가져오는 함수
def get_사업장명_목록():
    if st.session_state["checklist_df"].empty:
        return []
    return st.session_state["checklist_df"]["사업장명"].dropna().unique().tolist()

# 팀 목록을 가져오는 함수
def get_팀_목록(사업장명=None):
    if st.session_state["checklist_df"].empty:
        return []
    
    df = st.session_state["checklist_df"]
    if 사업장명:
        df = df[df["사업장명"] == 사업장명]
    
    return df["팀"].dropna().unique().tolist()

# 반 목록을 가져오는 함수
def get_반_목록(사업장명=None, 팀=None):
    if st.session_state["checklist_df"].empty:
        return []
    
    df = st.session_state["checklist_df"]
    if 사업장명:
        df = df[df["사업장명"] == 사업장명]
    if 팀:
        df = df[df["팀"] == 팀]
    
    return df["반"].dropna().unique().tolist()

# 부담작업 설명 매핑 (전역 변수)
부담작업_설명 = {
    "1호": "키보드/마우스 4시간 이상",
    "2호": "같은 동작 2시간 이상 반복",
    "3호": "팔 위/옆으로 2시간 이상",
    "4호": "목/허리 구부림 2시간 이상",
    "5호": "쪼그림/무릎굽힘 2시간 이상",
    "6호": "손가락 집기 2시간 이상",
    "7호": "한손 4.5kg 들기 2시간 이상",
    "8호": "25kg 이상 10회/일",
    "9호": "10kg 이상 25회/일",
    "10호": "4.5kg 이상 분당 2회",
    "11호": "손/무릎 충격 시간당 10회",
    "12호": "정적자세/진동/밀당기기"
}

# 사이드바에 데이터 관리 기능
with st.sidebar:
    st.title("📁 데이터 관리")
    
    # 작업현장 선택/입력
    st.markdown("### 🏭 작업현장 선택")
    작업현장_옵션 = ["현장 선택...", "A사업장", "B사업장", "C사업장", "신규 현장 추가"]
    선택된_현장 = st.selectbox("작업현장", 작업현장_옵션)
    
    if 선택된_현장 == "신규 현장 추가":
        새현장명 = st.text_input("새 현장명 입력")
        if 새현장명:
            st.session_state["workplace"] = 새현장명
            st.session_state["session_id"] = f"{새현장명}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    elif 선택된_현장 != "현장 선택...":
        st.session_state["workplace"] = 선택된_현장
        if not st.session_state.get("session_id") or 선택된_현장 not in st.session_state.get("session_id", ""):
            st.session_state["session_id"] = f"{선택된_현장}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 세션 정보 표시
    if st.session_state.get("session_id"):
        st.info(f"🔐 세션 ID: {st.session_state['session_id']}")
    
    # 자동 저장 상태
    if "last_successful_save" in st.session_state:
        last_save = st.session_state["last_successful_save"]
        st.success(f"✅ 마지막 자동저장: {last_save.strftime('%H:%M:%S')}")
    
    # 수동 저장 버튼
    if st.button("💾 Excel로 저장", use_container_width=True):
        if st.session_state.get("session_id") and st.session_state.get("workplace"):
            success, result = save_to_excel(st.session_state["session_id"], st.session_state.get("workplace"))
            if success:
                st.success(f"✅ Excel 파일로 저장되었습니다!\n📁 {result}")
                st.session_state["last_successful_save"] = datetime.now()
            else:
                st.error(f"저장 중 오류 발생: {result}")
        else:
            st.warning("먼저 작업현장을 선택해주세요!")
    
    # 저장된 세션 목록
    st.markdown("---")
    st.markdown("### 📂 저장된 세션")
    
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
    
    # Excel 파일 직접 업로드
    st.markdown("---")
    st.markdown("### 📤 Excel 파일 업로드")
    uploaded_file = st.file_uploader("Excel 파일 선택", type=['xlsx'])
    if uploaded_file is not None:
        if st.button("📥 데이터 가져오기", use_container_width=True):
            # 임시 파일로 저장
            temp_path = os.path.join(SAVE_DIR, f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            if load_from_excel(temp_path):
                st.success("✅ Excel 파일을 성공적으로 불러왔습니다!")
                os.remove(temp_path)  # 임시 파일 삭제
                st.rerun()
            else:
                st.error("파일을 불러오는 중 오류가 발생했습니다.")
                os.remove(temp_path)  # 임시 파일 삭제
    
    # 부담작업 참고 정보
    with st.expander("📖 부담작업 빠른 참조"):
        st.markdown("""
        **반복동작 관련**
        - 1호: 키보드/마우스 4시간↑
        - 2호: 같은동작 2시간↑ 반복
        - 6호: 손가락집기 2시간↑
        - 7호: 한손 4.5kg 2시간↑
        - 10호: 4.5kg 분당2회↑
        
        **부자연스러운 자세**
        - 3호: 팔 위/옆 2시간↑
        - 4호: 목/허리굽힘 2시간↑
        - 5호: 쪼그림/무릎 2시간↑
        
        **과도한 힘**
        - 8호: 25kg 10회/일↑
        - 9호: 10kg 25회/일↑
        
        **기타**
        - 11호: 손/무릎충격 시간당10회↑
        - 12호: 정적자세/진동/밀당기기
        """)

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

# 1. 사업장개요 탭
with tabs[0]:
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

# 2. 근골격계 부담작업 체크리스트 탭
with tabs[1]:
    st.subheader("근골격계 부담작업 체크리스트")
    
    # 엑셀 파일 업로드 기능 추가
    with st.expander("📤 엑셀 파일 업로드"):
        st.info("""
        📌 엑셀 파일 양식:
        - 첫 번째 열: 사업장명
        - 두 번째 열: 팀
        - 세 번째 열: 반
        - 네 번째 열: 작업명
        - 다섯 번째 열: 단위작업명
        - 6~17번째 열: 1호~12호 (O(해당), △(잠재위험), X(미해당) 중 입력)
        """)
        
        uploaded_excel = st.file_uploader("엑셀 파일 선택", type=['xlsx', 'xls'])
        
        if uploaded_excel is not None:
            try:
                # 엑셀 파일 읽기
                df_excel = pd.read_excel(uploaded_excel)
                
                # 컬럼명 확인 및 조정
                expected_columns = ["사업장명", "팀", "반", "작업명", "단위작업명"] + [f"{i}호" for i in range(1, 13)]
                
                # 컬럼 개수가 맞는지 확인
                if len(df_excel.columns) >= 17:
                    # 컬럼명 재설정
                    df_excel.columns = expected_columns[:len(df_excel.columns)]
                    
                    # 값 검증 (O(해당), △(잠재위험), X(미해당)만 허용)
                    valid_values = ["O(해당)", "△(잠재위험)", "X(미해당)"]
                    
                    # 6번째 열부터 17번째 열까지 검증
                    for col in expected_columns[5:]:
                        if col in df_excel.columns:
                            # 유효하지 않은 값은 X(미해당)으로 변경
                            df_excel[col] = df_excel[col].apply(
                                lambda x: x if x in valid_values else "X(미해당)"
                            )
                    
                    if st.button("✅ 데이터 적용하기"):
                        st.session_state["checklist_df"] = df_excel
                        
                        # 즉시 Excel 파일로 저장
                        if st.session_state.get("session_id") and st.session_state.get("workplace"):
                            success, _ = save_to_excel(st.session_state["session_id"], st.session_state.get("workplace"))
                            if success:
                                st.session_state["last_save_time"] = time.time()
                                st.session_state["last_successful_save"] = datetime.now()
                        
                        st.success("✅ 엑셀 데이터를 성공적으로 불러오고 저장했습니다!")
                        st.rerun()
                    
                    # 미리보기
                    st.markdown("#### 📋 데이터 미리보기")
                    if st.session_state.get("large_data_mode", False):
                        st.dataframe(df_excel.head(20))
                        st.info(f"전체 {len(df_excel)}개 행 중 상위 20개만 표시됩니다.")
                    else:
                        st.dataframe(df_excel)
                    
                else:
                    st.error("⚠️ 엑셀 파일의 컬럼이 17개 이상이어야 합니다. (사업장명, 팀, 반, 작업명, 단위작업명, 1호~12호)")
                    
            except Exception as e:
                st.error(f"❌ 파일 읽기 오류: {str(e)}")
    
    # 샘플 엑셀 파일 다운로드
    with st.expander("📥 샘플 엑셀 파일 다운로드"):
        # 샘플 데이터 생성
        sample_data = pd.DataFrame({
            "사업장명": ["A사업장", "A사업장", "A사업장", "A사업장", "A사업장"],
            "팀": ["생산1팀", "생산1팀", "생산2팀", "생산2팀", "물류팀"],
            "반": ["조립1반", "조립1반", "포장1반", "포장1반", "운반1반"],
            "작업명": ["조립작업", "조립작업", "포장작업", "포장작업", "운반작업"],
            "단위작업명": ["부품조립", "나사체결", "제품포장", "박스적재", "대차운반"],
            "1호": ["O(해당)", "X(미해당)", "X(미해당)", "O(해당)", "X(미해당)"],
            "2호": ["X(미해당)", "O(해당)", "X(미해당)", "X(미해당)", "O(해당)"],
            "3호": ["△(잠재위험)", "X(미해당)", "O(해당)", "X(미해당)", "X(미해당)"],
            "4호": ["X(미해당)", "X(미해당)", "X(미해당)", "△(잠재위험)", "X(미해당)"],
            "5호": ["X(미해당)", "△(잠재위험)", "X(미해당)", "X(미해당)", "O(해당)"],
            "6호": ["X(미해당)", "X(미해당)", "X(미해당)", "X(미해당)", "X(미해당)"],
            "7호": ["X(미해당)", "X(미해당)", "△(잠재위험)", "X(미해당)", "X(미해당)"],
            "8호": ["X(미해당)", "X(미해당)", "X(미해당)", "X(미해당)", "X(미해당)"],
            "9호": ["X(미해당)", "X(미해당)", "X(미해당)", "X(미해당)", "X(미해당)"],
            "10호": ["X(미해당)", "X(미해당)", "X(미해당)", "X(미해당)", "X(미해당)"],
            "11호": ["O(해당)", "X(미해당)", "X(미해당)", "O(해당)", "△(잠재위험)"],
            "12호": ["X(미해당)", "△(잠재위험)", "O(해당)", "X(미해당)", "X(미해당)"]
        })
        
        # 샘플 데이터 표시
        st.markdown("##### 샘플 데이터 구조:")
        st.dataframe(sample_data, use_container_width=True)
        
        # 엑셀 파일로 변환
        sample_output = BytesIO()
        with pd.ExcelWriter(sample_output, engine='openpyxl') as writer:
            sample_data.to_excel(writer, sheet_name='체크리스트', index=False)
        
        sample_output.seek(0)
        
        st.download_button(
            label="📥 샘플 엑셀 다운로드",
            data=sample_output,
            file_name="체크리스트_샘플.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    st.markdown("---")
    
    # 기존 데이터 편집기
    columns = [
        "사업장명", "팀", "반", "작업명", "단위작업명"
    ] + [f"{i}호" for i in range(1, 13)]
    
    # 세션 상태에 저장된 데이터가 있으면 사용, 없으면 빈 데이터
    if "checklist_df" in st.session_state and not st.session_state["checklist_df"].empty:
        data = st.session_state["checklist_df"]
        # 기존 데이터에 사업장명, 팀, 반 컬럼이 없으면 추가
        if "사업장명" not in data.columns:
            data.insert(0, "사업장명", st.session_state.get("workplace", ""))
        if "팀" not in data.columns:
            팀_위치 = 1 if "사업장명" in data.columns else 0
            data.insert(팀_위치, "팀", "")
        if "반" not in data.columns:
            반_위치 = 2 if "사업장명" in data.columns else 1
            data.insert(반_위치, "반", "")
    else:
        # 새로운 빈 데이터프레임 생성
        초기_데이터 = []
        for i in range(5):
            행 = [st.session_state.get("workplace", ""), "", "", "", ""] + ["X(미해당)"]*12
            초기_데이터.append(행)
        data = pd.DataFrame(초기_데이터, columns=columns)
    
    # 데이터 편집기 표시
    st.markdown("### 📝 부담작업 체크리스트 입력")
    
    # AgGrid 대신 기본 방식 사용
    ho_options = ["O(해당)", "△(잠재위험)", "X(미해당)"]
    
    # 수동으로 데이터 입력 폼 생성
    with st.form("checklist_form"):
        st.markdown("#### 새 데이터 추가")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            사업장명_입력 = st.text_input("사업장명", value=st.session_state.get("workplace", ""))
        with col2:
            팀_입력 = st.text_input("팀")
        with col3:
            반_입력 = st.text_input("반")
        with col4:
            작업명_입력 = st.text_input("작업명")
        with col5:
            단위작업명_입력 = st.text_input("단위작업명")
        
        # 1호~12호 입력
        st.markdown("##### 부담작업 선택")
        호_columns = st.columns(12)
        호_선택 = []
        for i in range(12):
            with 호_columns[i]:
                선택 = st.selectbox(f"{i+1}호", ho_options, index=2, key=f"ho_{i+1}")
                호_선택.append(선택)
        
        제출 = st.form_submit_button("➕ 추가", use_container_width=True)
        
        if 제출:
            새_행 = [사업장명_입력, 팀_입력, 반_입력, 작업명_입력, 단위작업명_입력] + 호_선택
            새_df = pd.DataFrame([새_행], columns=columns)
            data = pd.concat([data, 새_df], ignore_index=True)
            st.session_state["checklist_df"] = data
            st.rerun()
    
    # 현재 데이터 표시
    st.markdown("#### 📋 현재 입력된 데이터")
    if not data.empty:
        # 데이터 표시
        st.dataframe(data, use_container_width=True, height=400)
        
        # 삭제 기능
        if len(data) > 0:
            삭제_인덱스 = st.number_input("삭제할 행 번호 (0부터 시작)", min_value=0, max_value=len(data)-1, value=0)
            if st.button("🗑️ 선택한 행 삭제"):
                data = data.drop(index=삭제_인덱스).reset_index(drop=True)
                st.session_state["checklist_df"] = data
                st.rerun()
    else:
        st.info("아직 입력된 데이터가 없습니다. 위 폼을 사용하여 데이터를 추가하세요.")
    
    # 세션 상태에 저장
    st.session_state["checklist_df"] = data
    
    # 현재 등록된 작업명 표시
    작업명_목록 = get_작업명_목록()
    if 작업명_목록:
        st.info(f"📋 현재 등록된 작업: {', '.join(작업명_목록)}")

# 작업부하와 작업빈도에서 숫자 추출하는 함수
def extract_number(value):
    if value and "(" in value and ")" in value:
        return int(value.split("(")[1].split(")")[0])
    return 0

# 총점 계산 함수
def calculate_total_score(row):
    부하값 = extract_number(row["작업부하(A)"])
    빈도값 = extract_number(row["작업빈도(B)"])
    return 부하값 * 빈도값

# 3. 유해요인조사표 탭
with tabs[2]:
    st.title("유해요인조사표")
    
    # 계층적 선택 구조
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        사업장명_목록 = get_사업장명_목록()
        if not 사업장명_목록:
            st.warning("먼저 체크리스트에 데이터를 입력하세요.")
            selected_사업장명 = None
        else:
            selected_사업장명 = st.selectbox(
                "사업장명 선택",
                ["선택하세요"] + 사업장명_목록,
                key="유해요인_사업장명"
            )
            if selected_사업장명 == "선택하세요":
                selected_사업장명 = None
    
    with col2:
        if selected_사업장명:
            팀_목록 = get_팀_목록(selected_사업장명)
            selected_팀 = st.selectbox(
                "팀 선택",
                ["전체"] + 팀_목록,
                key="유해요인_팀"
            )
            if selected_팀 == "전체":
                selected_팀 = None
        else:
            st.selectbox("팀 선택", ["사업장을 먼저 선택하세요"], disabled=True)
            selected_팀 = None
    
    with col3:
        if selected_사업장명:
            반_목록 = get_반_목록(selected_사업장명, selected_팀)
            selected_반 = st.selectbox(
                "반 선택",
                ["전체"] + 반_목록,
                key="유해요인_반"
            )
            if selected_반 == "전체":
                selected_반 = None
        else:
            st.selectbox("반 선택", ["팀을 먼저 선택하세요"], disabled=True)
            selected_반 = None
    
    with col4:
        if selected_사업장명:
            작업명_목록 = get_작업명_목록(selected_사업장명, selected_팀, selected_반)
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
            st.selectbox("작업명 선택", ["사업장을 먼저 선택하세요"], disabled=True)
            selected_작업명_유해 = None
    
    if selected_작업명_유해:
        st.info(f"📋 선택된 작업: {selected_사업장명} > {selected_팀 or '전체'} > {selected_반 or '전체'} > {selected_작업명_유해}")
        
        # 해당 작업의 단위작업명 가져오기
        단위작업명_목록 = get_단위작업명_목록(selected_작업명_유해, selected_사업장명, selected_팀, selected_반)
        
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

# 4. 작업조건조사 탭
with tabs[3]:
    st.title("작업조건조사")
    
    # 계층적 선택 구조
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        사업장명_목록_조건 = get_사업장명_목록()
        if not 사업장명_목록_조건:
            st.warning("먼저 체크리스트에 데이터를 입력하세요.")
            selected_사업장명_조건 = None
        else:
            selected_사업장명_조건 = st.selectbox(
                "사업장명 선택",
                ["선택하세요"] + 사업장명_목록_조건,
                key="작업조건_사업장명"
            )
            if selected_사업장명_조건 == "선택하세요":
                selected_사업장명_조건 = None
    
    with col2:
        if selected_사업장명_조건:
            팀_목록_조건 = get_팀_목록(selected_사업장명_조건)
            selected_팀_조건 = st.selectbox(
                "팀 선택",
                ["전체"] + 팀_목록_조건,
                key="작업조건_팀"
            )
            if selected_팀_조건 == "전체":
                selected_팀_조건 = None
        else:
            st.selectbox("팀 선택", ["사업장을 먼저 선택하세요"], disabled=True)
            selected_팀_조건 = None
    
    with col3:
        if selected_사업장명_조건:
            반_목록_조건 = get_반_목록(selected_사업장명_조건, selected_팀_조건)
            selected_반_조건 = st.selectbox(
                "반 선택",
                ["전체"] + 반_목록_조건,
                key="작업조건_반"
            )
            if selected_반_조건 == "전체":
                selected_반_조건 = None
        else:
            st.selectbox("반 선택", ["팀을 먼저 선택하세요"], disabled=True)
            selected_반_조건 = None
    
    with col4:
        if selected_사업장명_조건:
            작업명_목록_조건 = get_작업명_목록(selected_사업장명_조건, selected_팀_조건, selected_반_조건)
            if 작업명_목록_조건:
                selected_작업명 = st.selectbox(
                    "작업명 선택",
                    작업명_목록_조건,
                    key="작업조건_작업명"
                )
            else:
                st.warning("해당 조건에 맞는 작업이 없습니다.")
                selected_작업명 = None
        else:
            st.selectbox("작업명 선택", ["사업장을 먼저 선택하세요"], disabled=True)
            selected_작업명 = None
    
    if selected_작업명:
        작업명_목록 = get_작업명_목록(selected_사업장명_조건, selected_팀_조건, selected_반_조건)
        st.info(f"📋 선택된 작업: {selected_사업장명_조건} > {selected_팀_조건 or '전체'} > {selected_반_조건 or '전체'} > {selected_작업명}")
        st.info(f"📋 총 {len(작업명_목록)}개의 작업이 있습니다. 각 작업별로 1,2,3단계를 작성하세요.")
        
        # 선택된 작업에 대한 1,2,3단계
        with st.container():
            # 1단계: 유해요인 기본조사
            st.subheader(f"1단계: 유해요인 기본조사 - [{selected_작업명}]")
            col1, col2 = st.columns(2)
            with col1:
                작업공정 = st.text_input("작업공정", value=selected_작업명, key=f"1단계_작업공정_{selected_작업명}")
            with col2:
                작업내용 = st.text_input("작업내용", key=f"1단계_작업내용_{selected_작업명}")
            
            st.markdown("---")
            
            # 2단계: 작업별 작업부하 및 작업빈도
            st.subheader(f"2단계: 작업별 작업부하 및 작업빈도 - [{selected_작업명}]")
            
            # 선택된 작업명에 해당하는 체크리스트 데이터 가져오기
            checklist_data = []
            if not st.session_state["checklist_df"].empty:
                작업_체크리스트 = st.session_state["checklist_df"][
                    (st.session_state["checklist_df"]["작업명"] == selected_작업명) &
                    (st.session_state["checklist_df"]["사업장명"] == selected_사업장명_조건)
                ]
                if selected_팀_조건:
                    작업_체크리스트 = 작업_체크리스트[작업_체크리스트["팀"] == selected_팀_조건]
                if selected_반_조건:
                    작업_체크리스트 = 작업_체크리스트[작업_체크리스트["반"] == selected_반_조건]
                
                for idx, row in 작업_체크리스트.iterrows():
                    if row["단위작업명"]:
                        부담작업호 = []
                        for i in range(1, 13):
                            if row[f"{i}호"] == "O(해당)":
                                부담작업호.append(f"{i}호")
                            elif row[f"{i}호"] == "△(잠재위험)":
                                부담작업호.append(f"{i}호(잠재)")
                        
                        checklist_data.append({
                            "단위작업명": row["단위작업명"],
                            "부담작업(호)": ", ".join(부담작업호) if 부담작업호 else "미해당",
                            "작업부하(A)": "",
                            "작업빈도(B)": "",
                            "총점": 0
                        })
            
            # 데이터프레임 생성
            if checklist_data:
                data = pd.DataFrame(checklist_data)
            else:
                data = pd.DataFrame({
                    "단위작업명": ["" for _ in range(3)],
                    "부담작업(호)": ["" for _ in range(3)],
                    "작업부하(A)": ["" for _ in range(3)],
                    "작업빈도(B)": ["" for _ in range(3)],
                    "총점": [0 for _ in range(3)],
                })

            부하옵션 = [
                "",
                "매우쉬움(1)", 
                "쉬움(2)", 
                "약간 힘듦(3)", 
                "힘듦(4)", 
                "매우 힘듦(5)"
            ]
            빈도옵션 = [
                "",
                "3개월마다(1)", 
                "가끔(2)", 
                "자주(3)", 
                "계속(4)", 
                "초과근무(5)"
            ]

            column_config = {
                "작업부하(A)": st.column_config.SelectboxColumn("작업부하(A)", options=부하옵션, required=False),
                "작업빈도(B)": st.column_config.SelectboxColumn("작업빈도(B)", options=빈도옵션, required=False),
                "단위작업명": st.column_config.TextColumn("단위작업명"),
                "부담작업(호)": st.column_config.TextColumn("부담작업(호)"),
                "총점": st.column_config.TextColumn("총점(자동계산)", disabled=True),
            }

            # 데이터 편집
            edited_df = st.data_editor(
                data,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                column_config=column_config,
                key=f"작업조건_data_editor_{selected_작업명}"
            )
            
            # 편집된 데이터를 세션 상태에 저장
            st.session_state[f"작업조건_data_{selected_작업명}"] = edited_df
            
            # 총점 자동 계산 후 다시 표시
            if not edited_df.empty:
                display_df = edited_df.copy()
                for idx in range(len(display_df)):
                    display_df.at[idx, "총점"] = calculate_total_score(display_df.iloc[idx])
                
                st.markdown("##### 계산 결과")
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "단위작업명": st.column_config.TextColumn("단위작업명"),
                        "부담작업(호)": st.column_config.TextColumn("부담작업(호)"),
                        "작업부하(A)": st.column_config.TextColumn("작업부하(A)"),
                        "작업빈도(B)": st.column_config.TextColumn("작업빈도(B)"),
                        "총점": st.column_config.NumberColumn("총점(자동계산)", format="%d"),
                    }
                )
                
                st.info("💡 총점은 작업부하(A) × 작업빈도(B)로 자동 계산됩니다.")
            
            # 3단계: 유해요인평가
            st.markdown("---")
            st.subheader(f"3단계: 유해요인평가 - [{selected_작업명}]")
            
            # 작업명과 근로자수 입력
            col1, col2 = st.columns(2)
            with col1:
                평가_작업명 = st.text_input("작업명", value=selected_작업명, key=f"3단계_작업명_{selected_작업명}")
            with col2:
                평가_근로자수 = st.text_input("근로자수", key=f"3단계_근로자수_{selected_작업명}")
            
            # 사진 업로드 및 설명 입력
            st.markdown("#### 작업 사진 및 설명")
            
            # 사진 개수 선택
            num_photos = st.number_input("사진 개수", min_value=1, max_value=10, value=3, key=f"사진개수_{selected_작업명}")
            
            # 각 사진별로 업로드와 설명 입력
            for i in range(num_photos):
                st.markdown(f"##### 사진 {i+1}")
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    uploaded_file = st.file_uploader(
                        f"사진 {i+1} 업로드",
                        type=['png', 'jpg', 'jpeg'],
                        key=f"사진_{i+1}_업로드_{selected_작업명}"
                    )
                    if uploaded_file:
                        st.image(uploaded_file, caption=f"사진 {i+1}", use_column_width=True)
                
                with col2:
                    photo_description = st.text_area(
                        f"사진 {i+1} 설명",
                        height=150,
                        key=f"사진_{i+1}_설명_{selected_작업명}",
                        placeholder="이 사진에 대한 설명을 입력하세요..."
                    )
                
                st.markdown("---")
            
            # 작업별로 관련된 유해요인에 대한 원인분석 (개선된 버전)
            st.markdown("---")
            st.subheader(f"작업별로 관련된 유해요인에 대한 원인분석 - [{selected_작업명}]")
            
            # 2단계에서 입력한 데이터와 체크리스트 정보 가져오기
            부담작업_정보 = []
            부담작업_힌트 = {}  # 단위작업명별 부담작업 정보 저장
            
            if 'display_df' in locals() and not display_df.empty:
                for idx, row in display_df.iterrows():
                    if row["단위작업명"] and row["부담작업(호)"] and row["부담작업(호)"] != "미해당":
                        부담작업_정보.append({
                            "단위작업명": row["단위작업명"],
                            "부담작업호": row["부담작업(호)"]
                        })
                        부담작업_힌트[row["단위작업명"]] = row["부담작업(호)"]
            
            # 원인분석 항목 초기화
            원인분석_key = f"원인분석_항목_{selected_작업명}"
            if 원인분석_key not in st.session_state:
                st.session_state[원인분석_key] = []
                # 부담작업 정보를 기반으로 초기 항목 생성 (부담작업이 있는 개수만큼)
                for info in 부담작업_정보:
                    st.session_state[원인분석_key].append({
                        "단위작업명": info["단위작업명"],
                        "부담작업호": info["부담작업호"],
                        "유형": "",
                        "부담작업": "",
                        "비고": ""
                    })
            
            # 추가/삭제 버튼
            col1, col2, col3 = st.columns([6, 1, 1])
            with col2:
                if st.button("➕ 추가", key=f"원인분석_추가_{selected_작업명}", use_container_width=True):
                    st.session_state[원인분석_key].append({
                        "단위작업명": "",
                        "부담작업호": "",
                        "유형": "",
                        "부담작업": "",
                        "비고": ""
                    })
                    st.rerun()
            with col3:
                if st.button("➖ 삭제", key=f"원인분석_삭제_{selected_작업명}", use_container_width=True):
                    if len(st.session_state[원인분석_key]) > 0:
                        st.session_state[원인분석_key].pop()
                        st.rerun()
            
            # 유형별 관련 부담작업 매핑
            유형별_부담작업 = {
                "반복동작": ["1호", "2호", "6호", "7호", "10호"],
                "부자연스러운 자세": ["3호", "4호", "5호"],
                "과도한 힘": ["8호", "9호"],
                "접촉스트레스 또는 기타(진동, 밀고 당기기 등)": ["11호", "12호"]
            }
            
            # 각 유해요인 항목 처리
            hazard_entries_to_process = st.session_state[원인분석_key]
            
            for k, hazard_entry in enumerate(hazard_entries_to_process):
                st.markdown(f"**유해요인 원인분석 항목 {k+1}**")
                
                # 단위작업명 입력 및 부담작업 힌트 표시
                col1, col2, col3 = st.columns([3, 2, 3])
                
                with col1:
                    hazard_entry["단위작업명"] = st.text_input(
                        "단위작업명", 
                        value=hazard_entry.get("단위작업명", ""), 
                        key=f"원인분석_단위작업명_{k}_{selected_작업명}"
                    )
                
                with col2:
                    # 해당 단위작업의 부담작업 정보를 힌트로 표시
                    if hazard_entry["단위작업명"] in 부담작업_힌트:
                        부담작업_리스트 = 부담작업_힌트[hazard_entry["단위작업명"]].split(", ")
                        힌트_텍스트= []
                        
                        for 항목 in 부담작업_리스트:
                            호수 = 항목.replace("(잠재)", "").strip()
                            if 호수 in 부담작업_설명:
                                if "(잠재)" in 항목:
                                    힌트_텍스트.append(f"🟡 {호수}: {부담작업_설명[호수]}")
                                else:
                                    힌트_텍스트.append(f"🔴 {호수}: {부담작업_설명[호수]}")
                        
                        if 힌트_텍스트:
                            st.info("💡 부담작업 힌트:\n" + "\n".join(힌트_텍스트))
                    else:
                        st.empty()  # 빈 공간 유지
                
                with col3:
                    hazard_entry["비고"] = st.text_input(
                        "비고", 
                        value=hazard_entry.get("비고", ""), 
                        key=f"원인분석_비고_{k}_{selected_작업명}"
                    )
                
                # 유해요인 유형 선택
                hazard_type_options = ["", "반복동작", "부자연스러운 자세", "과도한 힘", "접촉스트레스 또는 기타(진동, 밀고 당기기 등)"]
                selected_hazard_type_index = hazard_type_options.index(hazard_entry.get("유형", "")) if hazard_entry.get("유형", "") in hazard_type_options else 0
                
                hazard_entry["유형"] = st.selectbox(
                    f"[{k+1}] 유해요인 유형 선택", 
                    hazard_type_options, 
                    index=selected_hazard_type_index, 
                    key=f"hazard_type_{k}_{selected_작업명}",
                    help="선택한 단위작업의 부담작업 유형에 맞는 항목을 선택하세요"
                )

                if hazard_entry["유형"] == "반복동작":
                    burden_task_options = [
                        "",
                        "(1호)하루에 4시간 이상 집중적으로 자료입력 등을 위해 키보드 또는 마우스를 조작하는 작업",
                        "(2호)하루에 총 2시간 이상 목, 어깨, 팔꿈치, 손목 또는 손을 사용하여 같은 동작을 반복하는 작업",
                        "(6호)하루에 총 2시간 이상 지지되지 않은 상태에서 1kg 이상의 물건을 한손의 손가락으로 집어 옮기거나, 2kg 이상에 상응하는 힘을 가하여 한손의 손가락으로 물건을 쥐는 작업",
                        "(7호)하루에 총 2시간 이상 지지되지 않은 상태에서 4.5kg 이상의 물건을 한 손으로 들거나 동일한 힘으로 쥐는 작업",
                        "(10호)하루에 총 2시간 이상, 분당 2회 이상 4.5kg 이상의 물체를 드는 작업",
                        "(1호)하루에 4시간 이상 집중적으로 자료입력 등을 위해 키보드 또는 마우스를 조작하는 작업+(12호)정적자세(장시간 서서 작업, 또는 장시간 앉아서 작업)",
                        "(2호)하루에 총 2시간 이상 목, 어깨, 팔꿈치, 손목 또는 손을 사용하여 같은 동작을 반복하는 작업+(12호)정적자세(장시간 서서 작업, 또는 장시간 앉아서 작업)",
                        "(6호)하루에 총 2시간 이상 지지되지 않은 상태에서 1kg 이상의 물건을 한손의 손가락으로 집어 옮기거나, 2kg 이상에 상응하는 힘을 가하여 한손의 손가락으로 물건을 쥐는 작업+(12호)정적자세(장시간 서서 작업, 또는 장시간 앉아서 작업)",
                        "(7호)하루에 총 2시간 이상 지지되지 않은 상태에서 4.5kg 이상의 물건을 한 손으로 들거나 동일한 힘으로 쥐는 작업+(12호)정적자세(장시간 서서 작업, 또는 장시간 앉아서 작업)",
                        "(10호)하루에 총 2시간 이상, 분당 2회 이상 4.5kg 이상의 물체를 드는 작업+(12호)정적자세(장시간 서서 작업, 또는 장시간 앉아서 작업)"
                    ]
                    selected_burden_task_index = burden_task_options.index(hazard_entry.get("부담작업", "")) if hazard_entry.get("부담작업", "") in burden_task_options else 0
                    hazard_entry["부담작업"] = st.selectbox(f"[{k+1}] 부담작업", burden_task_options, index=selected_burden_task_index, key=f"burden_task_반복_{k}_{selected_작업명}")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        hazard_entry["수공구 종류"] = st.text_input(f"[{k+1}] 수공구 종류", value=hazard_entry.get("수공구 종류", ""), key=f"수공구_종류_{k}_{selected_작업명}")
                        hazard_entry["부담부위"] = st.text_input(f"[{k+1}] 부담부위", value=hazard_entry.get("부담부위", ""), key=f"부담부위_{k}_{selected_작업명}")
                    with col2:
                        hazard_entry["수공구 용도"] = st.text_input(f"[{k+1}] 수공구 용도", value=hazard_entry.get("수공구 용도", ""), key=f"수공구_용도_{k}_{selected_작업명}")
                        회당_반복시간_초_회 = st.text_input(f"[{k+1}] 회당 반복시간(초/회)", value=hazard_entry.get("회당 반복시간(초/회)", ""), key=f"반복_회당시간_{k}_{selected_작업명}")
                    with col3:
                        hazard_entry["수공구 무게(kg)"] = st.number_input(f"[{k+1}] 수공구 무게(kg)", value=hazard_entry.get("수공구 무게(kg)", 0.0), key=f"수공구_무게_{k}_{selected_작업명}")
                        작업시간동안_반복횟수_회_일 = st.text_input(f"[{k+1}] 작업시간동안 반복횟수(회/일)", value=hazard_entry.get("작업시간동안 반복횟수(회/일)", ""), key=f"반복_총횟수_{k}_{selected_작업명}")
                    with col4:
                        hazard_entry["수공구 사용시간(분)"] = st.text_input(f"[{k+1}] 수공구 사용시간(분)", value=hazard_entry.get("수공구 사용시간(분)", ""), key=f"수공구_사용시간_{k}_{selected_작업명}")
                        
                        # 총 작업시간(분) 자동 계산
                        calculated_total_work_time = 0.0
                        try:
                            parsed_회당_반복시간 = parse_value(회당_반복시간_초_회, val_type=float)
                            parsed_작업시간동안_반복횟수 = parse_value(작업시간동안_반복횟수_회_일, val_type=float)
                            
                            if parsed_회당_반복시간 > 0 and parsed_작업시간동안_반복횟수 > 0:
                                calculated_total_work_time = (parsed_회당_반복시간 * parsed_작업시간동안_반복횟수) / 60
                        except Exception:
                            pass
                        
                        hazard_entry["총 작업시간(분)"] = st.text_input(
                            f"[{k+1}] 총 작업시간(분) (자동계산)",
                            value=f"{calculated_total_work_time:.2f}" if calculated_total_work_time > 0 else "",
                            key=f"반복_총시간_{k}_{selected_작업명}",
                            disabled=True
                        )
                    
                    # 값 저장
                    hazard_entry["회당 반복시간(초/회)"] = 회당_반복시간_초_회
                    hazard_entry["작업시간동안 반복횟수(회/일)"] = 작업시간동안_반복횟수_회_일

                    # 10호 추가 필드
                    if "(10호)" in hazard_entry["부담작업"]:
                        col1, col2 = st.columns(2)
                        with col1:
                            hazard_entry["물체 무게(kg)_10호"] = st.number_input(f"[{k+1}] (10호)물체 무게(kg)", value=hazard_entry.get("물체 무게(kg)_10호", 0.0), key=f"물체_무게_10호_{k}_{selected_작업명}")
                        with col2:
                            hazard_entry["분당 반복횟수(회/분)_10호"] = st.text_input(f"[{k+1}] (10호)분당 반복횟수(회/분)", value=hazard_entry.get("분당 반복횟수(회/분)_10호", ""), key=f"분당_반복횟수_10호_{k}_{selected_작업명}")

                    # 12호 정적자세 관련 필드
                    if "(12호)정적자세" in hazard_entry["부담작업"]:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            hazard_entry["작업내용_12호_정적"] = st.text_input(f"[{k+1}] (정지자세)작업내용", value=hazard_entry.get("작업내용_12호_정적", ""), key=f"반복_작업내용_12호_정적_{k}_{selected_작업명}")
                        with col2:
                            hazard_entry["작업시간(분)_12호_정적"] = st.number_input(f"[{k+1}] (정지자세)작업시간(분)", value=hazard_entry.get("작업시간(분)_12호_정적", 0), key=f"반복_작업시간_12호_정적_{k}_{selected_작업명}")
                        with col3:
                            hazard_entry["휴식시간(분)_12호_정적"] = st.number_input(f"[{k+1}] (정지자세)휴식시간(분)", value=hazard_entry.get("휴식시간(분)_12호_정적", 0), key=f"반복_휴식시간_12호_정적_{k}_{selected_작업명}")
                        with col4:
                            hazard_entry["인체부담부위_12호_정적"] = st.text_input(f"[{k+1}] (정지자세)인체부담부위", value=hazard_entry.get("인체부담부위_12호_정적", ""), key=f"반복_인체부담부위_12호_정적_{k}_{selected_작업명}")

                elif hazard_entry["유형"] == "부자연스러운 자세":
                    burden_pose_options = [
                        "",
                        "(3호)하루에 총 2시간 이상 머리 위에 손이 있거나, 팔꿈치가 어깨위에 있거나, 팔꿈치를 몸통으로부터 들거나, 팔꿈치를 몸통뒤쪽에 위치하도록 하는 상태에서 이루어지는 작업",
                        "(4호)지지되지 않은 상태이거나 임의로 자세를 바꿀 수 없는 조건에서, 하루에 총 2시간 이상 목이나 허리를 구부리거나 트는 상태에서 이루어지는 작업",
                        "(5호)하루에 총 2시간 이상 쪼그리고 앉거나 무릎을 굽힌 자세에서 이루어지는 작업"
                    ]
                    selected_burden_pose_index = burden_pose_options.index(hazard_entry.get("부담작업", "")) if hazard_entry.get("부담작업", "") in burden_pose_options else 0
                    hazard_entry["부담작업"] = st.selectbox(f"[{k+1}] 부담작업", burden_pose_options, index=selected_burden_pose_index, key=f"burden_pose_{k}_{selected_작업명}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        hazard_entry["회당 반복시간(초/회)"] = st.text_input(f"[{k+1}] 회당 반복시간(초/회)", value=hazard_entry.get("회당 반복시간(초/회)", ""), key=f"자세_회당시간_{k}_{selected_작업명}")
                    with col2:
                        hazard_entry["작업시간동안 반복횟수(회/일)"] = st.text_input(f"[{k+1}] 작업시간동안 반복횟수(회/일)", value=hazard_entry.get("작업시간동안 반복횟수(회/일)", ""), key=f"자세_총횟수_{k}_{selected_작업명}")
                    with col3:
                        hazard_entry["총 작업시간(분)"] = st.text_input(f"[{k+1}] 총 작업시간(분)", value=hazard_entry.get("총 작업시간(분)", ""), key=f"자세_총시간_{k}_{selected_작업명}")

                elif hazard_entry["유형"] == "과도한 힘":
                    burden_force_options = [
                        "",
                        "(8호)하루에 10회 이상 25kg 이상의 물체를 드는 작업",
                        "(9호)하루에 25회 이상 10kg 이상의 물체를 무릎 아래에서 들거나, 어깨 위에서 들거나, 팔을 뻗은 상태에서 드는 작업",
                        "(12호)밀기/당기기 작업",
                        "(8호)하루에 10회 이상 25kg 이상의 물체를 드는 작업+(12호)밀기/당기기 작업",
                        "(9호)하루에 25회 이상 10kg 이상의 물체를 무릎 아래에서 들거나, 어깨 위에서 들거나, 팔을 뻗은 상태에서 드는 작업+(12호)밀기/당기기 작업"
                    ]
                    selected_burden_force_index = burden_force_options.index(hazard_entry.get("부담작업", "")) if hazard_entry.get("부담작업", "") in burden_force_options else 0
                    hazard_entry["부담작업"] = st.selectbox(f"[{k+1}] 부담작업", burden_force_options, index=selected_burden_force_index, key=f"burden_force_{k}_{selected_작업명}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        hazard_entry["중량물 명칭"] = st.text_input(f"[{k+1}] 중량물 명칭", value=hazard_entry.get("중량물 명칭", ""), key=f"힘_중량물_명칭_{k}_{selected_작업명}")
                    with col2:
                        hazard_entry["중량물 용도"] = st.text_input(f"[{k+1}] 중량물 용도", value=hazard_entry.get("중량물 용도", ""), key=f"힘_중량물_용도_{k}_{selected_작업명}")
                    
                    # 취급방법
                    취급방법_options = ["", "직접 취급", "크레인 사용"]
                    selected_취급방법_index = 취급방법_options.index(hazard_entry.get("취급방법", "")) if hazard_entry.get("취급방법", "") in 취급방법_options else 0
                    hazard_entry["취급방법"] = st.selectbox(f"[{k+1}] 취급방법", 취급방법_options, index=selected_취급방법_index, key=f"힘_취급방법_{k}_{selected_작업명}")

                    # 중량물 이동방법 (취급방법이 "직접 취급"인 경우만 해당)
                    if hazard_entry["취급방법"] == "직접 취급":
                        이동방법_options = ["", "1인 직접이동", "2인1조 직접이동", "여러명 직접이동", "이동대차(인력이동)", "이동대차(전력이동)", "지게차"]
                        selected_이동방법_index = 이동방법_options.index(hazard_entry.get("중량물 이동방법", "")) if hazard_entry.get("중량물 이동방법", "") in 이동방법_options else 0
                        hazard_entry["중량물 이동방법"] = st.selectbox(f"[{k+1}] 중량물 이동방법", 이동방법_options, index=selected_이동방법_index, key=f"힘_이동방법_{k}_{selected_작업명}")
                        
                        # 이동대차(인력이동) 선택 시 추가 드롭다운
                        if hazard_entry["중량물 이동방법"] == "이동대차(인력이동)":
                            직접_밀당_options = ["", "작업자가 직접 바퀴달린 이동대차를 밀고/당기기", "자동이동대차(AGV)", "기타"]
                            selected_직접_밀당_index = 직접_밀당_options.index(hazard_entry.get("작업자가 직접 밀고/당기기", "")) if hazard_entry.get("작업자가 직접 밀고/당기기", "") in 직접_밀당_options else 0
                            hazard_entry["작업자가 직접 밀고/당기기"] = st.selectbox(f"[{k+1}] 작업자가 직접 밀고/당기기", 직접_밀당_options, index=selected_직접_밀당_index, key=f"힘_직접_밀당_{k}_{selected_작업명}")
                            # '기타' 선택 시 설명 적는 난 추가
                            if hazard_entry["작업자가 직접 밀고/당기기"] == "기타":
                                hazard_entry["기타_밀당_설명"] = st.text_input(f"[{k+1}] 기타 밀기/당기기 설명", value=hazard_entry.get("기타_밀당_설명", ""), key=f"힘_기타_밀당_설명_{k}_{selected_작업명}")

                    # 8호, 9호 관련 필드 (밀기/당기기가 아닌 경우)
                    if "(8호)" in hazard_entry["부담작업"] and "(12호)" not in hazard_entry["부담작업"]:
                        col1, col2 = st.columns(2)
                        with col1:
                            hazard_entry["중량물 무게(kg)"] = st.number_input(f"[{k+1}] 중량물 무게(kg)", value=hazard_entry.get("중량물 무게(kg)", 0.0), key=f"중량물_무게_{k}_{selected_작업명}")
                        with col2:
                            hazard_entry["작업시간동안 작업횟수(회/일)"] = st.text_input(f"[{k+1}] 작업시간동안 작업횟수(회/일)", value=hazard_entry.get("작업시간동안 작업횟수(회/일)", ""), key=f"힘_총횟수_{k}_{selected_작업명}")
                    
                    elif "(9호)" in hazard_entry["부담작업"] and "(12호)" not in hazard_entry["부담작업"]:
                        col1, col2 = st.columns(2)
                        with col1:
                            hazard_entry["중량물 무게(kg)"] = st.number_input(f"[{k+1}] 중량물 무게(kg)", value=hazard_entry.get("중량물 무게(kg)", 0.0), key=f"중량물_무게_{k}_{selected_작업명}")
                        with col2:
                            hazard_entry["작업시간동안 작업횟수(회/일)"] = st.text_input(f"[{k+1}] 작업시간동안 작업횟수(회/일)", value=hazard_entry.get("작업시간동안 작업횟수(회/일)", ""), key=f"힘_총횟수_{k}_{selected_작업명}")
                    
                    # 12호 밀기/당기기 관련 필드
                    if "(12호)밀기/당기기" in hazard_entry["부담작업"]:
                        st.markdown("##### (12호) 밀기/당기기 세부 정보")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            hazard_entry["대차 무게(kg)_12호"] = st.number_input(f"[{k+1}] 대차 무게(kg)", value=hazard_entry.get("대차 무게(kg)_12호", 0.0), key=f"대차_무게_12호_{k}_{selected_작업명}")
                        with col2:
                            hazard_entry["대차위 제품무게(kg)_12호"] = st.number_input(f"[{k+1}] 대차위 제품무게(kg)", value=hazard_entry.get("대차위 제품무게(kg)_12호", 0.0), key=f"대차위_제품무게_12호_{k}_{selected_작업명}")
                        with col3:
                            hazard_entry["밀고-당기기 빈도(회/일)_12호"] = st.text_input(f"[{k+1}] 밀고-당기기 빈도(회/일)", value=hazard_entry.get("밀고-당기기 빈도(회/일)_12호", ""), key=f"밀고당기기_빈도_12호_{k}_{selected_작업명}")

                elif hazard_entry["유형"] == "접촉스트레스 또는 기타(진동, 밀고 당기기 등)":
                    burden_other_options = [
                        "",
                        "(11호)하루에 총 2시간 이상 시간당 10회 이상 손 또는 무릎을 사용하여 반복적으로 충격을 가하는 작업",
                        "(12호)진동작업(그라인더, 임팩터 등)"
                    ]
                    selected_burden_other_index = burden_other_options.index(hazard_entry.get("부담작업", "")) if hazard_entry.get("부담작업", "") in burden_other_options else 0
                    hazard_entry["부담작업"] = st.selectbox(f"[{k+1}] 부담작업", burden_other_options, index=selected_burden_other_index, key=f"burden_other_{k}_{selected_작업명}")

                    if hazard_entry["부담작업"] == "(11호)하루에 총 2시간 이상 시간당 10회 이상 손 또는 무릎을 사용하여 반복적으로 충격을 가하는 작업":
                        hazard_entry["작업시간(분)"] = st.text_input(f"[{k+1}] 작업시간(분)", value=hazard_entry.get("작업시간(분)", ""), key=f"기타_작업시간_{k}_{selected_작업명}")

                    if hazard_entry["부담작업"] == "(12호)진동작업(그라인더, 임팩터 등)":
                        st.markdown("##### (12호) 진동작업 세부 정보")
                        col1, col2 = st.columns(2)
                        with col1:
                            hazard_entry["진동수공구명"] = st.text_input(f"[{k+1}] 진동수공구명", value=hazard_entry.get("진동수공구명", ""), key=f"기타_진동수공구명_{k}_{selected_작업명}")
                            hazard_entry["작업시간(분)_진동"] = st.text_input(f"[{k+1}] 작업시간(분)", value=hazard_entry.get("작업시간(분)_진동", ""), key=f"기타_작업시간_진동_{k}_{selected_작업명}")
                            hazard_entry["작업량(회/일)_진동"] = st.text_input(f"[{k+1}] 작업량(회/일)", value=hazard_entry.get("작업량(회/일)_진동", ""), key=f"기타_작업량_진동_{k}_{selected_작업명}")
                        with col2:
                            hazard_entry["진동수공구 용도"] = st.text_input(f"[{k+1}] 진동수공구 용도", value=hazard_entry.get("진동수공구 용도", ""), key=f"기타_진동수공구_용도_{k}_{selected_작업명}")
                            hazard_entry["작업빈도(초/회)_진동"] = st.text_input(f"[{k+1}] 작업빈도(초/회)", value=hazard_entry.get("작업빈도(초/회)_진동", ""), key=f"기타_작업빈도_진동_{k}_{selected_작업명}")
                            
                            지지대_options = ["", "예", "아니오"]
                            selected_지지대_index = 지지대_options.index(hazard_entry.get("수공구사용시 지지대가 있는가?", "")) if hazard_entry.get("수공구사용시 지지대가 있는가?", "") in 지지대_options else 0
                            hazard_entry["수공구사용시 지지대가 있는가?"] = st.selectbox(f"[{k+1}] 수공구사용시 지지대가 있는가?", 지지대_options, index=selected_지지대_index, key=f"기타_지지대_여부_{k}_{selected_작업명}")
                
                st.markdown("---")
