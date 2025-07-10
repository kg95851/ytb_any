import streamlit as st
import pandas as pd
import prompts
import youtube_utils
import analysis_utils
import pdf_utils
import matplotlib.pyplot as plt
from datetime import datetime

def initialize_app_state():
    """앱의 모든 세션 상태 변수를 초기화합니다."""
    # 페이지 선택
    if 'page_selection' not in st.session_state:
        st.session_state.page_selection = "스크립트 & 댓글 수집"

    # 스크립트 & 댓글 수집 페이지
    if 'collection_type' not in st.session_state:
        st.session_state.collection_type = "채널"
    if 'collection_channel_input_type' not in st.session_state:
        st.session_state.collection_channel_input_type = "채널 URL"
    if 'collection_channel_urls' not in st.session_state:
        st.session_state.collection_channel_urls = ""
    if 'collection_video_count' not in st.session_state:
        st.session_state.collection_video_count = 10
    if 'collection_min_view_count' not in st.session_state:
        st.session_state.collection_min_view_count = 10
    if 'collection_individual_urls' not in st.session_state:
        st.session_state.collection_individual_urls = ""
    if 'collection_comment_count' not in st.session_state:
        st.session_state.collection_comment_count = 20
    if 'collection_script_numbering' not in st.session_state:
        st.session_state.collection_script_numbering = False
    if 'collection_comment_numbering' not in st.session_state:
        st.session_state.collection_comment_numbering = False
    if 'collected_channel_data' not in st.session_state:
        st.session_state.collected_channel_data = []
    if 'collected_individual_data' not in st.session_state:
        st.session_state.collected_individual_data = []

    # 개별 영상 분석 페이지
    if 'individual_source' not in st.session_state:
        st.session_state.individual_source = "URL"
    if 'individual_url_input' not in st.session_state:
        st.session_state.individual_url_input = ""
    if 'individual_selected_video' not in st.session_state:
        st.session_state.individual_selected_video = None

    # 채널 종합 분석 페이지
    if 'channel_source' not in st.session_state:
        st.session_state.channel_source = "URL"
    if 'channel_url_input' not in st.session_state:
        st.session_state.channel_url_input = ""
    if 'channel_analysis_video_count' not in st.session_state:
        st.session_state.channel_analysis_video_count = 5
    if 'channel_selected_channels' not in st.session_state:
        st.session_state.channel_selected_channels = []

    # 대본 비교 분석 페이지
    if 'comparison_foreign_script' not in st.session_state:
        st.session_state.comparison_foreign_script = ""
    if 'comparison_korean_script' not in st.session_state:
        st.session_state.comparison_korean_script = ""

    # 채널 업로드 시간 분석 페이지
    if 'time_analysis_url' not in st.session_state:
        st.session_state.time_analysis_url = ""
        
    # 데이터 분석 페이지
    if 'analysis_data' not in st.session_state:
        st.session_state.analysis_data = []

    # 테마 모드
    if 'theme_is_dark' not in st.session_state:
        st.session_state.theme_is_dark = True

def inject_dark_theme_css():
    """
    Streamlit 앱에 다크 모드 스타일을 적용하기 위한 CSS를 주입합니다.
    참고: Streamlit의 내부 클래스 이름은 업데이트 시 변경될 수 있어,
    이 CSS는 향후 버전과 호환되지 않을 수 있습니다.
    """
    dark_theme_css = """
        <style>
            /* 기본 배경 */
            .stApp {
                background-color: #0E1117;
            }

            /* 모든 텍스트 색상을 흰색으로 강제 지정 */
            body, .stApp, h1, h2, h3, h4, h5, h6, .stMarkdown, p, label, 
            [data-testid="stWidgetLabel"] > div, 
            .st-emotion-cache-1629p8f, .st-emotion-cache-keje6w {
                color: #FAFAFA !important;
            }

            /* 사이드바 */
            [data-testid="stSidebar"] {
                background-color: #262730;
            }

            /* 카드형 컨테이너 (테두리 제거 및 패딩 추가) */
            div.st-emotion-cache-1r4qj8v {
                background-color: #262730;
                border: none;
                border-radius: 10px;
                padding: 1rem;
            }

            /* 버튼 */
            .stButton>button {
                background-color: #7792E3;
                color: #FFFFFF;
                border: none;
            }
            .stButton>button:hover {
                background-color: #5A73E8;
            }

            /* 입력 위젯 배경/텍스트 */
            .stTextInput input, .stTextArea textarea, .stNumberInput input {
                background-color: #31333F;
                color: #FAFAFA !important;
            }
            
            /* 선택 박스(Selectbox) 스타일 */
            .stSelectbox div[data-baseweb="select"] > div {
                background-color: #31333F;
                color: #FAFAFA !important;
            }
            /* 선택 박스 드롭다운 메뉴 스타일 */
            [data-baseweb="popover"] ul {
                 background-color: #31333F;
            }

            /* Toast 메시지 텍스트 색상을 어둡게 유지 */
            [data-testid="stToast"] div[data-baseweb="toast"] > div:nth-of-type(2) {
                color: #31333F !important;
            }
            
            /* 다운로드 버튼 텍스트 색상을 어둡게 유지 */
            [data-testid="stDownloadButton"] p {
                color: #31333F !important;
            }
        </style>
    """
    st.markdown(dark_theme_css, unsafe_allow_html=True)

