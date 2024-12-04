import cv2
import pytesseract
import re
import pandas as pd
from datetime import datetime
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
    time = None
    store_name = None
    store_location = None

    for line in lines:
        line = line.strip()
        # 날짜 정보 찾기 (예: YYYY-MM-DD 또는 DD/MM/YYYY 형식)
        date_match = re.search(r'(\d{4}[\-/]\d{2}[\-/]\d{2})|(\d{2}[\-/]\d{2}[\-/]\d{4})', line)
        if date_match and date is None:
            date = date_match.group()
        # 시간 정보 찾기 (예: HH:MM 형식)
        time_match = re.search(r'\b(\d{2}:\d{2})\b', line)
        if time_match and time is None:
            time = time_match.group()
        # 매장 이름 및 위치 추출 (예: 특정 키워드를 포함한 라인)
        if "Store" in line or "Location" in line or "Address" in line:
            if store_name is None:
                store_name = line
            elif store_location is None:
                store_location = line
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
    if time:
        receipt_df['Time'] = time
    if store_name:
        receipt_df['Store Name'] = store_name
    if store_location:
        receipt_df['Store Location'] = store_location

    return receipt_df, date, time, store_name, store_location

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
            receipt_data, date, time, store_name, store_location = parse_receipt_text(extracted_text)
            print("\nParsed Receipt Data:\n", receipt_data)
            
            if date:
                print("\nExtracted Date:", date)
            if time:
                print("\nExtracted Time:", time)
            if store_name:
                print("\nStore Name:", store_name)
            if store_location:
                print("\nStore Location:", store_location)
            
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
