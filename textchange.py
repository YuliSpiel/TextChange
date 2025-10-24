# -*- coding: utf-8 -*-
import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def fetch_text_from_url(url):
    """URL에서 텍스트를 가져오는 함수"""
    try:
        # URL 유효성 검사
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return None, None, "유효하지 않은 URL입니다."

        # 헤더 설정 (일부 사이트는 User-Agent 필요)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        # URL에서 콘텐츠 가져오기
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # UTF-8 인코딩 설정
        response.encoding = response.apparent_encoding or "utf-8"

        # HTML 파싱
        soup = BeautifulSoup(response.text, "html.parser")

        # 페이지 타이틀 추출
        title = None
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            # 파일명으로 사용할 수 없는 문자 제거
            title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            # 공백을 언더스코어로 변경
            title = title.replace(' ', '_')

        # 스크립트, 스타일 태그 제거
        for script in soup(["script", "style"]):
            script.decompose()

        # <br> 태그를 줄바꿈으로 변환
        for br in soup.find_all("br"):
            br.replace_with("\n")

        # <p>, <div> 등의 블록 요소 뒤에 줄바꿈 추가
        for tag in soup.find_all(
            [
                "p",
                "div",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
                "li",
                "tr",
                "article",
                "section",
            ]
        ):
            if tag.string:
                tag.string = tag.get_text() + "\n"

        # 텍스트 추출 (원본 형식 완전 유지)
        text = soup.get_text(separator="", strip=False)

        return text, title, None

    except requests.exceptions.Timeout:
        return None, None, "요청 시간이 초과되었습니다."
    except requests.exceptions.RequestException as e:
        return None, None, f"URL 접근 오류: {str(e)}"
    except Exception as e:
        return None, None, f"오류 발생: {str(e)}"


def replace_text(original_text, find_word, replace_word):
    """텍스트에서 특정 단어를 교체하는 함수"""
    replaced_text = original_text.replace(find_word, replace_word)
    count = original_text.count(find_word)
    return replaced_text, count


