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
# Kütüphaneler eksikse uygulama çökmesin, net bir uyarı versin.
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
    st.warning(f"Eksik olanlar: {', '.join(missing_libs)}")
    st.info("Lütfen GitHub'daki 'requirements.txt' dosyasının içeriğini kontrol et.")
    st.stop()

# --- 3. ARAYÜZ ---
st.title("👕 AI Sanal Kabin (Final Sürüm)")
st.markdown("""
Bu uygulama **IDM-VTON** yapay zeka modelini kullanarak çalışır. 
Sol tarafa kendi fotoğrafını, sağ tarafa denemek istediğin kıyafetin linkini gir.
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
        # Dosyayı diske kaydetmemiz lazım ki gradio okuyabilsin
        with open("human.jpg", "wb") as f:
            f.write(human_file.getbuffer())
        human_img_path = os.path.abspath("human.jpg")

# SAĞ TARAFA - KIYAFET LİNKİ
with col2:
    st.header("2. Kıyafet Linki")
    garm_url = st.text_input("Kıyafet resminin linkini buraya yapıştır", placeholder="https://...")
    
    if garm_url:
        try:
            # Resmi indiriyoruz
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(garm_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                img = Image.open(BytesIO(resp.content))
                st.image(img, width=250)
                img.save("garm.jpg")
                garm_img_path = os.path.abspath("garm.jpg")
            else:
                st.warning("Resim indirilemedi. Linkin doğrudan bir resim dosyası olduğundan emin ol (.jpg veya .png ile bitmeli).")
        except Exception as e:
            st.error(f"Link hatası: {e}")

# --- 4. ÇALIŞTIRMA BUTONU ---
st.markdown("---")
if st.button("🚀 SANAL DENEMEYİ BAŞLAT", type="primary", use_container_width=True):
    
    if not human_img_path or not garm_img_path:
        st.error("⚠️ Lütfen önce hem fotoğrafını yükle hem de geçerli bir kıyafet linki gir.")
    else:
        status_container = st.status("AI Motoruna Bağlanılıyor...", expanded=True)
        
        try:
            # 1. Aşama: Bağlantı
            status_container.write("🔌 HuggingFace sunucusuna bağlanılıyor...")
            client = Client("yisol/IDM-VTON")
            status_container.write("✅ Bağlantı başarılı!")
            
            # 2. Aşama: Gönderme
            status_container.write("🧶 Kıyafet giydiriliyor (Yaklaşık 45-60 saniye sürer)...")
            
            # API Parametreleri
            # Not: Gradio API'si bazen güncellemelerle parametre sırasını değiştirebilir,
            # ancak dict=... yapısı en güvenli yöntemdir.
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
            
            # 3. Aşama: Sonuç
            status_container.update(label="İşlem Tamamlandı! 🎉", state="complete", expanded=False)
            st.balloons()
            
            # Sonuç işleme (Genellikle bir tuple döner: (resim_yolu, json_bilgisi))
            if isinstance(result, (list, tuple)):
                sonuc_resim = result[0]
            else:
                sonuc_resim = result
                
            st.subheader("✨ İşte Yeni Tarzın!")
            st.image(sonuc_resim, caption="Sanal Deneme Sonucu", use_column_width=True)
            
        except Exception as e:
            status_container.update(label="Hata Oluştu", state="error")
            st.error("❌ Bir sorun oluştu.")
            st.code(f"Hata Detayı: {str(e)}")
            st.info("Sunucu yoğun olabilir, lütfen 1 dakika sonra tekrar dene.")