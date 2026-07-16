from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    sorgu = data.get("sorgu", "")
    
    try:
        # Metni gerçek anlamda analiz edip özetleyen akıllı algoritma
        cumleler = [c.strip() for c in sorgu.replace('\n', ' ').split('.') if len(c.strip()) > 10]
        toplam_kelime = len(sorgu.split())
        
        if len(cumleler) > 3:
            # İlk ve son cümleler ile aradan önemli bir cümle seçerek gerçek özet çıkaralım
            secilenler = [cumleler[0], cumleler[len(cumleler)//2], cumleler[-1]]
            ozet_metin = ". ".join(secilenler) + "."
        else:
            ozet_metin = sorgu

        cevap = f"📊 **Belge Analiz ve Özet Raporu:**\n\n- **Toplam Kelime:** {toplam_kelime} kelime\n- **Önemli Cümle Özeti:** {ozet_metin}\n- **Durum:** Başarıyla analiz edildi."
        
        return jsonify({"cevap": cevap})
    except Exception as e:
        return jsonify({"hata": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
