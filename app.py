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

# 자동 저장 기능 (Excel 버전) - 성능 최적화
def auto_save():
    if "last_save_time" not in st.session_state:
        st.session_state["last_save_time"] = time.time()
    
    current_time = time.time()
    # 10초마다 자동 저장으로 변경 (더 빠른 저장)
    if current_time - st.session_state["last_save_time"] > 10:
        if st.session_state.get("session_id") and st.session_state.get("workplace"):
            # 백그라운드에서 저장하여 UI 블로킹 방지
            try:
                success, _ = save_to_excel(st.session_state["session_id"], st.session_state.get("workplace"))
                if success:
                    st.session_state["last_save_time"] = current_time
                    st.session_state["last_successful_save"] = datetime.now()
                    st.session_state["save_count"] = st.session_state.get("save_count", 0) + 1
            except Exception as e:
                st.session_state["save_error"] = str(e)

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
    
    # 필터링 (새로운 컬럼명에 맞게 수정)
    if 사업장명:
        df = df[df["회사명"] == 사업장명]
    if 팀:
        df = df[df["소속"] == 팀]
    if 반:
        # 반 컬럼이 없으므로 제거
        pass
    
    # 작업명 컬럼이 있는지 확인하고 안전하게 처리
    if "작업명" in df.columns:
        작업명_목록 = df["작업명"].dropna().unique().tolist()
        # 문자열로 변환하여 반환
        return [str(item) for item in 작업명_목록 if item is not None]
    else:
        return []

# 단위작업명 목록을 가져오는 함수
def get_단위작업명_목록(작업명=None, 사업장명=None, 팀=None, 반=None):
    if st.session_state["checklist_df"].empty:
        return []
    
    df = st.session_state["checklist_df"]
    
    # 필터링 (새로운 컬럼명에 맞게 수정)
    if 사업장명:
        df = df[df["회사명"] == 사업장명]
    if 팀:
        df = df[df["소속"] == 팀]
    if 반:
        # 반 컬럼이 없으므로 제거
        pass
    if 작업명:
        df = df[df["작업명"] == 작업명]
    
    # 단위작업명 컬럼이 있는지 확인하고 안전하게 처리
    if "단위작업명" in df.columns:
        단위작업명_목록 = df["단위작업명"].dropna().unique().tolist()
        # 문자열로 변환하여 반환
        return [str(item) for item in 단위작업명_목록 if item is not None]
    else:
        return []

# 사업장명 목록을 가져오는 함수
def get_사업장명_목록():
    if st.session_state["checklist_df"].empty:
        return []
    
    df = st.session_state["checklist_df"]
    # 새로운 컬럼명에 맞게 수정
    if "회사명" in df.columns:
        사업장명_목록 = df["회사명"].dropna().unique().tolist()
        # 문자열로 변환하여 반환
        return [str(item) for item in 사업장명_목록 if item is not None]
    else:
        return []

# 팀 목록을 가져오는 함수
def get_팀_목록(사업장명=None):
    if st.session_state["checklist_df"].empty:
        return []
    
    df = st.session_state["checklist_df"]
    if 사업장명:
        df = df[df["회사명"] == 사업장명]
    
    # 새로운 컬럼명에 맞게 수정
    if "소속" in df.columns:
        팀_목록 = df["소속"].dropna().unique().tolist()
        # 문자열로 변환하여 반환
        return [str(item) for item in 팀_목록 if item is not None]
    else:
        return []

