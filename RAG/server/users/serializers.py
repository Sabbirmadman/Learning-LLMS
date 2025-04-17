# users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name')

class RegisterSerializer(serializers.ModelSerializer):
    token = serializers.CharField(read_only=True)
    userId = serializers.IntegerField(source='id', read_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name', 'token', 'userId')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        
        # Generate token for the newly created user
        refresh = RefreshToken.for_user(user)
        validated_data['token'] = str(refresh.access_token)
        validated_data['id'] = user.id
        
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    token = serializers.CharField(read_only=True)
    userId = serializers.IntegerField(read_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        user = authenticate(email=email, password=password)
        if user and user.is_active:
            refresh = RefreshToken.for_user(user)
            return {
                'email': user.email,
                'token': str(refresh.access_token),
                'userId': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        raise serializers.ValidationError('Invalid credentials')