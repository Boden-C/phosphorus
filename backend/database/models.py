from django.db import models


class Authors(models.Model):
    author_id = models.AutoField(db_column="Author_id", primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column="Name", max_length=100)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "authors"


class Book(models.Model):
    isbn = models.CharField(db_column="Isbn", primary_key=True, max_length=13)  # Field name made lowercase.
    isbn10 = models.CharField(
        db_column="Isbn10", unique=True, max_length=10, blank=True, null=True
    )  # Field name made lowercase.
    title = models.CharField(db_column="Title", max_length=255)  # Field name made lowercase.
    cover = models.CharField(db_column="Cover", max_length=255, blank=True, null=True)  # Field name made lowercase.
    publisher = models.CharField(
        db_column="Publisher", max_length=255, blank=True, null=True
    )  # Field name made lowercase.
    pages = models.IntegerField(db_column="Pages", blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "book"


class BookAuthors(models.Model):
    author = models.OneToOneField(
        Authors, models.CASCADE, db_column="Author_id", primary_key=True
    )  # Field name made lowercase. The composite primary key (Author_id, Isbn) found, that is not supported. The first column is selected.
    isbn = models.ForeignKey(Book, models.CASCADE, db_column="Isbn")  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "book_authors"
        unique_together = (("author", "isbn"),)


class BookLoans(models.Model):
    loan_id = models.AutoField(db_column="Loan_id", primary_key=True)  # Field name made lowercase.
    isbn = models.ForeignKey(Book, models.CASCADE, db_column="Isbn")  # Field name made lowercase.
    card = models.ForeignKey("Borrower", models.CASCADE, db_column="Card_id")  # Field name made lowercase.
    date_out = models.DateField(db_column="Date_out")  # Field name made lowercase.
    due_date = models.DateField(db_column="Due_date")  # Field name made lowercase.
    date_in = models.DateField(db_column="Date_in", blank=True, null=True)  # Field name made lowercase.

    def calculate_fine(self):
        """
        Calculate fine amount based on loan status
        Returns Decimal(0) if not late
        """
        from decimal import Decimal
        if self.date_in:  # Book returned scenario
            days_late = (self.date_in - self.due_date).days
        else:  # Book not returned scenario
            from datetime import date
            days_late = (date.today() - self.due_date).days
        
        if days_late > 0:
            return Decimal(days_late) * Decimal('0.25')
        return Decimal('0.00')

    class Meta:
        managed = False
        db_table = "book_loans"


class Borrower(models.Model):
    card_id = models.CharField(db_column="Card_id", primary_key=True, max_length=10)  # Field name made lowercase.
    ssn = models.CharField(db_column="Ssn", unique=True, max_length=20)  # Field name made lowercase.
    bname = models.CharField(db_column="Bname", max_length=100)  # Field name made lowercase.
    email = models.CharField(
        db_column="Email", unique=True, max_length=100, blank=True, null=True
    )  # Field name made lowercase.
    address = models.CharField(db_column="Address", max_length=255, blank=True, null=True)  # Field name made lowercase.
    city = models.CharField(db_column="City", max_length=100, blank=True, null=True)  # Field name made lowercase.
    state = models.CharField(db_column="State", max_length=2, blank=True, null=True)  # Field name made lowercase.
    phone = models.CharField(db_column="Phone", max_length=20, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "borrower"


class Fines(models.Model):
    loan = models.OneToOneField(
        BookLoans, models.CASCADE, db_column="Loan_id", primary_key=True
    )  # Field name made lowercase.
    fine_amt = models.DecimalField(db_column="Fine_amt", max_digits=10, decimal_places=2)  # Field name made lowercase.
    paid = models.IntegerField(db_column="Paid", blank=True, null=True)  # Field name made lowercase.

    @classmethod
    def update_all_fines(cls):
        """
        Update all fines in the system
        Should be run daily via cron job
        """
        from django.db.models import Q
        from datetime import date
        
        # Get all relevant loans (late and not paid)
        loans = BookLoans.objects.filter(
            Q(date_in__gt=models.F('due_date')) |  # Returned late
            Q(date_in__isnull=True, due_date__lt=date.today())  # Not returned and overdue
        ).exclude(
            fines__paid=True  # Skip paid fines
        )
        
        for loan in loans:
            new_amount = loan.calculate_fine()
            fine, created = cls.objects.get_or_create(
                loan=loan,
                defaults={'fine_amt': new_amount, 'paid': 0}
            )
            
            if not created and not fine.paid and fine.fine_amt != new_amount:
                fine.fine_amt = new_amount
                fine.save()

    class Meta:
        managed = False
        db_table = "fines"
