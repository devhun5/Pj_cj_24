class CafeMap {
    constructor() {
        this.map = null;
        this.markers = [];
        this.geocoder = new kakao.maps.services.Geocoder();
    }

    init(containerId, initialLat = 37.566826, initialLng = 126.978656) {
        const container = document.getElementById(containerId);
        const options = {
            center: new kakao.maps.LatLng(initialLat, initialLng),
            level: 3
        };

        this.map = new kakao.maps.Map(container, options);
        
        // 지도 컨트롤 추가
        const zoomControl = new kakao.maps.ZoomControl();
        this.map.addControl(zoomControl, kakao.maps.ControlPosition.RIGHT);
    }

    addMarker(lat, lng, cafeInfo) {
        const position = new kakao.maps.LatLng(lat, lng);
        const marker = new kakao.maps.Marker({
            position: position,
            map: this.map
        });

        // 인포윈도우 내용
        const content = `
            <div class="info-window">
                <h5>${cafeInfo.name}</h5>
                <p>${cafeInfo.address}</p>
                <p>평점: ${cafeInfo.rating}점</p>
            </div>
        `;

        const infowindow = new kakao.maps.InfoWindow({
            content: content,
            removable: true
        });

        // 마커 클릭 이벤트
        kakao.maps.event.addListener(marker, 'click', () => {
            infowindow.open(this.map, marker);
        });

        this.markers.push(marker);
        return marker;
    }

    searchAddress(address) {
        return new Promise((resolve, reject) => {
            this.geocoder.addressSearch(address, (result, status) => {
                if (status === kakao.maps.services.Status.OK) {
                    resolve({
                        lat: result[0].y,
                        lng: result[0].x,
                        address: result[0].address_name
                    });
                } else {
                    reject(new Error('주소를 찾을 수 없습니다.'));
                }
            });
        });
    }

    clearMarkers() {
        this.markers.forEach(marker => marker.setMap(null));
        this.markers = [];
    }

    panTo(lat, lng) {
        const moveLatLon = new kakao.maps.LatLng(lat, lng);
        this.map.panTo(moveLatLon);
    }
}
