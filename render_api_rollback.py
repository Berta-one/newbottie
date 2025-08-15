# ROLLBACK VERSION - Original sentiment endpoint with demo data
# Use this if the updated sentiment endpoint is causing service issues

# Replace the sentiment endpoints in render_api.py with these if needed:

# Original sentiment endpoint (DEMO DATA)
@app.get("/sentiment")
def sentiment():
    return {"scores": demo_data["sentiment"]}

# Simple debug endpoint
@app.get("/sentiment/debug") 
def sentiment_debug():
    return {
        "status": "demo_mode",
        "using_real_data": False,
        "message": "Using demo sentiment data for stability"
    }

# INSTRUCTIONS TO ROLLBACK:
# 1. Copy the above endpoints 
# 2. Replace the current sentiment endpoints in render_api.py
# 3. Commit and push to restore service quickly
# 4. Then we can debug the real sentiment integration separately