import streamlit as st
import pandas as pd
import requests
import time
from io import BytesIO

st.set_page_config(page_title="ISBN 서지정보 조회기", layout="wide")

st.title("ISBN 서지정보 조회기")
st.caption("공공데이터포털 국립중앙도서관 서지 정보 제공 서비스 /getbookList 활용")

service_key = st.text_input("공공데이터포털 인증키를 입력하세요", type="password")

uploaded_file = st.file_uploader("ISBN 목록 엑셀 파일을 업로드하세요", type=["xlsx", "xls"])

BASE_URL = "https://apis.data.go.kr/1371029/BookInformationService/getbookList"


def clean_isbn(value):
    """ISBN 값에서 하이픈, 공백 등을 제거합니다."""
    if pd.isna(value):
        return ""
    return str(value).replace("-", "").replace(" ", "").strip()


def extract_items(data):
    """
    공공데이터 응답 구조가 서비스별로 약간 다를 수 있어
    여러 구조를 방어적으로 처리합니다.
    """
    if not isinstance(data, dict):
        return []

    body = data.get("response", {}).get("body", {})
    items = body.get("items", [])

    if isinstance(items, dict):
        item = items.get("item", [])
        if isinstance(item, list):
            return item
        if isinstance(item, dict):
            return [item]

    if isinstance(items, list):
        return items

    return []


def get_book_info(isbn, service_key):
    """ISBN 1건에 대해 /getbookList API를 호출하고 주요 서지정보를 반환합니다."""
    params = {
        "serviceKey": service_key,
        "pageNo": 1,
        "numOfRows": 10,
        "type": "json",
        "isbn": isbn,
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=15)

        if response.status_code != 200:
            return {
                "조회상태": "실패",
                "오류내용": f"HTTP {response.status_code}",
            }

        try:
            data = response.json()
        except Exception:
            return {
                "조회상태": "실패",
                "오류내용": "JSON 파싱 실패",
                "원문응답": response.text[:500],
            }

        items = extract_items(data)

        if not items:
            return {
                "조회상태": "검색결과 없음",
                "오류내용": "",
            }

        book = items[0]

        return {
            "조회상태": "성공",
            "오류내용": "",
            "도서명": book.get("title") or book.get("bookname") or book.get("titleInfo") or "",
            "저자": book.get("author") or book.get("authorInfo") or "",
            "출판사": book.get("publisher") or book.get("publisherInfo") or "",
            "발행연도": book.get("pubYear") or book.get("publicationYear") or "",
            "ISBN": book.get("isbn") or isbn,
            "자료유형": book.get("type") or book.get("resourceType") or "",
            "원자료ID": book.get("controlNo") or book.get("id") or "",
        }

    except Exception as e:
        return {
            "조회상태": "실패",
            "오류내용": str(e),
        }


if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("업로드한 엑셀 미리보기")
    st.dataframe(df.head())

    isbn_col = st.selectbox("ISBN이 들어 있는 열을 선택하세요", df.columns)

    if st.button("서지정보 조회 시작"):
        if not service_key:
            st.error("공공데이터포털 인증키를 입력해야 합니다.")
        else:
            result_rows = []
            progress = st.progress(0)

            isbn_list = df[isbn_col].apply(clean_isbn).tolist()
            total = len(isbn_list)

            for i, isbn in enumerate(isbn_list):
                if not isbn:
                    result = {
                        "조회상태": "실패",
                        "오류내용": "ISBN 없음",
                    }
                else:
                    result = get_book_info(isbn, service_key)

                original_row = df.iloc[i].to_dict()
                merged_row = {
                    **original_row,
                    "정리ISBN": isbn,
                    **result,
                }

                result_rows.append(merged_row)
                progress.progress((i + 1) / total)

                # API 과호출 방지
                time.sleep(0.15)

            result_df = pd.DataFrame(result_rows)

            st.success("조회가 완료되었습니다.")
            st.dataframe(result_df)

            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                result_df.to_excel(writer, index=False, sheet_name="서지정보조회결과")

            st.download_button(
                label="결과 엑셀 다운로드",
                data=output.getvalue(),
                file_name="ISBN_서지정보_조회결과.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