# 반 목록을 가져오는 함수 (새로운 구조에서는 사용하지 않음)
def get_반_목록(사업장명=None, 팀=None):
    # 새로운 엑셀 구조에서는 반 컬럼이 없으므로 빈 리스트 반환
    return []

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
    st.title("🔍 데이터 관리")
    
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
        st.info(f"📄 세션 ID: {st.session_state['session_id']}")
    
    # 자동 저장 상태 및 성능 정보
    if "last_successful_save" in st.session_state:
        last_save = st.session_state["last_successful_save"]
        save_count = st.session_state.get("save_count", 0)
        st.success(f"✅ 마지막 자동저장: {last_save.strftime('%H:%M:%S')} (총 {save_count}회)")
    
    if "save_error" in st.session_state:
        st.error(f"❌ 저장 오류: {st.session_state['save_error']}")
        # 오류 메시지 표시 후 삭제
        del st.session_state["save_error"]
    
    # 수동 저장 버튼
    if st.button("💾 Excel로 저장", use_container_width=True):
        if st.session_state.get("session_id") and st.session_state.get("workplace"):
            success, result = save_to_excel(st.session_state["session_id"], st.session_state.get("workplace"))
            if success:
                st.success(f"✅ Excel 파일로 저장되었습니다!\n📄 {result}")
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
    
    # Excel 파일 직접 업로드 - 성능 최적화
    st.markdown("---")
    st.markdown("### 📤 Excel 파일 업로드")
    
    # 파일 업로드 옵션
    upload_option = st.radio(
        "업로드 방식 선택",
        ["새 파일 업로드", "기존 데이터 병합", "데이터 백업 복구"],
        horizontal=True
    )
    
    uploaded_file = st.file_uploader("Excel 파일 선택", type=['xlsx'], help="새로운 엑셀 구조에 맞는 파일을 업로드하세요")
    
    if uploaded_file is not None:
        if st.button("📥 데이터 가져오기", use_container_width=True):
            with st.spinner("📊 파일을 처리하는 중..."):
                # 임시 파일로 저장
                temp_path = os.path.join(SAVE_DIR, f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                
                try:
                    if upload_option == "새 파일 업로드":
                        # 기존 데이터를 새 데이터로 교체
                        if load_from_excel(temp_path):
                            st.success("✅ Excel 파일을 성공적으로 불러왔습니다!")
                            st.session_state["data_changed"] = True
                            st.rerun()
                        else:
                            st.error("파일을 불러오는 중 오류가 발생했습니다.")
                    
                    elif upload_option == "기존 데이터 병합":
                        # 기존 데이터와 새 데이터 병합
                        new_data = pd.read_excel(temp_path)
                        if "checklist_df" in st.session_state and not st.session_state["checklist_df"].empty:
                            combined_data = pd.concat([st.session_state["checklist_df"], new_data], ignore_index=True)
                            st.session_state["checklist_df"] = combined_data
                            st.success(f"✅ 기존 {len(st.session_state['checklist_df'])}개 + 새 {len(new_data)}개 = 총 {len(combined_data)}개 데이터 병합 완료!")
                            st.session_state["data_changed"] = True
                            st.rerun()
                        else:
                            st.session_state["checklist_df"] = new_data
                            st.success("✅ 새 데이터를 성공적으로 불러왔습니다!")
                            st.session_state["data_changed"] = True
                            st.rerun()
                    
                    elif upload_option == "데이터 백업 복구":
                        # 백업 파일에서 복구
                        if load_from_excel(temp_path):
                            st.success("✅ 백업 파일에서 데이터를 성공적으로 복구했습니다!")
                            st.rerun()
                        else:
                            st.error("백업 파일 복구 중 오류가 발생했습니다.")
                
                finally:
                    # 임시 파일 삭제
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
    
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

# 자동 저장 실행 - 성능 최적화
if st.session_state.get("session_id") and st.session_state.get("workplace"):
    # 백그라운드에서 자동 저장 실행
    auto_save()
    
    # 성능 모니터링
    if "performance_start" not in st.session_state:
        st.session_state["performance_start"] = time.time()
    
    # 5분마다 성능 통계 출력
    current_time = time.time()
    if current_time - st.session_state.get("performance_start", current_time) > 300:  # 5분
        elapsed_time = current_time - st.session_state["performance_start"]
        save_count = st.session_state.get("save_count", 0)
        st.session_state["performance_start"] = current_time
        
        # 성능 통계를 사이드바에 표시
        st.sidebar.info(f"⚡ 성능 통계\n- 실행시간: {elapsed_time/60:.1f}분\n- 자동저장: {save_count}회")

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
        - 1-9열: 기본정보 (회사명, 소속, 작업명, 단위작업명, 작업내용(상세설명), 작업자 수, 작업자 이름, 작업형태, 1일 작업시간)
        - 10-21열: 부담작업체크 (부담작업_1호~부담작업_12호)
        - 22열~: 유해요인원인분석 (유형_1~5, 반복/자세/힘/기타 상세정보)
        - 마지막: 메타정보 (보호구, 작성자, 연락처, 파일명)
        
        💡 부담작업 값: O(해당), X(미해당), △(잠재위험) 또는 O, X, △
        """)
        
        uploaded_excel = st.file_uploader("엑셀 파일 선택", type=['xlsx', 'xls'])
        
        if uploaded_excel is not None:
            try:
                # 엑셀 파일 읽기 - 성능 최적화
                with st.spinner("📊 엑셀 파일을 읽는 중..."):
                    df_excel = pd.read_excel(uploaded_excel, engine='openpyxl')
                
                # 파일 크기 및 행 수 표시
                file_size = len(uploaded_excel.getvalue()) / 1024  # KB
                st.info(f"📄 파일 크기: {file_size:.1f}KB, 행 수: {len(df_excel)}개")
                
                # 새로운 엑셀 구조에 맞는 컬럼명 정의
                basic_columns = ["회사명", "소속", "작업명", "단위작업명", "작업내용(상세설명)", "작업자 수", "작업자 이름", "작업형태", "1일 작업시간"]
                burden_columns = [f"부담작업_{i}호" for i in range(1, 13)]
                
                # 유해요인 원인분석 컬럼들 (1~5번까지)
                hazard_analysis_columns = []
                for i in range(1, 6):  # 1~5번
                    hazard_analysis_columns.extend([
                        f"유해요인_원인분석_유형_{i}",
                        f"유해요인_원인분석_부담작업_{i}_반복",
                        f"유해요인_원인분석_수공구_종류_{i}",
                        f"유해요인_원인분석_수공구_용도_{i}",
                        f"유해요인_원인분석_수공구_무게(kg)_{i}",
                        f"유해요인_원인분석_수공구_사용시간(분)_{i}",
                        f"유해요인_원인분석_부담부위_{i}",
                        f"유해요인_원인분석_반복_회당시간(초/회)_{i}",
                        f"유해요인_원인분석_반복_총횟수(회/일)_{i}",
                        f"유해요인_원인분석_반복_총시간(분)_{i}",
                        f"유해요인_원인분석_반복_물체무게_10호(kg)_{i}",
                        f"유해요인_원인분석_반복_분당반복횟수_10호(회/분)_{i}",
                        f"유해요인_원인분석_반복_작업내용_12호_정적_{i}",
                        f"유해요인_원인분석_반복_작업시간_12호_정적_{i}",
                        f"유해요인_원인분석_반복_휴식시간_12호_정적_{i}",
                        f"유해요인_원인분석_반복_인체부담부위_12호_정적_{i}",
                        f"유해요인_원인분석_부담작업자세_{i}",
                        f"유해요인_원인분석_자세_회당시간(초/회)_{i}",
                        f"유해요인_원인분석_자세_총횟수(회/일)_{i}",
                        f"유해요인_원인분석_자세_총시간(분)_{i}",
                        f"유해요인_원인분석_부담작업_{i}_힘",
                        f"유해요인_원인분석_힘_중량물_명칭_{i}",
                        f"유해요인_원인분석_힘_중량물_용도_{i}",
                        f"유해요인_원인분석_중량물_무게(kg)_{i}",
                        f"유해요인_원인분석_하루8시간_중량물_횟수(회)_{i}",
                        f"유해요인_원인분석_힘_취급방법_{i}",
                        f"유해요인_원인분석_힘_이동방법_{i}",
                        f"유해요인_원인분석_힘_직접_밀당_{i}",
                        f"유해요인_원인분석_힘_기타_밀당_설명_{i}",
                        f"유해요인_원인분석_힘_총횟수(회/일)_{i}",
                        f"유해요인_원인분석_부담작업_{i}_기타",
                        f"유해요인_원인분석_기타_작업시간(분)_{i}",
                        f"유해요인_원인분석_기타_진동수공구명_{i}",
                        f"유해요인_원인분석_기타_진동수공구_용도_{i}",
                        f"유해요인_원인분석_기타_작업시간_진동_{i}",
                        f"유해요인_원인분석_기타_작업빈도_진동_{i}",
                        f"유해요인_원인분석_기타_작업량_진동_{i}",
                        f"유해요인_원인분석_기타_지지대_여부_{i}"
                    ])
                
                meta_columns = ["보호구", "작성자", "연락처", "파일명"]
                expected_columns = basic_columns + burden_columns + hazard_analysis_columns + meta_columns
                
                # 컬럼 개수가 맞는지 확인 (최소 기본정보 + 부담작업 + 메타정보)
                min_required_columns = len(basic_columns) + len(burden_columns) + len(meta_columns)
                if len(df_excel.columns) >= min_required_columns:
                    # 컬럼명 재설정
                    df_excel.columns = expected_columns[:len(df_excel.columns)]
                    
                    # 값 검증 (O(해당), △(잠재위험), X(미해당)만 허용)
                    valid_values = ["O(해당)", "△(잠재위험)", "X(미해당)"]
                    
                    # 부담작업 컬럼들만 검증 (10-21열)
                    for col in burden_columns:
                        if col in df_excel.columns:
                            # O, X, △ 값을 올바른 형식으로 변환
                            def convert_burden_value(x):
                                if pd.isna(x) or x == "":
                                    return "X(미해당)"
                                x_str = str(x).strip()
                                if x_str in ["O", "o", "O(해당)"]:
                                    return "O(해당)"
                                elif x_str in ["X", "x", "X(미해당)"]:
                                    return "X(미해당)"
                                elif x_str in ["△", "△(잠재)", "△(잠재위험)"]:
                                    return "△(잠재위험)"
                                else:
                                    return "X(미해당)"
                            
                            df_excel[col] = df_excel[col].apply(convert_burden_value)
                    
                    if st.button("✅ 데이터 적용하기", use_container_width=True):
                        with st.spinner("💾 데이터를 적용하고 저장하는 중..."):
                            # 변환된 데이터 미리보기
                            st.info("📊 변환된 부담작업 데이터 미리보기:")
                            burden_preview = df_excel[burden_columns].head(3)
                            st.dataframe(burden_preview, use_container_width=True)
                            
                            st.session_state["checklist_df"] = df_excel
                            
                            # 즉시 Excel 파일로 저장
                            if st.session_state.get("session_id") and st.session_state.get("workplace"):
                                success, _ = save_to_excel(st.session_state["session_id"], st.session_state.get("workplace"))
                                if success:
                                    st.session_state["last_save_time"] = time.time()
                                    st.session_state["last_successful_save"] = datetime.now()
                                    st.session_state["save_count"] = st.session_state.get("save_count", 0) + 1
                            
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
                    st.error(f"⚠️ 엑셀 파일의 컬럼이 {min_required_columns}개 이상이어야 합니다. (기본정보 + 부담작업체크 + 메타정보)")
                    
            except Exception as e:
                st.error(f"❌ 파일 읽기 오류: {str(e)}")
    
    # 샘플 엑셀 파일 다운로드
    with st.expander("📥 샘플 엑셀 파일 다운로드"):
        # 새로운 구조에 맞는 샘플 데이터 생성
        sample_data = pd.DataFrame({
            "회사명": ["A회사", "A회사", "A회사"],
            "소속": ["생산1팀", "생산2팀", "물류팀"],
            "작업명": ["조립작업", "포장작업", "운반작업"],
            "단위작업명": ["부품조립", "제품포장", "대차운반"],
            "작업내용(상세설명)": ["전자부품 조립작업", "완성품 포장작업", "화물 운반작업"],
            "작업자 수": [5, 3, 2],
            "작업자 이름": ["김철수, 이영희, 박민수, 정수진, 최지원", "홍길동, 김영수, 박미영", "이철수, 김미영"],
            "작업형태": ["정규직", "정규직", "정규직"],
            "1일 작업시간": [8, 8, 8],
            "부담작업_1호": ["O", "X", "X"],
            "부담작업_2호": ["X", "O", "X"],
            "부담작업_3호": ["△", "X", "O"],
            "부담작업_4호": ["X", "△", "X"],
            "부담작업_5호": ["X", "X", "O"],
            "부담작업_6호": ["X", "X", "X"],
            "부담작업_7호": ["X", "△", "X"],
            "부담작업_8호": ["X", "X", "X"],
            "부담작업_9호": ["X", "X", "X"],
            "부담작업_10호": ["X", "X", "X"],
            "부담작업_11호": ["O", "X", "△"],
            "부담작업_12호": ["X", "O", "X"],
            "보호구": ["안전장갑, 보안경", "안전장갑", "안전화, 안전장갑"],
            "작성자": ["김조사", "이조사", "박조사"],
            "연락처": ["010-1234-5678", "010-2345-6789", "010-3456-7890"],
            "파일명": ["조립작업_조사표.xlsx", "포장작업_조사표.xlsx", "운반작업_조사표.xlsx"]
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
    
    # 체크리스트 탭용 컬럼 (기본 정보만)
    checklist_columns = ["회사명", "소속", "작업명", "단위작업명"] + [f"부담작업_{i}호" for i in range(1, 13)]
    
    # 세션 상태에 저장된 데이터가 있으면 사용, 없으면 빈 데이터
    if "checklist_df" in st.session_state and not st.session_state["checklist_df"].empty:
        data = st.session_state["checklist_df"]
        
        # 기존 데이터가 이전 구조인지 확인 (사업장명, 팀, 반 컬럼이 있는지)
        if "사업장명" in data.columns or "팀" in data.columns or "반" in data.columns:
            st.warning("⚠️ 기존 데이터가 이전 구조입니다. 새로운 구조로 변환합니다.")
            # 새로운 구조로 데이터 변환 (체크리스트용 기본 정보만)
            new_data = []
            for idx, row in data.iterrows():
                new_row = {
                    "회사명": str(row.get("사업장명", st.session_state.get("workplace", ""))),
                    "소속": str(row.get("팀", "")),
                    "작업명": str(row.get("작업명", "")),
                    "단위작업명": str(row.get("단위작업명", ""))
                }
                
                # 부담작업 컬럼들 변환
                for i in range(1, 13):
                    old_col = f"{i}호"
                    new_col = f"부담작업_{i}호"
                    old_value = row.get(old_col, "X")
                    
                    # O, X, △ 값을 올바른 형식으로 변환
                    if pd.isna(old_value) or old_value == "":
                        new_row[new_col] = "X(미해당)"
                    else:
                        old_value_str = str(old_value).strip()
                        if old_value_str in ["O", "o", "O(해당)"]:
                            new_row[new_col] = "O(해당)"
                        elif old_value_str in ["X", "x", "X(미해당)"]:
                            new_row[new_col] = "X(미해당)"
                        elif old_value_str in ["△", "△(잠재)", "△(잠재위험)"]:
                            new_row[new_col] = "△(잠재위험)"
                        else:
                            new_row[new_col] = "X(미해당)"
                
                new_data.append(new_row)
            
            data = pd.DataFrame(new_data)
            st.session_state["checklist_df"] = data
            st.success("✅ 데이터가 새로운 구조로 변환되었습니다!")
            st.rerun()
        else:
            # 이미 새로운 구조인 경우, 체크리스트용 컬럼만 유지
            if all(col in data.columns for col in checklist_columns):
                data = data[checklist_columns]
            else:
                st.error("❌ 데이터 구조에 문제가 있습니다. 데이터를 리셋해주세요.")
                if st.button("🔄 데이터 리셋"):
                    초기_데이터 = []
                    for i in range(5):
                        행 = [st.session_state.get("workplace", ""), "", "", ""] + ["X(미해당)"]*12
                        초기_데이터.append(행)
                    st.session_state["checklist_df"] = pd.DataFrame(초기_데이터, columns=checklist_columns)
                    st.session_state["data_changed"] = True
                    st.rerun()
    else:
        # 새로운 빈 데이터프레임 생성 (체크리스트용)
        초기_데이터 = []
        for i in range(5):
            행 = [st.session_state.get("workplace", ""), "", "", ""] + ["X(미해당)"]*12
            초기_데이터.append(행)
        data = pd.DataFrame(초기_데이터, columns=checklist_columns)
    
    # 데이터 편집기 표시
    st.markdown("### 📝 부담작업 체크리스트 입력")
    
    # AgGrid 대신 기본 방식 사용
    ho_options = ["O(해당)", "△(잠재위험)", "X(미해당)"]
    
    # 수동으로 데이터 입력 폼 생성
    with st.form("checklist_form"):
        st.markdown("#### 새 데이터 추가")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            회사명_입력 = st.text_input("회사명", value=st.session_state.get("workplace", ""))
        with col2:
            소속_입력 = st.text_input("소속")
        with col3:
            작업명_입력 = st.text_input("작업명")
        with col4:
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
            새_행 = [회사명_입력, 소속_입력, 작업명_입력, 단위작업명_입력] + 호_선택
            새_df = pd.DataFrame([새_행], columns=checklist_columns)
            data = pd.concat([data, 새_df], ignore_index=True)
            st.session_state["checklist_df"] = data
            st.session_state["data_changed"] = True  # 데이터 변경 플래그
            st.rerun()
    
    # 현재 데이터 표시 - 성능 최적화
    if not data.empty:
        # 체크박스 상태 초기화
        if "selected_rows" not in st.session_state:
            st.session_state["selected_rows"] = set()
        
        # 데이터 표시 - 간단한 테이블 형태
        st.markdown("#### 📋 체크리스트 데이터")
        
        # 편집 가능한 데이터프레임으로 표시
        edited_data = st.data_editor(
            data, 
            use_container_width=True, 
            height=400,
            hide_index=False,  # 행 번호 표시
            column_config={
                "회사명": st.column_config.TextColumn("회사명", width="medium"),
                "소속": st.column_config.TextColumn("소속", width="medium"),
                "작업명": st.column_config.TextColumn("작업명", width="medium"),
                "단위작업명": st.column_config.TextColumn("단위작업명", width="medium"),
                **{f"부담작업_{i}호": st.column_config.SelectboxColumn(
                    f"{i}호",
                    width="small",
                    options=["O(해당)", "△(잠재위험)", "X(미해당)"],
                    required=True
                ) for i in range(1, 13)},
            },
            key="checklist_editor"
        )
        
        # 편집된 데이터를 세션 상태에 저장
        if not edited_data.equals(data):
            st.session_state["checklist_df"] = edited_data
            st.session_state["data_changed"] = True
            st.success("✅ 데이터가 업데이트되었습니다!")
            st.rerun()
        
        # 행 관리 컨트롤
        st.markdown("#### 🔧 행 관리")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            current_data = st.session_state["checklist_df"]
            max_insert = max(1, len(current_data)+1)
            insert_row_num = st.number_input("행 추가 위치", min_value=1, max_value=max_insert, value=max_insert, 
                                           help="선택한 행 번호 바로 밑에 새 행이 추가됩니다")
            if st.button("➕ 행 추가", use_container_width=True):
                # 현재 세션 상태의 데이터를 기준으로 사용
                current_data = st.session_state["checklist_df"]
                
                # 새 행 데이터 생성
                new_row = [st.session_state.get("workplace", ""), "", "", ""] + ["X(미해당)"]*12
                new_df = pd.DataFrame([new_row], columns=checklist_columns)
                
                # 선택한 위치에 행 삽입
                insert_idx = insert_row_num - 1  # 0-based index로 변환
                before_data = current_data.iloc[:insert_idx]
                after_data = current_data.iloc[insert_idx:]
                updated_data = pd.concat([before_data, new_df, after_data], ignore_index=True)
                
                st.session_state["checklist_df"] = updated_data
                st.session_state["data_changed"] = True
                st.success(f"✅ 행 {insert_row_num} 바로 밑에 새 행이 추가되었습니다!")
                st.rerun()
        
        with col2:
            max_delete = max(1, len(current_data))
            delete_row_num = st.number_input("삭제할 행 번호", min_value=1, max_value=max_delete, value=min(1, max_delete),
                                           help="선택한 행을 삭제합니다")
            if st.button("🗑️ 행 삭제", use_container_width=True):
                if len(current_data) > 1:  # 최소 1행은 유지
                    delete_idx = delete_row_num - 1
                    updated_data = current_data.drop(index=delete_idx).reset_index(drop=True)
                    st.session_state["checklist_df"] = updated_data
                    st.session_state["data_changed"] = True
                    st.success(f"✅ 행 {delete_row_num}이 삭제되었습니다!")
                    st.rerun()
                elif len(current_data) == 1:
                    st.warning("⚠️ 최소 1개의 행은 유지해야 합니다!")
                else:
                    st.warning("⚠️ 삭제할 데이터가 없습니다!")
        
        with col3:
            if st.button("📋 맨 밑에 추가", use_container_width=True):
                new_row = [st.session_state.get("workplace", ""), "", "", ""] + ["X(미해당)"]*12
                new_df = pd.DataFrame([new_row], columns=checklist_columns)
                updated_data = pd.concat([current_data, new_df], ignore_index=True)
                st.session_state["checklist_df"] = updated_data
                st.session_state["data_changed"] = True
                st.success("✅ 맨 밑에 새 행이 추가되었습니다!")
                st.rerun()
        
        with col4:
            if st.button("🔄 데이터 리셋", use_container_width=True):
                초기_데이터 = []
                for i in range(5):
                    행 = [st.session_state.get("workplace", ""), "", "", ""] + ["X(미해당)"]*12
                    초기_데이터.append(행)
                st.session_state["checklist_df"] = pd.DataFrame(초기_데이터, columns=checklist_columns)
                st.session_state["data_changed"] = True
                st.success("✅ 데이터가 리셋되었습니다!")
                st.rerun()
        
        # 편집 가이드
        st.info("💡 **편집 가이드:**\n"
               "- 셀을 클릭하여 직접 수정할 수 있습니다\n"
               "- 부담작업 컬럼은 드롭다운에서 선택하세요\n"
               "- 위의 행 관리 버튼으로 원하는 위치에 행 추가/삭제 가능합니다")
    else:
        st.info("아직 입력된 데이터가 없습니다. 위 폼을 사용하여 데이터를 추가하세요.")
    
    # 세션 상태에 저장 및 실시간 동기화
    st.session_state["checklist_df"] = data
    
    # 실시간 저장 트리거
    if st.session_state.get("data_changed", False):
        if st.session_state.get("session_id") and st.session_state.get("workplace"):
            try:
                success, _ = save_to_excel(st.session_state["session_id"], st.session_state.get("workplace"))
                if success:
                    st.session_state["last_successful_save"] = datetime.now()
                    st.session_state["save_count"] = st.session_state.get("save_count", 0) + 1
            except Exception as e:
                st.session_state["save_error"] = str(e)
        st.session_state["data_changed"] = False
    
    # 현재 등록된 작업명 표시
    작업명_목록 = get_작업명_목록()
    if 작업명_목록:
        # 문자열로 변환하여 안전하게 처리
        작업명_목록_문자열 = [str(item) for item in 작업명_목록 if item is not None]
        if 작업명_목록_문자열:
            st.info(f"📋 현재 등록된 작업: {', '.join(작업명_목록_문자열)}")
        
        # 데이터 통계
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 작업 수", len(data))
        with col2:
            st.metric("총 부담작업", sum(1 for col in data.columns if col.startswith("부담작업_") and data[col].isin(["O(해당)", "△(잠재위험)"]).any()))
        with col3:
            st.metric("총 단위작업", len(data["단위작업명"].dropna().unique()) if "단위작업명" in data.columns else 0)

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

# 헬퍼 함수: 문자열에서 숫자 추출 (단위 제거)
def parse_value(value_str, default_val=0, val_type=float):
    if pd.isna(value_str) or str(value_str).strip() == "":
        return default_val
    try:
        cleaned_value = str(value_str).replace("시간", "").replace("분", "").replace("kg", "").replace("회", "").replace("일", "").replace("/", "").replace("초", "").strip()
        return val_type(cleaned_value)
    except ValueError:
        return default_val

# 안전한 타입 변환 함수
def safe_convert(value, target_type, default_value):
    if pd.isna(value) or str(value).strip() == "":
        return default_value
    try:
        if target_type == str:
            return str(value)
        elif target_type == float:
            return float(value)
        elif target_type == int:
            return int(float(value))  # float을 거쳐서 int로 변환
        else:
            return value
    except (ValueError, TypeError):
        return default_value

# 3. 유해요인조사표 탭
with tabs[2]:
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

# 4. 작업조건조사 탭
with tabs[3]:
    st.title("작업조건조사")
    
    # 계층적 선택 구조
    col1, col2, col3 = st.columns(3)
    
    with col1:
        회사명_목록_조건 = get_사업장명_목록()
        if not 회사명_목록_조건:
            st.warning("먼저 체크리스트에 데이터를 입력하세요.")
            selected_회사명_조건 = None
        else:
            selected_회사명_조건 = st.selectbox(
                "회사명 선택",
                ["선택하세요"] + 회사명_목록_조건,
                key="작업조건_회사명"
            )
            if selected_회사명_조건 == "선택하세요":
                selected_회사명_조건 = None
    
    with col2:
        if selected_회사명_조건:
            소속_목록_조건 = get_팀_목록(selected_회사명_조건)
            selected_소속_조건 = st.selectbox(
                "소속 선택",
                ["전체"] + 소속_목록_조건,
                key="작업조건_소속"
            )
            if selected_소속_조건 == "전체":
                selected_소속_조건 = None
        else:
            st.selectbox("소속 선택", ["회사명을 먼저 선택하세요"], disabled=True, key="작업조건_소속_disabled")
            selected_소속_조건 = None
    
    with col3:
        if selected_회사명_조건:
            작업명_목록_조건 = get_작업명_목록(selected_회사명_조건, selected_소속_조건, None)
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
            st.selectbox("작업명 선택", ["회사명을 먼저 선택하세요"], disabled=True, key="작업조건_작업명_disabled")
            selected_작업명 = None
    
    if selected_작업명:
        작업명_목록 = get_작업명_목록(selected_회사명_조건, selected_소속_조건, None)
        st.info(f"📋 선택된 작업: {selected_회사명_조건} > {selected_소속_조건 or '전체'} > {selected_작업명}")
        st.info(f"📋 총 {len(작업명_목록)}개의 작업이 있습니다. 각 작업별로 1,2,3단계를 작성하세요.")
        
        # 선택된 작업에 대한 1,2,3단계
        with st.container():
            # 1단계: 유해요인 기본조사
            st.subheader(f"1단계: 유해요인 기본조사 - [{selected_작업명}]")
            
            # 엑셀에서 작업내용(상세설명) 가져오기
            작업내용_상세설명 = ""
            if not st.session_state["checklist_df"].empty:
                작업_데이터 = st.session_state["checklist_df"][
                    (st.session_state["checklist_df"]["작업명"] == selected_작업명) &
                    (st.session_state["checklist_df"]["회사명"] == selected_회사명_조건)
                ]
                if selected_소속_조건:
                    작업_데이터 = 작업_데이터[작업_데이터["소속"] == selected_소속_조건]
                
                if not 작업_데이터.empty and "작업내용(상세설명)" in 작업_데이터.columns:
                    # 첫 번째 행의 작업내용(상세설명) 사용
                    raw_value = 작업_데이터.iloc[0].get("작업내용(상세설명)", "")
                    작업내용_상세설명 = safe_convert(raw_value, str, "")
                    if 작업내용_상세설명:
                        st.success(f"✅ 작업내용 자동 로드됨")
                elif not 작업_데이터.empty:
                    st.warning("⚠️ '작업내용(상세설명)' 컬럼을 찾을 수 없습니다.")
                else:
                    st.warning("⚠️ 해당 조건에 맞는 데이터가 없습니다.")
            
            col1, col2 = st.columns(2)
            with col1:
                작업공정 = st.text_input("작업공정", value=selected_작업명, key=f"1단계_작업공정_{selected_작업명}")
            with col2:
                작업내용 = st.text_input("작업내용", value=작업내용_상세설명, key=f"1단계_작업내용_{selected_작업명}")
            
            st.markdown("---")
            
            # 2단계: 작업별 작업부하 및 작업빈도
            st.subheader(f"2단계: 작업별 작업부하 및 작업빈도 - [{selected_작업명}]")
            
            # 선택된 작업명에 해당하는 체크리스트 데이터 가져오기
            checklist_data = []
            if not st.session_state["checklist_df"].empty:
                작업_체크리스트 = st.session_state["checklist_df"][
                    (st.session_state["checklist_df"]["작업명"] == selected_작업명) &
                    (st.session_state["checklist_df"]["회사명"] == selected_회사명_조건)
                ]
                if selected_소속_조건:
                    작업_체크리스트 = 작업_체크리스트[작업_체크리스트["소속"] == selected_소속_조건]
                # 반 컬럼은 새로운 구조에서 제거됨
                
                for idx, row in 작업_체크리스트.iterrows():
                    if row["단위작업명"]:
                        부담작업호 = []
                        for i in range(1, 13):
                            if row[f"부담작업_{i}호"] == "O(해당)":
                                부담작업호.append(f"{i}호")
                            elif row[f"부담작업_{i}호"] == "△(잠재위험)":
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
                # 엑셀에서 근로자수 가져오기
                근로자수_값 = ""
                if not st.session_state["checklist_df"].empty:
                    작업_데이터 = st.session_state["checklist_df"][
                        (st.session_state["checklist_df"]["작업명"] == selected_작업명) &
                        (st.session_state["checklist_df"]["회사명"] == selected_회사명_조건)
                    ]
                    if selected_소속_조건:
                        작업_데이터 = 작업_데이터[작업_데이터["소속"] == selected_소속_조건]
                    
                    if not 작업_데이터.empty and "작업자 수" in 작업_데이터.columns:
                        # 첫 번째 행의 작업자수 사용
                        raw_value = 작업_데이터.iloc[0].get("작업자 수", "")
                        근로자수_값 = safe_convert(raw_value, str, "")
                        if 근로자수_값:
                            st.success(f"✅ 작업자수 자동 로드됨")
                    elif not 작업_데이터.empty:
                        st.warning("⚠️ '작업자 수' 컬럼을 찾을 수 없습니다.")
                    else:
                        st.warning("⚠️ 해당 조건에 맞는 데이터가 없습니다.")
                
                평가_근로자수 = st.text_input("근로자수", value=근로자수_값, key=f"3단계_근로자수_{selected_작업명}")
            
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
            
            # 작업별로 관련된 유해요인에 대한 원인분석 (새로운 구조)
            st.markdown("---")
            st.subheader(f"작업별로 관련된 유해요인에 대한 원인분석 - [{selected_작업명}]")
            
            # 원인분석 데이터 초기화 - 엑셀에서 자동 로드
            원인분석_key = f"원인분석_항목_{selected_작업명}"
            if 원인분석_key not in st.session_state:
                # 엑셀에서 해당 작업의 원인분석 데이터 가져오기
                엑셀_원인분석_데이터 = []
                
                if not st.session_state["checklist_df"].empty:
                    # 해당 작업의 데이터 필터링
                    작업_데이터 = st.session_state["checklist_df"][
                        (st.session_state["checklist_df"]["작업명"] == selected_작업명) &
                        (st.session_state["checklist_df"]["회사명"] == selected_회사명_조건)
                    ]
                    if selected_소속_조건:
                        작업_데이터 = 작업_데이터[작업_데이터["소속"] == selected_소속_조건]
                    
                    # 디버깅 정보 (자세하게)
                    if not 작업_데이터.empty:
                        원인분석_컬럼들 = [col for col in 작업_데이터.columns if "유해요인_원인분석" in col]
                        if 원인분석_컬럼들:
                            st.info(f"🔍 원인분석 관련 컬럼 {len(원인분석_컬럼들)}개 발견")
                            # 처음 몇 개 컬럼명 표시
                            st.info(f"🔍 컬럼 예시: {원인분석_컬럼들[:3]}")
                        else:
                            st.warning("⚠️ 원인분석 관련 컬럼을 찾을 수 없습니다.")
                            # 전체 컬럼명 중 일부 표시
                            전체_컬럼들 = list(작업_데이터.columns)
                            st.info(f"🔍 전체 컬럼 수: {len(전체_컬럼들)}개")
                            st.info(f"🔍 컬럼 예시: {전체_컬럼들[:10]}")
                    
                    # 각 행에서 원인분석 데이터 추출
                    st.info(f"🔍 {len(작업_데이터)}개 행에서 원인분석 데이터 검색 중...")
                    for idx, row in 작업_데이터.iterrows():
                        # 최대 5개의 원인분석 항목 확인
                        for j in range(5):
                            유형_컬럼 = f"유해요인_원인분석_유형_{j+1}"
                            # 컬럼이 존재하고 값이 있는지 확인
                            if 유형_컬럼 in row and pd.notna(row[유형_컬럼]) and str(row[유형_컬럼]).strip() != "":
                                유형_값 = str(row[유형_컬럼]).strip()
                                st.info(f"🔍 원인분석 항목 {j+1} 발견: {유형_값}")
                                
                                hazard_entry = {"유형": 유형_값}
                                
                                if hazard_entry["유형"] == "반복동작":
                                    hazard_entry["부담작업"] = safe_convert(row.get(f"유해요인_원인분석_부담작업_{j+1}_반복", ""), str, "")
                                    hazard_entry["수공구 종류"] = safe_convert(row.get(f"유해요인_원인분석_수공구_종류_{j+1}", ""), str, "")
                                    hazard_entry["수공구 용도"] = safe_convert(row.get(f"유해요인_원인분석_수공구_용도_{j+1}", ""), str, "")
                                    hazard_entry["수공구 무게(kg)"] = safe_convert(row.get(f"유해요인_원인분석_수공구_무게(kg)_{j+1}", ""), float, 0.0)
                                    hazard_entry["수공구 사용시간(분)"] = safe_convert(row.get(f"유해요인_원인분석_수공구_사용시간(분)_{j+1}", ""), str, "")
                                    hazard_entry["부담부위"] = safe_convert(row.get(f"유해요인_원인분석_부담부위_{j+1}", ""), str, "")
                                    hazard_entry["회당 반복시간(초/회)"] = safe_convert(row.get(f"유해요인_원인분석_반복_회당시간(초/회)_{j+1}", ""), str, "")
                                    hazard_entry["작업시간동안 반복횟수(회/일)"] = safe_convert(row.get(f"유해요인_원인분석_반복_총횟수(회/일)_{j+1}", ""), str, "")
                                    hazard_entry["총 작업시간(분)"] = safe_convert(row.get(f"유해요인_원인분석_반복_총시간(분)_{j+1}", ""), str, "")
                                    hazard_entry["물체 무게(kg)_10호"] = safe_convert(row.get(f"유해요인_원인분석_반복_물체무게_10호(kg)_{j+1}", ""), float, 0.0)
                                    hazard_entry["분당 반복횟수(회/분)_10호"] = safe_convert(row.get(f"유해요인_원인분석_반복_분당반복횟수_10호(회/분)_{j+1}", ""), str, "")
                                    hazard_entry["작업내용_12호_정적"] = safe_convert(row.get(f"유해요인_원인분석_반복_작업내용_12호_정적_{j+1}", ""), str, "")
                                    hazard_entry["작업시간(분)_12호_정적"] = safe_convert(row.get(f"유해요인_원인분석_반복_작업시간_12호_정적_{j+1}", ""), int, 0)
                                    hazard_entry["휴식시간(분)_12호_정적"] = safe_convert(row.get(f"유해요인_원인분석_반복_휴식시간_12호_정적_{j+1}", ""), int, 0)
                                    hazard_entry["인체부담부위_12호_정적"] = safe_convert(row.get(f"유해요인_원인분석_반복_인체부담부위_12호_정적_{j+1}", ""), str, "")
                                    
                                elif hazard_entry["유형"] == "부자연스러운 자세":
                                    hazard_entry["부담작업자세"] = safe_convert(row.get(f"유해요인_원인분석_부담작업자세_{j+1}", ""), str, "")
                                    hazard_entry["회당 반복시간(초/회)"] = safe_convert(row.get(f"유해요인_원인분석_자세_회당시간(초/회)_{j+1}", ""), str, "")
                                    hazard_entry["작업시간동안 반복횟수(회/일)"] = safe_convert(row.get(f"유해요인_원인분석_자세_총횟수(회/일)_{j+1}", ""), str, "")
                                    hazard_entry["총 작업시간(분)"] = safe_convert(row.get(f"유해요인_원인분석_자세_총시간(분)_{j+1}", ""), str, "")
                                    
                                elif hazard_entry["유형"] == "과도한 힘":
                                    hazard_entry["부담작업"] = safe_convert(row.get(f"유해요인_원인분석_부담작업_{j+1}_힘", ""), str, "")
                                    hazard_entry["중량물 명칭"] = safe_convert(row.get(f"유해요인_원인분석_힘_중량물_명칭_{j+1}", ""), str, "")
                                    hazard_entry["중량물 용도"] = safe_convert(row.get(f"유해요인_원인분석_힘_중량물_용도_{j+1}", ""), str, "")
                                    hazard_entry["중량물 무게(kg)"] = safe_convert(row.get(f"유해요인_원인분석_중량물_무게(kg)_{j+1}", ""), float, 0.0)
                                    hazard_entry["하루 8시간동안 중량물을 드는 횟수(회)"] = safe_convert(row.get(f"유해요인_원인분석_하루8시간_중량물_횟수(회)_{j+1}", ""), int, 0)
                                    hazard_entry["취급방법"] = safe_convert(row.get(f"유해요인_원인분석_힘_취급방법_{j+1}", ""), str, "")
                                    hazard_entry["중량물 이동방법"] = safe_convert(row.get(f"유해요인_원인분석_힘_이동방법_{j+1}", ""), str, "")
                                    hazard_entry["작업자가 직접 밀고/당기기"] = safe_convert(row.get(f"유해요인_원인분석_힘_직접_밀당_{j+1}", ""), str, "")
                                    hazard_entry["기타_밀당_설명"] = safe_convert(row.get(f"유해요인_원인분석_힘_기타_밀당_설명_{j+1}", ""), str, "")
                                    hazard_entry["작업시간동안 작업횟수(회/일)"] = safe_convert(row.get(f"유해요인_원인분석_힘_총횟수(회/일)_{j+1}", ""), str, "")
                                    
                                elif hazard_entry["유형"] == "접촉스트레스 또는 기타(진동, 밀고 당기기 등)":
                                    hazard_entry["부담작업"] = safe_convert(row.get(f"유해요인_원인분석_부담작업_{j+1}_기타", ""), str, "")
                                    if hazard_entry["부담작업"] == "(11호)접촉스트레스":
                                        hazard_entry["작업시간(분)"] = safe_convert(row.get(f"유해요인_원인분석_기타_작업시간(분)_{j+1}", ""), str, "")
                                    elif hazard_entry["부담작업"] == "(12호)진동작업(그라인더, 임팩터 등)":
                                        hazard_entry["진동수공구명"] = safe_convert(row.get(f"유해요인_원인분석_기타_진동수공구명_{j+1}", ""), str, "")
                                        hazard_entry["진동수공구 용도"] = safe_convert(row.get(f"유해요인_원인분석_기타_진동수공구_용도_{j+1}", ""), str, "")
                                        hazard_entry["작업시간(분)_진동"] = safe_convert(row.get(f"유해요인_원인분석_기타_작업시간_진동_{j+1}", ""), str, "")
                                        hazard_entry["작업빈도(초/회)_진동"] = safe_convert(row.get(f"유해요인_원인분석_기타_작업빈도_진동_{j+1}", ""), str, "")
                                        hazard_entry["작업량(회/일)_진동"] = safe_convert(row.get(f"유해요인_원인분석_기타_작업량_진동_{j+1}", ""), str, "")
                                        hazard_entry["수공구사용시 지지대가 있는가?"] = safe_convert(row.get(f"유해요인_원인분석_기타_지지대_여부_{j+1}", ""), str, "")
                                
                                엑셀_원인분석_데이터.append(hazard_entry)
                
                # 엑셀에서 데이터를 가져왔으면 사용, 없으면 기본값
                if 엑셀_원인분석_데이터:
                    st.session_state[원인분석_key] = 엑셀_원인분석_데이터
                    st.success(f"✅ 엑셀에서 {len(엑셀_원인분석_데이터)}개의 원인분석 항목을 자동으로 로드했습니다!")
                else:
                    st.session_state[원인분석_key] = [{"유형": "", "부담작업": "", "부담작업자세": ""}]
                    st.warning("⚠️ 엑셀에서 원인분석 데이터를 찾을 수 없습니다.")
                    st.info("💡 원인분석 데이터는 '유해요인_원인분석_유형_1', '유해요인_원인분석_유형_2' 등의 컬럼명으로 저장되어야 합니다.")
            else:
                # 이미 세션에 데이터가 있는 경우
                st.info(f"📋 기존 원인분석 데이터 사용 중 ({len(st.session_state[원인분석_key])}개 항목)")
            
            # 유해요인 원인분석 섹션
            col_hazard_title, col_hazard_add_btn = st.columns([0.8, 0.2])
            with col_hazard_title:
                st.markdown("**유해요인 원인분석**")
            with col_hazard_add_btn:
                if st.button(f"항목 추가", key=f"add_hazard_analysis_{selected_작업명}"):
                    st.session_state[원인분석_key].append({"유형": "", "부담작업": "", "부담작업자세": ""})
                    st.rerun()
            
            current_hazard_analysis_data = st.session_state[원인분석_key]
            
            # 유해요인 원인분석 항목들 처리
            for k, hazard_entry in enumerate(current_hazard_analysis_data):
                st.markdown(f"**유해요인 원인분석 항목 {k+1}**")
                
                hazard_type_options = ["", "반복동작", "부자연스러운 자세", "과도한 힘", "접촉스트레스 또는 기타(진동, 밀고 당기기 등)"]
                selected_hazard_type_index = hazard_type_options.index(hazard_entry.get("유형", "")) if hazard_entry.get("유형", "") in hazard_type_options else 0
                
                hazard_entry["유형"] = st.selectbox(
                    f"[{k+1}] 유해요인 유형 선택", 
                    hazard_type_options, 
                    index=selected_hazard_type_index, 
                    key=f"hazard_type_{k}_{selected_작업명}"
                )

                # 각 유해요인 유형별 세부 입력 필드들
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
                    
                    hazard_entry["수공구 종류"] = st.text_input(f"[{k+1}] 수공구 종류", value=hazard_entry.get("수공구 종류", ""), key=f"수공구_종류_{k}_{selected_작업명}")
                    hazard_entry["수공구 용도"] = st.text_input(f"[{k+1}] 수공구 용도", value=hazard_entry.get("수공구 용도", ""), key=f"수공구_용도_{k}_{selected_작업명}")
                    hazard_entry["수공구 무게(kg)"] = st.number_input(f"[{k+1}] 수공구 무게(kg)", value=hazard_entry.get("수공구 무게(kg)", 0.0), key=f"수공구_무게_{k}_{selected_작업명}")
                    hazard_entry["수공구 사용시간(분)"] = st.text_input(f"[{k+1}] 수공구 사용시간(분)", value=hazard_entry.get("수공구 사용시간(분)", ""), key=f"수공구_사용시간_{k}_{selected_작업명}")
                    hazard_entry["부담부위"] = st.text_input(f"[{k+1}] 부담부위", value=hazard_entry.get("부담부위", ""), key=f"부담부위_{k}_{selected_작업명}")
                    
                    # 총 작업시간 자동 계산을 위한 입력 필드
                    회당_반복시간_초_회 = st.text_input(f"[{k+1}] 회당 반복시간(초/회)", value=hazard_entry.get("회당 반복시간(초/회)", ""), key=f"반복_회당시간_{k}_{selected_작업명}")
                    작업시간동안_반복횟수_회_일 = st.text_input(f"[{k+1}] 작업시간동안 반복횟수(회/일)", value=hazard_entry.get("작업시간동안 반복횟수(회/일)", ""), key=f"반복_총횟수_{k}_{selected_작업명}")
                    
                    hazard_entry["회당 반복시간(초/회)"] = 회당_반복시간_초_회
                    hazard_entry["작업시간동안 반복횟수(회/일)"] = 작업시간동안_반복횟수_회_일

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
                        key=f"반복_총시간_{k}_{selected_작업명}"
                    )

                    # 10호 추가 필드
                    if "(10호)" in hazard_entry["부담작업"]:
                        hazard_entry["물체 무게(kg)_10호"] = st.number_input(f"[{k+1}] (10호)물체 무게(kg)", value=hazard_entry.get("물체 무게(kg)_10호", 0.0), key=f"물체_무게_10호_{k}_{selected_작업명}")
                        hazard_entry["분당 반복횟수(회/분)_10호"] = st.text_input(f"[{k+1}] (10호)분당 반복횟수(회/분)", value=hazard_entry.get("분당 반복횟수(회/분)_10호", ""), key=f"분당_반복횟수_10호_{k}_{selected_작업명}")
                    else:
                        hazard_entry["물체 무게(kg)_10호"] = 0.0
                        hazard_entry["분당 반복횟수(회/분)_10호"] = ""

                    # 12호 정적자세 관련 필드
                    if "(12호)정적자세" in hazard_entry["부담작업"]:
                        hazard_entry["작업내용_12호_정적"] = st.text_input(f"[{k+1}] (정적자세)작업내용", value=hazard_entry.get("작업내용_12호_정적", ""), key=f"반복_작업내용_12호_정적_{k}_{selected_작업명}")
                        hazard_entry["작업시간(분)_12호_정적"] = st.number_input(f"[{k+1}] (정적자세)작업시간(분)", value=hazard_entry.get("작업시간(분)_12호_정적", 0), key=f"반복_작업시간_12호_정적_{k}_{selected_작업명}")
                        hazard_entry["휴식시간(분)_12호_정적"] = st.number_input(f"[{k+1}] (정적자세)휴식시간(분)", value=hazard_entry.get("휴식시간(분)_12호_정적", 0), key=f"반복_휴식시간_12호_정적_{k}_{selected_작업명}")
                        hazard_entry["인체부담부위_12호_정적"] = st.text_input(f"[{k+1}] (정적자세)인체부담부위", value=hazard_entry.get("인체부담부위_12호_정적", ""), key=f"반복_인체부담부위_12호_정적_{k}_{selected_작업명}")
                    else:
                        hazard_entry["작업내용_12호_정적"] = ""
                        hazard_entry["작업시간(분)_12호_정적"] = 0
                        hazard_entry["휴식시간(분)_12호_정적"] = 0
                        hazard_entry["인체부담부위_12호_정적"] = ""

                elif hazard_entry["유형"] == "부자연스러운 자세":
                    burden_pose_options = [
                        "",
                        "(3호)하루에 총 2시간 이상 머리 위에 손이 있거나, 팔꿈치가 어깨위에 있거나, 팔꿈치를 몸통으로부터 들거나, 팔꿈치를 몸통뒤쪽에 위치하도록 하는 상태에서 이루어지는 작업",
                        "(4호)지지되지 않은 상태이거나 임의로 자세를 바꿀 수 없는 조건에서, 하루에 총 2시간 이상 목이나 허리를 구부리거나 트는 상태에서 이루어지는 작업",
                        "(5호)하루에 총 2시간 이상 쪼그리고 앉거나 무릎을 굽힌 자세에서 이루어지는 작업"
                    ]
                    selected_burden_pose_index = burden_pose_options.index(hazard_entry.get("부담작업자세", "")) if hazard_entry.get("부담작업자세", "") in burden_pose_options else 0
                    hazard_entry["부담작업자세"] = st.selectbox(f"[{k+1}] 부담작업자세", burden_pose_options, index=selected_burden_pose_index, key=f"burden_pose_{k}_{selected_작업명}")
                    
                    hazard_entry["회당 반복시간(초/회)"] = st.text_input(f"[{k+1}] 회당 반복시간(초/회)", value=hazard_entry.get("회당 반복시간(초/회)", ""), key=f"자세_회당시간_{k}_{selected_작업명}")
                    hazard_entry["작업시간동안 반복횟수(회/일)"] = st.text_input(f"[{k+1}] 작업시간동안 반복횟수(회/일)", value=hazard_entry.get("작업시간동안 반복횟수(회/일)", ""), key=f"자세_총횟수_{k}_{selected_작업명}")
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
                    
                    hazard_entry["중량물 명칭"] = st.text_input(f"[{k+1}] 중량물 명칭", value=hazard_entry.get("중량물 명칭", ""), key=f"힘_중량물_명칭_{k}_{selected_작업명}")
                    hazard_entry["중량물 용도"] = st.text_input(f"[{k+1}] 중량물 용도", value=hazard_entry.get("중량물 용도", ""), key=f"힘_중량물_용도_{k}_{selected_작업명}")
                    hazard_entry["중량물 무게(kg)"] = st.number_input(f"[{k+1}] 중량물 무게(kg)", value=hazard_entry.get("중량물 무게(kg)", 0.0), key=f"중량물_무게_기본_{k}_{selected_작업명}")
                    hazard_entry["하루 8시간동안 중량물을 드는 횟수(회)"] = st.number_input(f"[{k+1}] 하루 8시간동안 중량물을 드는 횟수(회)", value=hazard_entry.get("하루 8시간동안 중량물을 드는 횟수(회)", 0), min_value=0, step=1, key=f"중량물_횟수_{k}_{selected_작업명}")
                    
                    취급방법_options = ["", "직접 취급", "크레인 사용"]
                    selected_취급방법_index = 취급방법_options.index(hazard_entry.get("취급방법", "")) if hazard_entry.get("취급방법", "") in 취급방법_options else 0
                    hazard_entry["취급방법"] = st.selectbox(f"[{k+1}] 취급방법", 취급방법_options, index=selected_취급방법_index, key=f"힘_취급방법_{k}_{selected_작업명}")

                    if hazard_entry["취급방법"] == "직접 취급":
                        이동방법_options = ["", "1인 직접이동", "2인1조 직접이동", "여러명 직접이동", "이동대차(인력이동)", "이동대차(전력이동)", "지게차"]
                        selected_이동방법_index = 이동방법_options.index(hazard_entry.get("중량물 이동방법", "")) if hazard_entry.get("중량물 이동방법", "") in 이동방법_options else 0
                        hazard_entry["중량물 이동방법"] = st.selectbox(f"[{k+1}] 중량물 이동방법", 이동방법_options, index=selected_이동방법_index, key=f"힘_이동방법_{k}_{selected_작업명}")
                        
                        if hazard_entry["중량물 이동방법"] == "이동대차(인력이동)":
                            직접_밀당_options = ["", "작업자가 직접 바퀴달린 이동대차를 밀고/당기기", "자동이동대차(AGV)", "기타"]
                            selected_직접_밀당_index = 직접_밀당_options.index(hazard_entry.get("작업자가 직접 밀고/당기기", "")) if hazard_entry.get("작업자가 직접 밀고/당기기", "") in 직접_밀당_options else 0
                            hazard_entry["작업자가 직접 밀고/당기기"] = st.selectbox(f"[{k+1}] 작업자가 직접 밀고/당기기", 직접_밀당_options, index=selected_직접_밀당_index, key=f"힘_직접_밀당_{k}_{selected_작업명}")
                            
                            if hazard_entry["작업자가 직접 밀고/당기기"] == "기타":
                                hazard_entry["기타_밀당_설명"] = st.text_input(f"[{k+1}] 기타 밀기/당기기 설명", value=hazard_entry.get("기타_밀당_설명", ""), key=f"힘_기타_밀당_설명_{k}_{selected_작업명}")
                            else:
                                hazard_entry["기타_밀당_설명"] = ""
                        else:
                            hazard_entry["작업자가 직접 밀고/당기기"] = ""
                            hazard_entry["기타_밀당_설명"] = ""
                    else:
                        hazard_entry["중량물 이동방법"] = ""
                        hazard_entry["작업자가 직접 밀고/당기기"] = ""
                        hazard_entry["기타_밀당_설명"] = ""

                    if "(12호)밀기/당기기 작업" not in hazard_entry["부담작업"]:
                        # 밀기/당기기 작업이 아닌 경우에만 기존 필드들 숨김 처리 (이미 위에서 입력받음)
                        pass
                    else:
                        # 밀기/당기기 작업 선택 시 중량물 관련 필드들 초기화
                        hazard_entry["중량물 무게(kg)"] = 0.0
                        hazard_entry["하루 8시간동안 중량물을 드는 횟수(회)"] = 0

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
                    else:
                        hazard_entry["작업시간(분)"] = ""

                    if hazard_entry["부담작업"] == "(12호)진동작업(그라인더, 임팩터 등)":
                        st.markdown("**(12호) 세부 유형에 대한 추가 정보 (선택적 입력)**")
                        hazard_entry["진동수공구명"] = st.text_input(f"[{k+1}] 진동수공구명", value=hazard_entry.get("진동수공구명", ""), key=f"기타_진동수공구명_{k}_{selected_작업명}")
                        hazard_entry["진동수공구 용도"] = st.text_input(f"[{k+1}] 진동수공구 용도", value=hazard_entry.get("진동수공구 용도", ""), key=f"기타_진동수공구_용도_{k}_{selected_작업명}")
                        hazard_entry["작업시간(분)_진동"] = st.text_input(f"[{k+1}] 작업시간(분)", value=hazard_entry.get("작업시간(분)_진동", ""), key=f"기타_작업시간_진동_{k}_{selected_작업명}")
                        hazard_entry["작업빈도(초/회)_진동"] = st.text_input(f"[{k+1}] 작업빈도(초/회)", value=hazard_entry.get("작업빈도(초/회)_진동", ""), key=f"기타_작업빈도_진동_{k}_{selected_작업명}")
                        hazard_entry["작업량(회/일)_진동"] = st.text_input(f"[{k+1}] 작업량(회/일)", value=hazard_entry.get("작업량(회/일)_진동", ""), key=f"기타_작업량_진동_{k}_{selected_작업명}")
                        
                        지지대_options = ["", "예", "아니오"]
                        selected_지지대_index = 지지대_options.index(hazard_entry.get("수공구사용시 지지대가 있는가?", "")) if hazard_entry.get("수공구사용시 지지대가 있는가?", "") in 지지대_options else 0
                        hazard_entry["수공구사용시 지지대가 있는가?"] = st.selectbox(f"[{k+1}] 수공구사용시 지지대가 있는가?", 지지대_options, index=selected_지지대_index, key=f"기타_지지대_여부_{k}_{selected_작업명}")
                    else:
                        hazard_entry["작업시간(분)"] = ""
                        hazard_entry["진동수공구명"] = ""
                        hazard_entry["진동수공구 용도"] = ""
                        hazard_entry["작업시간(분)_진동"] = ""
                        hazard_entry["작업빈도(초/회)_진동"] = ""
                        hazard_entry["작업량(회/일)_진동"] = ""
                        hazard_entry["수공구사용시 지지대가 있는가?"] = ""
                
                # 현재 항목의 변경사항을 세션 상태에 반영
                st.session_state[원인분석_key][k] = hazard_entry

                # 삭제 버튼 (첫 번째 항목은 삭제 불가)
                if k > 0 or len(current_hazard_analysis_data) > 1:
                    col_delete_btn, _ = st.columns([0.2, 0.8])
                    with col_delete_btn:
                        if st.button(f"[{k+1}] 항목 삭제", key=f"delete_hazard_analysis_{k}_{selected_작업명}"):
                            st.session_state[원인분석_key].pop(k)
                            st.rerun()

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

# 5. 정밀조사 탭
with tabs[4]:
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

# 6. 증상조사 분석 탭
with tabs[5]:
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

# 7. 작업환경개선계획서 탭
with tabs[6]:
    st.title("작업환경개선계획서")
    
    if "개선계획_data" not in st.session_state:
        st.session_state["개선계획_data"] = pd.DataFrame({
            "작업공정": [""],
            "단위작업": [""],
            "유해요인": [""],
            "개선대책": [""],
            "추진일정": [""],
            "소요예산": [""],
            "담당자": [""],
            "비고": [""]
        })
    
    st.markdown("### 개선계획 입력")
    
    개선계획_data = st.data_editor(
        st.session_state["개선계획_data"],
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "작업공정": st.column_config.TextColumn("작업공정", width="medium"),
            "단위작업": st.column_config.TextColumn("단위작업", width="medium"),
            "유해요인": st.column_config.TextColumn("유해요인", width="large"),
            "개선대책": st.column_config.TextColumn("개선대책", width="large"),
            "추진일정": st.column_config.TextColumn("추진일정", width="small"),
            "소요예산": st.column_config.TextColumn("소요예산", width="small"),
            "담당자": st.column_config.TextColumn("담당자", width="small"),
            "비고": st.column_config.TextColumn("비고", width="medium"),
        },
        key="개선계획_editor"
    )
    
    st.session_state["개선계획_data"] = 개선계획_data
    st.session_state["개선계획_data_저장"] = 개선계획_data.copy()
    
    # PDF 생성 기능
    if PDF_AVAILABLE:
        st.markdown("---")
        st.subheader("📄 보고서 생성")
        
        if st.button("📑 PDF 보고서 생성", use_container_width=True):
            try:
                # PDF 생성 로직
                pdf_buffer = BytesIO()
                
                # 한글 폰트 설정 (필요시)
                # pdfmetrics.registerFont(TTFont('NanumGothic', 'NanumGothic.ttf'))
                
                doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
                story = []
                styles = getSampleStyleSheet()
                
                # 제목 스타일
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=24,
                    textColor=colors.HexColor('#1f77b4'),
                    spaceAfter=30,
                    alignment=TA_CENTER
                )
                
                # 제목 추가
                story.append(Paragraph("근골격계 유해요인조사 보고서", title_style))
                story.append(Spacer(1, 20))
                
                # 사업장 정보
                사업장_정보 = f"""
                <b>사업장명:</b> {st.session_state.get('사업장명', '')}<br/>
                <b>소재지:</b> {st.session_state.get('소재지', '')}<br/>
                <b>업종:</b> {st.session_state.get('업종', '')}<br/>
                <b>조사일:</b> {st.session_state.get('본조사', '')}<br/>
                """
                story.append(Paragraph(사업장_정보, styles['Normal']))
                story.append(Spacer(1, 20))
                
                # 개선계획 테이블
                if not 개선계획_data.empty:
                    story.append(Paragraph("작업환경개선계획", styles['Heading2']))
                    
                    # 테이블 데이터 준비
                    table_data = [list(개선계획_data.columns)]
                    for idx, row in 개선계획_data.iterrows():
                        table_data.append(list(row))
                    
                    # 테이블 생성
                    t = Table(table_data)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(t)
                
                # PDF 생성
                doc.build(story)
                pdf_buffer.seek(0)
                
                # 다운로드 버튼
                st.download_button(
                    label="📥 PDF 다운로드",
                    data=pdf_buffer,
                    file_name=f"근골격계유해요인조사보고서_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
                
                st.success("✅ PDF 보고서가 생성되었습니다!")
                
            except Exception as e:
                st.error(f"PDF 생성 중 오류 발생: {str(e)}")
    else:
        st.info("📌 PDF 생성 기능을 사용하려면 reportlab 라이브러리를 설치하세요: pip install reportlab")

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
