import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

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

def render_improvement_plan_tab():
    """작업환경개선계획서 탭 렌더링"""
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