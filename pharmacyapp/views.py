from django.shortcuts import render, redirect, get_object_or_404
import requests
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
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count, Avg
from .models import Board, Score

# ----------------------
# 약국 관련
# ----------------------

# 약국 리스트
def pharmacy_list(request):
    pharmacies = Pharmacy.objects.all()
    return render(request, 'pharmacy_list.html', {'pharmacies': pharmacies})

# 약국 디테일, 게시글, 스코어
@login_required
def pharmacy_detail(request, p_id):
    pharmacy = get_object_or_404(Pharmacy, p_id=p_id)
    boards = Board.objects.filter(pname=pharmacy).select_related('user')
    scores = Score.objects.filter(p=pharmacy).select_related('user')
    return render(request, 'pharmacy_detail.html', {
        'pharmacy': pharmacy,
        'boards': boards,
        'scores': scores
    })


# 유저 0.5km 반경 약국 찾기
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.conf import settings
from .models import Pharmacy
from geopy.distance import geodesic
import requests

GOOGLE_MAPS_API_KEY = settings.GOOGLE_MAPS_API_KEY

@login_required
def nearby_pharmacies(request):
    if request.method == 'POST':
        address = request.POST.get('address')
        if not address:
            return render(request, 'nearby_pharmacies.html', {'error': '주소를 입력해주세요.'})


        geocode_url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_MAPS_API_KEY}'

        try:
            response = requests.get(geocode_url).json()

            if response['status'] != 'OK':
                return render(request, 'nearby_pharmacies.html', {'error': '주소를 찾을 수 없습니다.'})

            user_lat = response['results'][0]['geometry']['location']['lat']
            user_lon = response['results'][0]['geometry']['location']['lng']
            user_location = (user_lat, user_lon)

            pharmacies = Pharmacy.objects.all()
            nearby = []

            for pharmacy in pharmacies:
                if pharmacy.latitude and pharmacy.longitude:
                    pharmacy_location = (pharmacy.latitude, pharmacy.longitude)
                    distance = geodesic(user_location, pharmacy_location).km
                    if distance <= 5:  # Changed to 5km radius
                        nearby.append({'pharmacy': pharmacy, 'distance': round(distance, 2)})

            nearby.sort(key=lambda x: x['distance'])

            return render(request, 'nearby_pharmacies.html', {'pharmacies': nearby, 'address': address})

        except requests.RequestException:
            return render(request, 'nearby_pharmacies.html', {'error': '서버 오류가 발생했습니다. 다시 시도해주세요.'})

    return render(request, 'nearby_pharmacies.html')


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
            address = board_form.cleaned_data.get('address')
            geocode_url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_MAPS_API_KEY}'
            response = requests.get(geocode_url).json()

            if response['status'] == 'OK':
                lat = response['results'][0]['geometry']['location']['lat']
                lon = response['results'][0]['geometry']['location']['lng']
            else:
                lat, lon = None, None

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
    boards = Board.objects.all().order_by('-uptime')
    total_boards = boards.count()

    paginator = Paginator(boards, 10)  # 페이지당 10개 항목
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    print(f"Total boards: {total_boards}")  # 디버깅용
    print(f"Boards on this page: {len(page_obj)}")  # 디버깅용
    print(f"First board: {page_obj[0] if page_obj else 'No boards'}")  # 디버깅용

    context = {
        'boards': page_obj,
        'total_boards': total_boards,
    }
    return render(request, 'board_list.html', context)

# 개별 보드/스코어 조회
def board_detail_view(request, pk):
    board = get_object_or_404(Board, board_id=board_id)
    score = Score.objects.filter(p=board.pname, user=board.user).first()

    geocode_url = f'https://maps.googleapis.com/maps/api/geocode/json?address={board.address}&key={GOOGLE_MAPS_API_KEY}'
    response = requests.get(geocode_url).json()

    if response['status'] == 'OK':
        lat = response['results'][0]['geometry']['location']['lat']
        lon = response['results'][0]['geometry']['location']['lng']
    else:
        lat, lon = None, None

    context = {
        'board': board,
        'score': score,
        'lat': lat,
        'lon': lon
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
    board = get_object_or_404(Board, board_id=board_id)
    if request.user == board.user:
        if request.method == 'POST':
            pharmacy_id = board.pname.p_id
            Score.objects.filter(p=board.pname, user=board.user).delete()
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

# 대시보드
@login_required
def dashboard(request):
    # 각 사용자가 작성한 게시글 수
    user_post_counts = Board.objects.values('user_id').annotate(post_count=Count('user_id')).order_by('-post_count')

    # 각 질문에 대한 평균 점수
    avg_scores = Score.objects.aggregate(
        q1_avg=Avg('q1_score'),
        q2_avg=Avg('q2_score'),
        q3_avg=Avg('q3_score'),
        q4_avg=Avg('q4_score'),
        q5_avg=Avg('q5_score')
    )

    # 각 약국들에 대한 평점 총점
    pharmacy_total_scores = Score.objects.values('p_id').annotate(
        total_score=Avg('q1_score') + Avg('q2_score') + Avg('q3_score') + Avg('q4_score') + Avg('q5_score')
    ).order_by('-total_score')

    # 전체 평점 평균
    total_avg = Score.objects.aggregate(
        total_avg=(Avg('q1_score') + Avg('q2_score') + Avg('q3_score') + Avg('q4_score') + Avg('q5_score')) / 5
    )['total_avg']

    context = {
        'user_post_counts': user_post_counts,
        'avg_scores': avg_scores,
        'pharmacy_total_scores': pharmacy_total_scores,
        'total_avg': total_avg,
    }

    return render(request, 'dashboard.html', context)




import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from io import BytesIO
from django.http import HttpResponse
from .models import Score
import matplotlib.font_manager as fm

def visualize_scores(request):
    # 한글 폰트 설정
    font_path = 'C:/Windows/Fonts/malgun.ttf'  # Windows의 경우
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()


    # 데이터 가져오기
    scores = Score.objects.all().values('p_id', 'q1_score', 'q2_score', 'q3_score', 'q4_score', 'q5_score')
    df = pd.DataFrame(scores)

    # 각 질문의 평균 계산
    mean_scores = df[['q1_score', 'q2_score', 'q3_score', 'q4_score', 'q5_score']].mean()

    # p_id별 각 질문의 총합 계산
    sum_scores_by_pharmacy = df.groupby('p_id')[['q1_score', 'q2_score', 'q3_score', 'q4_score', 'q5_score']].sum().mean(axis=1)

    # 게시글 총 개수 계산
    total_boards = Board.objects.count()

    # 시각화
    fig, axes = plt.subplots(3, 1, figsize=(10, 12))

    sns.barplot(x=mean_scores.index, y=mean_scores.values, ax=axes[0])
    axes[0].set_title('각 질문의 평균 점수')
    axes[0].set_ylabel('평균 점수')

    sns.barplot(x=sum_scores_by_pharmacy.index, y=sum_scores_by_pharmacy.values, ax=axes[1])
    axes[1].set_title('p_id별 질문 총합의 평균')
    axes[1].set_ylabel('총합 평균 점수')

    axes[2].bar(['게시글 총 개수'], [total_boards])
    axes[2].set_title('게시글 총 개수')
    axes[2].set_ylabel('개수')


    plt.tight_layout()

    # 이미지를 HttpResponse로 반환
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    return HttpResponse(buffer, content_type='image/png')

def visualize_scores_page(request):
    return render(request, 'visualize_scores.html')




# ----------------------
# 기타
# ----------------------

# 홈 가기
def home(request):
    return render(request, 'home.html')