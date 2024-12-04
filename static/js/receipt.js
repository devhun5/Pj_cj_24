class ReceiptHandler {
    constructor(formId, previewId) {
        this.form = document.getElementById(formId);
        this.previewElement = document.getElementById(previewId);
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.form.addEventListener('submit', this.handleSubmit.bind(this));
        const fileInput = this.form.querySelector('input[type="file"]');
        if (fileInput) {
            fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        }
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            // 이미지 미리보기 생성
            const reader = new FileReader();
            reader.onload = (e) => {
                this.previewElement.src = e.target.result;
                this.previewElement.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
    }

    async handleSubmit(event) {
        event.preventDefault();
        console.log('Form submitted');
        
        const formData = new FormData(this.form);
        console.log('File selected:', formData.get('receipt'));
        
        try {
            console.log('Sending request to server...');
            const response = await fetch('/upload_receipt', {
                method: 'POST',
                body: formData
            });

            console.log('Server response received:', response);
            const data = await response.json();
            console.log('Response data:', data);
            
            if (data.success) {
                console.log('OCR successful, populating form...');
                this.populateForm(data.data);
                
                // 성공 메시지 표시
                this.showMessage('영수증이 성공적으로 처리되었습니다.', 'success');
                
                // 지도에 마커 추가
                if (window.cafeMap) {
                    window.cafeMap.addMarker(data.data.latitude, data.data.longitude, {
                        name: data.data.store_name,
                        address: data.data.location,
                        rating: 0
                    });
                }
                
                // 페이지 새로고침
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                throw new Error(data.error || '영수증 처리 중 오류가 발생했습니다.');
            }
            
        } catch (error) {
            console.error('Error processing receipt:', error);
            this.showMessage(error.message, 'error');
        } finally {
            const loadingIndicator = document.getElementById('loading-indicator');
            loadingIndicator.style.display = 'none';
        }
    }

    populateForm(data) {
        // OCR 결과 표시 섹션 보이기
        document.getElementById('ocr-results').style.display = 'block';
        
        const fields = {
            'cafe-name': data.store_name,
            'visit-date': data.visit_date,
            'menu-items': data.menu_items,
            'total-price': data.total_price ? `${data.total_price}원` : '',
        };

        for (const [id, value] of Object.entries(fields)) {
            const element = document.getElementById(id);
            if (element) {
                element.value = value || '';
            }
        }
    }

    showMessage(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        const container = this.form.closest('.container');
        container.insertBefore(alertDiv, container.firstChild);

        // 3초 후 알림 자동 제거
        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    }
}
