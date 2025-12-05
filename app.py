import streamlit as st
import os
import sys
import time

# --- 1. AYARLAR (EN BAŞTA OLMALI) ---
st.set_page_config(
    page_title="Sanal Kabin AI",
    page_icon="👕",
    layout="wide"
)

# --- 2. KÜTÜPHANE KONTROLÜ ---
missing_libs = []
try:
    import requests
except ImportError:
    missing_libs.append("requests")

try:
    from PIL import Image
    from io import BytesIO
except ImportError:
    missing_libs.append("pillow")

try:
    from gradio_client import Client, handle_file
except ImportError:
    missing_libs.append("gradio_client")

if missing_libs:
    st.error("🚨 KRİTİK EKSİK: Bazı kütüphaneler yüklenemedi!")
    st.info("Lütfen GitHub'daki 'requirements.txt' dosyasını kontrol et.")
    st.stop()

# --- 3. ARAYÜZ ---
st.title("👕 AI Sanal Kabin (Akıllı Link Modu)")
st.markdown("""
**Nasıl Kullanılır?**
1. Sol tarafa kendi fotoğrafını yükle.
2. Sağ tarafa kıyafetin **resim linkini** yapıştır. (Site linki değil!)
""")

col1, col2 = st.columns(2)
human_img_path = None
garm_img_path = None

# SOL TARAFA - İNSAN FOTOĞRAFI
with col1:
    st.header("1. Senin Fotoğrafın")
    human_file = st.file_uploader("Boydan bir fotoğraf yükle", type=['png', 'jpg', 'jpeg'], key="human")
    if human_file:
        st.image(human_file, width=250)
        with open("human.jpg", "wb") as f:
            f.write(human_file.getbuffer())
        human_img_path = os.path.abspath("human.jpg")

# SAĞ TARAFA - KIYAFET LİNKİ
with col2:
    st.header("2. Kıyafet Linki")
    
    # Kullanıcıya ipucu veren bilgi kutusu
    st.info("💡 İPUCU: Ürün sayfasındayken resme **Sağ Tıkla** > **Resim Adresini Kopyala** de.")
    
    garm_url = st.text_input("Kıyafet resminin linkini buraya yapıştır:", placeholder="https://site.com/resim.jpg")
    
    if garm_url:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(garm_url, headers=headers, timeout=10)
            
            # İçerik tipini kontrol et (Resim mi, Web sitesi mi?)
            content_type = resp.headers.get('Content-Type', '')
            
            if 'image' not in content_type:
                st.error("❌ HATA: Bu bir resim linki değil, web sitesi linki!")
                st.warning("Lütfen ürünün fotoğrafına sağ tıklayıp 'Resim Adresini Kopyala' diyerek o linki yapıştırın.")
            elif resp.status_code == 200:
                img = Image.open(BytesIO(resp.content))
                st.image(img, width=250, caption="Seçilen Kıyafet")
                img.save("garm.jpg")
                garm_img_path = os.path.abspath("garm.jpg")
            else:
                st.warning("Resim indirilemedi. Bağlantıyı kontrol edin.")
                
        except Exception as e:
            st.error(f"Link işlenirken hata oluştu: {e}")

# --- 4. ÇALIŞTIRMA BUTONU ---
st.markdown("---")
if st.button("🚀 SANAL DENEMEYİ BAŞLAT", type="primary", use_container_width=True):
    
    if not human_img_path or not garm_img_path:
        st.error("⚠️ Lütfen önce hem fotoğrafını yükle hem de GEÇERLİ bir kıyafet resim linki gir.")
    else:
        status_container = st.status("AI Motoruna Bağlanılıyor...", expanded=True)
        
        try:
            status_container.write("🔌 Sunucuya bağlanılıyor...")
            client = Client("yisol/IDM-VTON")
            status_container.write("✅ Bağlantı başarılı!")
            
            status_container.write("🧶 Kıyafet giydiriliyor (Sabırlı ol, 45-60 saniye sürebilir)...")
            
            result = client.predict(
                dict={"background": handle_file(human_img_path), "layers": [], "composite": None},
                garm_img=handle_file(garm_img_path),
                garment_des="clothing",
                is_checked=True,
                is_checked_crop=False,
                denoise_steps=30,
                seed=42,
                api_name="/tryon"
            )
            
            status_container.update(label="İşlem Tamamlandı! 🎉", state="complete", expanded=False)
            st.balloons()
            
            if isinstance(result, (list, tuple)):
                sonuc_resim = result[0]
            else:
                sonuc_resim = result
                
            st.subheader("✨ İşte Sonuç!")
            st.image(sonuc_resim, use_column_width=True)
            
        except Exception as e:
            status_container.update(label="Hata Oluştu", state="error")
            st.error(f"Hata Detayı: {str(e)}")
            st.info("Eğer 'Queue is full' hatası alıyorsan, sunucu çok yoğundur. 1-2 dakika sonra tekrar dene.")