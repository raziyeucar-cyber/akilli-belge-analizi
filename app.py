HF_TOKEN = os.environ.get("HF_TOKEN")

import os
import gradio as gr
import torch
import numpy as np
import easyocr
import sqlite3
import requests
import fitz  # PDF işlemleri için PyMuPDF
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForObjectDetection

# ==========================================
# 0. HUGGING FACE API AYARI
# ==========================================
# Token'ı Hugging Face'in güvenli ortam değişkenlerinden (Secret) çekiyoruz:
HF_TOKEN = os.environ.get("HF_TOKEN") 
API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct"

# ==========================================
# 1. SQLITE VERİ TABANI AYARLARI
# ==========================================
DB_NAME = "proje_hafizasi.db"

def veritabanini_hazirla():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Belgeler (
            belge_id INTEGER PRIMARY KEY AUTOINCREMENT,
            dosya_adi TEXT NOT NULL,
            yukleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Metin_Sonuclari (
            sonuc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            belge_id INTEGER,
            okunan_metin TEXT,
            belge_ozeti TEXT,
            anahtar_kelimeler TEXT,
            FOREIGN KEY (belge_id) REFERENCES Belgeler(belge_id)
        )
    ''')
    conn.commit()
    conn.close()

veritabanini_hazirla()

# ==========================================
# 2. YAPAY ZEKA MODELLERİ
# ==========================================
print("Yapay zeka modelleri yükleniyor...")
model_path = "PaddlePaddle/PP-DocLayoutV3_safetensors"
model = AutoModelForObjectDetection.from_pretrained(model_path)
image_processor = AutoImageProcessor.from_pretrained(model_path)
reader = easyocr.Reader(['tr', 'en'])

# ==========================================
# 3. LLM ÖZETLEME VE ANALİZ FONKSİYONU
# ==========================================
def llm_ile_analiz_et(ham_metin):
    if not ham_metin.strip():
        return "Boş metin analiz edilemez.", "Yok"
        
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    # Yapay zekayı çok daha sıkı bir Türkçe kuralına tabi tutuyoruz:
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
            "temperature": 0.3,  # Sıcaklığı düşürdük ki daha mantıklı ve tutarlı cümleler kursun
            "return_full_text": False
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        sonuc = response.json()
        if isinstance(sonuc, list) and len(sonuc) > 0:
            analiz_raporu = sonuc[0].get("generated_text", "Analiz üretilemedi.")
        else:
            analiz_raporu = "Yapay zeka analiz sunucusundan yanıt alınamadı."
    except Exception as e:
        analiz_raporu = f"Analiz esnasında hata oluştu: {str(e)}"
        
    return analiz_raporu

# ==========================================
# 4. ANA İŞLEME VE SQL KAYIT SÜRECİ
# ==========================================
def belge_analiz_ve_sql_kayit(dosya_girdisi, dosya_adi_girdisi):
    if dosya_girdisi is None:
        return "Lütfen bir dosya (PDF veya Görsel) yükleyin.", "Lütfen analiz için dosya gönderin.", "Veri tabanında kayıt yok."
    
    dosya_yolu = dosya_girdisi.name
    dosya_uzantisi = os.path.splitext(dosya_yolu)[1].lower()
    
    if not dosya_adi_girdisi.strip():
        dosya_adi_girdisi = os.path.basename(dosya_yolu)

    islenmek_uzere_gorseller = []

    # ---- PDF veya RESİM AYIRT ETME VE TÜM SAYFALARI ALMA ----
    try:
        if dosya_uzantisi == ".pdf":
            pdf_dokumani = fitz.open(dosya_yolu)
            toplam_sayfa = len(pdf_dokumani)
            print(f"PDF tespit edildi. Toplam sayfa sayısı: {toplam_sayfa}")
            
            # Tüm sayfaları tek tek dolaşıp görsele çeviriyoruz
            for sayfa_no in range(toplam_sayfa):
                sayfa = pdf_dokumani.load_page(sayfa_no)
                # Bilgisayarı yormamak ve hızı korumak için 100 DPI kullanıyoruz
                piksel_haritasi = sayfa.get_pixmap(dpi=100) 
                img = Image.frombytes("RGB", [piksel_haritasi.width, piksel_haritasi.height], piksel_haritasi.samples)
                islenmek_uzere_gorseller.append(img)
        else:
            # Tek bir resimse listeye sadece onu ekle
            img = Image.open(dosya_yolu).convert("RGB")
            islenmek_uzere_gorseller.append(img)
            
    except Exception as e:
        return f"Dosya işlenirken hata oluştu: {str(e)}", "Dosya okunamadı.", "SQL Kaydı başarısız."

    # ---- TÜM SAYFALARIN TARANMASI (DÖNGÜ) ----
    nihai_metin = ""
    for index, image in enumerate(islenmek_uzere_gorseller):
        print(f"Sayfa {index+1}/{len(islenmek_uzere_gorseller)} taranıyor...")
        
        # 1. Aşama: Sayfa Düzeni Analizi
        inputs = image_processor(images=image, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
        results = image_processor.post_process_object_detection(outputs, target_sizes=[image.size[::-1]])[0]
        
        anlamli_bloklar = []
        for score, label_id, box in zip(results["scores"], results["labels"], results["boxes"]):
            if score.item() >= 0.50:
                anlamli_bloklar.append((box.tolist(), model.config.id2label[label_id.item()]))
                
        # Okuma sırasına göre diz
        anlamli_bloklar.sort(key=lambda x: x[0][1])
        
        # 2. Aşama: OCR ile Metinleri Okuma
        for box, etiket in anlamli_bloklar:
            x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
            kripilmis = image.crop((x1, y1, x2, y2))
            ocr_sonucu = reader.readtext(np.array(kripilmis), detail=0)
            okunan_metin = " ".join(ocr_sonucu)
            if okunan_metin.strip():
                nihai_metin += okunan_metin + " "
        
        # Sayfa aralarına boşluk ekle
        nihai_metin += "\n\n"
            
    if not nihai_metin.strip():
        return "Seçilen belgede okunabilir hiçbir metin tespit edilemedi.", "Analiz yapılamadı.", "SQL Kaydı yapılmadı."
        
    # 3. Aşama: LLM ile Otomatik Özetleme ve Analiz (Tüm sayfaların birleşik metni gidiyor)
    print("Tüm döküman başarıyla dijitalleştirildi. LLM analizi başlıyor...")
    analiz_raporu = llm_ile_analiz_et(nihai_metin)
    
    # ---- 4. Aşama: SQL VERİ TABANI KAYDI ----
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO Belgeler (dosya_adi) VALUES (?)", (dosya_adi_girdisi,))
    son_belge_id = cursor.lastrowid
    
    cursor.execute('''
        INSERT INTO Metin_Sonuclari (belge_id, okunan_metin, belge_ozeti, anahtar_kelimeler)
        VALUES (?, ?, ?, ?)
    ''', (son_belge_id, nihai_metin, analiz_raporu, dosya_adi_girdisi))
    
    conn.commit()
    conn.close()
    
    # Güncel SQL Tablosunu çekelim
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Metin_Sonuclari ORDER BY sonuc_id DESC LIMIT 3")
    gecmis = cursor.fetchall()
    conn.close()
    
    sql_ekran_raporu = "💾 VERİ TABANINA KAYDEDİLEN SON BELGE RAPORU:\n"
    for satir in gecmis:
        sql_ekran_raporu += f"Kayıt ID: {satir[0]} | Belge ID: {satir[1]} | Metin Boyutu: {len(satir[2])} karakter | Detaylı Özet Kaydedildi ✔️\n"
        
    return nihai_metin, analiz_raporu, sql_ekran_raporu

# ==========================================
# 5. AKILLI ARAYÜZ TASARIMI (GRADIO)
# ==========================================
with gr.Blocks(theme="soft") as demo:
    gr.Markdown("# 🤖 Akıllı Çok Sayfalı Belge Analiz ve Özetleme Asistanı")
    gr.Markdown("Bu sistem yüklenen **çok sayfalı PDF** belgelerini sayfa sayfa analiz eder, tüm içeriği birleştirir ve yapay zeka ile **derinlemesine kapsamlı bir özet rapor** çıkartır.")
    
    with gr.Row():
        with gr.Column(scale=1):
            dosya_girdisi = gr.File(
                label="Çok Sayfalı PDF veya Fotoğraf Yükle", 
                file_types=[".pdf", ".jpg", ".jpeg", ".png"]
            )
            isim_girdisi = gr.Textbox(label="Belge Adı / Etiket (Örn: Sakarya_Meydan_Muharebesi)", placeholder="Belge adını buraya yazın...")
            btn = gr.Button("🔍 Tüm Belgeyi Baştan Sona Tara ve Analiz Et", variant="primary")
        
        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.TabItem("📊 Yapay Zeka Detaylı Analiz Raporu"):
                    llm_ciktisi = gr.Markdown(label="LLM Analizi")
                with gr.TabItem("📝 Çıkarılan Tüm Ham Metin"):
                    metin_ciktisi = gr.Textbox(label="OCR Metni", lines=15, interactive=False)
                with gr.TabItem("💾 SQL Arşiv Kayıtları"):
                    sql_ciktisi = gr.Textbox(label="SQL Canlı Kayıt Bilgisi (SELECT * From Metin_Sonuclari)", lines=6)
            
    btn.click(fn=belge_analiz_ve_sql_kayit, inputs=[dosya_girdisi, isim_girdisi], outputs=[metin_ciktisi, llm_ciktisi, sql_ciktisi])

if __name__ == "__main__":
    demo.launch(share=True)