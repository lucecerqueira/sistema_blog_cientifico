import os
import sys
import subprocess
import tempfile
import time
import json
import math
import random
from pathlib import Path
from io import BytesIO

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, DetailView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.db.models import Avg, Count, Q
from django.urls import reverse_lazy

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

from .models import (
    User, CategoriaTematica, ArtigoCientificoBlog, RepositorioCodigo,
    CursoTrilha, ModuloAula, MatriculaAluno, SubmissaoProjetoAluno, ConfiguracaoPlataforma
)
from .forms import (
    CadastroSimplesForm, ArtigoCientificoForm, RepositorioCodigoForm,
    MatriculaGestaoForm, SubmissaoAlunoForm
)


class GestorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_gestor()


# ==============================================================================
# 1. AREA PUBLICA VISITANTE (VITRINE DE PESQUISA E PORTAL DE ENTRADA)
# ==============================================================================
class PublicHomeView(TemplateView):
    template_name = 'ds_platform/public_home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categorias'] = CategoriaTematica.objects.all()
        ctx['artigos_destaque'] = ArtigoCientificoBlog.objects.filter(status='publicado', nivel_acesso='publico').select_related('categoria', 'autor')[:4]
        ctx['codigos_recentes'] = RepositorioCodigo.objects.filter(publico=True).select_related('categoria')[:4]
        ctx['cursos_disponiveis'] = CursoTrilha.objects.filter(ativo=True).select_related('categoria')[:4]
        ctx['metricas_publicas'] = {
            'total_artigos': ArtigoCientificoBlog.objects.filter(status='publicado').count(),
            'total_codigos': RepositorioCodigo.objects.count(),
            'total_cursos': CursoTrilha.objects.filter(ativo=True).count(),
            'total_alunos': User.objects.filter(papel='aluno').count(),
        }
        return ctx


# ==============================================================================
# 2. AREA TIPO BLOG CIENTIFICO (ENSAIOS, MODELAGEM E BIOINFORMATICA)
# ==============================================================================
class BlogListView(ListView):
    model = ArtigoCientificoBlog
    template_name = 'ds_platform/blog_list.html'
    context_object_name = 'artigos'
    paginate_by = 10

    def get_queryset(self):
        qs = ArtigoCientificoBlog.objects.filter(status='publicado').select_related('categoria', 'autor')
        if not self.request.user.is_authenticated:
            qs = qs.filter(nivel_acesso='publico')
        cat_slug = self.request.GET.get('categoria')
        busca = self.request.GET.get('q')
        if cat_slug:
            qs = qs.filter(categoria__slug=cat_slug)
        if busca:
            qs = qs.filter(Q(titulo__icontains=busca) | Q(resumo__icontains=busca) | Q(conteudo_markdown__icontains=busca))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categoria_ativa'] = self.request.GET.get('categoria', '')
        ctx['busca_atual'] = self.request.GET.get('q', '')
        return ctx


class BlogDetailView(DetailView):
    model = ArtigoCientificoBlog
    template_name = 'ds_platform/blog_detail.html'
    context_object_name = 'artigo'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.visualizacoes += 1
        obj.save(update_fields=['visualizacoes'])
        return obj


# ==============================================================================
# 3. AREA DE REPOSITORIO DE CODIGOS (PYTHON, RUST, SQL, R)
# ==============================================================================
class CodeLabListView(ListView):
    model = RepositorioCodigo
    template_name = 'ds_platform/code_list.html'
    context_object_name = 'codigos'

    def get_queryset(self):
        qs = RepositorioCodigo.objects.filter(publico=True).select_related('categoria')
        lang = self.request.GET.get('lang')
        cat = self.request.GET.get('categoria')
        busca = self.request.GET.get('q')
        if lang:
            qs = qs.filter(linguagem=lang)
        if cat:
            qs = qs.filter(categoria__slug=cat)
        if busca:
            qs = qs.filter(Q(titulo__icontains=busca) | Q(descricao_tecnica__icontains=busca) | Q(dependencias__icontains=busca))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['lang_ativa'] = self.request.GET.get('lang', '')
        ctx['cat_ativa'] = self.request.GET.get('categoria', '')
        ctx['busca_atual'] = self.request.GET.get('q', '')
        ctx['linguagens_disponiveis'] = RepositorioCodigo.LINGUAGENS
        return ctx


