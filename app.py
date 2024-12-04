from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from PIL import Image
import pytesseract
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # 실제 배포 시에는 환경 변수로 관리
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafe_diary.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Google Maps API 설정
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', 'your-api-key-here')  # 실제 키로 교체 필요

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 데이터베이스 모델
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    cafes = db.relationship('CafeVisit', backref='user', lazy=True)
    receipts = db.relationship('Receipt', backref='user', lazy=True)

class CafeVisit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cafe_name = db.Column(db.String(100), nullable=False)
    visit_date = db.Column(db.DateTime, nullable=False)
    menu_items = db.Column(db.Text)
    total_price = db.Column(db.Float)
    location = db.Column(db.String(200))
    rating = db.Column(db.Float)
    comment = db.Column(db.Text)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    store_name = db.Column(db.String(100), nullable=False)
    visit_date = db.Column(db.DateTime, nullable=False)
    total_amount = db.Column(db.Float)
    menu_items = db.relationship('MenuItem', backref='receipt', lazy=True, cascade='all, delete-orphan')

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipt.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 데이터베이스 초기화
with app.app_context():
    # 테이블이 없을 때만 생성
    db.create_all()
    
    # 테스트 사용자 생성 (없는 경우에만)
    test_user = User.query.filter_by(username='test').first()
    if not test_user:
        test_user = User(
            username='test',
            email='test@example.com',
            password_hash=generate_password_hash('test123')
        )
        db.session.add(test_user)
        db.session.commit()
        print("Test user created successfully")
    
    print("Database initialized successfully")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
            
        user = User(username=username, 
                   email=email,
                   password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
            
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    visits = CafeVisit.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', 
                         visits=visits,
                         google_maps_api_key=GOOGLE_MAPS_API_KEY,
                         kakao_map_api_key=os.getenv('KAKAO_MAP_API_KEY', 'your-kakao-api-key'))

@app.route('/upload_receipt', methods=['POST'])
@login_required
def upload_receipt():
    try:
        print("\n=== Receipt Upload Started ===")
        print(f"Request Files: {request.files}")
        print(f"Request Form: {request.form}")
        
        if 'receipt' not in request.files:
            print("No file in request")
            return jsonify({'error': '파일이 업로드되지 않았습니다.'}), 400
            
        file = request.files['receipt']
        print(f"Received file: {file.filename}, Content Type: {file.content_type}")
        
        if file.filename == '':
            print("Empty filename")
            return jsonify({'error': '선택된 파일이 없습니다.'}), 400
        
        try:
            # 이미지 파일 열기
            image = Image.open(file.stream)
            print(f"Opened image: {file.filename}, Mode: {image.mode}, Size: {image.size}")
            
            # OCR 처리
            from utils.ocr_helper import extract_receipt_info
            receipt_info = extract_receipt_info(image)
            print("Receipt info extracted successfully")
            print(f"Extracted Receipt Info: {receipt_info}")
            
            # 영수증 정보 저장
            try:
                # Receipt 테이블에 저장
                receipt = Receipt(
                    user_id=current_user.id,
                    store_name=receipt_info['store_name'],
                    visit_date=receipt_info['datetime'],
                    total_amount=receipt_info['total_price']
                )
                db.session.add(receipt)
                db.session.flush()
                print(f"Created receipt record: {receipt.id}")
                
                # 메뉴 항목 저장
                menu_items_text = []
                for item in receipt_info['menu_items']:
                    menu_item = MenuItem(
                        receipt_id=receipt.id,
                        name=item['name'],
                        price=item['price']
                    )
                    db.session.add(menu_item)
                    menu_items_text.append(f"{item['name']}: {item['price']}원")
                    print(f"Added menu item: {item['name']} - {item['price']}원")
                
                # CafeVisit 테이블에도 저장
                cafe_visit = CafeVisit(
                    user_id=current_user.id,
                    cafe_name=receipt_info['store_name'],
                    visit_date=receipt_info['datetime'],
                    menu_items='\n'.join(menu_items_text),
                    total_price=receipt_info['total_price'],
                    latitude=37.5665,  # 기본값으로 서울 시청 좌표 사용
                    longitude=126.9780
                )
                db.session.add(cafe_visit)
                print("Added cafe visit record")
                
                db.session.commit()
                print("Receipt, menu items, and cafe visit saved to database successfully")
                
                return jsonify({
                    'success': True,
                    'message': '영수증이 성공적으로 처리되었습니다.',
                    'receipt_info': {
                        'store_name': receipt_info['store_name'],
                        'datetime': receipt_info['datetime'].strftime('%Y-%m-%d %H:%M'),
                        'menu_items': receipt_info['menu_items'],
                        'total_price': receipt_info['total_price']
                    }
                })
                
            except Exception as e:
                print(f"Database error: {str(e)}")
                db.session.rollback()
                return jsonify({'error': f'데이터베이스 저장 중 오류가 발생했습니다: {str(e)}'}), 500
            
        except Exception as e:
            print(f"OCR processing error: {str(e)}")
            return jsonify({'error': f'영수증 처리 중 오류가 발생했습니다: {str(e)}'}), 500
            
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'서버 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/update_visit/<int:visit_id>', methods=['POST'])
@login_required
def update_visit(visit_id):
    visit = CafeVisit.query.get_or_404(visit_id)
    if visit.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.json
    visit.cafe_name = data.get('cafe_name', visit.cafe_name)
    visit.location = data.get('location', visit.location)
    visit.rating = float(data.get('rating', visit.rating))
    visit.comment = data.get('comment', visit.comment)
    visit.latitude = float(data.get('latitude', visit.latitude))
    visit.longitude = float(data.get('longitude', visit.longitude))
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/add_visit', methods=['POST'])
@login_required
def add_visit():
    data = request.json
    visit = CafeVisit(
        user_id=current_user.id,
        cafe_name=data['cafe_name'],
        visit_date=datetime.strptime(data['visit_date'], '%Y-%m-%d %H:%M'),
        menu_items=data['menu_items'],
        total_price=float(data['total_price']),
        location=data['location'],
        rating=float(data['rating']),
        comment=data['comment'],
        latitude=float(data['latitude']),
        longitude=float(data['longitude'])
    )
    db.session.add(visit)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/search_places', methods=['POST'])
def search_places():
    query = request.form.get('query')
    try:
        # Places API를 사용하여 장소 검색
        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_place_details/<place_id>')
def get_place_details(place_id):
    try:
        # Places API를 사용하여 장소 상세 정보 가져오기
        url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/calculate_distance', methods=['POST'])
def calculate_distance():
    origin = request.form.get('origin')
    destination = request.form.get('destination')
    try:
        # Distance Matrix API를 사용하여 거리 계산
        url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
