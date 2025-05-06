from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import json
import requests
import urllib.parse
from django.conf import settings
from spotipy.oauth2 import SpotifyOAuth
import time
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse

CLIENT_ID = "a4d5b58097904826a731c8561d84a60c"
CLIENT_SECRET = "8cf45756c2494cf9a692cc41666b22c0"
REDIRECT_URI = 'https://spotify-cafe.onrender.com/callback/'  # bu önemli!
SPOTIFY_API_URL = 'https://accounts.spotify.com/api/token'

# Spotify OAuth ayarları
sp_oauth = SpotifyOAuth(
    client_id=settings.SPOTIFY_CLIENT_ID,
    client_secret=settings.SPOTIFY_CLIENT_SECRET,
    redirect_uri=settings.SPOTIFY_REDIRECT_URI,
    scope="user-modify-playback-state playlist-modify-public playlist-modify-private user-top-read"
)

# Spotify bağlantısı
sp = spotipy.Spotify(auth_manager=sp_oauth)

def home(request):
    access_token = request.session.get('spotify_access_token')
    return render(request, 'app/index.html', {'is_logged_in': bool(access_token)})


def spotify(request):
    return render(request, "app/spotify.html")

# Kullanıcıyı Spotify'a yönlendiren view
def giris_yap(request):
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope="user-modify-playback-state playlist-modify-public playlist-modify-private user-top-read"
    )
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

# Callback işlemini yöneten view


from django.shortcuts import redirect

def callback(request):
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri='https://spotify-cafe.onrender.com/callback/',
        scope="user-read-private user-read-email user-modify-playback-state playlist-modify-public playlist-modify-private user-top-read"
    )

    code = request.GET.get('code')
    if not code:
        return redirect('home')  # Hatalıysa anasayfaya at

    try:
        token_info = sp_oauth.get_access_token(code, as_dict=True)

        request.session['spotify_access_token'] = token_info['access_token']
        request.session['spotify_refresh_token'] = token_info.get('refresh_token')
        request.session['expires_at'] = int(time.time()) + token_info['expires_in']

        user_data = {
            "access_token": token_info['access_token'],
            "refresh_token": token_info.get('refresh_token'),
            "expires_in": token_info['expires_in']
        }

        return render(request, 'spotify/callback.html', {
            "user_data_json": json.dumps(user_data)
        })

    except Exception as e:
        print("Access token alınamadı:", str(e))
        return redirect('home')  # Hatalıysa yine anasayfaya at




# Token yenileme fonksiyonu
def refresh_access_token(refresh_token):
    token_data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    token_response = requests.post(SPOTIFY_API_URL, data=token_data)
    if token_response.status_code == 200:
        return token_response.json().get('access_token')
    else:
        print(f"⚠ Token yenileme hatası: {token_response.status_code}, {token_response.text}")
        return None

# Arama sonuçlarını döndüren view
def arama_sonuclari(request):
    access_token = get_valid_access_token(request)
    if isinstance(access_token, HttpResponse):
        return access_token  # Eğer redirect dönüyorsa yönlendir

    query = request.GET.get('q')
    if not query:
        return render(request, 'app/arama_sonuclari.html', {'error': "Lütfen bir arama terimi girin."})

    headers = {'Authorization': f'Bearer {access_token}'}
    search_url = f'https://api.spotify.com/v1/search?q={query}&type=track&limit=10'

    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        tracks = data.get('tracks', {}).get('items', [])
        return render(request, 'app/arama_sonuclari.html', {'tracks': tracks})
    except requests.exceptions.RequestException as e:
        return render(request, 'app/arama_sonuclari.html', {'error': f"Spotify API isteği başarısız: {str(e)}"})

