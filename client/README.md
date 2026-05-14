# 경소고 급식 Windows 트레이 앱

FastAPI 백엔드에서 급식 정보를 받아 작업표시줄 트레이에 작은 위젯으로 보여주는 Windows 클라이언트입니다.

## 실행 준비

```bash
cd client
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Windows PowerShell:

```powershell
cd client
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

.env_example을 참고하여 환경변수를 설정해야 합니다.

## 개발 실행

백엔드를 먼저 실행합니다.

```bash
cd ../backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

클라이언트를 실행합니다.

```bash
cd ../client
python -m app.main
```

앱이 실행되면 작업표시줄 트레이에 아이콘이 생기고, 시작과 동시에 오늘 급식 위젯이 열립니다.

## 기능

- 실행 시 오늘 급식 표시
- 트레이 아이콘 클릭 시 급식 위젯 열기
- 새로고침
- 급식 복사
- 작은 날짜 조회
- 화이트/다크 테마 선택
- 우클릭 메뉴에서 급식 보기, 새로고침, 종료

## exe 빌드

Windows에서 실행합니다.

```bat
packaging\windows\build.bat
```

pywebview와 트레이 의존성을 단일 exe로 묶기 때문에 몇 분 정도 걸릴 수 있습니다. `Building single exe` 단계에서 오래 걸리는 것은 정상입니다.

빌드 결과:

```text
dist\WhatsMeal.exe
```

서버 주소를 나중에 바꾸고 싶으면 `WhatsMeal.exe`와 같은 폴더에 `.env` 파일을 추가로 두면 그 값이 우선 적용됩니다.

```env
API_BASE_URL=
REQUEST_TIMEOUT=7
```

## macOS 앱 빌드

macOS에서 실행합니다. Windows나 Linux에서는 macOS 앱을 빌드할 수 없습니다.

```bash
cd client
chmod +x packaging/macos/build-macos.sh
./packaging/macos/build-macos.sh
```

빌드 결과:

```text
dist/WhatsMeal.app
dist/WhatsMeal-macOS.zip
```

배포할 때는 `WhatsMeal-macOS.zip`을 올리면 됩니다. 압축을 풀면 `WhatsMeal.app`이 나옵니다.

## 로그 파일

실행 문제가 있으면 아래 로그를 확인합니다.

```text
%APPDATA%\WhatsMeal\client.log
```

로그에서 `Frozen executable: True`가 보이면 exe로 실행된 것입니다. `False`면 `python -m app.main`으로 실행된 상태입니다.
