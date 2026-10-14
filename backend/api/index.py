import sys
from pathlib import Path

# Adiciona o diretório backend ao sys.path para importações no runtime serverless da Vercel
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
