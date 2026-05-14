# 급식 조회 FastAPI 백엔드

Windows exe / Linux deb 클라이언트가 NEIS Open API를 직접 호출하지 않도록 중간에서 급식 정보를 조회하는 FastAPI MVP입니다.

클라이언트는 이 백엔드만 호출하고, `NEIS_API_KEY`는 백엔드 환경변수에만 둡니다. API 응답에는 NEIS API 키를 포함하지 않습니다.

## 실행 방법

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Windows PowerShell에서는 가상환경 활성화 명령만 다음처럼 사용하면 됩니다.

```powershell
.\.venv\Scripts\Activate.ps1
```

## .env 설정

`.env.example`을 복사해서 `.env`를 만듭니다.

```bash
cp .env.example .env
```

설정 예시:

```env
NEIS_API_KEY= # NEIS API 키
SCHOOL_NAME=경북소프트웨어마이스터고등학교
DEFAULT_REGION_CODE=R10
DEFAULT_SCHOOL_CODE=8750829
CORS_ORIGINS=*
```

이 백엔드는 경북소프트웨어마이스터고등학교 전용 MVP입니다. `DEFAULT_REGION_CODE`와 `DEFAULT_SCHOOL_CODE` 값으로 바로 급식을 조회하며, 학교 검색 API는 제공하지 않습니다.

`CORS_ORIGINS`는 `*` 또는 쉼표로 구분한 origin 목록을 사용할 수 있습니다.

## API 목록

### GET /health

헬스 체크입니다.

```json
{
  "status": "ok"
}
```

### GET /api/meals/today

한국 시간 기준 오늘 급식을 조회합니다.

### GET /api/meals/date/{date}

특정 날짜 급식을 조회합니다.

허용 형식:

- `20260513`
- `2026-05-13`

응답 예시:

```json
{
  "date": "2026-05-13",
  "school": {
    "name": "경북소프트웨어마이스터고등학교",
    "region_code": "R10",
    "school_code": "8750829"
  },
  "lunch": ["쌀밥", "김치찌개", "돈까스"],
  "dinner": ["볶음밥", "계란국"]
}
```

## curl 테스트

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/meals/today
curl http://localhost:8000/api/meals/date/20260513
```

## 에러 응답

- 학교 코드 설정 없음: `404 {"detail":"School not found"}`
- 급식 없음: `404 {"detail":"Meal not found"}`
- 날짜 형식 오류: `400 {"detail":"Invalid date format"}`
- NEIS API 오류: `502 {"detail":"Failed to fetch data from NEIS"}`

## 캐싱

DB 없이 dict 기반 in-memory cache를 사용합니다.

- 급식 결과: 다음날 00:10까지

캐시는 프로세스 메모리에 저장되므로 서버를 재시작하면 비워집니다.
