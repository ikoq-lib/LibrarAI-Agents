import streamlit as st
import pandas as pd
import requests
import time
from io import BytesIO
from urllib.parse import urlencode
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

st.set_page_config(page_title="ISBN 서지정보 조회기 v2", layout="wide")

st.title("ISBN 서지정보 조회기 v2")
st.caption("공공데이터포털 국립중앙도서관 서지 정보 제공 서비스 /getbookList 활용")

DEFAULT_BASE_URL = "https://apis.data.go.kr/1371029/BookInformationService/getbookList"

with st.sidebar:
    st.header("API 설정")
    service_key = st.text_input("공공데이터포털 인증키", type="password")
    base_url = st.text_input("/getbookList 호출 URL", value=DEFAULT_BASE_URL)
    json_param_name = st.selectbox("JSON 응답 파라미터명", ["_type", "type", "resultType"], index=0)
    isbn_param_name = st.text_input("ISBN 요청 파라미터명", value="isbn")
    timeout_sec = st.number_input("응답 대기시간(초)", min_value=5, max_value=180, value=60, step=5)
    delay_sec = st.number_input("건별 호출 간격(초)", min_value=0.0, max_value=5.0, value=0.5, step=0.1)
    max_retry = st.number_input("재시도 횟수", min_value=0, max_value=5, value=2, step=1)

st.info(
    "Read timed out 오류는 API 서버가 정해진 시간 안에 응답하지 않았다는 뜻입니다. "
    "v2에서는 대기시간을 60초로 늘리고, 재시도 기능과 단건 테스트 기능을 추가했습니다."
)

uploaded_file = st.file_uploader("ISBN 목록 엑셀 파일을 업로드하세요", type=["xlsx", "xls"])


def clean_isbn(value):
    if pd.isna(value):
        return ""
    value = str(value).strip()
    # 엑셀에서 숫자로 읽히며 .0이 붙는 경우 처리
    if value.endswith(".0"):
        value = value[:-2]
    return value.replace("-", "").replace(" ", "").strip()


def make_session():
    session = requests.Session()
    retry = Retry(
        total=int(max_retry),
        connect=int(max_retry),
        read=int(max_retry),
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 ISBN-BookInfo-Checker/1.0",
        "Accept": "application/json, application/xml, text/plain, */*",
    })
    return session


def build_params(isbn):
    return {
        "serviceKey": service_key,
        "pageNo": 1,
        "numOfRows": 10,
        json_param_name: "json",
        isbn_param_name: isbn,
    }


def mask_key_url(url, params):
    safe = dict(params)
    if "serviceKey" in safe and safe["serviceKey"]:
        safe["serviceKey"] = "인증키_숨김"
    return url + "?" + urlencode(safe)


def find_items(obj):
    """응답 구조가 달라도 item/items를 최대한 찾아냅니다."""
    if obj is None:
        return []
    if isinstance(obj, list):
        return obj
    if not isinstance(obj, dict):
        return []

    # 흔한 공공데이터 구조
    body = obj.get("response", {}).get("body", {}) if isinstance(obj.get("response"), dict) else {}
    items = body.get("items") if isinstance(body, dict) else None
    if isinstance(items, dict):
        item = items.get("item")
        if isinstance(item, list):
            return item
        if isinstance(item, dict):
            return [item]
    if isinstance(items, list):
        return items

    # 다른 구조 방어
    for key in ["items", "item", "docs", "doc", "data", "list", "result", "book"]:
        val = obj.get(key)
        if isinstance(val, list):
            return val
        if isinstance(val, dict):
            # item이 단일 객체일 수 있음
            if key in ["item", "doc", "book"]:
                return [val]
            nested = find_items(val)
            if nested:
                return nested

    for val in obj.values():
        if isinstance(val, (dict, list)):
            nested = find_items(val)
            if nested:
                return nested

    return []


def pick(book, candidates):
    for key in candidates:
        value = book.get(key)
        if value not in [None, ""]:
            return value
    return ""


