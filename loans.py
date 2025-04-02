from datetime import timedelta, date
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.db.models import Q


class Book(models.Model):
    isbn = models.CharField(max_length=13, primary_key=True)
    title = models.CharField(max_length=225)


class Borrower(models.Model):
    card_id = models.CharField(max_length=8, primary_key=True)
    bname = models.CharField(max_length=100)


class BookLoan(models.Model):
    loan_id = models.AutoField(primary_key=True)
    isbn = models.ForeignKey(Book, on_delete=models.CASCADE)
    card_id = models.ForeignKey(Borrower, on_delete=models.CASCADE)
    date_out = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    date_in = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = self.date_out + timedelta(days=14)
        super().save(*args, **kwargs)


class Fine(models.Model):
    load = models.OneToOneField(BookLoan, on_delete=models.CASCADE, primary_key=True)
    fine_amt = models.FloatField(max_digits=10, decimal_places=2, default=0.00)
    paid = models.BooleanField(default=False)


def checkout(isbn, card_id):
    with transaction.atomic():
        borrower = Borrower.objects.get(card_id=card_id)
        book = Book.objects.get(isbn=isbn)

        if BookLoan.objects.filter(card_id=borrower, date_in_isnull=True).count() >= 3:
            raise ValidationError("Borrower has reached the limit of 3 active book loans.")

        if BookLoan.objects.filter(isbn=book, date_in_isnull=True).exists():
            raise ValidationError("This book is already checked out.")

        if Fine.objects.filter(loan_card_id=borrower, paid=False).exists():
            raise ValidationError("Borrower has unpaid fines.")

        loan = BookLoan(isbn=book, card_id=borrower)
        loan.save()
        return f"Book {isbn} checked out successfully to {card_id}."


def locate_loans(search_term):
    loans = BookLoan.objects.filter(
        Q(date_in_isnull=True) & (
            Q(isbn_icontains=search_term) |
            Q(card_id_icontains=search_term) |
            Q(card_id_bname_icontains=search_term)
        )
    )
    return loans


def checkin(loan_ids):
    with transaction.atomic():
        loans = BookLoan.objects.filter(loan_id_in=loan_ids, date_in_isnull=True)
        if not loans.exists():
            raise ValidationError("No valid book loans found to check in.")

        for loan in loans:
            loan.date_in = date.today()
            loan.save()

        return f"Checked in {loans.count()} books successfully."
