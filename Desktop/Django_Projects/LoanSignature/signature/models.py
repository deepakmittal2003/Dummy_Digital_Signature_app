# signature/models.py

from django.db import models # type: ignore

class LoanAgreement(models.Model):
    borrower = models.CharField(max_length=100)
    document = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.borrower

class Signature(models.Model):
    agreement = models.ForeignKey(LoanAgreement, on_delete=models.CASCADE)
    lender = models.CharField(max_length=100)
    date_signed = models.DateTimeField(auto_now_add=True)
    x_position = models.IntegerField(default=100)
    y_position = models.IntegerField(default=50)

    def __str__(self):
        return f"Signature for {self.agreement}"

class Borrower(models.Model):
    loan_agreement = models.ForeignKey(LoanAgreement, on_delete=models.CASCADE, related_name='borrowers')
    loan_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15)

    def __str__(self):
        return f"Borrower: {self.name}, Loan ID: {self.loan_id}"
    
class BorrowerSignature(models.Model):
    borrower = models.ForeignKey(Borrower, on_delete=models.CASCADE)
    signature_image = models.ImageField(upload_to='signatures/')
    signed_at = models.DateTimeField(auto_now_add=True)
    signed_document = models.FileField(upload_to='signed_documents/', null=True, blank=True)
    def __str__(self):
        return f"Signature of {self.borrower.name} on {self.signed_at}"