# Kullanıcı verilerini döndüren view
def get_user_data(request):
    access_token = request.session.get('spotify_access_token')
    refresh_token = request.session.get('spotify_refresh_token')

    if not access_token:
        return redirect('giris_yap')

    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    user_info_url = 'https://api.spotify.com/v1/me'
    response = requests.get(user_info_url, headers=headers)

    if response.status_code == 401:  # Token süresi dolmuş
        print("⚠ Token süresi dolmuş, yenileniyor...")
        new_access_token = refresh_access_token(refresh_token)
        if not new_access_token:
            return JsonResponse({"error": "Token yenileme başarısız. Lütfen tekrar giriş yapın."}, status=401)
        request.session['spotify_access_token'] = new_access_token
        headers['Authorization'] = f'Bearer {new_access_token}'
        response = requests.get(user_info_url, headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        return render(request, 'app/user_data.html', {'user_data': user_data})
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return JsonResponse({"error": "Spotify API'den veri alınamadı."}, status=400)

# Sanatçı listesini döndüren view
def sanatci_listesi(request):
    access_token = request.session.get('spotify_access_token')
    if not access_token:
        return JsonResponse({"error": "Spotify'a giriş yapmanız gerekiyor."}, status=401)

    try:
        sp = spotipy.Spotify(auth=access_token)
        results = sp.search(q='*', type='artist', limit=request.GET.get('limit', 9))  # Dinamik limit

        artists = []
        for item in results['artists']['items']:
            artists.append({
                'id': item['id'],
                'name': item['name'],
                'image': item['images'][0]['url'] if item['images'] else 'https://via.placeholder.com/150'
            })

        return JsonResponse({'artists': artists})
    except Exception as e:
        print(f"⚠ Spotify API Hatası: {e}")
        return JsonResponse({"error": "Sanatçı listesi alınamadı."}, status=500)

# Şarkıyı çalma sırasına ekleme view
@csrf_exempt
def add_to_queue(request):
    if request.method == 'POST':
        print("POST isteği alındı.")  # Hata ayıklama için log
        access_token = request.session.get('spotify_access_token')
        if not access_token:
            print("Access token eksik.")  # Hata ayıklama için log
            return JsonResponse({"error": "Spotify'a giriş yapmanız gerekiyor."}, status=401)

        try:
            data = json.loads(request.body)
            track_uri = data.get('track_uri')
            print("Alınan track_uri:", track_uri)  # Hata ayıklama için log
        except json.JSONDecodeError:
            print("Geçersiz JSON verisi.")  # Hata ayıklama için log
            return JsonResponse({"error": "Geçersiz JSON verisi."}, status=400)

        if not track_uri:
            print("Şarkı URI'si eksik.")  # Hata ayıklama için log
            return JsonResponse({"error": "Şarkı URI'si eksik."}, status=400)

        headers = {'Authorization': f'Bearer {access_token}'}
        queue_url = f'https://api.spotify.com/v1/me/player/queue?uri={track_uri}'
        response = requests.post(queue_url, headers=headers)

        print("Spotify API yanıtı:", response.status_code, response.text)  # Hata ayıklama için log

        if response.status_code == 204:
            return JsonResponse({"message": "Şarkı çalma sırasına başarıyla eklendi!"})  # Başarı mesajını güncelle
        else:
            error_message = response.json().get('error', {}).get('message', 'Bilinmeyen bir hata oluştu.')
            return JsonResponse({"error": f"Şarkı eklenemedi: {error_message}"}, status=400)

    print("GET isteği alındı.")  # Hata ayıklama için log
    return JsonResponse({"error": "Sadece POST istekleri destekleniyor."}, status=405)


# Access token alma view
def get_access_token(request):
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope="user-modify-playback-state playlist-modify-public playlist-modify-private user-top-read"
    )
    token_info = sp_oauth.get_cached_token()
    if not token_info or sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        request.session['spotify_access_token'] = token_info['access_token']
    return token_info['access_token']

# Access token doğrulama ve yenileme fonksiyonu
def get_valid_access_token(request):
    access_token = request.session.get('spotify_access_token')
    refresh_token = request.session.get('spotify_refresh_token')
    expires_at = request.session.get('expires_at', 0)

    if not access_token or int(time.time()) >= expires_at:
        if not refresh_token:
            print("Refresh token eksik. Kullanıcıyı tekrar giriş yapmaya yönlendiriyorum.")  # Log
            return redirect('giris_yap')

        sp_oauth = SpotifyOAuth(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIFY_REDIRECT_URI
        )

        try:
            token_info = sp_oauth.refresh_access_token(refresh_token)
            access_token = token_info['access_token']
            request.session['spotify_access_token'] = access_token
            request.session['expires_at'] = int(time.time()) + token_info['expires_in']
            print("Access token yenilendi:", access_token)  # Log
        except Exception as e:
            print(f"Token yenileme hatası: {str(e)}")  # Log
            return redirect('giris_yap')

    return access_token

@csrf_exempt
def get_top_tracks(request):
    if request.method != "GET":
        return JsonResponse({"error": "Sadece GET istekleri destekleniyor."}, status=405)

    access_token = request.session.get('spotify_access_token')
    if not access_token:
        return JsonResponse({"error": "Spotify'a giriş yapmanız gerekiyor."}, status=401)

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    limit = 5  # Sabit 5 olarak ayarladık
    url = f"https://open.spotify.com/playlist/37i9dQZEVXbMDoHDwVN2tF?si=bf2b6a5b86484dc4?limit={limit}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return JsonResponse({"error": f"Spotify API hatası: {response.status_code}"}, status=response.status_code)

    data = response.json()
    tracks = []

    for track in data['items']:
        tracks.append({
            'name': track['name'],
            'artist': ', '.join([artist['name'] for artist in track['artists']]),
            'uri': track['uri'],
            'image': track['album']['images'][0]['url'] if track['album']['images'] else None
        })

    return JsonResponse({"tracks": tracks})