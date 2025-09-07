import streamlit as st
import pandas as pd
import time
from datetime import datetime
import os

# 저장 디렉토리
SAVE_DIR = "saved_sessions"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

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

def safe_convert(value, target_type, default_value):
    """안전한 타입 변환 함수"""
    if pd.isna(value) or str(value).strip() == "":
        return default_value
    try:
        if target_type == str:
            return str(value)
        elif target_type == float:
            return float(value)
        elif target_type == int:
            return int(float(value))
        else:
            return value
    except (ValueError, TypeError):
        return default_value

def extract_number(value):
    """작업부하와 작업빈도에서 숫자 추출하는 함수"""
    if value and "(" in value and ")" in value:
        return int(value.split("(")[1].split(")")[0])
    return 0

def calculate_total_score(row):
    """총점 계산 함수"""
    부하값 = extract_number(row["작업부하(A)"])
    빈도값 = extract_number(row["작업빈도(B)"])
    return 부하값 * 빈도값

def auto_save():
    """자동 저장 기능"""
    if "last_save_time" not in st.session_state:
        st.session_state["last_save_time"] = time.time()
    
    current_time = time.time()
    # 10초마다 자동 저장
    if current_time - st.session_state["last_save_time"] > 10:
        if st.session_state.get("session_id") and st.session_state.get("workplace"):
            try:
                from data_manager import save_to_excel
                success, _ = save_to_excel(st.session_state["session_id"], st.session_state.get("workplace"))
                if success:
                    st.session_state["last_save_time"] = current_time
                    st.session_state["last_successful_save"] = datetime.now()
                    st.session_state["save_count"] = st.session_state.get("save_count", 0) + 1
            except Exception as e:
                st.session_state["save_error"] = str(e)

def get_saved_sessions():
    """저장된 Excel 세션 파일 목록 반환"""
    sessions = []
    if os.path.exists(SAVE_DIR):
        for filename in os.listdir(SAVE_DIR):
            if filename.endswith('.xlsx'):
                filepath = os.path.join(SAVE_DIR, filename)
                try:
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

# 작업명 목록 관련 함수들
def get_사업장명_목록():
    if st.session_state["checklist_df"].empty:
        return []
    
    df = st.session_state["checklist_df"]
    if "회사명" in df.columns:
        사업장명_목록 = df["회사명"].dropna().unique().tolist()
        return [str(item) for item in 사업장명_목록 if item is not None]
    else:
        return []

def get_팀_목록(사업장명=None):
    if st.session_state["checklist_df"].empty:
        return []
    
    df = st.session_state["checklist_df"]
    if 사업장명:
        df = df[df["회사명"] == 사업장명]
    
    if "소속" in df.columns:
        팀_목록 = df["소속"].dropna().unique().tolist()
        return [str(item) for item in 팀_목록 if item is not None]
    else:
        return []

def get_작업명_목록(사업장명=None, 팀=None, 반=None):
    if st.session_state["checklist_df"].empty:
        return []
    
    df = st.session_state["checklist_df"]
    
    if 사업장명:
        df = df[df["회사명"] == 사업장명]
    if 팀:
        df = df[df["소속"] == 팀]
    
    if "작업명" in df.columns:
        작업명_목록 = df["작업명"].dropna().unique().tolist()
        return [str(item) for item in 작업명_목록 if item is not None]
    else:
        return []

def get_단위작업명_목록(작업명=None, 사업장명=None, 팀=None, 반=None):
    if st.session_state["checklist_df"].empty:
        return []
    
    df = st.session_state["checklist_df"]
    
    if 사업장명:
        df = df[df["회사명"] == 사업장명]
    if 팀:
        df = df[df["소속"] == 팀]
    if 작업명:
        df = df[df["작업명"] == 작업명]
    
    if "단위작업명" in df.columns:
        단위작업명_목록 = df["단위작업명"].dropna().unique().tolist()
        return [str(item) for item in 단위작업명_목록 if item is not None]
    else:
        return []

# 부담작업 설명 (전역 변수)
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