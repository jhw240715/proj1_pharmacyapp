from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, UpdateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth import login, authenticate
from django.core.paginator import Paginator
from .models import Pharmacy, Score, Board
from .forms import BoardForm, ScoreForm, CustomUserCreationForm
from django.db import transaction
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.contrib.auth import login

# ----------------------
# 약국 관련
# ----------------------

# 약국 리스트
def pharmacy_list(request):
    pharmacies = Pharmacy.objects.all()
    return render(request, 'pharmacy_list.html', {'pharmacies': pharmacies})

# 약국 디테일, 게시글, 스코어
@login_required
def pharmacy_detail(request, pharmacy_id):
    pharmacy = get_object_or_404(Pharmacy, pk=pharmacy_id)
    boards = Board.objects.filter(pname=pharmacy).select_related('user')
    scores = Score.objects.filter(p=pharmacy).select_related('user')
    return render(request, 'pharmacy_detail.html', {
        'pharmacy': pharmacy,
        'boards': boards,
        'scores': scores
    })


# 유저 5km 반경 약국 찾기
@login_required
def nearby_pharmacies(request):
    user_lat = request.GET.get('latitude')
    user_lon = request.GET.get('longitude')
    if not user_lat or not user_lon:
        return render(request, 'error.html', {'message': '위치 정보를 제공해주세요.'})

    try:
        user_lat = float(user_lat)
        user_lon = float(user_lon)
    except ValueError:
        return render(request, 'error.html', {'message': '올바른 위치 정보를 입력해주세요.'})


    user_location = (user_lat, user_lon)

    pharmacies = Pharmacy.objects.all()
    nearby = []

    for pharmacy in pharmacies:
        pharmacy_location = (pharmacy.latitude, pharmacy.longitude)
        distance = geodesic(user_location, pharmacy_location).km
        if distance <= 5:
            nearby.append(pharmacy)

    return render(request, 'nearby_pharmacies.html', {'pharmacies': nearby})

# ----------------------
# 약국 보드(리뷰)/스코어 관련
# ----------------------

# 약국 보드/스코어 생성
@login_required
@transaction.atomic
def create_board_and_score(request, pharmacy_id):
    pharmacy = get_object_or_404(Pharmacy, pk=pharmacy_id)
    if request.method == 'POST':
        board_form = BoardForm(request.POST)
        score_form = ScoreForm(request.POST)
        if board_form.is_valid() and score_form.is_valid():
            board = board_form.save(commit=False)
            board.user = request.user
            board.pname = pharmacy
            board.save()

            score = score_form.save(commit=False)
            score.p = pharmacy
            score.save()

            return redirect('board_list')
    else:
        board_form = BoardForm()
        score_form = ScoreForm()

    return render(request, 'create_board_and_score.html', {
        'board_form': board_form,
        'score_form': score_form,
        'pharmacy': pharmacy
    })

# 모든 보드/스코어 리스트
def board_list_view(request):
    boards = Board.objects.all()
    paginator = Paginator(boards, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'board_list.html', {'boards': page_obj})

# 개별 보드/스코어 조회
def board_detail_view(request, pk):
    board = get_object_or_404(Board, pk=pk)
    score = Score.objects.filter(p=board.pname, user=board.user).first()
    context = {
        'board': board,
        'score': score
    }
    return render(request, 'board_detail.html', context)

# 보드/스코어 수정하기
class BoardUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Board
    fields = ['title', 'content']
    template_name = 'board_update.html'
    success_url = reverse_lazy('board_list')
    permission_required = 'pharmacyapp.change_board'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

# 보드/스코어 삭제하기
@login_required
def delete_board_and_score(request, board_id):
    board = get_object_or_404(Board, id=board_id)
    if request.user == board.user:
        if request.method == 'POST':
            pharmacy_id = board.pname.p_id
            # Delete the associated score if it exists
            Score.objects.filter(p=board.pname, user=board.user).delete()
            # Delete the board
            board.delete()
            return redirect('pharmacy_detail', pk=pharmacy_id)
        return render(request, 'board_delete_confirm.html', {'board': board})
    else:
        return redirect('board_list')

# ----------------------
# 유저 관련
# ----------------------

# 이메일 로그인
class CustomLoginView(LoginView):
    def form_valid(self, form):
        template_name = 'login.html'
        backend = 'myproject.backend.EmailAuthBackend'  # 사용할 백엔드 지정
        user = form.get_user()
        login(self.request, user, backend=backend)  # 로그인 호출 시 백엔드 지정
        return super().form_valid(form)


# 회원가입
def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})

# 로그아웃 시 홈으로
def custom_logout(request):
    logout(request)
    return redirect('home')

# 로그인 후 대시보드
@login_required
def dashboard(request):
    return render(request, 'dashboard.html', {'user': request.user})

# ----------------------
# 기타
# ----------------------

# 홈 가기
def home(request):
    return render(request, 'home.html')