def render_data_table(title, data_key):
    """주어진 session_state 키에 대한 데이터 테이블과 관리 버튼을 렌더링합니다."""
    if not st.session_state.get(data_key):
        return

    with st.container(border=True):
        st.subheader(title)
        
        df = pd.DataFrame(st.session_state[data_key])
        
        df_to_display = df.copy()
        df_to_display.insert(0, "삭제", False)
        df_to_display.insert(1, "분석으로 이동", False)

        edited_df = st.data_editor(
            df_to_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "삭제": st.column_config.CheckboxColumn("삭제", default=False),
                "분석으로 이동": st.column_config.CheckboxColumn("이동", default=False),
            },
            disabled=df.columns,
            key=f"{data_key}_editor"
        )

        indices_to_delete = edited_df[edited_df["삭제"] == True].index.tolist()
        indices_to_move = edited_df[edited_df["분석으로 이동"] == True].index.tolist()

        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"🗑️ 선택한 항목 삭제", type="primary", disabled=not indices_to_delete, key=f"{data_key}_delete_selected"):
                for index in sorted(indices_to_delete, reverse=True):
                    del st.session_state[data_key][index]
                st.rerun()
        
        with col2:
            if st.button(f"➡️ 분석으로 이동", disabled=not indices_to_move, key=f"{data_key}_move_selected"):
                items_to_move = [st.session_state[data_key][i] for i in indices_to_move]
                st.session_state.analysis_data.extend(items_to_move)

                # Move한 항목은 원래 리스트에서 삭제
                for index in sorted(indices_to_move, reverse=True):
                    del st.session_state[data_key][index]
                
                st.toast(f"{len(items_to_move)}개 항목을 분석으로 이동했습니다.")
                st.rerun()

