from django.contrib import admin
from .models import SentimentResult


@admin.register(SentimentResult)
class SentimentResultAdmin(admin.ModelAdmin):
    list_display = ('classification', 'polarity', 'subjectivity', 'short_text', 'created_at')
    list_filter = ('classification', 'created_at')
    search_fields = ('text',)
    readonly_fields = ('created_at',)

    def short_text(self, obj):
        return obj.text[:80] + ('...' if len(obj.text) > 80 else '')
    short_text.short_description = 'Text'
