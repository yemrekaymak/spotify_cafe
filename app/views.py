from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import requests
from django.conf import settings
import time
import json
from django.views.decorators.csrf import csrf_exempt

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
        print("Spotify'dan geri dönüş kodu alınamadı.")  # Log
        return redirect('giris_yap')

    try:
        token_info = sp_oauth.get_access_token(code)
        request.session['spotify_access_token'] = token_info['access_token']
        request.session['spotify_refresh_token'] = token_info.get('refresh_token')
        request.session['expires_at'] = int(time.time()) + token_info['expires_in']
        print("Access token başarıyla alındı:", token_info)  # Log
        return redirect('home')  # Kullanıcıyı ana sayfaya yönlendir
    except Exception as e:
        print(f"Access token alınamadı: {str(e)}")  # Log
        return redirect('giris_yap')

# Şarkıyı çalma sırasına ekleme view
@csrf_exempt
def add_to_queue(request):
    if request.method == 'POST':
        access_token = request.session.get('spotify_access_token')
        if not access_token:
            print("Access token eksik.")  # Log
            return JsonResponse({"error": "Spotify'a giriş yapmanız gerekiyor."}, status=401)

        try:
            data = json.loads(request.body)
            track_uri = data.get('track_uri')
            print("Alınan track_uri:", track_uri)  # Log
        except json.JSONDecodeError:
            print("Geçersiz JSON verisi.")  # Log
            return JsonResponse({"error": "Geçersiz JSON verisi."}, status=400)

        if not track_uri:
            print("Şarkı URI'si eksik.")  # Log
            return JsonResponse({"error": "Şarkı URI'si eksik."}, status=400)

        headers = {'Authorization': f'Bearer {access_token}'}
        queue_url = f'https://api.spotify.com/v1/me/player/queue?uri={track_uri}' # Doğru API endpoint'i ve HTTPS
        response = requests.post(queue_url, headers=headers)

        print("Spotify API yanıtı:", response.status_code, response.text)  # Log

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

    print("GET isteği alındı.")  # Log
    return JsonResponse({"error": "Sadece POST istekleri destekleniyor."}, status=405)


# Şarkı arama view
import requests
from django.shortcuts import render
from django.http import JsonResponse

# Şarkı arama view
def search_tracks(request):
    # Spotify erişim token'ını al
    access_token = request.session.get('spotify_access_token')

    # Eğer token yoksa, kullanıcıyı uyar
    if not access_token:
        return JsonResponse({"error": "Spotify'a giriş yapmanız gerekiyor."}, status=401)

    # Arama sorgusunu al
    query = request.GET.get('q')
    if not query:
        return JsonResponse({"error": "Arama sorgusu eksik."}, status=400)

    # Spotify API'ye istek gönder
    headers = {'Authorization': f'Bearer {access_token}'}
    search_url = f'https://api.spotify.com/v1/search?q={query}&type=track&limit=10' # Doğru API endpoint'i ve HTTPS
    response = requests.get(search_url, headers=headers)

    # Eğer başarılı bir sonuç geldiyse
    if response.status_code == 200:
        data = response.json()
        tracks = data.get('tracks', {}).get('items', [])
        # Şarkıları HTML şablonuna gönder
        return render(request, 'app/arama_sonuclari.html', {'tracks': tracks})
    else:
        # Eğer bir hata olduysa
        return JsonResponse({"error": "Şarkılar alınamadı."}, status=response.status_code)

# Access token alma view (gerekirse kullanılabilir)
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
    expires_at = request.session.get('expires_at', 0)

    # Token yoksa veya süresi dolmuşsa
    if not access_token or token_is_expired({'expires_at': expires_at}):
        if not refresh_token:
            print("Refresh token eksik. Kullanıcıyı tekrar giriş yapmaya yönlendiriyorum.")  # Log
            return redirect('giris_yap')

        # Refresh token kullanarak yeni access token almak için Spotify'a istek gönder
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
            print("Access token yenilendi:", access_token)  # Log
        except Exception as e:
            print(f"Token yenileme hatası: {str(e)}")  # Log
            return redirect('giris_yap')  # Kullanıcıyı tekrar giriş yapmaya yönlendir

    return access_token


import time

def token_is_expired(token_info):
    expires_at = token_info.get('expires_at', 0)
    current_time = int(time.time())
    return current_time >= expires_at

# Kullanıcı verilerini döndüren view
def get_user_data(request):
    access_token = request.session.get('spotify_access_token')
    if not access_token:
        return redirect('giris_yap')

    headers = {'Authorization': f'Bearer {access_token}'}
    user_info_url = 'https://api.spotify.com/v1/me' # Doğru API endpoint'i ve HTTPS
    response = requests.get(user_info_url, headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        return render(request, 'app/user_data.html', {'user_data': user_data})
    else:
        return JsonResponse({"error": "Spotify API'den veri alınamadı."}, status=response.status_code)

# Arama sonuçlarını döndüren view (zaten search_tracks var, bu gerekmeyebilir)
def arama_sonuclari(request):
    access_token = get_valid_access_token(request)
    if not access_token:
        return redirect('giris_yap')  # Kullanıcı giriş yapmamışsa yönlendir

    query = request.GET.get('q')
    if not query:
        return render(request, 'app/arama_sonuclari.html', {'error': "Lütfen bir arama terimi girin."})

    headers = {'Authorization': f'Bearer {access_token}'}
    search_url = f'https://api.spotify.com/v1/search?q={query}&type=track&limit=10' # Doğru API endpoint'i ve HTTPS

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
        return redirect('giris_yap')  # Kullanıcı giriş yapmamışsa yönlendir

    query = request.GET.get('q')  # Kullanıcının arama sorgusunu al
    if not query:
        return render(request, 'app/sanatci_listesi.html', {'error': "Lütfen bir sanatçı adı girin."})

    headers = {'Authorization': f'Bearer {access_token}'}
    search_url = f'https://api.spotify.com/v1/search?q={query}&type=artist&limit=10' # Doğru API endpoint'i ve HTTPS

    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()  # Hata durumlarını kontrol et
        data = response.json()
        artists = data.get('artists', {}).get('items', [])
        return render(request, 'app/sanatci_listesi.html', {'artists': artists})
    except requests.exceptions.RequestException as e:
        return render(request, 'app/sanatci_listesi.html', {'error': f"Spotify API isteği başarısız: {str(e)}"})