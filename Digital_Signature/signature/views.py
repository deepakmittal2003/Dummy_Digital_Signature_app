# signature/views.py

from django.shortcuts import render, redirect, get_object_or_404 # type: ignore
from django.http import FileResponse,HttpResponseBadRequest,HttpResponse # type: ignore
from django.urls import reverse # type: ignore
from django.core.files.base import ContentFile # type: ignore
from django.utils import timezone # type: ignore
from .models import BorrowerSignature, LoanAgreement
from .forms import LoanAgreementForm
#SignatureForm
from .forms import NumberOfBorrowersForm, BorrowerDetailFormSet,BorrowerDetailForm
from PyPDF2 import PdfReader, PdfWriter # type: ignore
from reportlab.lib.pagesizes import letter # type: ignore
from reportlab.pdfgen import canvas # type: ignore
from reportlab.lib.utils import ImageReader # type: ignore
from django.forms import formset_factory # type: ignore
import io
import base64
from PIL import Image
import datetime
from django.conf import settings # type: ignore
import logging

# Set up logging
logger = logging.getLogger(__name__)

def number_of_borrowers_view(request):
    if request.method == 'POST':
        form = NumberOfBorrowersForm(request.POST)
        if form.is_valid():
            num_borrowers = form.cleaned_data['num_borrowers']
            return redirect('borrower_details', num_borrowers=num_borrowers)
    else:
        form = NumberOfBorrowersForm()
    return render(request, 'number_of_borrowers.html', {'form': form})


def borrower_details_view(request, num_borrowers):
    BorrowerDetailFormSet = formset_factory(BorrowerDetailForm, extra=num_borrowers)
    
    if request.method == 'POST':
        formset = BorrowerDetailFormSet(request.POST)
        if formset.is_valid():
            agreement = LoanAgreement.objects.create()  # Create a new LoanAgreement instance
            for form in formset:
                loan_id = form.cleaned_data['loan_id']
                name = form.cleaned_data['name']
                mobile_number = form.cleaned_data['mobile_number']
                BorrowerSignature.objects.create(
                    agreement=agreement,
                    loan_id=loan_id,
                    name=name,
                    mobile_number=mobile_number
                )
            return redirect('upload_agreement', agreement_id=agreement.id)  # Redirect to upload_agreement with agreement_id
    else:
        formset = BorrowerDetailFormSet()
    return render(request, 'borrower_details.html', {'formset': formset, 'num_borrowers': num_borrowers})

def upload_agreement(request, agreement_id):
    agreement = get_object_or_404(LoanAgreement, pk=agreement_id)
    if request.method == 'POST':
        form = LoanAgreementForm(request.POST, request.FILES, instance=agreement)
        if form.is_valid():
            form.save()
            return redirect('generate_links', agreement_id=agreement.id)  # Redirect to generate_links with agreement_id
    else:
        form = LoanAgreementForm(instance=agreement)
    return render(request, 'upload_agreement.html', {'form': form, 'agreement': agreement})

def generate_links(request, agreement_id):
    agreement = get_object_or_404(LoanAgreement, pk=agreement_id)
    borrowers = BorrowerSignature.objects.filter(agreement=agreement)
    
    # Assuming you want to generate unique links based on some criteria (e.g., Django's reverse mechanism)
    borrower_links = {}
    for borrower in borrowers:
        borrower_links[borrower.name] = request.build_absolute_uri(reverse('view_original_document', args=[agreement_id, borrower.id]))
    
    return render(request, 'generate_links.html', {'agreement': agreement, 'borrower_links': borrower_links})


def view_original_document(request, agreement_id,borrower_id):
    agreement = get_object_or_404(LoanAgreement, pk=agreement_id)
    borrower = get_object_or_404(BorrowerSignature, pk=borrower_id, agreement=agreement)
    if request.method == 'POST':
        # Check if the user has acknowledged the document
        if request.POST.get('acknowledge_checkbox'):
            return redirect('sign_agreement', agreement_id=agreement_id,borrower_id = borrower_id)
        else:
            return HttpResponseBadRequest("Please acknowledge the document.") # type: ignore
        
    context = {
        'document_url': agreement.document.url,
        'borrower': borrower,
    }
    return render(request, 'original_document.html', context)



