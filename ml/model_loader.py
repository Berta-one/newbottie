
import os
import requests

MODEL_URLS = {
    'lstm': 'https://example.com/lstm_model.h5',
    'xgb': 'https://example.com/xgboost_model.json'
}

def download_models():
    os.makedirs('models', exist_ok=True)
    for name, url in MODEL_URLS.items():
        file_path = f'models/{name}_model.' + ('h5' if name == 'lstm' else 'json')
        if not os.path.exists(file_path):
            print(f"Downloading {name} model...")
            r = requests.get(url)
            with open(file_path, 'wb') as f:
                f.write(r.content)
