# Akıllı Belge Analizi ve Özetleme (MetinÖz)

Bu proje, BTK Akademi Antalya Büyük Dil Modelleri (LLMs) Tabanlı Uygulama Geliştirme Atölyesi kapsamında geliştirilmiştir. Kullanıcıların sisteme girdikleri uzun metinleri ve belgeleri analiz eden, kelime sayısını çıkaran ve yapay zeka destekli özet raporu üreten web tabanlı bir sistemdir.

## 🚀 Canlı Demo
Uygulamayı canlı olarak incelemek için tıklayın: [Akıllı Belge Özetleyici](https://akilli-ozetleyici.onrender.com/)



## 🛠️ Kullanılan Teknolojiler

Projede geliştirme, model eğitimi, barındırma ve arayüz süreçlerinde şu modern araçlar ve teknolojiler tercih edilmiştir:
- **Google Colab:** Model ince ayar (fine-tuning) süreçlerinin yürütüldüğü bulut ortamı.
- **Hugging Face:** Eğitilen modelin ve veri setlerinin barındırıldığı platform.
- **Render:** Web uygulamasının canlıya alınması ve barındırılması için kullanılan bulut platformu.
- **Gemini AI:** Destekleyici yapay zeka entegrasyonları.
- **Gradio / Flask:** Kullanıcı arayüzü ve web sunucusu altyapısı.
- **GitHub:** Versiyon kontrolü ve kaynak kod yönetimi.
- **Prompt Mühendisliği:** Model çıktı kalitesini artırmak için kullanılan yönlendirme teknikleri.



## 🧠 Model ve Veri Seti

- **Dil Modeli:** Yapılandırılmış JSON çıktısı üretmek amacıyla **Gemma 3** dil modeli temel alınmıştır.
- **Eğitim Süreci:** Modelin ince ayar (fine-tuning) süreci ve QLoRA optimizasyonları Google Colab ortamında gerçekleştirilmiştir.



## 🏗️ Mimari ve Nasıl Çalışıyor?

1. **Girdi:** Kullanıcı, web arayüzü üzerinden sistemine uzun bir metin veya belge girer.
2. **İstek Yönetimi:** İstek, GitHub altyapısıyla yönetilen ve **Render** üzerinde canlıda çalışan sistem üzerinden modelimize iletilir.
3. **İşleme:** Hugging Face üzerinde barındırılan ve özelleştirilen **Gemma 3** modeli metni analiz eder.
4. **Çıktı:** Model; kelime sayısını çıkaran, yapılandırılmış JSON formatında ve yapay zeka destekli özet raporunu kullanıcıya geri döndürür.



## 👩‍💻 Geliştirici
* **Raziye Uçar** 
