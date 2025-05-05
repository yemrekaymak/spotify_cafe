from django.urls import path
from .views import (
    home,
    spotify,
    arama_sonuclari,
    giris_yap,
    callback,
    get_user_data,
    sanatci_listesi,
    add_to_queue,
    search_tracks,
    search_and_add_track,  # Yeni eklenen view
    get_user_playlists,    # Yeni eklenen view
    add_track_to_playlist, # Yeni eklenen view
)

urlpatterns = [
    path("", home, name='home'),
    path("spotify/", spotify, name='spotify_home'),
    path("arama/", arama_sonuclari, name='arama_sonuclari'),
    path("giris_yap/", giris_yap, name='giris_yap'),
    path("callback/", callback, name='callback'),
    path("user/", get_user_data, name='get_user_data'),
    path("sanatci_listesi/", sanatci_listesi, name='sanatci_listesi'),
    path("add_to_queue/", add_to_queue, name='add_to_queue'),
    path("search_tracks/", search_tracks, name='search_tracks'),
    path("search_and_add_track/", search_and_add_track, name='search_and_add_track'),
    path("get_user_playlists/", get_user_playlists, name='get_user_playlists'),
    path("add_track_to_playlist/", add_track_to_playlist, name='add_track_to_playlist'),
]
