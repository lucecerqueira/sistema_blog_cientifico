from .models import ConfiguracaoPlataforma, CategoriaTematica

def platform_context(request):
    config = ConfiguracaoPlataforma.objects.first()
    categorias_menu = CategoriaTematica.objects.all()[:6]
    return {
        'plataforma_config': config,
        'categorias_globais': categorias_menu,
    }
