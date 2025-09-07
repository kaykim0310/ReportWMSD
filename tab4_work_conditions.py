import streamlit as st
import pandas as pd
from utils import get_사업장명_목록, get_팀_목록, get_작업명_목록, safe_convert, extract_number, calculate_total_score

def render_work_conditions_tab():
    """작업조건조사 탭 렌더링"""
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
            
            # 작업별로 관련된 유해요인에 대한 원인분석 섹션 추가
            render_hazard_analysis_section(selected_작업명, selected_회사명_조건, selected_소속_조건)


def render_hazard_analysis_section(selected_작업명, selected_회사명_조건, selected_소속_조건):
    """작업별 유해요인 원인분석 섹션"""
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
            
            # 디버깅 정보
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
                            # 10호 관련 필드
                            hazard_entry["물체 무게(kg)_10호"] = safe_convert(row.get(f"유해요인_원인분석_반복_물체무게_10호(kg)_{j+1}", ""), float, 0.0)
                            hazard_entry["분당 반복횟수(회/분)_10호"] = safe_convert(row.get(f"유해요인_원인분석_반복_분당반복횟수_10호(회/분)_{j+1}", ""), str, "")
                            # 12호 정적자세 관련 필드
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
                from utils import parse_value
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
        
        # 현재 항목의 변경사항을 세션 상태에 반영
        st.session_state[원인분석_key][k] = hazard_entry

        # 삭제 버튼 (첫 번째 항목은 삭제 불가)
        if k > 0 or len(current_hazard_analysis_data) > 1:
            col_delete_btn, _ = st.columns([0.2, 0.8])
            with col_delete_btn:
                if st.button(f"[{k+1}] 항목 삭제", key=f"delete_hazard_analysis_{k}_{selected_작업명}"):
                    st.session_state[원인분석_key].pop(k)
                    st.rerun()

        st.markdown("---")