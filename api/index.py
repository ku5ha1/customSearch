import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from main import app

# Export the FastAPI app for Vercel
# This is the standard way to deploy FastAPI on Vercel 