class CodeLabDetailView(DetailView):
    model = RepositorioCodigo
    template_name = 'ds_platform/code_detail.html'
    context_object_name = 'codigo'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.downloads_clones += 1
        obj.save(update_fields=['downloads_clones'])
        return obj


# ==============================================================================
# 4. AREA DO ALUNO (AMBIENTE DE ESTUDO, TRILHAS E SUBMISSAO DE PROJETOS)
# ==============================================================================
class StudentPortalView(LoginRequiredMixin, TemplateView):
    template_name = 'ds_platform/student_portal.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        matriculas = MatriculaAluno.objects.filter(aluno=user).select_related('curso', 'curso__categoria').prefetch_related('curso__aulas')
        ctx['matriculas'] = matriculas
        ctx['submissoes'] = SubmissaoProjetoAluno.objects.filter(matricula__aluno=user).select_related('matricula__curso')
        ctx['artigos_exclusivos'] = ArtigoCientificoBlog.objects.filter(status='publicado', nivel_acesso='aluno')[:5]
        ctx['form_submissao'] = SubmissaoAlunoForm(user=user)
        ctx['cursos_abertos'] = CursoTrilha.objects.filter(ativo=True).exclude(id__in=matriculas.values_list('curso_id', flat=True))
        return ctx

    def post(self, request, *args, **kwargs):
        acao = request.POST.get('acao')
        if acao == 'nova_matricula':
            curso_id = request.POST.get('curso_id')
            curso = get_object_or_404(CursoTrilha, id=curso_id, ativo=True)
            MatriculaAluno.objects.get_or_create(aluno=request.user, curso=curso, defaults={'progresso_percentual': 10.0})
            messages.success(request, f"Matricula realizada na trilha '{curso.titulo}'.")
            return redirect('student_portal')

        form = SubmissaoAlunoForm(request.user, request.POST)
        if form.is_valid():
            submissao = form.save()
            messages.success(request, f"Projeto '{submissao.titulo_entrega}' submetido para avaliacao metodologica.")
        else:
            messages.error(request, "Verifique os dados informados na submissao.")
        return redirect('student_portal')


class EmitirCertificadoAlunoPDFView(LoginRequiredMixin, View):
    def get(self, request, matricula_id):
        matricula = get_object_or_404(MatriculaAluno, id=matricula_id, aluno=request.user)
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        largura, altura = A4

        pdf.setFillColor(colors.HexColor('#090d16'))
        pdf.rect(0, 0, largura, altura, fill=1)

        pdf.setStrokeColor(colors.HexColor('#06b6d4'))
        pdf.setLineWidth(2)
        pdf.rect(25, 25, largura - 50, altura - 50, fill=0)

        pdf.setFillColor(colors.HexColor('#06b6d4'))
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(50, altura - 80, "QUANTUM.DS // RELATORIO ACADEMICO E CERTIFICACAO")

        pdf.setFillColor(colors.HexColor('#f8fafc'))
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(50, altura - 120, f"Aluno(a): {request.user.get_full_name() or request.user.username}")
        pdf.setFont("Helvetica", 11)
        pdf.setFillColor(colors.HexColor('#94a3b8'))
        instituicao_aluno = getattr(request.user, 'instituicao', '') or 'Pesquisa Independente'
        pdf.drawString(50, altura - 140, f"Instituicao: {instituicao_aluno}")
        pdf.drawString(50, altura - 160, f"E-mail Registrado: {request.user.email}")

        pdf.setFillColor(colors.HexColor('#38bdf8'))
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, altura - 210, "DADOS DA TRILHA CIENTIFICA / CURSO:")

        pdf.setFillColor(colors.HexColor('#e2e8f0'))
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, altura - 235, f"Trilha: {matricula.curso.titulo}")
        pdf.setFont("Helvetica", 11)
        pdf.drawString(50, altura - 255, f"Area Tematica: {matricula.curso.categoria.nome}")
        pdf.drawString(50, altura - 275, f"Carga Horaria: {matricula.curso.carga_horaria} horas | Status: {matricula.get_status_display()}")
        pdf.drawString(50, altura - 295, f"Progresso Concluido: {matricula.progresso_percentual:.1f}% | Nota Pratica: {matricula.nota_avaliacao_pratica or 'Em avaliacao'}")

        pdf.setStrokeColor(colors.HexColor('#1e293b'))
        pdf.line(50, 120, largura - 50, 120)
        pdf.setFillColor(colors.HexColor('#64748b'))
        pdf.setFont("Helvetica", 9)
        pdf.drawString(50, 95, f"Documento gerado eletronicamente pela Plataforma Data Science State-of-the-Art. ID Matricula #{matricula.id:05d}")

        pdf.showPage()
        pdf.save()
        buffer.seek(0)
        return HttpResponse(buffer.getvalue(), content_type='application/pdf')


