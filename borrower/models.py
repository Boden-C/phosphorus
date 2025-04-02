from django.db import models
from django.core.exceptions import ValidationError

class Borrower(models.Model):
    card_id = models.CharField(max_length=8, unique=True, primary_key=True, blank=True)
    ssn = models.CharField(max_length=11, unique=True)
    bname = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        db_table = 'borrower'

    def save(self, *args, **kwargs):
        if not self.card_id:
            self.card_id = self.generate_card_id()
        super().save(*args, **kwargs)

    def clean(self):
        if Borrower.objects.filter(ssn=self.ssn).exists():
            raise ValidationError("Borrower with this SSN already exists.")

    def generate_card_id(self):
        latest = Borrower.objects.order_by('-card_id').first()
        if latest and latest.card_id.isdigit():
            next_id = int(latest.card_id) + 1
        else:
            next_id = 10000000
        return str(next_id).zfill(8)
