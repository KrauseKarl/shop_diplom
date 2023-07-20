from django.core.management import BaseCommand, CommandError
from django.shortcuts import redirect

from app_order.models import Invoice
from app_order.services.order_services import Payment
from app_order.views import SuccessPaid, redirect_func


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def add_arguments(self, parser):
        parser.add_argument("invoice_id", nargs="+", type=int)

    def handle(self, *args, **options):
        for invoice_id in options["invoice_id"]:
            try:
                current_invoice = Payment.get_invoice(invoice_id)
            except Invoice.DoesNotExist:
                raise CommandError('Invoice "%s" does not exist' % invoice_id)
            Payment.add_order_to_job(current_invoice.id)
            redirect_func()
            print("redirect_func is active")

            # self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % invoice_id))
