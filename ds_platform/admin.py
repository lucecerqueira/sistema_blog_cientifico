from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, CategoriaTematica, ArtigoCientificoBlog, RepositorioCodigo,
    CursoTrilha, ModuloAula, MatriculaAluno, SubmissaoProjetoAluno, ConfiguracaoPlataforma
)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'papel', 'instituicao', 'is_staff')
    list_filter = ('papel', 'is_staff', 'instituicao')
    fieldsets = UserAdmin.fieldsets + (
        ('Credenciais Cientificas & Profissionais', {
            'fields': ('papel', 'instituicao', 'cargo_atuacao', 'bio_curta', 'orcid_id', 'lattes_url', 'github_url', 'linkedin_url')
        }),
    )

@admin.register(CategoriaTematica)
class CategoriaTematicaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'codigo_area', 'slug', 'ordem')
    prepopulated_fields = {'slug': ('nome',)}

@admin.register(ArtigoCientificoBlog)
class ArtigoCientificoBlogAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'autor', 'status', 'nivel_acesso', 'visualizacoes', 'criado_em')
    list_filter = ('status', 'nivel_acesso', 'categoria')
    prepopulated_fields = {'slug': ('titulo',)}

@admin.register(RepositorioCodigo)
class RepositorioCodigoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'linguagem', 'categoria', 'complexidade_tempo', 'publico', 'downloads_clones')
    list_filter = ('linguagem', 'categoria', 'publico')
    prepopulated_fields = {'slug': ('titulo',)}

@admin.register(CursoTrilha)
class CursoTrilhaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'nivel', 'carga_horaria', 'ativo')
    prepopulated_fields = {'slug': ('titulo',)}

admin.site.register(ModuloAula)
admin.site.register(MatriculaAluno)
admin.site.register(SubmissaoProjetoAluno)
admin.site.register(ConfiguracaoPlataforma)
