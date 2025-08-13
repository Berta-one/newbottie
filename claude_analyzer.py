#!/usr/bin/env python3
"""
Fixed Claude API Analyzer for Bottie Trading Bot
Updated with correct model names
"""

import os
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  anthropic library not found. Install with: pip install anthropic")

def check_setup():
    """Check if everything is properly set up"""
    print("🔧 Checking setup...")
    
    # Check API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found in environment variables")
        print("   Set it with: export ANTHROPIC_API_KEY=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")
        return False
    
    if not api_key.startswith('sk-ant-'):
        print("❌ API key format looks incorrect (should start with 'sk-ant-')")
        return False
    
    print(f"✅ API Key found: {api_key[:20]}...")
    
    # Check library
    if not ANTHROPIC_AVAILABLE:
        print("❌ Anthropic library not installed")
        return False
    
    print("✅ Anthropic library available")
    
    # Check files exist
    required_files = ['api/app.py', 'sentiment/sentiment_service.py']
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ Found {file_path}")
        else:
            print(f"❌ Missing {file_path}")
            return False
    
    print("✅ All checks passed!")
    return True

def test_api_connection():
    """Test API connection with a simple request"""
    if not ANTHROPIC_AVAILABLE:
        return False
    
    print("🔌 Testing API connection...")
    
    client = anthropic.Anthropic(
        api_key=os.getenv('ANTHROPIC_API_KEY')
    )
    
    try:
        # Test with a simple message using the current model
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # Updated model name
            max_tokens=100,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": "Hello, this is a test. Please respond with 'API connection successful'."
                }
            ]
        )
        
        response = message.content[0].text
        if "successful" in response.lower():
            print("✅ API connection test passed")
            return True
        else:
            print(f"⚠️  Unexpected API response: {response}")
            return True  # Still working, just unexpected response
            
    except Exception as e:
        print(f"❌ API connection test failed: {e}")
        
        # Try alternative model names
        alternative_models = [
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229", 
            "claude-3-haiku-20240307"
        ]
        
        for model in alternative_models:
            try:
                print(f"🔄 Trying alternative model: {model}")
                message = client.messages.create(
                    model=model,
                    max_tokens=50,
                    messages=[{"role": "user", "content": "Test"}]
                )
                print(f"✅ Working model found: {model}")
                return model
            except:
                continue
        
        return False

def read_file_safely(file_path, max_chars=8000):
    """Read file with size limits for API"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if len(content) > max_chars:
            print(f"⚠️  {file_path} is large ({len(content)} chars), truncating to {max_chars}")
            content = content[:max_chars] + "\n\n... [TRUNCATED] ..."
        
        return content
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return None

def analyze_with_claude(file_contents, analysis_type="general", working_model=None):
    """Send analysis request to Claude"""
    if not ANTHROPIC_AVAILABLE:
        print("❌ Cannot analyze: anthropic library not available")
        return None
    
    client = anthropic.Anthropic(
        api_key=os.getenv('ANTHROPIC_API_KEY')
    )
    
    # Use working model or default to latest
    model_to_use = working_model if working_model else "claude-3-5-sonnet-20241022"
    
    # Create specific prompts based on analysis type
    if analysis_type == "threshold_sentiment":
        prompt = f"""
I'm having issues with my cryptocurrency trading bot. The thresholds and sentiment functionality are not working properly.

Here are the relevant files:

API/APP.PY:
```python
{file_contents['api/app.py']}
```

SENTIMENT/SENTIMENT_SERVICE.PY:
```python
{file_contents['sentiment/sentiment_service.py']}
```

**Specific Issues I'm Experiencing:**
1. Sentiment scores not updating properly
2. Adaptive thresholds not working correctly  
3. Signal generation seems inconsistent
4. Environment variables might not be configured correctly

**Please analyze and provide:**
1. Root cause analysis of why sentiment might be failing
2. Issues with the threshold calculation logic
3. Configuration or environment problems
4. Specific code fixes with examples
5. Step-by-step debugging instructions

Focus on actionable solutions I can implement immediately.
"""
    
    elif analysis_type == "environment":
        prompt = f"""
Analyze the environment and configuration setup for this trading bot:

API/APP.PY:
```python
{file_contents['api/app.py']}
```

Please check:
1. Environment variable usage and validation
2. Default values and their appropriateness
3. Missing configuration checks
4. Potential startup issues
5. Dependencies between different config variables

Provide a configuration checklist and validation script.
"""
    
    else:  # general analysis
        prompt = f"""