def render_settings_page():
    st.title("⚙️ 설정")
    st.markdown("API 키와 분석 유형을 관리합니다.")

    st.divider()

    with st.container(border=True):
        st.subheader("API 키 관리")
        st.info("입력한 API 키는 현재 세션에만 임시로 저장되며, 페이지를 새로고침하면 다시 입력해야 합니다.")

        # Gemini API Key
        st.text_input(
            "Gemini API 키", 
            type="password",
            key="gemini_api_key"
        )
        if st.button("Gemini 키 저장"):
            # The key is already saved to session state by the text_input widget's key
            st.success("Gemini API 키가 현재 세션에 저장되었습니다.")

        # YouTube API Keys
        st.markdown("#### YouTube API 키")
        youtube_keys = st.session_state.get('youtube_api_keys', [])
    
        for i in range(len(youtube_keys)):
            col1, col2 = st.columns([4, 1])
            col1.text_input(f"키 {i+1}", value=youtube_keys[i], disabled=True, key=f"yt_key_disp_{i}")
            if col2.button("삭제", key=f"del_yt_key_{i}"):
                st.session_state.youtube_api_keys.pop(i)
                st.rerun()

        new_yt_key = st.text_input("새 YouTube API 키 추가")
        if st.button("YouTube 키 추가"):
            if new_yt_key and new_yt_key not in st.session_state.get('youtube_api_keys', []):
                st.session_state.youtube_api_keys.append(new_yt_key)
                st.rerun()
            elif not new_yt_key:
                st.warning("API 키를 입력해주세요.")
            else:
                st.warning("이미 등록된 키입니다.")

        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 API 클라이언트 초기화", type="primary"):
                with st.spinner("클라이언트를 초기화하는 중..."):
                    youtube_utils.initialize_clients(st)
                if st.session_state.get('youtube_client'):
                    st.success("클라이언트가 성공적으로 초기화되었습니다.")
                    st.session_state.clients_initialized = True
                else:
                    st.error("클라이언트 초기화에 실패했습니다. API 키를 확인해주세요.")

        with col2:
            if st.button("⚠️ 모든 저장된 키 삭제"):
                st.session_state.youtube_api_keys = []
                st.session_state.gemini_api_key = ""
                st.success("현재 세션의 모든 API 키가 삭제되었습니다.")
                st.rerun()

    st.divider()

    with st.container(border=True):
        st.subheader("기승전결 유형 관리")
        st.info("아래 표에서 직접 유형을 추가, 수정, 삭제할 수 있습니다. 변경 후에는 반드시 '유형 변경사항 저장' 버튼을 눌러주세요.")
        
        archetypes = prompts.load_archetypes()
        df = pd.DataFrame(archetypes)

        edited_df = st.data_editor(
            df, num_rows="dynamic", key="archetype_editor", use_container_width=True, hide_index=True
        )

        if st.button("💾 유형 변경사항 저장", type="primary"):
            try:
                updated_archetypes = edited_df.to_dict('records')
                for i, archetype in enumerate(updated_archetypes):
                    archetype['번호'] = i + 1
                
                prompts.save_archetypes(updated_archetypes)
                st.success("✅ 유형이 성공적으로 저장되었습니다!")
                st.rerun()
            except Exception as e:
                st.error(f"유형 저장 중 오류가 발생했습니다: {e}")


def render_collection_page():
    st.title("📊 스크립트 & 댓글 수집")
    st.markdown("수집 유형을 선택하고, 아래에 URL을 입력하여 데이터를 수집하세요.")

    with st.container(border=True):
        # --- Input UI ---
        st.radio("수집 유형 선택:", ("채널", "개별 영상"), horizontal=True, key="collection_type")

        if st.session_state.collection_type == "채널":
            st.radio("채널 입력 유형:", ("채널 URL", "채널명"), key="collection_channel_input_type", horizontal=True)
            
            if st.session_state.collection_channel_input_type == "채널 URL":
                label_text = "채널 URL 목록 (한 줄에 하나씩):"
                placeholder_text = "https://www.youtube.com/channel/...\nhttps://www.youtube.com/@..."
            else: # 채널명
                label_text = "채널명 목록 (한 줄에 하나씩):"
                placeholder_text = "채널 이름을 한 줄에 하나씩 입력하세요..."

            st.text_area(label_text, placeholder=placeholder_text, key="collection_channel_urls")
            col1, col2 = st.columns(2)
            with col1:
                st.number_input("채널당 가져올 최대 영상 수:", min_value=1, max_value=50, key="collection_video_count")
            with col2:
                st.number_input("최소 조회수 (만 단위):", min_value=0, key="collection_min_view_count")
        else:  # 개별 영상
            st.text_area("영상 URL 목록 (한 줄에 하나씩):", placeholder="https://www.youtube.com/watch?v=...\nhttps://youtu.be/...", key="collection_individual_urls")

        st.number_input("영상당 가져올 최대 댓글 수:", min_value=1, max_value=100, key="collection_comment_count")
        
        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("스크립트 번호 붙이기", key="collection_script_numbering")
        with col2:
            st.checkbox("댓글 번호 붙이기", key="collection_comment_numbering")
    
        start_button_pressed = st.button("📥 데이터 수집 시작", type="primary")

    # --- Data Display and Management ---
    all_data = st.session_state.get('collected_channel_data', []) + st.session_state.get('collected_individual_data', [])
    if all_data:
        st.divider()

    render_data_table("채널 수집 데이터", "collected_channel_data")
    render_data_table("개별 영상 수집 데이터", "collected_individual_data")

    if all_data:
        st.divider()
        with st.container(border=True):
            st.subheader("종합 데이터 관리")
            col1, col2 = st.columns([1, 1.2])
            with col1:
                if st.button("💥 전체 데이터 일괄 삭제"):
                    st.session_state.collected_channel_data = []
                    st.session_state.collected_individual_data = []
                    st.rerun()
            
            with col2:
                pdf_bytes = pdf_utils.generate_pdf_in_memory(all_data)
                st.download_button(
                    label="📄 전체 목록 PDF로 다운로드",
                    data=pdf_bytes,
                    file_name="youtube_analysis_report.pdf",
                    mime="application/pdf"
                )
    
    # --- Data Collection Logic ---
    if start_button_pressed:
        if st.session_state.collection_type == "채널":
            urls_input = st.session_state.collection_channel_urls
            video_count = st.session_state.collection_video_count
            min_view_count = st.session_state.collection_min_view_count * 10000
            target_data_key = 'collected_channel_data'
        else: # 개별 영상
            urls_input = st.session_state.collection_individual_urls
            video_count = 1
            min_view_count = 0
            target_data_key = 'collected_individual_data'

        comment_count = st.session_state.collection_comment_count
        script_numbering = st.session_state.collection_script_numbering
        comment_numbering = st.session_state.collection_comment_numbering

        urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
        if not urls:
            st.warning("URL을 입력해주세요.")
        else:
            with st.spinner("데이터를 수집하는 중입니다... (중복 영상은 제외됩니다)"):
                # 전체 데이터에서 기존 영상 ID 목록을 전달하여 중복 수집 방지
                all_existing_data = st.session_state.get('collected_channel_data', []) + st.session_state.get('collected_individual_data', [])
                existing_video_ids = [youtube_utils.get_video_id(item['영상 URL']) for item in all_existing_data]
                
                new_results = youtube_utils.process_urls(
                    st, urls, video_count, min_view_count, comment_count, 
                    script_numbering, comment_numbering, existing_video_ids
                )
            
            if new_results:
                st.session_state[target_data_key].extend(new_results)
                st.success(f"✅ 새로운 영상 {len(new_results)}개를 추가했습니다!", icon="🎉")
            else:
                st.info("✅ 추가할 새로운 영상이 없습니다.", icon="👍")
            
            st.rerun()

