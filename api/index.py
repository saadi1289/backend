import sys
import traceback

try:
    from mangum import Mangum
    from app.main import app
    
    # Vercel serverless handler
    handler = Mangum(app, lifespan="off")
except Exception as e:
    print(f"Error loading app: {e}", file=sys.stderr)
    print(traceback.format_exc(), file=sys.stderr)
    raise
