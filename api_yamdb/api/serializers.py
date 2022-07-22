from rest_framework import serializers

from users.models import User
from reviews.models import Review, Category, Genre, Title, Comment


class UserConfirmationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)

    def validate(self, data):
        if data["username"] == "me":
            raise serializers.ValidationError("В username нельзя указывать me")
        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError("Такой email уже есть")
        return data

    class Meta:
        model = User
        fields = ("username", "email")


class UserAuthSerializer(serializers.Serializer):
    username = serializers.CharField()
    confirmation_code = serializers.CharField()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("name", "slug")
        model = Category


class GenresSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("name", "slug")
        model = Genre


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field="username"
    )

    class Meta:
        fields = ("id", "text", "author", "score", "pub_date")
        model = Review

    def validate_score(self, value):
        if not (0 < value <= 10):
            raise serializers.ValidationError(
                "Проверьте свою оценку. Оценка - это целое число от 1 до 10!"
            )
        return value


class CategoryField(serializers.SlugRelatedField):
    def to_representation(self, value):
        serializer = CategorySerializer(value)
        return serializer.data


class GenreField(serializers.SlugRelatedField):
    def to_representation(self, value):
        serializer = GenresSerializer(value)
        return serializer.data


class TitleSerializer(serializers.ModelSerializer):
    """category = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Category.objects.all()
    )
    genre = serializers.SlugRelatedField(
        many=True,
        slug_field="slug",
        queryset=Genre.objects.all()
    )"""

    category = CategoryField(
        slug_field="slug",
        queryset=Category.objects.all(),
        required=False
    )
    genre = GenreField(
        slug_field="slug",
        queryset=Genre.objects.all(),
        required=False,
        many=True
    )

    class Meta:
        fields = (
            "id", "name", "year", "category",
            "genre", "description", "rating"
        )
        model = Title


class ListTitleSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField()
    genre = GenresSerializer(many=True)
    category = CategorySerializer()

    class Meta:
        model = Title
        fields = "__all__"


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field="username"
    )

    class Meta:
        fields = ("id", "text", "author", "pub_date")
        model = Comment


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "username", "email", "first_name",
            "last_name", "bio", "role"
        )


class OnlyUserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ("username", "email",
                  "first_name", "last_name", "bio", "role"
                  )
