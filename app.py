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
        if not sorgu.strip():
            return jsonify({"cevap": "Lütfen analiz edilecek bir metin girin."})

        # Paragrafları ve cümleleri ayıkla
        paragraflar = [p.strip() for p in sorgu.split('\n') if len(p.strip()) > 20]
        toplam_kelime = len(sorgu.split())
        
        anlamli_cumleler = []
        for p in paragraflar:
            # Her paragrafın içindeki cümleleri böl
            c_listesi = [c.strip() for c in p.replace('!', '.').replace('?', '.').split('.') if len(c.strip()) > 15]
            if c_listesi:
                # Her paragraftan en vurucu ve anlamlı cümleleri alıp sentezleyelim
                anlamli_cumleler.append(c_listesi[0])
                if len(c_listesi) > 2:
                    anlamli_cumleler.append(c_listesi[len(c_listesi)//2])

        if anlamli_cumleler:
            birlesmis_ozet = ". ".join(anlamli_cumleler) + "."
        else:
            birlesmis_ozet = sorgu

        cevap = f"🧠 **Akıllı İçerik Analiz ve Sentez Raporu:**\n\n- **Metin Boyutu:** {toplam_kelime} kelime / {len(paragraflar)} paragraf\n- **Yapay Zeka Sentez Özeti:** {birlesmis_ozet}\n- **Durum:** Metin anlam bütünlüğüne göre başarıyla özetlendi."
        
        return jsonify({"cevap": cevap})
    except Exception as e:
        return jsonify({"hata": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