def run_individual_analysis(details):
    st.subheader(f"분석 대상: {details.get('title')}")
    st.write(f"채널: {details.get('channel_name', '알 수 없음')}, 조회수: {details.get('view_count', '알 수 없음')}")
    
    analysis_type = st.selectbox("분석 유형 선택", ["일반", "드라마", "정치"], key=f"analysis_type_{details.get('title')}")
    
    if analysis_type == "일반":
        prompt_template = prompts.INDIVIDUAL_ANALYSIS_TEMPLATE
    elif analysis_type == "드라마":
        prompt_template = prompts.DRAMA_ANALYSIS_PROMPT
    else: # 정치
        prompt_template = prompts.POLITICS_ANALYSIS_PROMPT

    dynamic_prompt = prompts.create_dynamic_prompt(prompt_template)
    
    with st.expander("프롬프트 수정/확인"):
        edited_prompt = st.text_area("분석 프롬프트:", value=dynamic_prompt, height=300, key=f"prompt_editor_{details.get('title')}")

    with st.spinner("🤖 Gemini API로 분석 중..."):
        final_prompt_text = edited_prompt.format(
            title=details.get('title', ''),
            script=details.get('script', ''),
            description=details.get('description', ''),
            comments=details.get('comments', '')
        )
        analysis_utils.analyze_with_gemini(st, final_prompt_text)
        st.success(f"✅ '{details.get('title')}' 영상 분석이 완료되었습니다!", icon="🔎")

