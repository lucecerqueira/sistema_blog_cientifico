import os
import sys
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_config.settings')

try:
    application = get_wsgi_application()
except Exception as e:
    print(f"ERRO CRITICO AO INICIALIZAR DJANGO: {e}", file=sys.stderr)
    raise e