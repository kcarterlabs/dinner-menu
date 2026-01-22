#!/bin/bash

# Start the Flask API in the background
echo "🚀 Starting Flask API on port 5000..."
cd "$(dirname "$0")/.." && python app.py &
API_PID=$!

# Wait for API to start
echo "⏳ Waiting for API to initialize..."
sleep 3

# Start Streamlit
echo "🎨 Starting Streamlit frontend on port 8501..."
python -m streamlit run scripts/deprecated/streamlit_app.py

# When Streamlit is stopped, also stop the API
kill $API_PID
