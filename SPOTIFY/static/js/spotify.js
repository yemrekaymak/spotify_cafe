// Backend'den sanatçıları al ve göster
fetch('/sanatci-listesi/')
    .then(response => response.json())
    .then(data => {
        if (data.artists && data.artists.length > 0) {
            showArtists(data.artists);
        } else {
            alert("Sanatçı bulunamadı.");
        }
    })
    .catch(error => {
        console.error("Sanatçıları alırken bir hata oluştu:", error);
        alert("Bir hata oluştu. Lütfen tekrar deneyin.");
    });

// Sanatçıları grid yapısında göster
function showArtists(artists) {
    const artistGrid = document.getElementById('artist-grid');
    artistGrid.innerHTML = ''; // Önceki sanatçıları temizle

    artists.forEach(artist => {
        const artistCard = document.createElement('div');
        artistCard.className = 'artist-card';
        artistCard.innerHTML = `
            <h4>${artist.name}</h4>
            <img src="${artist.image}" alt="${artist.name}" style="width: 100%; border-radius: 10px;">
            <button onclick="selectArtist('${artist.id}')">Seç</button>
        `;
        artistGrid.appendChild(artistCard);
    });
}

// Sanatçı seçildiğinde yapılacak işlem
function selectArtist(artistId) {
    alert(`Sanatçı ID: ${artistId} seçildi!`);
    // Burada sanatçıyla ilgili başka işlemler yapabilirsiniz
}

document.querySelector('form').addEventListener('submit', function (e) {
    e.preventDefault(); // Sayfanın yenilenmesini engelle

    const formData = new FormData(this);
    const data = {
        name: formData.get('name'),
        description: formData.get('description'),
        public: formData.get('public') === 'true'
    };

    fetch('/create-playlist/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        },
        body: formData
    })
        .then(response => response.json())
        .then(result => {
            if (result.message) {
                alert(result.message);
            } else {
                alert(result.error);
            }
        })
        .catch(error => console.error('Hata:', error));
});

document.getElementById('search-add-track-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const response = await fetch(e.target.action, {
        method: 'POST',
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        },
        body: formData
    });

    const result = await response.json();
    if (result.message) {
        alert(result.message);
    } else {
        alert(result.error);
    }
});