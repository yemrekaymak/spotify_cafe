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
    set_session,  # Bunu ekle
    get_session
)

urlpatterns = [
    path("", home, name='home'),
    path("spotify/", spotify, name='spotify_home'),
    path("arama/", arama_sonuclari, name='arama_sonuclari'),
    path("giris_yap/", giris_yap, name='giris_yap'),
    path("callback/", callback, name='callback'),
    path("user/", get_user_data, name='get_user_data'),
    path("sanatci-listesi/", sanatci_listesi, name='sanatci_listesi'),
    path("add-to-queue/", add_to_queue, name='add_to_queue'),
    path("search/", search_tracks, name='search_tracks'),
    path('set_session/', views.set_session, name='set_session'),
    path('get_session/', views.get_session, name='get_session'),
]