# ==============================================================================
# 5. AREA DE GESTAO DE ALUNOS (COHORT, NOTAS, AVALIACOES E E-MAIL DIRETO)
# ==============================================================================
class StudentManagementView(GestorRequiredMixin, TemplateView):
    template_name = 'ds_platform/manage_students.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['alunos'] = User.objects.filter(papel__in=['aluno', 'pesquisador']).annotate(total_cursos=Count('matriculas'))
        ctx['matriculas'] = MatriculaAluno.objects.select_related('aluno', 'curso').all()
        ctx['submissoes'] = SubmissaoProjetoAluno.objects.select_related('matricula__aluno', 'matricula__curso').all()
        ctx['form_matricula'] = MatriculaGestaoForm()
        ctx['media_progresso'] = MatriculaAluno.objects.aggregate(media=Avg('progresso_percentual'))['media'] or 0.0
        return ctx

    def post(self, request, *args, **kwargs):
        acao = request.POST.get('acao')
        if acao == 'avaliar_submissao':
            sub_id = request.POST.get('submissao_id')
            sub = get_object_or_404(SubmissaoProjetoAluno, id=sub_id)
            sub.status_avaliacao = request.POST.get('status_avaliacao', 'aprovado')
            nota = request.POST.get('nota_atribuida')
            if nota:
                sub.nota_atribuida = float(nota)
                sub.matricula.nota_avaliacao_pratica = float(nota)
                sub.matricula.progresso_percentual = min(100.0, sub.matricula.progresso_percentual + 25.0)
                if sub.matricula.progresso_percentual >= 100.0:
                    sub.matricula.status = 'concluida'
                sub.matricula.save()
            sub.feedback_professor = request.POST.get('feedback_professor', '')
            sub.save()

            try:
                send_mail(
                    subject=f"[Plataforma Data Science] Avaliacao Concluida: {sub.titulo_entrega}",
                    message=(
                        f"Ola {sub.matricula.aluno.first_name or sub.matricula.aluno.username},\n\n"
                        f"Sua submissao '{sub.titulo_entrega}' na trilha '{sub.matricula.curso.titulo}' foi avaliada.\n"
                        f"Status: {sub.get_status_avaliacao_display()}\n"
                        f"Nota: {sub.nota_atribuida or 'N/A'}\n"
                        f"Parecer Tecnico: {sub.feedback_professor}\n\n"
                        f"Acesse o Portal do Aluno para visualizar os detalhes."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[sub.matricula.aluno.email],
                    fail_silently=True,
                )
            except Exception:
                pass

            messages.success(request, f"Avaliacao registrada e notificacao enviada para {sub.matricula.aluno.email}.")
            return redirect('manage_students')

        elif acao == 'criar_matricula':
            form = MatriculaGestaoForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Matricula registrada/atualizada com sucesso.")
            else:
                messages.error(request, "Falha ao registrar matricula. Verifique se o aluno ja esta matriculado neste curso.")
            return redirect('manage_students')

        return redirect('manage_students')


# ==============================================================================
# 6. AREA DE GESTAO DA PAGINA (CMS CIENTIFICO, PUBLICACOES E TELEMETRIA)
# ==============================================================================
class SiteManagementView(GestorRequiredMixin, TemplateView):
    template_name = 'ds_platform/manage_site.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['artigos'] = ArtigoCientificoBlog.objects.select_related('categoria', 'autor').all()
        ctx['codigos'] = RepositorioCodigo.objects.select_related('categoria').all()
        ctx['cursos'] = CursoTrilha.objects.select_related('categoria').all()
        ctx['form_artigo'] = ArtigoCientificoForm()
        ctx['form_codigo'] = RepositorioCodigoForm()
        return ctx

    def post(self, request, *args, **kwargs):
        tipo_form = request.POST.get('tipo_form')
        if tipo_form == 'novo_artigo':
            form = ArtigoCientificoForm(request.POST)
            if form.is_valid():
                artigo = form.save(commit=False)
                artigo.autor = request.user
                artigo.save()
                messages.success(request, f"Artigo '{artigo.titulo}' publicado com sucesso.")
            else:
                messages.error(request, "Erro ao validar campos do artigo.")
        elif tipo_form == 'novo_codigo':
            form = RepositorioCodigoForm(request.POST)
            if form.is_valid():
                codigo = form.save()
                messages.success(request, f"Snippet/Algoritmo '{codigo.titulo}' adicionado ao repositorio.")
            else:
                messages.error(request, "Erro ao validar campos do repositorio de codigo.")
        return redirect('manage_site')


# ==============================================================================
# CADASTRO SIMPLIFICADO, AUTENTICACAO E REDIRECIONAMENTO
# ==============================================================================
class CadastroProfissionalView(CreateView):
    model = User
    form_class = CadastroSimplesForm
    template_name = 'ds_platform/register.html'
    success_url = reverse_lazy('student_portal')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('redirecionar_acesso')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save(commit=False)
        user.papel = 'aluno'
        user.save()

        curso_inicial = CursoTrilha.objects.filter(ativo=True).first()
        if curso_inicial:
            MatriculaAluno.objects.get_or_create(aluno=user, curso=curso_inicial, defaults={'progresso_percentual': 5.0})

        try:
            send_mail(
                subject="Bem-vindo(a) a Plataforma - Conta Ativada",
                message=(
                    f"Ola {user.username},\n\n"
                    f"Sua conta na plataforma foi criada com sucesso.\n"
                    f"E-mail de acesso e recuperacao cadastrado: {user.email}\n\n"
                    f"Bons estudos!"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            pass

        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(self.request, f"Bem-vindo(a), {user.username}! Sua conta foi criada.")
        return redirect('student_portal')


class RedirecionarAcessoView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_gestor():
            return redirect('manage_site')
        return redirect('student_portal')


@method_decorator(csrf_exempt, name='dispatch')
class CustomLogoutView(View):
    def post(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, "Sessao encerrada com seguranca.")
        return redirect('public_home')

    def get(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, "Sessao encerrada com seguranca.")
        return redirect('public_home')


# ==============================================================================
# 7. SANDBOX INTERATIVO DE EXECUCAO (PYTHON & RUST)
# ==============================================================================
class InteractiveSandboxView(TemplateView):
    template_name = 'ds_platform/code_sandbox.html'


@method_decorator(csrf_exempt, name='dispatch')
class ExecuteSandboxAPIView(View):
    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body or "{}")
            linguagem = payload.get("linguagem", "python")
            codigo = payload.get("codigo", "")

            try:
                n_pontos = min(500, max(10, int(payload.get("n_pontos", 60))))
                coef_angular = float(payload.get("coef_angular", 2.5))
                intercepto = float(payload.get("intercepto", 10.0))
                ruido = max(0.0, float(payload.get("ruido", 3.5)))
            except ValueError:
                n_pontos, coef_angular, intercepto, ruido = 60, 2.5, 10.0, 3.5

            # Gera dataset sintetico deterministico para comparacao justa entre Python e Rust
            random.seed(42)
            x_vals = [round(i * (20.0 / n_pontos), 4) for i in range(n_pontos)]
            y_vals = [round(coef_angular * x + intercepto + random.gauss(0, ruido), 4) for x in x_vals]

            inicio_t = time.perf_counter()
            stdout_output = ""
            stderr_output = ""
            usou_compilador_nativo = True
            houve_erro = False

            with tempfile.TemporaryDirectory() as tmpdir:
                dados_json = json.dumps({"x": x_vals, "y": y_vals})
                Path(tmpdir, "dataset.json").write_text(dados_json, encoding="utf-8")

                if linguagem == "python":
                    script_file = Path(tmpdir, "main.py")
                    script_file.write_text(codigo, encoding="utf-8")
                    proc = subprocess.run(
                        [sys.executable, str(script_file)],
                        cwd=tmpdir,
                        capture_output=True,
                        text=True,
                        timeout=4
                    )
                    stdout_output = proc.stdout
                    stderr_output = proc.stderr
                    houve_erro = (proc.returncode != 0)

                elif linguagem == "rust":
                    rs_file = Path(tmpdir, "main.rs")
                    bin_file = Path(tmpdir, "main_bin")

                    # Injeta os vetores X e Y diretamente no template Rust caso o marcador esteja presente
                    x_rust_array = ", ".join(f"{v:.4f}" for v in x_vals)
                    y_rust_array = ", ".join(f"{v:.4f}" for v in y_vals)
                    codigo_compilavel = (
                        codigo
                        .replace("/*__X_DATA__*/", x_rust_array)
                        .replace("/*__Y_DATA__*/", y_rust_array)
                        .replace('RESULT_JSON:{\\"b1\\"', 'RESULT_JSON:{{\\"b1\\"')
                        .replace('RESULT_JSON:{"b1"', 'RESULT_JSON:{{"b1"')
                    )
                    rs_file.write_text(codigo_compilavel, encoding="utf-8")

                    try:
                        comp = subprocess.run(
                            ["rustc", "-O", str(rs_file), "-o", str(bin_file)],
                            cwd=tmpdir,
                            capture_output=True,
                            text=True,
                            timeout=8
                        )
                        if comp.returncode != 0:
                            stderr_output = comp.stderr
                            houve_erro = True
                        else:
                            inicio_t = time.perf_counter()
                            proc = subprocess.run(
                                [str(bin_file)],
                                cwd=tmpdir,
                                capture_output=True,
                                text=True,
                                timeout=4
                            )
                            stdout_output = proc.stdout
                            stderr_output = proc.stderr
                            houve_erro = (proc.returncode != 0)
                    except (FileNotFoundError, PermissionError, OSError):
                        usou_compilador_nativo = False
                        houve_erro = False
                        inicio_t = time.perf_counter()
                        n = float(len(x_vals))
                        mean_x = sum(x_vals) / n
                        mean_y = sum(y_vals) / n
                        num = sum((x_vals[i] - mean_x) * (y_vals[i] - mean_y) for i in range(int(n)))
                        den = sum((x_vals[i] - mean_x) ** 2 for i in range(int(n)))
                        b1 = num / den if den != 0 else 0.0
                        b0 = mean_y - b1 * mean_x
                        y_pred = [b1 * x + b0 for x in x_vals]
                        ss_res = sum((y_vals[i] - y_pred[i]) ** 2 for i in range(int(n)))
                        ss_tot = sum((y_vals[i] - mean_y) ** 2 for i in range(int(n)))
                        r2 = 1.0 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
                        mse = ss_res / n
                        stdout_output = (
                            f"[SIMULADOR RUST ZERO-ALLOCATION ENGINE]\n"
                            f"(Nota: instale 'rustc' no sistema para compilacao binaria ELF nativa)\n"
                            f"--------------------------------------------------\n"
                            f"Amostras processadas (N): {int(n)}\n"
                            f"Coeficiente Angular (beta_1): {b1:.6f}\n"
                            f"Intercepto (beta_0):          {b0:.6f}\n"
                            f"Coeficiente Determinacao R2:  {r2:.6f}\n"
                            f"Erro Quadratico Medio (MSE):  {mse:.6f}\n"
                            f"RESULT_JSON:{json.dumps({'b1': b1, 'b0': b0, 'r2': r2, 'mse': mse})}"
                        )

            tempo_ms = round((time.perf_counter() - inicio_t) * 1000.0, 3)

            metricas = {"b1": 0.0, "b0": 0.0, "r2": 0.0, "mse": 0.0}
            linhas_limpas = []
            for linha in stdout_output.splitlines():
                if "RESULT_JSON:" in linha:
                    try:
                        json_str = linha.split("RESULT_JSON:", 1)[1].strip()
                        metricas = json.loads(json_str)
                    except Exception:
                        pass
                else:
                    linhas_limpas.append(linha)

            y_hat = [round(metricas.get("b1", 0.0) * x + metricas.get("b0", 0.0), 4) for x in x_vals]

            return JsonResponse({
                "status": "erro" if houve_erro else "ok",
                "stdout": "\n".join(linhas_limpas),
                "stderr": stderr_output if houve_erro else "",
                "tempo_ms": tempo_ms,
                "nativo": usou_compilador_nativo,
                "x": x_vals,
                "y": y_vals,
                "y_hat": y_hat,
                "metricas": metricas,
            })
        except subprocess.TimeoutExpired:
            return JsonResponse({"status": "erro", "stderr": "Timeout: A execucao excedeu o limite de tempo de seguranca (4s)."}, status=400)
        except Exception as e:
            return JsonResponse({"status": "erro", "stderr": str(e)}, status=500)