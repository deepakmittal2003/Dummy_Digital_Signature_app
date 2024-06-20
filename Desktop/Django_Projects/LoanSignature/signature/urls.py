from django.urls import path # type: ignore
from django.conf import settings # type: ignore
from django.conf.urls.static import static # type: ignore
from . import views

urlpatterns = [
    path('number_of_borrowers/', views.number_of_borrowers_view, name='number_of_borrowers'),
    
    path('borrower_details/<int:num_borrowers>/', views.borrower_details_view, name='borrower_details'),
    path('upload_agreement/<int:agreement_id>/', views.upload_agreement, name='upload_agreement'),
    path('generate_links/<int:agreement_id>/', views.generate_links, name='generate_links'),
    #path('borrower/<int:agreement_id>/<int:borrower_id>/', views.borrower_detail, name='borrower_detail'),
    #path('upload/', views.upload_agreement, name='upload_agreement'),
    path('view_original_document/<int:agreement_id>/<int:borrower_id>/', views.view_original_document, name='view_original_document'),
    #path('view/<int:agreement_id>/', views.view_loan_agreement, name='view_loan_agreement'),
    path('sign/<int:agreement_id>/<int:borrower_id>/', views.sign_agreement, name='sign_agreement'),
    path('sign/success/<int:agreement_id>/<int:borrower_id>/', views.sign_agreement_success, name='sign_agreement_success'),
    path('view_signed_agreement/<int:agreement_id>/<int:borrower_id>/', views.view_signed_agreement, name='view_signed_agreement'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
