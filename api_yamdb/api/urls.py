from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import ReviewViewSet, CategoryViewSet
from .views import GenresViewSet, UsersViewSet
from .views import CommentViewSet, TitleViewSet
from .views import UserConfirmationView, AuthenticationView


router = SimpleRouter()
router.register('categories', CategoryViewSet)
router.register('genres', GenresViewSet)
router.register('titles', TitleViewSet)
router.register(
    'titles/(?P<title_id>\\d+)/reviews',
    ReviewViewSet,
    basename="reviews",
)
router.register(
    'titles/(?P<title_id>\\d+)/reviews/(?P<review_id>\\d+)/comments',
    CommentViewSet,
    basename="comments",
)
router.register('users', UsersViewSet, basename='users')


urlpatterns = [
    path('v1/', include(router.urls)),
    path(
        'v1/auth/signup/',
        UserConfirmationView.as_view()
    ),
    path(
        'v1/auth/token/', AuthenticationView.as_view()
    ),
]
