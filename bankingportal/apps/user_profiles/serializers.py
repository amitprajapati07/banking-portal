"""Serializers for user registration, authentication, and profile management."""

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.user_profiles.models import UserProfile


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class RegisterSerializer(serializers.ModelSerializer):
    """Validates and creates a new User (UserProfile is created via signal)."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        validators=[validate_password],
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
        )
        extra_kwargs = {
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value.lower()

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data: dict) -> User:
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            password=validated_data["password"],
        )
        return user


# ---------------------------------------------------------------------------
# User Profile read / update
# ---------------------------------------------------------------------------


class UserProfileSerializer(serializers.ModelSerializer):
    """Read-only serializer for UserProfile (nested in UserDetailSerializer)."""

    can_transact = serializers.BooleanField(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = UserProfile
        fields = (
            "id",
            "phone_number",
            "date_of_birth",
            "address",
            "is_verified",
            "kyc_status",
            "last_login_ip",
            "can_transact",
            "full_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "is_verified",
            "kyc_status",
            "last_login_ip",
            "can_transact",
            "full_name",
            "created_at",
            "updated_at",
        )


class UserDetailSerializer(serializers.ModelSerializer):
    """Full user detail including nested profile."""

    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "date_joined",
            "profile",
        )
        read_only_fields = ("id", "username", "is_active", "date_joined")


class UpdateUserProfileSerializer(serializers.ModelSerializer):
    """
    Allows authenticated users to update their own mutable profile fields.

    The ``User`` model fields (first_name, last_name, email) are exposed here
    as writable so the client needs only one PATCH call.
    """

    first_name = serializers.CharField(
        source="user.first_name", required=False
    )
    last_name = serializers.CharField(
        source="user.last_name", required=False
    )
    email = serializers.EmailField(source="user.email", required=False)

    class Meta:
        model = UserProfile
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "date_of_birth",
            "address",
        )

    def validate_email(self, value: str) -> str:
        user = self.instance.user
        if (
            User.objects.filter(email__iexact=value)
            .exclude(pk=user.pk)
            .exists()
        ):
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value.lower()

    def update(self, instance: UserProfile, validated_data: dict) -> UserProfile:
        user_data: dict = validated_data.pop("user", {})

        # Update User fields.
        user: User = instance.user
        for attr, val in user_data.items():
            setattr(user, attr, val)
        user.save()

        # Update profile fields.
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        return instance


# ---------------------------------------------------------------------------
# Change password
# ---------------------------------------------------------------------------


class ChangePasswordSerializer(serializers.Serializer):
    """Validates a password-change request."""

    old_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    new_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        validators=[validate_password],
    )
    new_password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    def validate_old_password(self, value: str) -> str:
        user: User = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )
        return attrs
