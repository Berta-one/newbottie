 -*- coding: utf-8 -*-
from flask import Flask
import os

app = Flask(__name__)


@app.route("/")
def home():
    port = os.environ.get("PORT", "Not Set")
    return f"""
   <h1>ðŸ¤– Bottie Trading Bot</h1>
   <h2>âœ… Successfully deployed on Railway!</h2>
   <p><strong>PORT:</strong> {port}</p>
   <p><strong>Environment:</strong> {os.environ.get('RAILWAY_ENVIRONMENT', 'Unknown')}</p>
   <p>Flask is working perfectly on Railway!</p>
   <hr>
   <p>Ready to add Streamlit back once we confirm deployment works.</p>
   """


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

