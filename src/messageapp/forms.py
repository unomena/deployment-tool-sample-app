"""
Forms for the messages app.
"""

from django import forms
from .models import Message


class MessageForm(forms.ModelForm):
    """Form for creating new messages."""

    class Meta:
        model = Message
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Type your message here...",
                    "required": True,
                }
            )
        }
        labels = {"content": "Your Message"}
