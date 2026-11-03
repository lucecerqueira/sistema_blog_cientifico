from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # 1. Area Publica Visitante
    path('', views.PublicHomeView.as_view(), name='public_home'),
    
    # 2. Area Blog Cientifico
    path('blog/', views.BlogListView.as_view(), name='blog_list'),
    path('blog/<slug:slug>/', views.BlogDetailView.as_view(), name='blog_detail'),
    
    # 3. Area Repositorio de Codigos (Python & Rust)
    path('codigos/', views.CodeLabListView.as_view(), name='code_list'),
    path('laboratorio-interativo/', views.InteractiveSandboxView.as_view(), name='code_sandbox'),
    path('api/executar-codigo/', views.ExecuteSandboxAPIView.as_view(), name='api_executar_codigo'),
    path('codigos/<slug:slug>/', views.CodeLabDetailView.as_view(), name='code_detail'),
    
    # 4. Area do Aluno
    path('aluno/', views.StudentPortalView.as_view(), name='student_portal'),
    path('aluno/certificado/<int:matricula_id>/', views.EmitirCertificadoAlunoPDFView.as_view(), name='emitir_certificado_pdf'),
    
    # 5. Area de Gestao de Alunos
    path('gestao-alunos/', views.StudentManagementView.as_view(), name='manage_students'),
    
    # 6. Area de Gestao da Pagina (CMS)
    path('gestao-pagina/', views.SiteManagementView.as_view(), name='manage_site'),
    
    # Autenticacao e Cadastro Profissional
    path('login/', auth_views.LoginView.as_view(template_name='ds_platform/login.html'), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('cadastro/', views.CadastroProfissionalView.as_view(), name='register'),
    path('redirecionar-acesso/', views.RedirecionarAcessoView.as_view(), name='redirecionar_acesso'),
]
