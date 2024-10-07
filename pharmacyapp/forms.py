from django import forms
from .models import Board, Score
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class BoardForm(forms.ModelForm):
    class Meta:
        model = Board
        fields = ['title', 'content']

class ScoreForm(forms.ModelForm):
    class Meta:
        model = Score
        fields = ['q1_score', 'q2_score', 'q3_score', 'q4_score', 'q5_score']
        labels = {
            'q1_score': '1. 의약품 가격 책정은 잘되었나요?',
            'q2_score': '2. 의약품, 영양제 구비가 잘 되어 있나요?',
            'q3_score': '3. 약사의 설명과 행동이 친절한가요?',
            'q4_score': '4. 시설이 깨끗한가요?',
            'q5_score': '5. 접근성이 좋았나요? (교통 편의성, 거주지와의 거리 등)',
        }
        widgets = {
            'q1_score': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'q2_score': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'q3_score': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'q4_score': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'q5_score': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
        }

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
