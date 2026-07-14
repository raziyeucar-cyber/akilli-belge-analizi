import streamlit as st
import os
import requests
import sqlite3
import pandas as pd
from PIL import Image
import fitz  # PyMuPDF
import easyocr
import numpy as np

# Sayfa Yapılandırması
st.set_page_config(page_title="Akıllı Belge Analiz Asistanı", page_icon="🤖", layout="wide")

# Hugging Face Token Bilgisi
F_TOKEN = os.environ.get("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct"

# Veritabanı Kurulumu
def veritabanı_hazirla():
    conn = sqlite3.connect("proje_hafizasi.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS belgeler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            belge_adi TEXT,
            ham_metin TEXT,
            analiz_raporu TEXT
        )
    ''')
    conn.commit()
    conn.close()

veritabanı_hazirla()

# OCR Okuma Fonksiyonu
@st.cache_resource
def ocr_yukle():
    return easyocr.Reader(['tr', 'en'])

reader = ocr_yukle()

# LLM Analiz Fonksiyonu
def llm_ile_analiz_et(ham_metin):
    if not ham_metin.strip():
        return "Boş metin analiz edilemez."
        
    headers = {"Authorization": f"Bearer {F_TOKEN}"}
    
    prompt = (
        f"<|im_start|>system\n"
        f"Sen çok deneyimli bir Türkçe öğretmenisin ve karmaşık konuları en basit, "
        f"en akıcı ve en anlaşılır şekilde anlatma konusunda uzmansın. "
        f"Sana verilen metin, OCR (resimden yazıya dönüştürme) ile taranmıştır; bu yüzden içinde "
        f"bozuk kelimeler, gereksiz sayfa numaraları ve tekrarlar olabilir. "
        f"Görevin, bu hataları görmezden gelerek metni temizlemek ve okuyucuya harika, "
        f"akıcı ve tamamen anlamlı bir Türkçe ile analiz sunmaktır.\n\n"
        f"KURALLAR:\n"
        f"- Kesinlikle devrik, çok uzun veya anlamsız akademik cümleler kurma.\n"
        f"- Sanki bir öğrenciye konuyu sıfırdan öğretiyormuş gibi net, sade ve duru cümleler tercih et.\n"
        f"- Her başlık altında dökümanın can alıcı noktalarını açıkla.\n\n"
        f"Lütfen şu başlıklar altında en az 1-2 sayfalık detaylı ve çok akıcı bir rapor hazırla:\n"
        f"1. 📌 Bu Dökümanın Ana Amacı Nedir? (En fazla 3-4 net cümleyle)\n"
        f"2. 💡 Bölüm Bölüm Kritik Konular ve Detaylı Anlatımları (Her konuyu basit bir dille açıkla)\n"
        f"3. ⏳ Önemli Tarihler, Olaylar ve İsimler (Varsa listele)\n"
        f"4. 🎯 En Önemli 5 Çıkarım (Akılda kalıcı maddeler halinde)\n"
        f"Son olarak en önemli 5 anahtar kelimeyi listele.<|im_end|>\n"
        f"<|im_start|>user\nLütfen şu metni analiz et:\n\n{ham_metin}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 1200,
            "temperature": 0.3,
            "return_full_text": False
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        sonuc = response.json()
        if isinstance(sonuc, list) and len(sonuc) > 0:
            return sonuc[0].get("generated_text", "Analiz üretilemedi.")
        return "Yapay zeka analiz sunucusundan yanıt alınamadı."
    except Exception as e:
        return f"Analiz esnasında hata oluştu: {str(e)}"

# Arayüz Tasarımı
st.title("🤖 Akıllı Çok Sayfalı Belge Analiz ve Özetleme Asistanı")
st.write("Bu sistem yüklenen dökümanları sayfa sayfa analiz eder ve yapay zeka ile rapor çıkarır.")

# Sekmeler (Tabs)
tab1, tab2, tab3 = st.tabs(["📊 Analiz Ekranı", "📝 Çıkarılan Ham Metin", "💾 SQL Arşiv Kayıtları"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        yuklenen_dosya = st.file_uploader("Çok Sayfalı PDF veya Fotoğraf Yükle", type=["pdf", "png", "jpg", "jpeg"])
        belge_adi = st.text_input("Belge Adı / Etiket", placeholder="Örn: Sakarya_Meydan_Muharebesi")
        baslat_butonu = st.button("🚀 Tüm Belgeyi Baştan Sona Tara ve Analiz Et", use_container_width=True)
        
    with col2:
        st.subheader("📋 Yapay Zeka Detaylı Analiz Raporu")
        rapor_alani = st.empty()
        rapor_alani.info("Lütfen sol taraftan bir belge yükleyip analizi başlatın.")

# İşlem Bloğu
if baslat_butonu and yuklenen_dosya and belge_adi:
    tüm_metin = ""
    st.toast("OCR İşlemi Başlatıldı, sayfalar taranıyor...")
    
    if yuklenen_dosya.type == "application/pdf":
        doc = fitz.open(stream=yuklenen_dosya.read(), filetype="pdf")
        for sayfa_no in range(len(doc)):
            page = doc.load_page(sayfa_no)
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            img = Image.open(fitz.io.BytesIO(img_data))
            sonuc = reader.readtext(np.array(img), detail=0)
            tüm_metin += f"\n--- Sayfa {sayfa_no+1} ---\n" + " ".join(sonuc)
    else:
        img = Image.open(yuklenen_dosya)
        sonuc = reader.readtext(np.array(img), detail=0)
        tüm_metin = " ".join(sonuc)
        
    with tab2:
        st.text_area("OCR Tarafından Okunan Ham Metin", tüm_metin, height=300)
        
    rapor_alani.warning("Metin tarandı, Yapay Zeka (LLM) analizi yapılıyor... Lütfen bekleyin.")
    
    # LLM Analizi
    rapor = llm_ile_analiz_et(tüm_metin)
    rapor_alani.success("Analiz Tamamlandı!")
    rapor_alani.markdown(rapor)
    
    # Veritabanına Kaydet
    conn = sqlite3.connect("proje_hafizasi.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO belgeler (belge_adi, ham_metin, analiz_raporu) VALUES (?, ?, ?)", (belge_adi, tüm_metin, rapor))
    conn.commit()
    conn.close()

# Arşiv Sekmesi Güncellemesi
with tab3:
    st.subheader("📂 Geçmiş SQL Kayıtları")
    conn = sqlite3.connect("proje_hafizasi.db")
    df = pd.read_sql_query("SELECT id, belge_adi, analiz_raporu FROM belgeler", conn)
    st.dataframe(df, use_container_width=True)
    conn.close()
