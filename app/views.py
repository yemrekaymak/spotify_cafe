from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import requests
from django.conf import settings
import time
import json
from django.views.decorators.csrf import csrf_exempt

CLIENT_ID = "98872c7e52444cdba5ebef97b89198c5"
CLIENT_SECRET = "0f6afd0d8552472e995967fca812eeb7"
REDIRECT_URI = 'https://spotify-cafe.onrender.com/callback/'

# Ana sayfa view
def home(request):
    access_token = get_valid_access_token(request)
    if not access_token:
        return redirect('giris_yap')  # Token geçersizse kullanıcıyı girişe yönlendir
    return render(request, 'app/index.html')

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
        print("Spotify'dan geri dönüş kodu alınamadı.")  # Log
        return redirect('giris_yap')

    try:
        token_info = sp_oauth.get_access_token(code)
        request.session['spotify_access_token'] = token_info['access_token']
        request.session['spotify_refresh_token'] = token_info.get('refresh_token')
        request.session['expires_at'] = int(time.time()) + token_info['expires_in']
        print("Access token başarıyla alındı:", token_info)  # Log
        return redirect('home')
    except Exception as e:
        print(f"Access token alınamadı: {str(e)}")  # Log
        return redirect('giris_yap')

# Şarkıyı çalma sırasına ekleme view
@csrf_exempt
def add_to_queue(request):
    if request.method == 'POST':
        print("POST isteği alındı.")
        access_token = request.session.get('spotify_access_token')
        if not access_token:
            print("Access token eksik.")
            return redirect('giris_yap')

        try:
            data = json.loads(request.body)
            track_uri = data.get('track_uri')
            print("Alınan track_uri:", track_uri)
        except json.JSONDecodeError:
            print("Geçersiz JSON verisi.")
            return JsonResponse({"error": "Geçersiz JSON verisi."}, status=400)

        if not track_uri:
            print("Şarkı URI'si eksik.")
            return JsonResponse({"error": "Şarkı URI'si eksik."}, status=400)

        headers = {'Authorization': f'Bearer {access_token}'}
        queue_url = f'https://api.spotify.com/v1/me/player/queue?uri={track_uri}'
        response = requests.post(queue_url, headers=headers)

        print("Spotify API yanıtı:", response.status_code, response.text)

        if response.status_code == 204:
            print("Şarkı başarıyla çalma sırasına eklendi.")  # Log
            return JsonResponse({"message": "Şarkı çalma sırasına başarıyla eklendi!"})
        else:
            try:
                error_message = response.json().get('error', {}).get('message', 'Bilinmeyen bir hata oluştu.')
            except json.JSONDecodeError:
                error_message = f"Spotify API yanıtı çözümlenemedi: {response.text}"
            print(f"Şarkı eklenemedi: {error_message}")  # Log
            return JsonResponse({"error": f"Şarkı eklenemedi: {error_message}"}, status=response.status_code)

    print("GET isteği alındı.")
    return JsonResponse({"error": "Sadece POST istekleri destekleniyor."}, status=405)


# Şarkı arama view
import requests
from django.shortcuts import render
from django.http import JsonResponse

# Şarkı arama view
def search_tracks(request):
    access_token = get_valid_access_token(request)
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

# Access token alma view
def get_access_token(request):
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope="user-modify-playback-state playlist-modify-public playlist-modify-private"
    )
    try:
        token_info = sp_oauth.get_cached_token()
        if not token_info or sp_oauth.is_token_expired(token_info):
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            request.session['spotify_access_token'] = token_info['access_token']
        return token_info['access_token']
    except Exception as e:
        return JsonResponse({"error": f"Access token yenilenemedi: {str(e)}"}, status=400)

# Token yenileme işlemi
def get_valid_access_token(request):
    access_token = request.session.get('spotify_access_token')
    refresh_token = request.session.get('spotify_refresh_token')

    # Eğer access token yoksa veya süresi dolmuşsa
    if not access_token or token_is_expired({'expires_at': request.session.get('expires_at', 0)}):
        if not refresh_token:
            return None  # Refresh token da yoksa hiçbir şey yapılamaz

        sp_oauth = SpotifyOAuth(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIFY_REDIRECT_URI
        )

        try:
            # Refresh token ile yeni access token al
            token_info = sp_oauth.refresh_access_token(refresh_token)
            access_token = token_info['access_token']
            request.session['spotify_access_token'] = access_token
            request.session['spotify_refresh_token'] = token_info.get('refresh_token', refresh_token)
            request.session['expires_at'] = int(time.time()) + token_info['expires_in']
        except Exception as e:
            print(f"Access token alınamadı: {str(e)}")

            # Token alınamadıysa oturumu sıfırla
            request.session.flush()
            return None

    return access_token

import time

def token_is_expired(token_info):
    # Token'ın süresinin dolup dolmadığını kontrol et
    expires_at = token_info.get('expires_at', 0)  # Token'ın sona erme zamanı
    current_time = int(time.time())  # Şu anki zaman (saniye cinsinden)
    return current_time >= expires_at  # Eğer şu anki zaman sona erme zamanını geçmişse True döner

# Kullanıcı verilerini döndüren view
def get_user_data(request):
    access_token = get_valid_access_token(request)
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
        return redirect('giris_yap')  # Kullanıcı giriş yapmamışsa yönlendir

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
    access_token = get_valid_access_token(request)
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
