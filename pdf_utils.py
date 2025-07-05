import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
import streamlit as st
import fitz  # PyMuPDF
import sys

def find_font_path():
    """다양한 OS에서 사용 가능한 한글 폰트 경로를 찾습니다."""
    # Windows
    if os.name == 'nt':
        font_path = "c:/Windows/Fonts/malgun.ttf"
        if os.path.exists(font_path):
            return font_path
        font_path = "c:/Windows/Fonts/NanumGothic.ttf" # Fallback for Nanum Gothic
        if os.path.exists(font_path):
            return font_path
    # macOS
    elif sys.platform == 'darwin':
        font_path = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
        if os.path.exists(font_path):
            return font_path
    # Linux (common paths for Nanum fonts)
    else:
        font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
        if os.path.exists(font_path):
            return font_path
        font_path = "/usr/share/fonts/nanum/NanumGothic.ttf"
        if os.path.exists(font_path):
            return font_path
    
    st.warning("한글 폰트(맑은 고딕 또는 나눔 고딕)를 찾을 수 없습니다. PDF에서 한글이 깨질 수 있습니다.")
    return None

def register_font():
    """Registers a Korean font for ReportLab, returns the font name."""
    font_path = find_font_path()
    if font_path:
        try:
            font_name = os.path.splitext(os.path.basename(font_path))[0]
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            return font_name
        except Exception as e:
            st.warning(f"폰트 등록 실패: {e}. 기본 폰트로 대체합니다.")
            return 'Helvetica'
    return 'Helvetica'

def generate_pdf_in_memory(data):
    """Generates a PDF from the data in memory and returns it as bytes."""
    from io import BytesIO
    
    buffer = BytesIO()
    font_name = register_font()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1*cm, rightMargin=1*cm,
        topMargin=1*cm, bottomMargin=1*cm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName=font_name, fontSize=14, alignment=1, spaceAfter=12)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontName=font_name, fontSize=9, leading=12)
    detail_style = ParagraphStyle('DetailStyle', parent=styles['Normal'], fontName=font_name, fontSize=8, leading=10, wordWrap='CJK')
    subheader_style = ParagraphStyle('SubheaderStyle', parent=styles['Heading2'], fontName=font_name, fontSize=12, spaceAfter=8, spaceBefore=15)

    elements = []
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    elements.append(Paragraph(f"YouTube 채널 분석 리포트 ({current_date})", title_style))
    elements.append(Spacer(1, 12))

    total_rows = len(data)
    
    for i, row in enumerate(data):
        # XML 특수문자 이스케이프 함수
        def escape_xml(text):
            text = str(text)
            return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # 데이터 항목 확인 및 기본값 설정
        channel = escape_xml(row.get("채널명", "N/A"))
        title = escape_xml(row.get("제목", "N/A"))
        view_count = escape_xml(row.get("조회수", "N/A"))
        published_at = escape_xml(row.get("게시일", "N/A"))
        url = escape_xml(row.get("영상 URL", "N/A"))
        transcript = escape_xml(row.get("자막", "자막 없음"))
        comments = escape_xml(row.get("댓글", "댓글 없음"))
        description = escape_xml(row.get("설명", "설명 없음"))
        
        elements.append(Paragraph(f"영상 #{i+1}: {title}", subheader_style))
        elements.append(Paragraph(f"<b>채널:</b> {channel}", detail_style))
        elements.append(Paragraph(f"<b>조회수:</b> {view_count}", detail_style))
        elements.append(Paragraph(f"<b>게시일:</b> {published_at}", detail_style))
        elements.append(Paragraph(f"<b>URL:</b> {url}", detail_style))
        elements.append(Spacer(1, 5))
        
        elements.append(Paragraph("<b>자막:</b>", detail_style))
        elements.append(Paragraph(transcript, detail_style))
        elements.append(Spacer(1, 5))
        
        elements.append(Paragraph("<b>댓글:</b>", detail_style))
        elements.append(Paragraph(comments, detail_style))
        elements.append(Spacer(1, 5))

        elements.append(Paragraph("<b>설명:</b>", detail_style))
        elements.append(Paragraph(description, detail_style))
        
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("_" * 100, detail_style))
        elements.append(Spacer(1, 10))

    doc.build(elements)
    
    buffer.seek(0)
    return buffer.getvalue()

def read_pdf_from_upload(uploaded_file):
    """Extracts text from an uploaded PDF file."""
    try:
        # Streamlit's UploadedFile object has a getvalue() method to get bytes
        pdf_bytes = uploaded_file.getvalue()
        text = ""
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        st.error(f"PDF 파일을 읽는 중 오류가 발생했습니다: {e}")
        return None 