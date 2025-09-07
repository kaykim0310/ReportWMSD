import streamlit as st
import pandas as pd
from io import BytesIO
from utils import safe_convert
import time
from datetime import datetime

def render_checklist_tab():
    """근골격계 부담작업 체크리스트 탭 렌더링"""
    st.subheader("근골격계 부담작업 체크리스트")
    
    # 엑셀 파일 업로드 기능
    with st.expander("📤 엑셀 파일 업로드"):
        st.info("""
        📌 **엑셀 파일 양식 가이드:**
        - **필수 컬럼:** `회사명`, `소속`, `작업명`, `단위작업명`, `작업내용(상세설명)`, `작업자 수`, `작업자 이름`, `작업형태`, `1일 작업시간`, `부담작업_1호` ~ `부담작업_12호`가 반드시 포함되어야 합니다.
        - **선택 컬럼:** 유해요인 원인분석, 보호구, 작성자 등 관련 데이터를 추가할 수 있습니다.
        - **부담작업 값:** `O(해당)`, `X(미해당)`, `△(잠재위험)` 또는 `O`, `X`, `△`로 입력해주세요. (자동으로 변환됩니다)
        
        💡 샘플 엑셀 파일을 다운로드하여 양식을 확인하세요.
        """)
        
        uploaded_excel = st.file_uploader("엑셀 파일 선택", type=['xlsx', 'xls'])
        
        if uploaded_excel is not None:
            try:
                # 엑셀 파일 읽기
                with st.spinner("📊 엑셀 파일을 읽는 중..."):
                    df_excel = pd.read_excel(uploaded_excel, engine='openpyxl')
                
                # 파일 정보 표시
                file_size = len(uploaded_excel.getvalue()) / 1024  # KB
                st.info(f"📄 파일 크기: {file_size:.1f}KB, 행 수: {len(df_excel)}개")

                # --- 여기부터 수정된 부분 ---

                # 1. 필수 컬럼 목록 정의
                required_columns = [
                    "회사명", "소속", "작업명", "단위작업명", "작업내용(상세설명)", 
                    "작업자 수", "작업자 이름", "작업형태", "1일 작업시간"
                ] + [f"부담작업_{i}호" for i in range(1, 13)]

                # 2. 업로드된 파일에 필수 컬럼이 모두 있는지 확인
                actual_columns = df_excel.columns.tolist()
                missing_columns = [col for col in required_columns if col not in actual_columns]

                if missing_columns:
                    # 필수 컬럼이 없으면 에러 메시지 표시
                    st.error(f"❌ 엑셀 파일에 필수 컬럼이 누락되었습니다: **{', '.join(missing_columns)}**")
                    st.warning("📥 샘플 엑셀 파일을 다운로드하여 양식을 확인해주세요.")
                else:
                    # 3. 필수 컬럼이 모두 있으면 데이터 처리 진행
                    st.success("✅ 필수 컬럼이 모두 확인되었습니다. 데이터 처리를 진행합니다.")
                    
                    # 부담작업 컬럼 값 변환 (O, X, △ -> O(해당), X(미해당), △(잠재위험))
                    burden_columns = [f"부담작업_{i}호" for i in range(1, 13)]
                    for col in burden_columns:
                        if col in df_excel.columns:
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
                    
                    # 미리보기
                    st.markdown("#### 📋 데이터 미리보기 (상위 20개)")
                    st.dataframe(df_excel.head(20))
                    
                    if st.button("✅ 데이터 적용하기", use_container_width=True):
                        with st.spinner("💾 데이터를 적용하고 저장하는 중..."):
                            st.session_state["checklist_df"] = df_excel
                            
                            # 즉시 Excel 파일로 저장
                            if st.session_state.get("session_id") and st.session_state.get("workplace"):
                                from data_manager import save_to_excel
                                success, _ = save_to_excel(st.session_state["session_id"], st.session_state.get("workplace"))
                                if success:
                                    st.session_state["last_save_time"] = time.time()
                                    st.session_state["last_successful_save"] = datetime.now()
                                    st.session_state["save_count"] = st.session_state.get("save_count", 0) + 1
                            
                            st.success("✅ 엑셀 데이터를 성공적으로 불러오고 저장했습니다!")
                            st.rerun()

            except Exception as e:
                st.error(f"❌ 파일 읽기 오류: {str(e)}")

    # --- 수정된 부분 끝 ---
    
    # 샘플 엑셀 파일 다운로드
    with st.expander("📥 샘플 엑셀 파일 다운로드"):
        # 샘플 데이터 생성 (필수 컬럼 포함)
        sample_data = pd.DataFrame({
            "회사명": ["A회사", "A회사"],
            "소속": ["생산1팀", "물류팀"],
            "작업명": ["조립작업", "운반작업"],
            "단위작업명": ["부품조립", "대차운반"],
            "작업내용(상세설명)": ["전자부품 조립", "화물 운반"],
            "작업자 수": [5, 2],
            "작업자 이름": ["김철수 외 4명", "이철수, 김미영"],
            "작업형태": ["정규직", "정규직"],
            "1일 작업시간": [8, 8],
            **{f"부담작업_{i}호": ["X", "O"] if i % 2 == 0 else ["O", "X"] for i in range(1, 13)},
            "보호구": ["안전장갑", "안전화"], # 선택 컬럼 예시
            "작성자": ["김조사", "박조사"] # 선택 컬럼 예시
        })
        
        st.markdown("##### 샘플 데이터 구조:")
        st.dataframe(sample_data, use_container_width=True)
        
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
    
    # 체크리스트 테이블용 컬럼 (기본 정보만)
    checklist_columns = ["회사명", "소속", "작업명", "단위작업명"] + [f"부담작업_{i}호" for i in range(1, 13)]
    
    # 세션 상태에 저장된 데이터가 있으면 사용, 없으면 빈 데이터
    if "checklist_df" in st.session_state and not st.session_state["checklist_df"].empty:
        data = st.session_state["checklist_df"]
    else:
        # 새로운 빈 데이터프레임 생성
        초기_데이터 = []
        for i in range(5):
            행 = [st.session_state.get("workplace", ""), "", "", ""] + ["X(미해당)"]*12
            초기_데이터.append(행)
        data = pd.DataFrame(초기_데이터, columns=checklist_columns)

    # 데이터 편집기 표시
    st.markdown("### 📝 부담작업 체크리스트 입력/수정")

    # 표시할 데이터 (전체 데이터에서 체크리스트에 필요한 컬럼만 선택)
    display_data = data[checklist_columns].copy()

    # 편집 가능한 데이터프레임으로 표시
    edited_data = st.data_editor(
        display_data, 
        num_rows="dynamic",
        use_container_width=True, 
        height=400,
        hide_index=True,
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
    if not edited_data.equals(display_data):
        # 원본 데이터에 변경사항 병합 (다른 탭의 데이터 유지를 위해)
        updated_df = st.session_state["checklist_df"].copy()
        
        # 행 개수가 달라졌을 경우 처리
        if len(edited_data) > len(updated_df): # 행 추가
            new_rows = edited_data.iloc[len(updated_df):]
            updated_df = pd.concat([updated_df, new_rows], ignore_index=True)
        elif len(edited_data) < len(updated_df): # 행 삭제
            updated_df = updated_df.iloc[:len(edited_data)]

        # 내용 변경
        for col in checklist_columns:
            if col in updated_df.columns:
                updated_df[col] = edited_data[col]

        st.session_state["checklist_df"] = updated_df
        st.session_state["data_changed"] = True
        st.success("✅ 데이터가 업데이트되었습니다!")
        st.rerun()

    # 편집 가이드
    st.info("💡 **편집 가이드:** 셀을 클릭하여 직접 수정하거나, 표 하단의 `+` 버튼으로 행을 추가할 수 있습니다.")

    # 세션 상태에 저장 및 실시간 동기화
    if st.session_state.get("data_changed", False):
        if st.session_state.get("session_id") and st.session_state.get("workplace"):
            try:
                from data_manager import save_to_excel
                save_to_excel(st.session_state["session_id"], st.session_state.get("workplace"))
            except Exception:
                pass
        st.session_state["data_changed"] = False