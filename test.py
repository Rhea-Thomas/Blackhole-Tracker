# test.py
try:
    import flask
    import psycopg2
    print("✅ All packages installed successfully!")
    print(f"Flask version: {flask.__version__}")
except ImportError as e:
    print(f"❌ Missing package: {e}")