def get_book_info(isbn, session):
    params = build_params(isbn)
    try:
        response = session.get(base_url, params=params, timeout=(10, int(timeout_sec)))
        raw_text = response.text[:1000]

        if response.status_code != 200:
            return {
                "조회상태": "실패",
                "오류내용": f"HTTP {response.status_code}",
                "요청URL확인용": mask_key_url(base_url, params),
                "원문응답": raw_text,
            }

        try:
            data = response.json()
        except Exception:
            return {
                "조회상태": "실패",
                "오류내용": "JSON 파싱 실패 - XML/HTML 또는 오류문이 반환되었을 수 있음",
                "요청URL확인용": mask_key_url(base_url, params),
                "원문응답": raw_text,
            }

        # 공공데이터 오류 메시지 확인
        header = data.get("response", {}).get("header", {}) if isinstance(data, dict) else {}
        result_code = str(header.get("resultCode", ""))
        result_msg = header.get("resultMsg", "")
        if result_code and result_code not in ["00", "0", "NORMAL SERVICE."]:
            return {
                "조회상태": "실패",
                "오류내용": f"API 오류: {result_code} {result_msg}",
                "요청URL확인용": mask_key_url(base_url, params),
                "원문응답": raw_text,
            }

        items = find_items(data)
        if not items:
            return {
                "조회상태": "검색결과 없음",
                "오류내용": result_msg or "item/items를 찾지 못함",
                "요청URL확인용": mask_key_url(base_url, params),
                "원문응답": raw_text,
            }

        book = items[0] if isinstance(items[0], dict) else {}
        return {
            "조회상태": "성공",
            "오류내용": "",
            "도서명": pick(book, ["title", "bookname", "bookName", "titleInfo", "titleStatement", "book_title"]),
            "저자": pick(book, ["author", "authors", "authorInfo", "creator", "creatorInfo", "name"]),
            "출판사": pick(book, ["publisher", "publisherInfo", "pub", "pubName", "provider"]),
            "발행연도": pick(book, ["pubYear", "publicationYear", "publishYear", "issued", "date", "pubDate"]),
            "ISBN": pick(book, ["isbn", "isbn13", "EA_ISBN", "setIsbn"]) or isbn,
            "자료유형": pick(book, ["type", "resourceType", "format", "mediaType"]),
            "원자료ID": pick(book, ["controlNo", "id", "docId", "uci", "bibId"]),
            "요청URL확인용": mask_key_url(base_url, params),
        }

    except requests.exceptions.ReadTimeout:
        return {
            "조회상태": "실패",
            "오류내용": f"Read timed out - API 서버가 {timeout_sec}초 안에 응답하지 않음",
            "요청URL확인용": mask_key_url(base_url, params),
        }
    except requests.exceptions.ConnectTimeout:
        return {
            "조회상태": "실패",
            "오류내용": "Connect timed out - apis.data.go.kr 접속 자체가 지연됨",
            "요청URL확인용": mask_key_url(base_url, params),
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "조회상태": "실패",
            "오류내용": f"ConnectionError - 네트워크/DNS/방화벽 또는 서버 접속 문제: {e}",
            "요청URL확인용": mask_key_url(base_url, params),
        }
    except Exception as e:
        return {
            "조회상태": "실패",
            "오류내용": str(e),
            "요청URL확인용": mask_key_url(base_url, params),
        }


st.subheader("단건 테스트")
test_isbn = st.text_input("먼저 ISBN 1건으로 테스트하세요", value="9791199239098")
if st.button("단건 테스트 실행"):
    if not service_key:
        st.error("공공데이터포털 인증키를 입력해야 합니다.")
    else:
        session = make_session()
        result = get_book_info(clean_isbn(test_isbn), session)
        st.write(result)

if uploaded_file:
    df = pd.read_excel(uploaded_file, dtype=str)
    st.subheader("업로드한 엑셀 미리보기")
    st.dataframe(df.head())

    isbn_col = st.selectbox("ISBN이 들어 있는 열을 선택하세요", df.columns)

    if st.button("서지정보 조회 시작"):
        if not service_key:
            st.error("공공데이터포털 인증키를 입력해야 합니다.")
        else:
            result_rows = []
            progress = st.progress(0)
            status = st.empty()
            session = make_session()

            isbn_list = df[isbn_col].apply(clean_isbn).tolist()
            total = len(isbn_list)

            for i, isbn in enumerate(isbn_list):
                status.write(f"조회 중: {i + 1}/{total} - {isbn}")
                if not isbn:
                    result = {"조회상태": "실패", "오류내용": "ISBN 없음"}
                else:
                    result = get_book_info(isbn, session)

                original_row = df.iloc[i].to_dict()
                merged_row = {**original_row, "정리ISBN": isbn, **result}
                result_rows.append(merged_row)
                progress.progress((i + 1) / total)
                time.sleep(float(delay_sec))

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
