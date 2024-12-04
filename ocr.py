import cv2
import pytesseract
import re
import pandas as pd
from datetime import datetime, timedelta
from PIL import Image

# Tesseract 경로 설정 (윈도우의 경우 필요시 수정)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# OCR로 텍스트 추출 함수
def extract_text_from_image(image):
    # OCR을 이용해 텍스트 추출
    extracted_text = pytesseract.image_to_string(image, lang='eng')
    return extracted_text

# 영수증 정보 파싱 함수
def parse_receipt_text(text):
    lines = text.split('\n')
    items = []
    prices = []
    date = None

    for line in lines:
        line = line.strip()
        # 날짜 정보 찾기 (예: YYYY-MM-DD 또는 DD/MM/YYYY 형식)
        date_match = re.search(r'(\d{4}[\-/]\d{2}[\-/]\d{2})|(\d{2}[\-/]\d{2}[\-/]\d{4})', line)
        if date_match and date is None:
            date = date_match.group()
        # 항목과 가격이 있는 라인 찾기 (간단한 패턴 매칭)
        match = re.match(r'(.+)\s+(\d+[,.]?\d*)$', line)
        if match:
            item, price = match.groups()
            items.append(item)
            prices.append(price)

    # 데이터프레임으로 정리
    receipt_df = pd.DataFrame({'Item': items, 'Price': prices})
    if date:
        receipt_df['Date'] = date
    return receipt_df, date

# 주차 비용 계산 함수
def calculate_parking_fee(entry_time_str, total_amount, is_today):
    # 현재 시각 가져오기
    current_time = datetime.now()
    # 입차 시간 변환
    entry_time = datetime.strptime(entry_time_str, '%Y-%m-%d %H:%M')
    # 주차 시간 계산 (시간 단위)
    parking_duration = (current_time - entry_time).total_seconds() / 3600
    # 1시간당 10000원 비용 계산
    total_fee = max(0, parking_duration * 10000)
    
    # 영수증 금액이 10000원 이상이고 날짜가 오늘이면 2시간 주차비 감면
    if float(total_amount) >= 10000 and is_today:
        discount = 2 * 10000
        total_fee = max(0, total_fee - discount)
    
    return total_fee

# 메인 함수
def main():
    cam = cv2.VideoCapture(0)
    print("Press 'Enter' to capture the receipt image or 'q' to quit.")
    
    while True:
        ret, frame = cam.read()
        if not ret:
            print("Failed to grab frame")
            break
        
        cv2.imshow("Live Camera - Show Receipt", frame)
        
        key = cv2.waitKey(1)
        if key == 13:  # Enter key
            # 텍스트 추출
            extracted_text = extract_text_from_image(frame)
            print("Extracted Text:\n", extracted_text)
            
            # 영수증 정보 파싱
            receipt_data, date = parse_receipt_text(extracted_text)
            print("\nParsed Receipt Data:\n", receipt_data)
            is_today = False
            if date:
                print("\nExtracted Date:", date)
                # 오늘 날짜와 비교
                today = datetime.now().strftime('%Y-%m-%d')
                try:
                    receipt_date = datetime.strptime(date, '%Y-%m-%d') if '-' in date else datetime.strptime(date, '%d/%m/%Y')
                    today_date = datetime.now()
                    date_diff = (today_date - receipt_date).days
                    if date_diff == 0:
                        print("\nThe receipt date is today.")
                        is_today = True
                    else:
                        print("\nThe receipt date is not today. No discount will be applied.")
                except ValueError:
                    print("\nUnable to compare dates due to incorrect format.")
                    return receipt_data, date
            
            # 주차비 계산
            entry_time_str = input("Enter entry time (YYYY-MM-DD HH:MM): ")
            total_amount = receipt_data['Price'].astype(float).sum() if not receipt_data.empty else 0
            total_fee = calculate_parking_fee(entry_time_str, total_amount, is_today)
            print(f"\nTotal Parking Fee: {total_fee:.2f} KRW")

            # 데이터 파일로 저장
            receipt_data.to_csv('receipt_data.csv', index=False)
            print("\nReceipt data has been saved to 'receipt_data.csv'")

            break
        elif key == ord('q'):  # 'q' key to quit
            break

    cam.release()
    cv2.destroyAllWindows()

# 실행 부분
if __name__ == "__main__":
    main()