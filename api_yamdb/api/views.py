from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Avg

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status, viewsets, filters
from rest_framework import mixins, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import IsAppAdminOrSuperUser, IsAdminOrReadOnly
from .permissions import ReviewCommentPermission
from .validators import check_conformity_title_and_review
from .filters import TitleFilter

from .serializers import UserSerializer
from .serializers import UserConfirmationSerializer, UserAuthSerializer
from .serializers import ReviewSerializer, CommentSerializer
from .serializers import CategorySerializer, GenresSerializer
from .serializers import OnlyUserSerializer, TitleSerializer

from reviews.models import Review, Title, Category, Genre, Comment
from users.models import User


class UserConfirmationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserConfirmationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            username = request.data["username"]
            email = request.data["email"]
            user = User.objects.get(username=username)
            confirmation_code = default_token_generator.make_token(user)
            send_mail(
                "код авторизации",
                f"Ваш код для авторизации: {confirmation_code}",
                "from@bestapp.ru",
                [email],
                fail_silently=False,
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AuthenticationView(APIView):
    permission_classes = [AllowAny]

    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "acesses": str(refresh.access_token),
        }

    def post(self, request):
        serializer = UserAuthSerializer(data=request.data)

        if serializer.is_valid():
            username = request.data["username"]
            conf_code = request.data["confirmation_code"]
            if not User.objects.filter(username=username).exists():
                return Response(
                    "Такого username нет",
                    status=status.HTTP_404_NOT_FOUND
                )
            user = User.objects.get(username=username)
            if not default_token_generator.check_token(user, conf_code):
                return Response(
                    "неправильный confirmation_code",
                    status=status.HTTP_400_BAD_REQUEST
                )
            tokens = self.get_tokens_for_user(user)
            return Response(tokens, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = PageNumberPagination
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("=name",)
    lookup_field = "slug"

    def retrieve(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class GenresViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenresSerializer
    pagination_class = PageNumberPagination
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("=name",)
    lookup_field = "slug"

    def retrieve(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all()
    serializer_class = TitleSerializer
    pagination_class = PageNumberPagination
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = TitleFilter

    """def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ListTitleSerializer
        return TitleSerializer"""


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = (ReviewCommentPermission,)

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs.get("title_id"))
        new_queryset = title.reviews.all()
        return new_queryset

    def perform_create(self, serializer):
        title_id = self.kwargs.get("title_id")
        title = get_object_or_404(Title, id=title_id)
        if Review.objects.filter(
                author=self.request.user, title=title).exists():
            raise serializers.ValidationError(
                "Извините, но Вы уже создали один отзыв к данному произведению"
            )
        serializer.save(author=self.request.user, title=title)
        rating_dict = Review.objects.filter(
            title=title).aggregate(Avg("score"))
        new_rating = rating_dict["score__avg"]
        Title.objects.filter(id=title_id).update(rating=new_rating)

    def perform_update(self, serializer):
        title_id = self.kwargs.get("title_id")
        title = get_object_or_404(Title, id=title_id)
        serializer.save(author=self.request.user, title=title)
        rating_dict = Review.objects.filter(
            title=title).aggregate(Avg("score"))
        new_rating = rating_dict["score__avg"]

        Title.objects.filter(id=title_id).update(rating=new_rating)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = (ReviewCommentPermission,)

    def get_queryset(self):
        check_conformity_title_and_review(self)
        review = get_object_or_404(Review, id=self.kwargs.get("review_id"))
        new_queryset = review.comments.all()
        return new_queryset

    def perform_create(self, serializer):
        check_conformity_title_and_review(self)
        review_id = self.kwargs.get("review_id")
        review = get_object_or_404(Review, id=review_id)
        serializer.save(author=self.request.user, review_id=review)


class UsersViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    lookup_field = "username"
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination
    permission_classes = [IsAppAdminOrSuperUser]

    @action(
        methods=["get"],
        detail=False,
        url_path="me",
        permission_classes=[IsAuthenticated],
    )
    def get_me(self, request):
        username = request.user.username
        user = get_object_or_404(User, username=username)
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["patch"],
        detail=False,
        url_path="me",
        permission_classes=[IsAuthenticated],
    )
    def patch(self, request):
        username = request.user.username
        user = get_object_or_404(User, username=username)
        if request.user.role == "admin":
            serializer = UserSerializer(
                user, data=request.data, partial=True
            )
        else:
            serializer = OnlyUserSerializer(
                user, data=request.data, partial=True
            )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
