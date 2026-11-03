from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import (
    User, ArtigoCientificoBlog, RepositorioCodigo,
    CursoTrilha, MatriculaAluno, SubmissaoProjetoAluno, ConfiguracaoPlataforma
)

TAILWIND_INPUT = "w-full bg-slate-950 border border-slate-800 text-slate-100 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:border-cyan-500 transition"

class CadastroProfissionalForm(UserCreationForm):
    first_name = forms.CharField(max_length=80, required=True, label="Nome")
    last_name = forms.CharField(max_length=80, required=True, label="Sobrenome")
    email = forms.EmailField(required=True, label="E-mail Profissional ou Academico")
    instituicao = forms.CharField(max_length=150, required=True, label="Instituicao / Empresa")
    cargo_atuacao = forms.CharField(max_length=120, required=True, label="Area de Atuacao / Cargo")
    papel = forms.ChoiceField(
        choices=[('aluno', 'Aluno (Cursos e Trilhas)'), ('pesquisador', 'Pesquisador / Leitor Tecnico')],
        label="Perfil de Acesso Desejado"
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'instituicao', 'cargo_atuacao', 'papel', 'orcid_id', 'github_url')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = TAILWIND_INPUT


class ArtigoCientificoForm(forms.ModelForm):
    class Meta:
        model = ArtigoCientificoBlog
        fields = ['titulo', 'categoria', 'resumo', 'conteudo_markdown', 'referencias_bibliograficas', 'status', 'nivel_acesso', 'destaque_home']
        widgets = {
            'resumo': forms.Textarea(attrs={'rows': 3}),
            'conteudo_markdown': forms.Textarea(attrs={'rows': 12}),
            'referencias_bibliograficas': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = TAILWIND_INPUT


class RepositorioCodigoForm(forms.ModelForm):
    class Meta:
        model = RepositorioCodigo
        fields = ['titulo', 'linguagem', 'categoria', 'descricao_tecnica', 'codigo_fonte', 'dependencias', 'complexidade_tempo', 'benchmark_nota', 'url_repositorio_externo', 'publico']
        widgets = {
            'descricao_tecnica': forms.Textarea(attrs={'rows': 3}),
            'codigo_fonte': forms.Textarea(attrs={'rows': 12, 'class': 'font-mono'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = TAILWIND_INPUT


class MatriculaGestaoForm(forms.ModelForm):
    class Meta:
        model = MatriculaAluno
        fields = ['aluno', 'curso', 'status', 'progresso_percentual', 'nota_avaliacao_pratica', 'observacoes_orientador']
        widgets = {
            'observacoes_orientador': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = TAILWIND_INPUT


class SubmissaoAlunoForm(forms.ModelForm):
    class Meta:
        model = SubmissaoProjetoAluno
        fields = ['matricula', 'titulo_entrega', 'repositorio_link', 'relatorio_metodologico']
        widgets = {
            'relatorio_metodologico': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['matricula'].queryset = MatriculaAluno.objects.filter(aluno=user)
        for field in self.fields.values():
            field.widget.attrs['class'] = TAILWIND_INPUT

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class CadastroSimplesForm(forms.ModelForm):
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-slate-100 focus:outline-none focus:border-cyan-500',
            'placeholder': '••••••••'
        })
    )
    confirm_password = forms.CharField(
        label="Confirmação de senha",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-slate-100 focus:outline-none focus:border-cyan-500',
            'placeholder': '••••••••'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-slate-100 focus:outline-none focus:border-cyan-500',
                'placeholder': 'ex: lucenildo'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-slate-100 focus:outline-none focus:border-cyan-500',
                'placeholder': 'seuemail@exemplo.com'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este e-mail já está em uso.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get('password')
        confirma = cleaned_data.get('confirm_password')

        if senha and confirma and senha != confirma:
            self.add_error('confirm_password', 'As senhas informadas não coincidem.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user