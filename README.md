# Spotify Cafe

Spotify Cafe, restoranlar, kafeler, spor salonları gibi mekanlar için geliştirilmiş bir müzik çalma sırası yönetim uygulamasıdır. Kullanıcılar, mekan çalışanlarının QR kodunu tarayarak çalma sırasına şarkılar ekleyebilirler. Bu sayede, kullanıcılar şarkı isteklerini hızlı bir şekilde gönderebilir ve müzik akışını kontrol edebilirler.

## Özellikler

- **QR Kod ile Giriş:** Çalışanlar, mekanın Spotify hesabına QR kodu ile bağlanabilir.
- **Şarkı Ekleme:** Kullanıcılar, Spotify çalma sırasına şarkı ekleyebilir.
- **Spotify API Entegrasyonu:** Spotify hesaplarıyla entegre edilmiştir.
- **Yönetici Hesabı:** Yalnızca mekan sahibi/çalışanları tarafından erişilebilen yönetici hesabı.

## Teknolojiler

- Python (Django)
- Spotify API
- HTML/CSS/JavaScript
- SQLite/PostgreSQL (Veritabanı)

## Kurulum

1. Projeyi GitHub'dan klonlayın:

    ```bash
    git clone https://github.com/yemrekaymak/spotify_cafe.git
    ```

2. Sanal ortam oluşturun ve aktifleştirin:

    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows için: venv\Scripts\activate
    ```

3. Gereksinimleri yükleyin:

    ```bash
    pip install -r requirements.txt
    ```

4. Django ayarlarını yapılandırın (settings.py içindeki gerekli ayarları yapın):

    - Spotify API bilgilerini `settings.py` dosyasına ekleyin:

      ```python
      SPOTIFY_CLIENT_ID = 'your-client-id'
      SPOTIFY_CLIENT_SECRET = 'your-client-secret'
      SPOTIFY_REDIRECT_URI = 'http://127.0.0.1:8000/callback/'
      ```

5. Veritabanını oluşturun:

    ```bash
    python manage.py migrate
    ```

6. Geliştirme sunucusunu başlatın:

    ```bash
    python manage.py runserver
    ```

7. Web uygulamanız `http://127.0.0.1:8000` adresinde çalışmaya başlayacaktır.

## Kullanım

- **Giriş Yap:** Kullanıcılar Spotify hesaplarıyla giriş yaparak müzik çalma sırasına şarkı ekleyebilir.
- **QR Kod Kullanımı:** Çalışanlar, mekanın özel QR kodunu tarayarak yönetici hesaplarına giriş yapabilir ve çalma sırasını kontrol edebilir.

## Lisans

Bu proje, [MIT Lisansı](LICENSE) ile lisanslanmıştır.

## Katkıda Bulunma

Katkıda bulunmak isterseniz, lütfen bir pull request açın. Herhangi bir hata ya da iyileştirme öneriniz için issues sayfasını kullanabilirsiniz.

## Telif Hakkı

© 2025 **Spotify Cafe**. Tüm hakları saklıdır.

---

Bu proje, öğrenme amaçlı ve açık kaynak olarak geliştirilmiştir. Telif hakkı veya ticari kullanım için ilgili Spotify API kullanım koşullarına uymalısınız.

