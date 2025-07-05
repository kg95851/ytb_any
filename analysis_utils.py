import google.generativeai as genai
import time

def analyze_with_gemini(st, prompt, stream=True):
    """
    Calls the Gemini API with the given prompt and streams the response.
    'st' is the streamlit object to display real-time responses.
    """
    if not st.session_state.get("gemini_api_key"):
        st.error("Gemini API 키가 설정되지 않았습니다. '설정' 페이지에서 키를 입력해주세요.")
        return None

    try:
        genai.configure(api_key=st.session_state.gemini_api_key)
        model = genai.GenerativeModel(
            model_name="gemini-2.5-pro-preview-06-05", # Corrected model name
            system_instruction="You are an expert YouTube content creator and analyst. You analyze scripts, comments, and channel data to provide actionable insights. Please respond in Korean."
        )

        response = model.generate_content(prompt, stream=stream)
        
        if stream:
            full_response = ""
            response_container = st.empty()
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    response_container.markdown(full_response)
                    time.sleep(0.05) # Small delay for better streaming effect
            return full_response
        else:
            return response.text

    except Exception as e:
        st.error(f"Gemini API 호출 중 오류 발생: {e}")
        return None 