def render_individual_analysis_page():
    st.title("🔎 개별 영상 분석")
    st.markdown("분석 소스를 선택하고, URL을 입력하거나, 수집된 데이터 또는 PDF 파일을 선택하세요.")
    
    st.radio("분석 소스 선택", ["URL", "수집된 데이터", "PDF 업로드"], key="individual_source", horizontal=True)
    st.divider()

    if st.session_state.individual_source == "URL":
        with st.container(border=True):
            st.subheader("🌐 URL로 분석")
            st.text_area("분석할 영상 URL (한 줄에 하나씩):", key="individual_url_input")
            if st.button("🚀 URL로 분석 시작", type="primary"):
                urls_input = st.session_state.individual_url_input
                urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
                if not urls:
                    st.warning("분석할 영상 URL을 입력해주세요.")
                else:
                    for url in urls:
                        with st.spinner(f"영상 정보 수집 중: {url}"):
                            video_id = youtube_utils.get_video_id(url)
                            if video_id:
                                details = youtube_utils.get_video_details(st, video_id, 20)
                                if details:
                                    run_individual_analysis(details)
                            else: 
                                st.error(f"올바른 유튜브 영상 URL이 아닙니다: {url}")

    elif st.session_state.individual_source == "수집된 데이터":
        with st.container(border=True):
            st.subheader("📊 수집된 데이터로 분석")
            all_collected_data = st.session_state.get('collected_channel_data', []) + st.session_state.get('collected_individual_data', [])
            if all_collected_data:
                video_options = {f"{i+1}. {item.get('제목', '제목 없음')}": item for i, item in enumerate(all_collected_data)}
                
                # Get the index for the selectbox
                options_list = list(video_options.keys())

                st.selectbox("분석할 영상 선택:", options=options_list, key="individual_selected_video")
                
                if st.button("🚀 선택한 데이터로 분석 시작", type="primary"):
                    selected_title = st.session_state.individual_selected_video
                    if selected_title:
                        selected_video = video_options[selected_title]
                        run_individual_analysis(selected_video)
            else:
                st.warning("'스크립트 & 댓글 수집' 탭에서 먼저 데이터를 수집해주세요.")

    elif st.session_state.individual_source == "PDF 업로드":
        with st.container(border=True):
            st.subheader("📄 PDF로 분석")
            uploaded_file = st.file_uploader("분석할 PDF 파일을 업로드하세요.", type="pdf")
            if uploaded_file:
                if st.button("🚀 업로드한 PDF로 분석 시작", type="primary"):
                    script_text = pdf_utils.read_pdf_from_upload(uploaded_file)
                    if script_text:
                        details = { "title": uploaded_file.name, "script": script_text, "description": "", "comments": "" }
                        run_individual_analysis(details)

def run_channel_analysis(url=None, video_count=None, channel_name=None, pdf_file=None):
    all_scripts_text = ""
    display_name = ""

    with st.spinner(f"데이터 준비 중..."):
        if url:
            display_name = url
            channel_id = youtube_utils.get_channel_id(st, url)
            if channel_id:
                channel_info = youtube_utils.get_channel_info(st, channel_id)
                display_name = channel_info.get('snippet', {}).get('title', url)
                videos = youtube_utils.get_latest_videos(st, channel_id, video_count, 0)
                for video in videos:
                    details = youtube_utils.get_video_details(st, video['videoId'], 5)
                    if details and details.get('자막', '자막 없음') not in ["자막 없음", "자막 추출 오류"]:
                        all_scripts_text += f"제목: {details['제목']}\n대본: {details['자막']}\n\n"
            else:
                st.error(f"채널 ID를 찾을 수 없습니다: {url}")
                return
        
        elif channel_name:
            display_name = channel_name
            for item in st.session_state.collected_data:
                if item.get("채널명") == channel_name and item.get('자막', '자막 없음') not in ["자막 없음", "자막 추출 오류"]:
                    all_scripts_text += f"제목: {item.get('제목', '')}\n대본: {item.get('자막', '')}\n\n"

        elif pdf_file:
            display_name = pdf_file.name
            all_scripts_text = pdf_utils.read_pdf_from_upload(pdf_file)
            if all_scripts_text:
                st.text_area("추출된 텍스트 (분석에 사용됩니다):", all_scripts_text, height=150)

    if not all_scripts_text:
        st.warning(f"'{display_name}'에서 분석할 스크립트를 찾지 못했습니다.")
        return

    st.subheader(f"'{display_name}' 채널 분석 결과")
    dynamic_prompt = prompts.create_dynamic_prompt(prompts.CHANNEL_ANALYSIS_TEMPLATE)
    with st.expander("프롬프트 수정/확인"):
        edited_prompt = st.text_area("분석 프롬프트:", value=dynamic_prompt, height=300, key=f"channel_editor_{display_name}")
    
    with st.spinner(f"🤖 '{display_name}' 채널 분석 중..."):
        final_prompt = edited_prompt.format(channel_name=display_name, all_scripts=all_scripts_text)
        analysis_utils.analyze_with_gemini(st, final_prompt)
        st.success(f"✅ '{display_name}' 채널 분석이 완료되었습니다!", icon="📈")

