import json
import pandas as pd
import os

# 파일 경로를 스크립트 위치 기준으로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHETYPES_FILE = os.path.join(BASE_DIR, 'archetypes.json')

def load_archetypes():
    """archetypes.json 파일에서 유형 목록을 로드합니다."""
    try:
        with open(ARCHETYPES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # 파일이 없으면 기본값으로 새로 생성
        default_archetypes = [
          {
            "번호": 1, "기 (문제 제기)": "자극적인 욕망 제시 (돈/성/권력)", "승 (예상 밖 전개)": "점점 수상한 흐름",
            "전 (몰입,긴장 유도)": "갑작스러운 반전 상황", "결 (결론/인사이트)": "허무 or 반전 결말", "특징": "유머 + 반전 + 유머"
          }
        ]
        save_archetypes(default_archetypes)
        return default_archetypes

def save_archetypes(archetypes):
    """유형 목록을 archetypes.json 파일에 저장합니다."""
    with open(ARCHETYPES_FILE, 'w', encoding='utf-8') as f:
        json.dump(archetypes, f, ensure_ascii=False, indent=2)

def get_archetypes_table_string():
    """유형 목록을 마크다운 테이블 문자열로 변환합니다."""
    archetypes = load_archetypes()
    if not archetypes:
        return "등록된 유형이 없습니다."
    df = pd.DataFrame(archetypes)
    return df.to_markdown(index=False)

def create_dynamic_prompt(base_prompt_template):
    """Dynamically inserts the archetypes table into a prompt template."""
    table_string = get_archetypes_table_string()
    return base_prompt_template.replace("{archetypes_table}", table_string)

# --- Base Prompt Templates ---

INDIVIDUAL_ANALYSIS_TEMPLATE = """
필수 입력 항목:
- 제목: {title}
- 대본: {script}
- 설명: {description}
- 댓글: {comments}
---
[작업 지시]
1. 먼저 외국어 콘텐츠는 한글로 번역해주세요.
2. 아래에 제시된 기승전결 유형을 참고하여, 주어진 대본이 어떤 유형에 가장 가까운지 분석하고 그 이유를 설명해주세요.
3. 대본의 구조(기-승-전-결)를 분석하고, 개선점을 제안하여 최종 대본을 작성해주세요.
4. 새로운 구조의 대본이라고 판단되면, 9번 항목의 지시에 따라 새로운 유형을 제안해주세요.
5. 유튜브 정책 위반 여부를 검토하고, 문제가 없다면 검색 최적화(SEO)에 유리한 제목, 설명, 해시태그를 제안해주세요.
---
[기승전결 유형 목록]
{archetypes_table}
---
[분석 결과 양식]
(아래 양식에 맞춰서 결과를 작성해주세요)
1. **타겟 정보**: (콘텐츠에 가장 적합한 타겟층을 추정하여 작성)
2. **매력도 분석**: (이 콘텐츠가 타겟에게 얼마나 매력적인지 분석)
3. **구조 분석 (기-승-전-결)**: (대본의 현재 구조를 기-승-전-결로 나누어 분석)
4. **유형 매칭**:
   - **매칭되는 유형 번호**: (위 목록에서 가장 유사한 유형의 번호)
   - **매칭 근거**: (왜 해당 유형으로 판단했는지 구체적인 설명)
5. **유튜브 정책 검토**: (가이드라인 위반 소지 여부 및 내용)
6. **최적화 제안**:
   - **제목**: (후킹을 강화한 30자 이내의 새 제목)
   - **설명**: (SEO 또는 오해 방지를 위한 설명)
   - **해시태그**: (트렌드를 반영한 해시태그 5개)
7. **최종 추천 대본**: (위 분석과 제안을 모두 반영하여 재구성한 최종 대본)
8. **썸네일 추천**: (내용을 잘 나타내면서도 시선을 끄는 썸네일 아이디어)
9. **새로운 유형 제안**: (기존 유형과 다르다고 판단될 경우, |번호|기|승|전|결|특징| 형식으로 새 유형 제시. 해당 없으면 "해당 없음"으로 작성)
10. **원본 검색 키워드**: (콘텐츠의 원본을 찾을 수 있는 검색어 제안 - 한국어, 영어, 중국어)
11. **유사 소재 추천**: (분석된 구조와 유사한 다른 소재나 아이템 제안)
"""

CHANNEL_ANALYSIS_TEMPLATE = """
다음 유튜브 채널의 쇼츠 영상 대본을 분석하여 아래의 형식대로 상세한 보고서를 작성해주세요.
채널명: {channel_name}
---
[기승전결 유형 목록]
{archetypes_table}
---
[분석 지시사항]
1.  **콘텐츠 구조 분석**: 제공된 스크립트들을 바탕으로 채널의 전체적인 기승전결 구조 흐름을 분석해주세요.
2.  **주요 패턴 분석**: 위 '기승전결 유형 목록'을 참고하여, 이 채널이 주로 사용하는 패턴은 무엇인지 비율과 함께 설명해주세요.
3.  **언어 및 표현 스타일**: 채널의 어조, 반복 표현, 마무리 문장 등의 특징을 분석해주세요.
4.  **주제 및 소재 분포**: 어떤 주제의 영상을 주로 다루는지 분석해주세요.
5.  **후킹 전략**: 시청자의 시선을 끄는 전략은 무엇인지 분석해주세요.
6.  **개선 아이디어 제안**: 분석 결과를 바탕으로 채널이 더 성장할 수 있는 아이디어를 제안해주세요.
---
[스크립트 모음]
{all_scripts}
"""

DRAMA_ANALYSIS_PROMPT = """당신은 드라마 스토리텔링 전문가입니다. 유튜브 영상의 스크립트와 댓글을 분석하여 다음 항목에 대해 심층적으로 분석해주세요:

1. 이야기 구조 분석: 드라마 영상의 3막 구조와 절정 포인트는 무엇인가?
2. 캐릭터 발전: 등장인물들의 아크와 발전 과정을 분석
3. 갈등 요소: 주요 갈등과 그 해결 방식에 대한 분석
4. 주제와 메시지: 드라마가 전달하고자 하는 핵심 주제는 무엇인가?
5. 감정적 요소: 시청자들의 감정적 반응을 이끌어내는 요소들
6. 시청자 반응: 댓글에서 나타나는 시청자들의 주요 반응 패턴
7. 유사 드라마: 비슷한 구조나 사건을 가진 다른 드라마 작품 추천
8. 개선 제안: 스토리텔링 측면에서 더 향상될 수 있는 부분
9. 확장 가능성: 이 드라마가 시리즈로 확장될 경우의 발전 방향
10. 인상적인 대사: 가장 효과적이었던 대사와 그 이유
11. 비슷한 주제를 다루고 싶다면 어떤 드라마 작품들을 참고하면 좋을지 추천
12. 비슷한 드라마 소재를 활용해 새로운 콘텐츠를 만들고 싶다면 어떤 방향으로 접근할 수 있을지 제안

분석은 구체적이고 세부적으로 진행하며, 예시와 함께 설명해주세요. 드라마의 강점과 개선점을 균형 있게 다루어 콘텐츠 제작자에게 유용한 피드백이 될 수 있도록 해주세요.
"""

POLITICS_ANALYSIS_PROMPT = INDIVIDUAL_ANALYSIS_TEMPLATE # For now, politics uses the same template
COMPARE_ANALYSIS_PROMPT = """(이전 대본 비교 프롬프트 내용과 동일)"""

# Dynamically create the final prompts
INDIVIDUAL_ANALYSIS_PROMPT = create_dynamic_prompt(INDIVIDUAL_ANALYSIS_TEMPLATE)
CHANNEL_ANALYSIS_PROMPT = create_dynamic_prompt(CHANNEL_ANALYSIS_TEMPLATE)