def sign_agreement(request, agreement_id, borrower_id):
    agreement = get_object_or_404(LoanAgreement, pk=agreement_id)
    borrower = get_object_or_404(BorrowerSignature, pk=borrower_id, agreement=agreement)
    existing_signature = BorrowerSignature.objects.filter(agreement=agreement,borrower_name = borrower).exists()
    if existing_signature:
        return render(request, 'already_signed.html', {'agreement': agreement})
    if request.method == 'POST':
        #form = SignatureForm(request.POST)
        #if form.is_valid():
            #lender = form.cleaned_data['lender']
            signature_data_url = request.POST.get('signature')
            if signature_data_url:
                signatures = BorrowerSignature.objects.filter(agreement=agreement).count()
                signatures_per_row = 5  # Change this value to adjust the number of signatures per row
                horizontal_spacing = 120  # Spacing between signatures horizontally
                vertical_spacing = 120  # Spacing between signatures vertically
                x_offset = 25  # Initial x offset
                y_offset = 25  # Initial y offset

                # Calculate position for the new signature
                x_position = x_offset + (signatures % signatures_per_row) * horizontal_spacing  # Adjust horizontal spacing
                y_position = y_offset + (signatures // signatures_per_row) * vertical_spacing  # Adjust vertical spacing

                signature_instance = BorrowerSignature(
                    agreement=agreement,
                    borrower_name=borrower,
                    x_position=x_position,
                    y_position=y_position
                )
                signature_instance.save()
                ip_address = request.META.get('REMOTE_ADDR')
                timestamp = timezone.now()

                add_signature(agreement.document.path, signature_data_url, borrower.loan_id, signature_instance,x_position,y_position,ip_address,timestamp)
                
                return redirect('sign_agreement_success', agreement_id=agreement_id,borrower_id = borrower_id)
    else:
        #form = SignatureForm()
        context = {
        #'form': form,
        'agreement': agreement,
        'borrower': borrower,
        }
    return render(request, 'signature/sign_agreement.html', {'borrower': borrower})

def add_signature(pdf_path, signature_data_url, loan_id, signature_instance,x_position,y_position,ip_address, timestamp):
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    # Decode the base64 image data for the signature
    signature_data = base64.b64decode(signature_data_url.split(',')[1])
    signature_image = Image.open(io.BytesIO(signature_data))
    
    current_date = timezone.now().date().strftime('%Y-%m-%d')
    current_time = timezone.now().time().strftime('%H:%M:%S')

    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        
        width, height = letter
        signature_image = signature_image.resize((80, 90))
        can.drawImage(ImageReader(signature_image), x_position,y_position + 10, width=80, height=90)
        #can.drawString(signature_instance.x_position, signature_instance.y_position + 110, f"Loan ID: {loan_id}")
        text_y_position = y_position + 20  # Adjust this value to position below
        can.drawString(x_position, text_y_position-10, f"{loan_id}")
        can.drawString(x_position, text_y_position - 20 , f"{ip_address}")
        
        # Add timestamp (date)
        can.drawString(x_position, text_y_position-30, f"{current_date}")

        # Add timestamp (time)
        can.drawString(x_position, text_y_position-40, f"{current_time}")

        can.save()

        packet.seek(0)
        overlay_pdf = PdfReader(packet)
        overlay_page = overlay_pdf.pages[0]

        # Merge the overlay page with the original page
        page.merge_page(overlay_page)
        writer.add_page(page)

    with open(pdf_path, 'wb') as output_pdf:
        writer.write(output_pdf)
        
def sign_agreement_success(request, agreement_id,borrower_id):
    agreement = get_object_or_404(LoanAgreement, pk=agreement_id)
    borrower = get_object_or_404(BorrowerSignature, pk=borrower_id,agreement=agreement)
    return render(request, 'sign_agreement_success.html', {'agreement': agreement,'borrower': borrower})

def view_signed_agreement(request, agreement_id,borrower_id):
    agreement = get_object_or_404(LoanAgreement, pk=agreement_id)
    return FileResponse(agreement.document.open(), content_type='application/pdf')