def render_channel_analysis_page():
    st.title("📈 채널 종합 분석")
    st.markdown("분석 소스를 선택하고 URL을 입력하거나, 수집된 데이터 또는 PDF 파일을 선택하세요.")
    
    st.radio("분석 소스 선택", ["URL", "수집된 데이터", "PDF 업로드"], key="channel_source", horizontal=True)
    st.divider()

    if st.session_state.channel_source == "URL":
        with st.container(border=True):
            st.subheader("🌐 URL로 분석")
            st.text_area("분석할 채널 URL (한 줄에 하나씩):", key="channel_url_input")
            st.number_input("채널당 분석할 최신 영상 수:", min_value=1, max_value=50, key="channel_analysis_video_count")
            
            if st.button("🚀 채널 분석 시작 (URL)", type="primary"):
                urls_input = st.session_state.channel_url_input
                video_count = st.session_state.channel_analysis_video_count
                urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
                if not urls:
                    st.warning("채널 URL을 입력해주세요.")
                else:
                    for url in urls:
                        run_channel_analysis(url=url, video_count=video_count)

    elif st.session_state.channel_source == "수집된 데이터":
        with st.container(border=True):
            st.subheader("📊 수집된 데이터로 분석")
            st.info("'스크립트 & 댓글 수집' 탭에서 가져온 데이터를 채널별로 선택하여 종합 분석합니다.")
            all_collected_data = st.session_state.get('collected_channel_data', []) + st.session_state.get('collected_individual_data', [])
            if all_collected_data:
                all_channels = sorted(list(set(item.get("채널명", "알 수 없는 채널") for item in all_collected_data)))
                st.multiselect("분석할 채널을 선택하세요:", options=all_channels, key="channel_selected_channels")

                if st.button("🚀 선택한 채널 종합 분석 시작", type="primary"):
                    selected_channels = st.session_state.channel_selected_channels
                    if not selected_channels:
                        st.warning("분석할 채널을 하나 이상 선택해주세요.")
                    else:
                        for channel_name in selected_channels:
                            run_channel_analysis(channel_name=channel_name)
            else:
                st.warning("'스크립트 & 댓글 수집' 탭에서 먼저 데이터를 수집해주세요.")

    elif st.session_state.channel_source == "PDF 업로드":
        with st.container(border=True):
            st.subheader("📄 PDF로 분석")
            uploaded_file = st.file_uploader("분석할 PDF 파일을 업로드하세요.", type="pdf", key="channel_pdf_uploader")
            
            if st.button("🚀 업로드한 PDF로 분석 시작", type="primary"):
                if uploaded_file:
                    run_channel_analysis(pdf_file=uploaded_file)
                else:
                    st.warning("분석할 PDF 파일을 먼저 업로드해주세요.")

def render_comparison_page():
    st.title("🔄 대본 비교 분석")
    st.markdown("좌우에 비교할 대본을 각각 입력하고 분석을 시작하세요.")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("외국 대본 (원본)")
            st.text_area("외국 대본 또는 원본 대본", height=300, key="comparison_foreign_script", label_visibility="collapsed")
        with col2:
            st.subheader("한국 대본 (수정본)")
            st.text_area("한국 대본 또는 번역/수정된 대본", height=300, key="comparison_korean_script", label_visibility="collapsed")
    
    dynamic_prompt = prompts.create_dynamic_prompt(prompts.COMPARE_ANALYSIS_PROMPT)
    with st.expander("프롬프트 수정/확인"):
        edited_prompt = st.text_area("분석 프롬프트:", value=dynamic_prompt, height=300, key="compare_prompt_editor")
        
    if st.button("🚀 대본 비교 분석 시작", type="primary"):
        foreign_script = st.session_state.comparison_foreign_script
        korean_script = st.session_state.comparison_korean_script
        if not foreign_script or not korean_script:
            st.warning("비교할 두 대본을 모두 입력해주세요.")
            return
            
        with st.spinner("🤖 Gemini API로 비교 분석 중..."):
            final_prompt = edited_prompt.format(
                foreign_script=foreign_script,
                korean_script=korean_script
            )
            analysis_utils.analyze_with_gemini(st, final_prompt)
            st.success("✅ 대본 비교 분석이 완료되었습니다!", icon="🔄")

