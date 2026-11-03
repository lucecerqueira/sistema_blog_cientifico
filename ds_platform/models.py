import markdown
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.utils import timezone

class User(AbstractUser):
    PAPEL_CHOICES = (
        ('visitante', 'Visitante Cadastrado'),
        ('aluno', 'Aluno Matriculado'),
        ('pesquisador', 'Pesquisador / Colaborador'),
        ('admin', 'Administrador / Cientista Chefe'),
    )
    papel = models.CharField(max_length=20, choices=PAPEL_CHOICES, default='aluno')
    instituicao = models.CharField(max_length=150, blank=True, help_text="Universidade, Instituto de Pesquisa ou Empresa")
    cargo_atuacao = models.CharField(max_length=120, blank=True, help_text="Ex: Doutor em Ciencias, Engenheiro de ML, Analista")
    bio_curta = models.TextField(blank=True)
    orcid_id = models.CharField(max_length=50, blank=True)
    lattes_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    email_verificado = models.BooleanField(default=False)
    receber_newsletter = models.BooleanField(default=True)

    def is_gestor(self):
        return self.is_superuser or self.is_staff or self.papel == 'admin'

    def is_aluno_ativo(self):
        return self.papel in ('aluno', 'pesquisador', 'admin') or self.is_staff

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_papel_display()})"


class CategoriaTematica(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    codigo_area = models.CharField(max_length=20, default="DS-CORE", help_text="Sigla tecnica: ML, BIO, STAT, MATH, RUST, PY")
    descricao = models.TextField()
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordem', 'nome']
        verbose_name = "Categoria Tematica"
        verbose_name_plural = "Categorias Tematicas"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.codigo_area}] {self.nome}"


class ArtigoCientificoBlog(models.Model):
    STATUS_CHOICES = (
        ('rascunho', 'Rascunho'),
        ('publicado', 'Publicado'),
    )
    NIVEL_ACESSO = (
        ('publico', 'Publico Visitante'),
        ('aluno', 'Exclusivo para Alunos'),
    )
    titulo = models.CharField(max_length=220)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    categoria = models.ForeignKey(CategoriaTematica, on_delete=models.PROTECT, related_name='artigos')
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='artigos_escritos')
    resumo = models.TextField(help_text="Sintese executiva ou abstract do artigo.")
    conteudo_markdown = models.TextField(help_text="Suporta Markdown, tabelas e equacoes LaTeX via MathJax ($$...$$).")
    referencias_bibliograficas = models.TextField(blank=True, help_text="Referencias formato ABNT ou IEEE.")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='publicado')
    nivel_acesso = models.CharField(max_length=15, choices=NIVEL_ACESSO, default='publico')
    destaque_home = models.BooleanField(default=False)
    tempo_leitura_min = models.PositiveIntegerField(default=8)
    visualizacoes = models.PositiveIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)[:220]
        palavras = len((self.conteudo_markdown or "").split())
        self.tempo_leitura_min = max(1, round(palavras / 180))
        super().save(*args, **kwargs)

    def conteudo_html(self):
        return markdown.markdown(
            self.conteudo_markdown,
            extensions=['fenced_code', 'tables', 'toc', 'nl2br']
        )

    def __str__(self):
        return self.titulo


class RepositorioCodigo(models.Model):
    LINGUAGENS = (
        ('python', 'Python 3.12+'),
        ('rust', 'Rust (Edition 2024)'),
        ('sql', 'PostgreSQL / SQL'),
        ('r', 'R Statistical Computing'),
        ('cpp', 'C++ / CUDA'),
    )
    titulo = models.CharField(max_length=180)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    linguagem = models.CharField(max_length=20, choices=LINGUAGENS, default='python')
    categoria = models.ForeignKey(CategoriaTematica, on_delete=models.PROTECT, related_name='codigos')
    descricao_tecnica = models.TextField(help_text="Explicacao da arquitetura, algoritmo e complexidade assintotica.")
    codigo_fonte = models.TextField(help_text="Codigo completo para syntax highlighting.")
    dependencias = models.CharField(max_length=250, blank=True, help_text="Ex: numpy, scipy, polars, tokio, ndarray")
    complexidade_tempo = models.CharField(max_length=50, default="O(n log n)")
    benchmark_nota = models.CharField(max_length=120, blank=True, help_text="Ex: Latencia media de 1.2ms em 1M registros")
    url_repositorio_externo = models.URLField(blank=True)
    publico = models.BooleanField(default=True)
    downloads_clones = models.PositiveIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)[:180]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.get_linguagem_display()}] {self.titulo}"


