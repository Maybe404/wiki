from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(
        label="账号",
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "username", "autofocus": True}),
    )
    password = forms.CharField(
        label="密码",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