def render_time_analysis_page():
    st.title("⏰ 채널 업로드 시간 분석")
    st.markdown("채널의 모든 영상을 분석하여 업로드 시간 패턴을 시각화합니다.")
    
    with st.container(border=True):
        st.text_input("분석할 채널 URL:", key="time_analysis_url")

        if st.button("🚀 업로드 시간 분석 시작", type="primary"):
            channel_url = st.session_state.time_analysis_url
            if not channel_url:
                st.warning("채널 URL을 입력해주세요.")
                return
            
            with st.spinner("채널 영상 목록 수집 중... (영상 수에 따라 시간이 걸릴 수 있습니다)"):
                channel_id = youtube_utils.get_channel_id(st, channel_url)
                if channel_id:
                    channel_info = youtube_utils.get_channel_info(st, channel_id)
                    uploads_playlist_id = channel_info.get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads')
                    
                    if uploads_playlist_id:
                        videos = youtube_utils.get_uploaded_videos_playlist(st, uploads_playlist_id)
                        st.session_state.time_analysis_videos = videos
                        st.session_state.time_analysis_channel_name = channel_info.get('snippet',{}).get('title','N/A')
                        st.success(f"'{st.session_state.time_analysis_channel_name}' 채널의 영상 {len(videos)}개를 찾았습니다. 아래에 분석 결과가 표시됩니다.")
                    else:
                        st.error("업로드 목록을 찾을 수 없습니다.")
                else:
                    st.error("채널 ID를 찾을 수 없습니다.")

    if 'time_analysis_videos' in st.session_state:
        st.divider()
        with st.container(border=True):
            st.subheader(f"'{st.session_state.time_analysis_channel_name}' 채널 분석 결과")
            videos_to_analyze = st.session_state.time_analysis_videos
            
            with st.spinner("업로드 패턴 분석 중..."):
                analysis_results = youtube_utils.analyze_upload_patterns(videos_to_analyze)

            if analysis_results:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("요일별 업로드 수:")
                    st.dataframe(analysis_results['weekday'])
                with col2:
                    st.write("시간대별 업로드 수 (KST):")
                    st.dataframe(analysis_results['hourly'])
                    
                try:
                    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
                    plt.rc('font', family='Malgun Gothic')

                    analysis_results['weekday'].plot(kind='bar', ax=ax1, title="요일별 업로드 패턴", rot=0)
                    ax1.set_ylabel("업로드 수")
                    
                    analysis_results['hourly'].plot(kind='bar', ax=ax2, title="시간대별 업로드 패턴 (KST)", rot=0, color='skyblue')
                    ax2.set_ylabel("업로드 수")
                    ax2.set_xlabel("시간")
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    st.success(f"✅ '{st.session_state.time_analysis_channel_name}' 채널의 업로드 시간 분석이 완료되었습니다!", icon="⏰")
                except Exception as e:
                    st.warning(f"그래프 생성 중 오류가 발생했습니다: {e}\n'Malgun Gothic' 폰트가 설치되어 있는지 확인해주세요.")
            else:
                st.warning("분석할 영상 데이터가 없습니다.")

