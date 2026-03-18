"""
Account serializers — registration, login response, profile read/update.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Validates and creates a new inactive user."""

    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm password')

    class Meta:
        model = User
        fields = (
            'email', 'user_name', 'first_name', 'last_name', 'password', 'password2'
        )

    def validate_user_name(self, value):
        if User.objects.filter(user_name__iexact=value).exists():
            raise serializers.ValidationError('This username is already taken.')
        return value.lower()

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value.lower()

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = False   # activation required
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Read-only full user representation."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'user_name', 'first_name', 'last_name', 'full_name',
            'about', 'country', 'phone_number', 'postcode',
            'address_line_1', 'address_line_2', 'town_city',
            'is_active', 'is_staff', 'created', 'updated',
        )
        read_only_fields = ('id', 'email', 'is_active', 'is_staff', 'created', 'updated')

    def get_full_name(self, obj):
        return obj.get_full_name()


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Allows updating profile fields.
    Email and username are read-only after registration.
    """

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'about',
            'country', 'phone_number', 'postcode',
            'address_line_1', 'address_line_2', 'town_city',
        )


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True, write_only=True, validators=[validate_password]
    )
    new_password2 = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password': 'Passwords do not match.'})
        return attrs
