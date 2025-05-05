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
]