def render_analysis_page():
    st.title("📊 데이터 분석")
    st.markdown("수집된 데이터의 일 평균 조회수를 분석합니다.")
    
    if not st.session_state.get('analysis_data'):
        st.warning("'스크립트 & 댓글 수집' 탭에서 분석할 데이터를 먼저 옮겨주세요.")
        return

    df = pd.DataFrame(st.session_state.analysis_data)
    
    # --- 일 평균 조회수 계산 ---
    # '게시일' 컬럼을 datetime 객체로 변환
    df['게시일'] = pd.to_datetime(df['게시일'])
    
    # 영상이 게시된 후 지난 날짜 계산
    now = pd.to_datetime(datetime.now())
    df['게시 후 일수'] = (now - df['게시일']).dt.days
    # 최소 1일로 설정하여 0으로 나누는 오류 방지
    df['게시 후 일수'] = df['게시 후 일수'].apply(lambda x: max(x, 1))

    # 일 평균 조회수 계산
    df['일 평균 조회수'] = df['조회수'] / df['게시 후 일수']
    df['일 평균 조회수'] = df['일 평균 조회수'].astype(int)

    # --- 채널별 통계 ---
    st.divider()
    st.subheader("📈 채널별 일 평균 조회수 합계")

    # 채널별로 그룹화하여 일 평균 조회수 합산
    channel_avg_views = df.groupby('채널명')['일 평균 조회수'].sum().reset_index()
    channel_avg_views = channel_avg_views.sort_values(by='일 평균 조회수', ascending=False)
    
    st.dataframe(channel_avg_views, use_container_width=True)

    # --- 전체 통계 ---
    total_avg_daily_views = df['일 평균 조회수'].sum()
    st.metric(label="전체 채널의 일 평균 조회수 총합", value=f"{total_avg_daily_views:,}")

    # --- 원본 데이터 표시 ---
    st.divider()
    with st.expander("분석에 사용된 데이터 보기"):
        st.dataframe(df[['채널명', '제목', '조회수', '게시일', '게시 후 일수', '일 평균 조회수']], use_container_width=True)

def main():
    st.set_page_config(page_title="YouTube 분석 도구", layout="wide")
    
    # Initialize all session state variables at the beginning
    youtube_utils.init_session_state(st)
    initialize_app_state()

    # Inject dark theme CSS if enabled
    if st.session_state.theme_is_dark:
        inject_dark_theme_css()
    
    # Automatically initialize clients if they haven't been, and keys are available.
    if not st.session_state.get('clients_initialized'):
        if st.session_state.get('youtube_api_keys') and st.session_state.get('gemini_api_key'):
            youtube_utils.initialize_clients(st)
            if st.session_state.get('youtube_client'):
                st.session_state.clients_initialized = True
                # Show a one-time success message
                if 'client_init_success_msg' not in st.session_state:
                    st.success("✅ API 클라이언트가 자동으로 초기화되었습니다.", icon="🎉")
                    st.session_state.client_init_success_msg = True

    st.sidebar.title("메뉴")
    st.sidebar.toggle("🌙 다크 모드", key="theme_is_dark")
    st.sidebar.divider()
    
    page_options = {
        "스크립트 & 댓글 수집": "📊 스크립트 & 댓글 수집",
        "데이터 분석": "📊 데이터 분석",
        "개별 영상 분석": "🔎 개별 영상 분석",
        "채널 종합 분석": "📈 채널 종합 분석",
        "대본 비교 분석": "🔄 대본 비교 분석",
        "채널 업로드 시간 분석": "⏰ 채널 업로드 시간 분석",
        "설정": "⚙️ 설정"
    }
    
    page_keys = list(page_options.keys())
    page_labels = list(page_options.values())
    
    selected_page_label = st.sidebar.radio(
        "기능을 선택하세요:", 
        options=page_labels,
        key="sidebar_selection"
    )
    
    # Map label back to key
    st.session_state.page_selection = page_keys[page_labels.index(selected_page_label)]

    if st.session_state.page_selection != "설정":
        # Check for keys and initialization status to provide better guidance
        if not (st.session_state.get('youtube_api_keys') and st.session_state.get('gemini_api_key')):
             st.warning("API 키가 없습니다. '⚙️ 설정' 페이지에서 키를 입력해주세요.")
        elif not st.session_state.get('clients_initialized'):
             st.error("API 클라이언트 초기화에 실패했습니다. '⚙️ 설정' 페이지에서 키를 확인하고 '클라이언트 초기화' 버튼을 눌러주세요.")

    page_map = {
        "스크립트 & 댓글 수집": render_collection_page,
        "데이터 분석": render_analysis_page,
        "개별 영상 분석": render_individual_analysis_page,
        "채널 종합 분석": render_channel_analysis_page,
        "대본 비교 분석": render_comparison_page,
        "채널 업로드 시간 분석": render_time_analysis_page,
        "설정": render_settings_page
    }
    page_map[st.session_state.page_selection]()

if __name__ == "__main__":
    main()
