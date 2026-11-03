import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_config.settings')

# A variável 'application' TEM de estar declarada exatamente assim na raiz do ficheiro
application = get_wsgi_application()