# Streamlit 앱 UI
def main():
    st.set_page_config(page_title="텍스트 교체 앱", page_icon="🔄", layout="wide")

    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 설정")
        st.markdown("---")

        # 배경색 선택
        bg_color = st.color_picker(
            "배경색 선택",
            value="#FFFFFF",
            help="앱의 배경색을 선택하세요"
        )

        st.markdown("---")

        # 자동 대치 단어 쌍 설정
        st.subheader("🔄 자동 대치 단어 쌍")
        st.caption("모든 파일에 자동으로 적용됩니다")

        # 자동 대치 단어 쌍 세션 상태 초기화
        if "auto_replace_pairs" not in st.session_state:
            st.session_state.auto_replace_pairs = []

        # 기존 자동 대치 단어 쌍 표시
        if st.session_state.auto_replace_pairs:
            for idx, pair in enumerate(st.session_state.auto_replace_pairs):
                col1, col2, col3 = st.columns([4, 4, 1])

                with col1:
                    st.session_state.auto_replace_pairs[idx]["find"] = st.text_input(
                        f"찾을 단어 {idx + 1}",
                        value=pair["find"],
                        placeholder="찾을 단어",
                        key=f"auto_find_{idx}",
                        label_visibility="collapsed",
                    )

                with col2:
                    st.session_state.auto_replace_pairs[idx]["replace"] = st.text_input(
                        f"바꿀 단어 {idx + 1}",
                        value=pair["replace"],
                        placeholder="바꿀 단어",
                        key=f"auto_replace_{idx}",
                        label_visibility="collapsed",
                    )

                with col3:
                    if st.button("🗑️", key=f"auto_delete_{idx}", help="삭제"):
                        st.session_state.auto_replace_pairs.pop(idx)
                        st.rerun()

        # 자동 대치 단어 쌍 추가 버튼
        if st.button("➕ 자동 대치 추가", use_container_width=True, key="add_auto_pair"):
            st.session_state.auto_replace_pairs.append({"find": "", "replace": ""})
            st.rerun()

        st.markdown("---")
        st.markdown("### 📖 사용 방법")
        st.markdown("""
        1. URL을 입력하세요
        2. 찾을 단어를 입력하세요
        3. 바꿀 단어를 입력하세요
        4. 실행 버튼을 클릭하세요
        """)

    # 배경색 적용을 위한 CSS
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {bg_color};
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("🔄 텍스트 교체 앱")
    st.markdown("---")

    # 사용자 입력 받기
    col1, col2 = st.columns([2, 1])

    with col1:
        url = st.text_input(
            "1️⃣ 텍스트 원본이 있는 링크",
            placeholder="https://example.com/article",
            help="텍스트를 가져올 웹페이지 URL을 입력하세요",
        )

    # 단어 쌍 리스트 세션 상태 초기화
    if "word_pairs" not in st.session_state:
        st.session_state.word_pairs = [{"find": "", "replace": ""}]

    st.subheader("2️⃣ 교체할 단어 쌍 설정")

    # 기존 단어 쌍 표시
    for idx, pair in enumerate(st.session_state.word_pairs):
        col_a, col_b, col_c = st.columns([5, 5, 1])

        with col_a:
            st.session_state.word_pairs[idx]["find"] = st.text_input(
                f"교체하고 싶은 단어 {idx + 1}",
                value=pair["find"],
                placeholder="찾을 단어",
                key=f"find_word_{idx}",
                label_visibility="collapsed" if idx > 0 else "visible",
            )

        with col_b:
            st.session_state.word_pairs[idx]["replace"] = st.text_input(
                f"교체할 단어 {idx + 1}",
                value=pair["replace"],
                placeholder="바꿀 단어",
                key=f"replace_word_{idx}",
                label_visibility="collapsed" if idx > 0 else "visible",
            )

        with col_c:
            # 첫 번째 행이 아닐 때만 삭제 버튼 표시
            if idx > 0:
                if st.button("🗑️", key=f"delete_pair_{idx}", help="삭제"):
                    st.session_state.word_pairs.pop(idx)
                    st.rerun()
            else:
                st.write("")  # 공간 유지

    # 단어 쌍 추가 버튼
    if st.button("➕ 단어 쌍 추가", use_container_width=True):
        st.session_state.word_pairs.append({"find": "", "replace": ""})
        st.rerun()

    st.markdown("---")

    # 실행 버튼
    if st.button(
        "🚀 텍스트 가져오기 및 교체", type="primary", use_container_width=True
    ):
        # 입력값 검증
        if not url:
            st.error("❌ URL을 입력해주세요.")
            return

        # 유효한 단어 쌍이 있는지 확인
        valid_pairs = [pair for pair in st.session_state.word_pairs if pair["find"]]
        if not valid_pairs:
            st.error("❌ 교체하고 싶은 단어를 최소 1개 이상 입력해주세요.")
            return

        # 진행 상태 표시
        with st.spinner("텍스트를 가져오는 중..."):
            original_text, page_title, error = fetch_text_from_url(url)

        if error:
            st.error(f"❌ {error}")
            return

        if not original_text:
            st.error("❌ 텍스트를 가져올 수 없습니다.")
            return

        # 자동 대치 단어 쌍을 먼저 적용
        replaced_text = original_text
        total_count = 0

        # 1. 자동 대치 단어 쌍 적용
        auto_valid_pairs = [pair for pair in st.session_state.auto_replace_pairs if pair["find"]]
        for pair in auto_valid_pairs:
            temp_text, count = replace_text(replaced_text, pair["find"], pair["replace"])
            replaced_text = temp_text
            total_count += count

        # 2. 메인 단어 쌍 적용
        for pair in valid_pairs:
            temp_text, count = replace_text(replaced_text, pair["find"], pair["replace"])
            replaced_text = temp_text
            total_count += count

        # 결과 텍스트를 세션 상태에 저장
        st.session_state.replaced_text = replaced_text
        st.session_state.original_text = original_text
        st.session_state.count = total_count
        st.session_state.page_title = page_title if page_title else "replaced_text"

    # 결과가 있을 때만 표시
    if "replaced_text" in st.session_state:
        replaced_text = st.session_state.replaced_text
        original_text = st.session_state.original_text
        count = st.session_state.count
        page_title = st.session_state.get("page_title", "replaced_text")

        # 결과 표시 (성공 메시지, 파일명 입력, 다운로드 버튼을 같은 행에 배치)
        result_col1, result_col2, result_col3 = st.columns([2, 1, 1])

        with result_col1:
            st.success(f"✅ 텍스트를 성공적으로 가져왔습니다! (총 {count}개 교체됨)")

        with result_col2:
            file_name = st.text_input(
                "파일명",
                value=page_title,
                label_visibility="collapsed",
                placeholder=page_title,
                key="file_name_input"
            )

        with result_col3:
            st.download_button(
                label="💾 다운로드",
                data=replaced_text.encode("utf-8"),
                file_name=f"{file_name}.txt" if file_name else f"{page_title}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        # 탭으로 원본/교체본 구분
        tab1, tab2 = st.tabs(["📄 교체된 텍스트", "📋 원본 텍스트"])

        with tab1:
            st.text_area(
                "교체된 텍스트",
                value=replaced_text,
                height=800,
                label_visibility="collapsed",
            )

        with tab2:
            st.text_area(
                "원본 텍스트",
                value=original_text,
                height=800,
                label_visibility="collapsed",
            )

            # 원본 텍스트 다운로드 (파일명 입력 + 다운로드 버튼)
            original_col1, original_col2 = st.columns([3, 1])

            with original_col1:
                original_file_name = st.text_input(
                    "원본 파일명",
                    value=f"{page_title}_original",
                    label_visibility="collapsed",
                    placeholder=f"{page_title}_original",
                    key="original_file_name_input"
                )

            with original_col2:
                st.download_button(
                    label="💾 다운로드",
                    data=original_text.encode("utf-8"),
                    file_name=f"{original_file_name}.txt" if original_file_name else f"{page_title}_original.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

        # 통계 정보
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("원본 텍스트 길이", f"{len(original_text):,} 자")
        with col2:
            st.metric("교체된 단어 수", f"{count:,} 개")
        with col3:
            st.metric("교체 후 텍스트 길이", f"{len(replaced_text):,} 자")


if __name__ == "__main__":
    main()
