from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from spotipy.oauth2 import SpotifyOAuth
import requests
import time
import json
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

# Spotify API Client bilgileri
CLIENT_ID = "75b0577d87af4f3e869017902eba769d"
CLIENT_SECRET = "8824e08491e84b17bdcf98d26c75dd9a"
REDIRECT_URI = 'https://spotify-cafe.onrender.com/callback/'

# Ana sayfa view
def home(request):
    return render(request, 'app/index.html')  # Ana sayfa template'i

# Spotify sayfası view
def spotify(request):
    return render(request, "app/spotify.html")

# Kullanıcıyı Spotify'a yönlendiren view
def giris_yap(request):
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope="user-modify-playback-state playlist-modify-public playlist-modify-private"
    )
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

# Callback işlemini yöneten view
def callback(request):
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope="user-modify-playback-state playlist-modify-public playlist-modify-private"
    )
    
    code = request.GET.get('code')
    if not code:
        return JsonResponse({"error": "Spotify'dan geri dönüş kodu alınamadı."}, status=400)
    
    try:
        # Yeni access token al
        token_info = sp_oauth.get_access_token(code)
        
        # Token'ları oturuma kaydet
        request.session['spotify_access_token'] = token_info['access_token']
        request.session['spotify_refresh_token'] = token_info.get('refresh_token')
        request.session['expires_at'] = int(time.time()) + token_info['expires_in']
        
        return redirect('home')
    
    except Exception as e:
        return redirect('giris_yap')

# Şarkıyı çalma sırasına ekleme view
@csrf_exempt
def add_to_queue(request):
    if request.method == 'POST':
        access_token = request.session.get('spotify_access_token')
        if not access_token:
            return JsonResponse({"error": "Spotify'a giriş yapmanız gerekiyor."}, status=401)

        try:
            data = json.loads(request.body)
            track_uri = data.get('track_uri')
        except json.JSONDecodeError:
            return JsonResponse({"error": "Geçersiz JSON verisi."}, status=400)

        if not track_uri:
            return JsonResponse({"error": "Şarkı URI'si eksik."}, status=400)

        headers = {'Authorization': f'Bearer {access_token}'}
        queue_url = f'https://api.spotify.com/v1/me/player/queue?uri={track_uri}'
        response = requests.post(queue_url, headers=headers)

        if response.status_code == 204:
            return JsonResponse({"message": "Şarkı çalma sırasına başarıyla eklendi!"})
        else:
            error_message = response.json().get('error', {}).get('message', 'Bilinmeyen bir hata oluştu.')
            return JsonResponse({"error": f"Şarkı eklenemedi: {error_message}"}, status=400)

    return JsonResponse({"error": "Sadece POST istekleri destekleniyor."}, status=405)

# Şarkı arama view
def search_tracks(request):
    access_token = request.session.get('spotify_access_token')
    
    if not access_token:
        return JsonResponse({"error": "Spotify'a giriş yapmanız gerekiyor."}, status=401)

    query = request.GET.get('q')
    if not query:
        return JsonResponse({"error": "Arama sorgusu eksik."}, status=400)

    headers = {'Authorization': f'Bearer {access_token}'}
    search_url = f'https://api.spotify.com/v1/search?q={query}&type=track&limit=10'
    response = requests.get(search_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        tracks = data.get('tracks', {}).get('items', [])
        return render(request, 'search_results.html', {'tracks': tracks})
    else:
        return JsonResponse({"error": "Şarkılar alınamadı."}, status=400)

# Token yenileme işlemi
def get_valid_access_token(request):
    access_token = request.session.get('spotify_access_token')
    refresh_token = request.session.get('spotify_refresh_token')

    if not access_token or token_is_expired({'expires_at': request.session.get('expires_at', 0)}):
        if not refresh_token:
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
            request.session['spotify_refresh_token'] = token_info.get('refresh_token', refresh_token)
            request.session['expires_at'] = int(time.time()) + token_info['expires_in']
        except Exception as e:
            return redirect('giris_yap')

    return access_token

# Kullanıcı verilerini döndüren view
def get_user_data(request):
    access_token = request.session.get('spotify_access_token')
    if not access_token:
        return redirect('giris_yap')

    headers = {'Authorization': f'Bearer {access_token}'}
    user_info_url = 'https://api.spotify.com/v1/me'
    response = requests.get(user_info_url, headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        return render(request, 'app/user_data.html', {'user_data': user_data})
    else:
        return JsonResponse({"error": "Spotify API'den veri alınamadı."}, status=400)

# Arama sonuçlarını döndüren view
def arama_sonuclari(request):
    access_token = get_valid_access_token(request)
    if not access_token:
        return redirect('giris_yap')

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

# Tüm sanatçıları döndüren view
def sanatci_listesi(request):
    access_token = request.session.get('spotify_access_token')
    if not access_token:
        return redirect('giris_yap')

    query = request.GET.get('q')
    if not query:
        return render(request, 'app/sanatci_listesi.html', {'error': "Lütfen bir sanatçı adı girin."})

    headers = {'Authorization': f'Bearer {access_token}'}
    search_url = f'https://api.spotify.com/v1/search?q={query}&type=artist&limit=10'

    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        artists = data.get('artists', {}).get('items', [])
        return render(request, 'app/sanatci_listesi.html', {'artists': artists})
    except requests.exceptions.RequestException as e:
        return render(request, 'app/sanatci_listesi.html', {'error': f"Spotify API isteği başarısız: {str(e)}"})

# Token süresinin dolup dolmadığını kontrol eden fonksiyon
def token_is_expired(token_info):
    expires_at = token_info.get('expires_at', 0)
    current_time = int(time.time())
    return current_time >= expires_at