Analyze these files from a cryptocurrency trading bot for issues:

{chr(10).join([f"{path}:{chr(10)}```python{chr(10)}{content}{chr(10)}```{chr(10)}" for path, content in file_contents.items()])}

Focus on:
1. Potential bugs or logic errors
2. Performance issues
3. Security vulnerabilities
4. Best practices violations
5. Error handling improvements
"""
    
    try:
        print(f"🤖 Sending request to Claude (model: {model_to_use})...")
        message = client.messages.create(
            model=model_to_use,
            max_tokens=4000,
            temperature=0.1,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        return message.content[0].text
        
    except Exception as e:
        print(f"❌ Error calling Claude API: {e}")
        
        # If the model failed, try alternatives
        if "not_found_error" in str(e) or "404" in str(e):
            print("🔄 Model not found, trying alternatives...")
            alternative_models = [
                "claude-3-5-sonnet-20241022",
                "claude-3-sonnet-20240229", 
                "claude-3-opus-20240229",
                "claude-3-haiku-20240307"
            ]
            
            for alt_model in alternative_models:
                if alt_model == model_to_use:
                    continue
                try:
                    print(f"🔄 Trying {alt_model}...")
                    message = client.messages.create(
                        model=alt_model,
                        max_tokens=4000,
                        temperature=0.1,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    print(f"✅ Success with {alt_model}")
                    return message.content[0].text
                except Exception as alt_e:
                    print(f"❌ {alt_model} also failed: {alt_e}")
                    continue
        
        return None

def save_results(analysis_results, analysis_type):
    """Save analysis results to files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"claude_analysis_{analysis_type}_{timestamp}.md"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# Claude Analysis Results - {analysis_type.title()}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            f.write(analysis_results)
        
        print(f"✅ Results saved to: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Error saving results: {e}")
        return None

def main():
    print("🚀 Claude Bottie Trading Bot Analyzer (Fixed)")
    print("=" * 50)
    
    # Step 1: Check setup
    if not check_setup():
        print("\n❌ Setup check failed. Please fix the issues above and try again.")
        sys.exit(1)
    
    # Step 2: Test API connection
    working_model = test_api_connection()
    if not working_model:
        print("\n❌ API connection failed. Please check:")
        print("• Your API key is correct")
        print("• You have internet connection")
        print("• You have API credits available")
        print("• The Anthropic service is not down")
        sys.exit(1)
    
    if isinstance(working_model, str) and working_model != True:
        print(f"🔧 Using working model: {working_model}")
    else:
        working_model = "claude-3-5-sonnet-20241022"
    
    print("\n" + "=" * 50)
    
    # Step 3: Read files
    print("📁 Reading project files...")
    file_contents = {}
    
    files_to_analyze = {
        'api/app.py': 'Main API file with threshold and sentiment logic',
        'sentiment/sentiment_service.py': 'Sentiment analysis service'
    }
    
    for file_path, description in files_to_analyze.items():
        print(f"   📄 Reading {file_path} ({description})...")
        content = read_file_safely(file_path)
        if content:
            file_contents[file_path] = content
        else:
            print(f"   ❌ Failed to read {file_path}")
    
    if not file_contents:
        print("❌ No files could be read. Exiting.")
        sys.exit(1)
    
    print(f"✅ Successfully read {len(file_contents)} files")
    
    # Step 4: Quick analysis (just threshold & sentiment for now)
    print("\n" + "=" * 50)
    print("🔍 Running Threshold & Sentiment Analysis...")
    
    result = analyze_with_claude(file_contents, "threshold_sentiment", working_model)
    
    if result:
        print("✅ Analysis completed successfully!")
        
        # Save result
        filename = save_results(result, "threshold_sentiment")
        
        # Show preview
        print(f"\n📋 Preview:")
        print("-" * 40)
        lines = result.split('\n')
        for line in lines[:25]:  # Show first 25 lines
            print(line)
        if len(lines) > 25:
            print("... (see full results in the saved file)")
        print("-" * 40)
        
        print(f"\n🎯 Next steps:")
        print(f"1. Open {filename} to see the complete analysis")
        print("2. Implement the suggested fixes")
        print("3. Test the changes")
        print("4. Re-run this script to verify improvements")
        
    else:
        print("❌ Analysis failed completely.")
        print("\n🔧 Troubleshooting:")
        print("• Try running with a simpler prompt")
        print("• Check if the Anthropic service is experiencing issues")
        print("• Verify your API credits haven't been exhausted")

if __name__ == "__main__":
    main()