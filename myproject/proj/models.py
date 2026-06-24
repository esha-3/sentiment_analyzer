from django.db import models


class SentimentResult(models.Model):
    """Stores the result of a sentiment analysis."""

    CLASSIFICATION_CHOICES = [
        ('very_positive', 'Very Positive'),
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
        ('very_negative', 'Very Negative'),
    ]

    text = models.TextField(help_text="The input text that was analysed.")
    polarity = models.FloatField(
        help_text="Polarity score from -1.0 (most negative) to +1.0 (most positive)."
    )
    subjectivity = models.FloatField(
        help_text="Subjectivity score from 0.0 (objective) to 1.0 (subjective)."
    )
    classification = models.CharField(
        max_length=20,
        choices=CLASSIFICATION_CHOICES,
        help_text="Human-readable sentiment classification.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.classification} ({self.polarity:+.2f}) — {self.text[:50]}"
