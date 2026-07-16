from flask import Flask, render_template, request, jsonify
from huggingface_hub import InferenceClient
import os

app = Flask(__name__)

HF_TOKEN = os.environ.get("HF_TOKEN")
client = InferenceClient(token=HF_TOKEN)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    sorgu = data.get("sorgu", "")
    
    try:
        # Doğru ve güncel Hugging Face sohbet metodu
        response = client.chat.completions.create(
            model="HuggingFaceH4/zephyr-7b-beta",
            messages=[{"role": "user", "content": sorgu}],
            max_tokens=250
        )
        cevap = response.choices[0].message.content
        return jsonify({"cevap": cevap})
    except Exception as e:
        return jsonify({"hata": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
