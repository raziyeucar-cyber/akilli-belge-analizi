from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

HF_TOKEN = os.environ.get("HF_TOKEN")
# Hugging Face'in en kararlı çalışan doğrudan API uç noktası
API_URL = "https://api-inference.huggingface.co/models/google/gemma-2-2b-it"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    sorgu = data.get("sorgu", "")
    
    payload = {
        "inputs": sorgu,
        "parameters": {"max_new_tokens": 250}
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        res_data = response.json()
        
        # Gelen yanıtın formatını güvenli bir şekilde yakalayalım
        if isinstance(res_data, list) and len(res_data) > 0:
            cevap = res_data[0].get("generated_text", str(res_data))
        elif isinstance(res_data, dict) and "generated_text" in res_data:
            cevap = res_data["generated_text"]
        else:
            cevap = str(res_data)
            
        return jsonify({"cevap": cevap})
    except Exception as e:
        return jsonify({"hata": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
