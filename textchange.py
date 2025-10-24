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
            return None, "유효하지 않은 URL입니다."

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

        return text, None

    except requests.exceptions.Timeout:
        return None, "요청 시간이 초과되었습니다."
    except requests.exceptions.RequestException as e:
        return None, f"URL 접근 오류: {str(e)}"
    except Exception as e:
        return None, f"오류 발생: {str(e)}"


def replace_text(original_text, find_word, replace_word):
    """텍스트에서 특정 단어를 교체하는 함수"""
    replaced_text = original_text.replace(find_word, replace_word)
    count = original_text.count(find_word)
    return replaced_text, count


# Streamlit 앱 UI
def main():
    st.set_page_config(page_title="텍스트 교체 앱", page_icon="🔄", layout="wide")

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

    col_a, col_b = st.columns(2)

    with col_a:
        find_word = st.text_input(
            "2️⃣ 교체하고 싶은 단어",
            placeholder="찾을 단어",
            help="원본 텍스트에서 찾을 단어를 입력하세요",
        )

    with col_b:
        replace_word = st.text_input(
            "3️⃣ 교체할 단어",
            placeholder="바꿀 단어",
            help="대체할 새로운 단어를 입력하세요",
        )

    st.markdown("---")

    # 실행 버튼
    if st.button(
        "🚀 텍스트 가져오기 및 교체", type="primary", use_container_width=True
    ):
        # 입력값 검증
        if not url:
            st.error("❌ URL을 입력해주세요.")
            return

        if not find_word:
            st.error("❌ 교체하고 싶은 단어를 입력해주세요.")
            return

        if not replace_word:
            st.warning("⚠️ 교체할 단어가 비어있습니다. 단어를 삭제하시겠습니까?")

        # 진행 상태 표시
        with st.spinner("텍스트를 가져오는 중..."):
            original_text, error = fetch_text_from_url(url)

        if error:
            st.error(f"❌ {error}")
            return

        if not original_text:
            st.error("❌ 텍스트를 가져올 수 없습니다.")
            return

        # 텍스트 교체
        replaced_text, count = replace_text(original_text, find_word, replace_word)

        # 결과 표시
        st.success(f"✅ 텍스트를 성공적으로 가져왔습니다! (총 {count}개 교체됨)")

        # 탭으로 원본/교체본 구분
        tab1, tab2 = st.tabs(["📄 교체된 텍스트", "📋 원본 텍스트"])

        with tab1:
            st.text_area(
                "교체된 텍스트",
                value=replaced_text,
                height=400,
                label_visibility="collapsed",
            )

            # 다운로드 버튼
            st.download_button(
                label="💾 교체된 텍스트 다운로드",
                data=replaced_text.encode("utf-8"),
                file_name="replaced_text.txt",
                mime="text/plain",
            )

        with tab2:
            st.text_area(
                "원본 텍스트",
                value=original_text,
                height=400,
                label_visibility="collapsed",
            )

            # 다운로드 버튼
            st.download_button(
                label="💾 원본 텍스트 다운로드",
                data=original_text.encode("utf-8"),
                file_name="original_text.txt",
                mime="text/plain",
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
