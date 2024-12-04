# 카페 다이어리 프로젝트

카페 다이어리는 사용자의 카페 방문 경험을 기록하고 공유할 수 있는 웹 애플리케이션입니다. 영수증 OCR 기능과 지도 시각화를 통해 사용자의 카페 방문 기록을 효과적으로 관리할 수 있습니다.

## 주요 기능

- 회원 가입 및 로그인
- 영수증 OCR을 통한 자동 정보 추출
  - 카페 이름
  - 방문 날짜/시간
  - 주문 메뉴
  - 결제 금액
- 카카오맵 기반 방문 카페 위치 시각화
- 카페 방문 기록 관리
- 카페 리뷰 및 평점 시스템

## 기술 스택

- Backend: Flask (Python)
- Frontend: HTML, CSS, JavaScript
- Database: SQLite
- OCR: Tesseract
- Map: Kakao Maps API
- UI Framework: Bootstrap 5

## 설치 방법

1. 프로젝트 클론
```bash
git clone [repository-url]
cd cafe-diary
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
```

3. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

4. Tesseract OCR 설치 (macOS)
```bash
brew install tesseract
brew install tesseract-lang
```

5. 환경 변수 설정
- `.env` 파일을 생성하고 다음 내용을 추가:
```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
KAKAO_MAP_API_KEY=your-kakao-map-api-key
```

## 실행 방법

1. 데이터베이스 초기화
```bash
flask db upgrade
```

2. 개발 서버 실행
```bash
flask run
```

3. 웹 브라우저에서 접속
```
http://localhost:5000
```

## 주의사항

1. Kakao Maps API 키 발급
- [Kakao Developers](https://developers.kakao.com)에서 애플리케이션을 등록하고 JavaScript 키를 발급받아야 합니다.
- 발급받은 키를 `templates/base.html`의 Kakao Maps API 스크립트 태그에 입력해주세요.

2. OCR 인식률 향상
- 영수증 이미지는 밝고 선명하게 촬영해주세요.
- 가능한 영수증이 프레임 안에 꽉 차도록 촬영해주세요.

## 기여 방법

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.