class CursoTrilha(models.Model):
    NIVEL_CHOICES = (
        ('fundamentos', 'Fundamentos Matematicos e Computacionais'),
        ('avancado', 'Avancado / Estado da Arte'),
        ('pesquisa', 'Pesquisa Aplicada & Produçao'),
    )
    titulo = models.CharField(max_length=180)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    categoria = models.ForeignKey(CategoriaTematica, on_delete=models.PROTECT, related_name='cursos')
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='avancado')
    ementa = models.TextField()
    carga_horaria = models.PositiveIntegerField(default=40, help_text="Carga horaria em horas")
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['titulo']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)[:180]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo


class ModuloAula(models.Model):
    curso = models.ForeignKey(CursoTrilha, on_delete=models.CASCADE, related_name='aulas')
    ordem = models.PositiveIntegerField(default=1)
    titulo = models.CharField(max_length=200)
    resumo_aula = models.TextField()
    conteudo_teorico_markdown = models.TextField(help_text="Notas de aula completas com suporte a LaTeX e blocos de codigo.")
    url_video_embed = models.URLField(blank=True, help_text="URL de embed de video aula")
    caderno_jupyter_url = models.URLField(blank=True, help_text="Link para Notebook ou script complementar")
    duracao_minutos = models.PositiveIntegerField(default=45)

    class Meta:
        ordering = ['curso', 'ordem']

    def conteudo_html(self):
        return markdown.markdown(self.conteudo_teorico_markdown, extensions=['fenced_code', 'tables'])

    def __str__(self):
        return f"{self.curso.titulo} - Aula {self.ordem}: {self.titulo}"


class MatriculaAluno(models.Model):
    STATUS_MATRICULA = (
        ('ativa', 'Ativa / Em Curso'),
        ('concluida', 'Concluida com Aprovacao'),
        ('trancada', 'Trancada / Suspensa'),
    )
    aluno = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matriculas')
    curso = models.ForeignKey(CursoTrilha, on_delete=models.CASCADE, related_name='matriculas')
    status = models.CharField(max_length=20, choices=STATUS_MATRICULA, default='ativa')
    progresso_percentual = models.FloatField(default=0.0)
    nota_avaliacao_pratica = models.FloatField(null=True, blank=True)
    observacoes_orientador = models.TextField(blank=True)
    data_matricula = models.DateTimeField(auto_now_add=True)
    ultimo_acesso = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('aluno', 'curso')
        ordering = ['-data_matricula']

    def __str__(self):
        return f"{self.aluno.username} -> {self.curso.titulo} ({self.progresso_percentual}%)"


class SubmissaoProjetoAluno(models.Model):
    STATUS_AVALIACAO = (
        ('pendente', 'Aguardando Revisao de Codigo'),
        ('aprovado', 'Aprovado / Validado'),
        ('revisao', 'Requer Ajustes Metodologicos'),
    )
    matricula = models.ForeignKey(MatriculaAluno, on_delete=models.CASCADE, related_name='submissoes')
    titulo_entrega = models.CharField(max_length=180)
    repositorio_link = models.URLField(help_text="Link do repositorio GitHub/GitLab com o codigo ou analise")
    relatorio_metodologico = models.TextField(help_text="Descricao das metricas, validacao cruzada e resultados")
    status_avaliacao = models.CharField(max_length=20, choices=STATUS_AVALIACAO, default='pendente')
    feedback_professor = models.TextField(blank=True)
    nota_atribuida = models.FloatField(null=True, blank=True)
    enviado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-enviado_em']

    def __str__(self):
        return f"{self.titulo_entrega} - {self.matricula.aluno.username}"


class ConfiguracaoPlataforma(models.Model):
    nome_plataforma = models.CharField(max_length=120, default="QUANTUM.DS // Lab & Learning")
    subtitulo_hero = models.CharField(
        max_length=250,
        default="Ciencia de Dados no Estado da Arte: Modelagem Matematica, Bioinformatica, Saude e Sistemas de Alta Performance em Python e Rust."
    )
    nome_cientista_chefe = models.CharField(max_length=150, default="Dr. Cientista Chefe, Ph.D.")
    credenciais_cientista = models.CharField(
        max_length=250,
        default="Doutor em Ciencias | Pesquisador em Inteligencia Computacional, Fisiologia Quantitativa, Epidemiologia Espacial e Engenharia de Machine Learning"
    )
    email_contato = models.EmailField(default="contato@datascience.pro")
    github_oficial = models.URLField(default="https://github.com/")
    lattes_oficial = models.URLField(default="http://lattes.cnpq.br/")
    manutencao_ativa = models.BooleanField(default=False)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome_plataforma
