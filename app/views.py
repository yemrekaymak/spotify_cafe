from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import json
import requests
import urllib.parse
from django.conf import settings

CLIENT_ID = "a4d5b58097904826a731c8561d84a60c"
CLIENT_SECRET = "8cf45756c2494cf9a692cc41666b22c0"
REDIRECT_URI = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_URL = 'https://accounts.spotify.com/api/token'

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
        return JsonResponse({"error": "Spotify'dan geri dönüş kodu alınamadı. Lütfen tekrar giriş yapın."}, status=400)

    try:
        token_info = sp_oauth.get_access_token(code)
        request.session['spotify_access_token'] = token_info['access_token']
        request.session['spotify_refresh_token'] = token_info.get('refresh_token')
        request.session['expires_at'] = int(time.time()) + token_info['expires_in']
        print("Access token başarıyla alındı:", token_info)  # Log
        return redirect('home')  # Kullanıcıyı ana sayfaya yönlendir
    except Exception as e:
        print(f"Access token alınamadı: {str(e)}")  # Log
        return JsonResponse({"error": f"Access token alınamadı: {str(e)}"}, status=400)

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
    arama_terimi = request.GET.get('q')
    if not arama_terimi:
        return HttpResponse("⚠ Lütfen bir arama terimi girin.")

    try:
        sonuclar = arama_yap(request, arama_terimi)
        if not sonuclar['tracks']['items'] and not sonuclar['artists']['items']:
            return HttpResponse("⚠ Arama sonuçları bulunamadı.")
        return render(request, 'app/arama_sonuclari.html', {'sonuclar': sonuclar})
    except Exception as e:
        print(f"⚠ Arama sırasında hata oluştu: {e}")
        return HttpResponse("⚠ Spotify ile bağlantı kurulamadı. Lütfen tekrar deneyin.")

# Spotify API ile arama yapan fonksiyon
def arama_yap(request, arama_terimi):
    access_token = request.session.get('spotify_access_token')
    if not access_token:
        raise Exception("Spotify'a giriş yapılmamış.")

    try:
        sp = spotipy.Spotify(auth=access_token)
        sonuclar = sp.search(q=arama_terimi, type='track,artist')
        return sonuclar
    except Exception as e:
        print(f"⚠ Spotify API Hatası: {e}")
        raise e

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


# Şarkı ekleme view
def add_track_to_playlist(request):
    if request.method == 'POST':
        playlist_id = request.POST.get('playlist_id')
        track_uri = request.POST.get('track_uri')

        if not playlist_id or not track_uri:
            return JsonResponse({"error": "Çalma listesi ID'si veya şarkı URI'si eksik."}, status=400)

        access_token = request.session.get('spotify_access_token')
        if not access_token:
            return JsonResponse({"error": "Spotify'a giriş yapmanız gerekiyor."}, status=401)

        # Şarkı ekleme isteği
        add_track_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        headers = {'Authorization': f'Bearer {access_token}'}
        payload = {
            'uris': [track_uri]
        }
        response = requests.post(add_track_url, headers=headers, json=payload)

        if response.status_code == 201:  # Başarılı
            return JsonResponse({"message": "Şarkı başarıyla eklendi!"})
        else:
            error_message = response.json().get('error', {}).get('message', 'Bilinmeyen bir hata oluştu.')
            return JsonResponse({"error": f"Şarkı eklenemedi: {error_message}"}, status=400)

# Şarkı arama ve ekleme view
def search_and_add_track(request):
    if request.method == 'POST':
        playlist_id = request.POST.get('playlist_id')
        track_name = request.POST.get('track_name')

        if not playlist_id or not track_name:
            return JsonResponse({"error": "Çalma listesi ID'si veya şarkı adı eksik."}, status=400)

        access_token = request.session.get('spotify_access_token')
        if not access_token:
            return JsonResponse({"error": "Spotify'a giriş yapmanız gerekiyor."}, status=401)

        search_url = 'https://api.spotify.com/v1/search'
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {'q': track_name, 'type': 'track', 'limit': 1}
        search_response = requests.get(search_url, headers=headers, params=params)

        if search_response.status_code != 200:
            return JsonResponse({"error": "Şarkı arama başarısız."}, status=400)

        try:
            search_results = search_response.json()
            tracks = search_results.get('tracks', {}).get('items', [])
            if not tracks:
                return JsonResponse({"error": "Şarkı bulunamadı."}, status=404)

            track_uri = tracks[0].get('uri')
            add_track_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
            payload = {'uris': [track_uri]}
            add_response = requests.post(add_track_url, headers=headers, json=payload)

            if add_response.status_code == 201:
                return JsonResponse({"message": "Şarkı başarıyla eklendi!"})
            else:
                error_message = add_response.json().get('error', {}).get('message', 'Bilinmeyen bir hata oluştu.')
                return JsonResponse({"error": f"Şarkı eklenemedi: {error_message}"}, status=400)
        except ValueError:
            return JsonResponse({"error": "Spotify API yanıtı çözümlenemedi."}, status=400)

# Kullanıcının çalma listelerini döndüren view
def get_user_playlists(request):
    access_token = request.session.get('spotify_access_token')
    if not access_token:
        return JsonResponse({"error": "Spotify'a giriş yapmanız gerekiyor."}, status=401)

    # Kullanıcının çalma listelerini alma isteği
    playlists_url = 'https://api.spotify.com/v1/me/playlists'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(playlists_url, headers=headers)

    if response.status_code == 200:  # Başarılı
        playlists = response.json().get('items', [])
        return JsonResponse({"playlists": playlists})
    else:
        error_message = response.json().get('error', {}).get('message', 'Bilinmeyen bir hata oluştu.')
        return JsonResponse({"error": f"Çalma listeleri alınamadı: {error_message}"}, status=400)

# Şarkıyı çalma sırasına ekleme view
def add_to_queue(request):
    if request.method == 'POST':
        access_token = request.session.get('spotify_access_token')
        if not access_token:
            return JsonResponse({"error": "Spotify'a giriş yapmanız gerekiyor."}, status=401)

        track_uri = request.POST.get('track_uri')
        if not track_uri:
            return JsonResponse({"error": "Şarkı URI'si eksik."}, status=400)

        headers = {'Authorization': f'Bearer {access_token}'}
        queue_url = f'https://api.spotify.com/v1/me/player/queue?uri={track_uri}'
        response = requests.post(queue_url, headers=headers)

        if response.status_code == 204:  # Başarılı
            return JsonResponse({"message": "Şarkı çalma sırasına eklendi!"})
        else:
            try:
                error_message = response.json().get('error', {}).get('message', 'Bilinmeyen bir hata oluştu.')
            except ValueError:
                error_message = f"Spotify API yanıtı çözümlenemedi: {response.text}"
            return JsonResponse({"error": f"Şarkı eklenemedi: {error_message}"}, status=response.status_code)

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
        # Şarkı URI'lerini kontrol edelim
        for track in tracks:
            print(track.get('uri'))  # Şarkı URI'sini konsola yazdır
        return JsonResponse({"tracks": tracks})
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
