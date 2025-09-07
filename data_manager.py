import streamlit as st
import pandas as pd
import os
from datetime import datetime
from utils import SAVE_DIR, get_작업명_목록

def save_to_excel(session_id, workplace):
    """현재 세션 상태의 모든 데이터를 Excel 파일로 저장합니다."""
    if not session_id or not workplace:
        return False, "세션 ID 또는 작업장 정보가 없습니다."

    filepath = os.path.join(SAVE_DIR, f"{session_id}.xlsx")
    
    try:
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            all_keys = list(st.session_state.keys())

            # --- 탭 1: 사업장 개요 ---
            overview_data = {
                "분류": ["사업장명", "소재지", "업종", "예비조사일", "수행기관", "본조사일", "성명"],
                "내용": [
                    st.session_state.get("사업장명", ""),
                    st.session_state.get("소재지", ""),
                    st.session_state.get("업종", ""),
                    st.session_state.get("예비조사", ""),
                    st.session_state.get("수행기관", ""),
                    st.session_state.get("본조사", ""),
                    st.session_state.get("성명", "")
                ]
            }
            pd.DataFrame(overview_data).to_excel(writer, sheet_name="1_사업장개요", index=False)

            # --- 탭 2: 체크리스트 ---
            if "checklist_df" in st.session_state and not st.session_state["checklist_df"].empty:
                st.session_state["checklist_df"].to_excel(writer, sheet_name="2_체크리스트", index=False)

            # --- 탭 3 & 4 & 5: 작업별 상세 데이터 ---
            작업명_목록 = get_작업명_목록()
            if not 작업명_목록: # 체크리스트에 작업이 없을 경우를 대비
                작업명_목록 = []

            for 작업명 in 작업명_목록:
                # 시트 이름은 31자 제한이 있으므로 작업명 일부만 사용
                safe_sheet_name = 작업명.replace("/", "_").replace("\\", "_")[:25]

                # --- 탭 3: 유해요인조사표 ---
                hazard_data = {
                    "항목": ["조사일시", "조사자", "부서명", "작업공정명", "작업명"],
                    "내용": [
                        st.session_state.get(f"조사일시_{작업명}", ""),
                        st.session_state.get(f"조사자_{작업명}", ""),
                        st.session_state.get(f"부서명_{작업명}", ""),
                        st.session_state.get(f"작업공정명_{작업명}", ""),
                        st.session_state.get(f"작업명_{작업명}", "")
                    ]
                }
                pd.DataFrame(hazard_data).to_excel(writer, sheet_name=f"3_{safe_sheet_name}_유해요인", index=False)
                
                # --- 탭 4: 작업조건조사 ---
                # 1단계, 3단계 정보
                work_cond_data = {
                     "항목": ["(1단계)작업공정", "(1단계)작업내용", "(3단계)작업명", "(3단계)근로자수"],
                     "내용": [
                         st.session_state.get(f"1단계_작업공정_{작업명}", ""),
                         st.session_state.get(f"1단계_작업내용_{작업명}", ""),
                         st.session_state.get(f"3단계_작업명_{작업명}", ""),
                         st.session_state.get(f"3단계_근로자수_{작업명}", "")
                     ]
                }
                pd.DataFrame(work_cond_data).to_excel(writer, sheet_name=f"4_{safe_sheet_name}_작업조건", index=False, startrow=0)
                
                # 2단계 데이터 (DataFrame)
                if f"작업조건_data_{작업명}" in st.session_state:
                    df_work_cond = st.session_state[f"작업조건_data_{작업명}"]
                    df_work_cond.to_excel(writer, sheet_name=f"4_{safe_sheet_name}_작업조건", index=False, startrow=len(work_cond_data)+2)

                # 원인분석 데이터
                if f"원인분석_항목_{작업명}" in st.session_state:
                    df_analysis = pd.DataFrame(st.session_state[f"원인분석_항목_{작업명}"])
                    df_analysis.to_excel(writer, sheet_name=f"4_{safe_sheet_name}_원인분석", index=False)
            
            # (기타 탭 데이터 추가 영역)
            # tab5_detailed_investigation, tab6_symptom_analysis, tab7_improvement_plan 관련 데이터가 
            # st.session_state에 저장된다면 여기에 유사한 로직으로 추가할 수 있습니다.

        return True, filepath
    except Exception as e:
        return False, str(e)


def load_from_excel(filepath):
    """Excel 파일에서 데이터를 불러와 세션 상태를 복원합니다."""
    try:
        xls = pd.ExcelFile(filepath)
        
        # 1. 사업장개요
        if "1_사업장개요" in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name="1_사업장개요")
            # key-value 쌍으로 st.session_state에 저장
            # 예: st.session_state["사업장명"] = "A사업장"
            for _, row in df.iterrows():
                if pd.notna(row["분류"]) and pd.notna(row["내용"]):
                     # overview 탭의 key값으로 저장
                    if row["분류"] == "예비조사일": st.session_state["예비조사"] = row["내용"]
                    elif row["분류"] == "본조사일": st.session_state["본조사"] = row["내용"]
                    else: st.session_state[row["분류"]] = row["내용"]
        
        # 2. 체크리스트
        if "2_체크리스트" in xls.sheet_names:
            st.session_state["checklist_df"] = pd.read_excel(xls, sheet_name="2_체크리스트")
        else:
            st.session_state["checklist_df"] = pd.DataFrame()

        # 3, 4, 5. 작업별 데이터
        for sheet_name in xls.sheet_names:
            if sheet_name.startswith("3_"):
                df = pd.read_excel(xls, sheet_name=sheet_name)
                작업명 = sheet_name.split("_")[1]
                for _, row in df.iterrows():
                    key_suffix = row['항목'].replace(" ", "_") # "조사 일시" -> "조사_일시"
                    state_key = f"{key_suffix}_{작업명}"
                    st.session_state[state_key] = row['내용']
            
            elif sheet_name.startswith("4_") and "작업조건" in sheet_name:
                 # 작업조건조사 데이터 로드 로직 (필요시 상세 구현)
                pass
            
            elif sheet_name.startswith("4_") and "원인분석" in sheet_name:
                작업명 = sheet_name.split("_")[1]
                df_analysis = pd.read_excel(xls, sheet_name=sheet_name)
                st.session_state[f"원인분석_항목_{작업명}"] = df_analysis.to_dict('records')

        return True
    except Exception as e:
        st.error(f"파일 로딩 중 오류 발생: {e}")
        return False