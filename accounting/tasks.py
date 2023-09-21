from accounting.models import Event as AccEvent
from crm.models import Customer
from elk.celery import app as celery
from elk.logging import logger
from mailer.owl import Owl
from timeline.models import Entry as TimelineEntry

from celery import shared_task


@celery.task
def bill_timeline_entries():
    for entry in TimelineEntry.objects.to_be_marked_as_finished().filter(taken_slots__gte=1):
        entry.is_finished = True
        entry.save()

        if not AccEvent.objects.by_originator(entry).count():
            ev = AccEvent(
                teacher=entry.teacher,
                originator=entry,
                event_type='class',
            )
            ev.save()
        else:
            logger.warning('Tried to bill already billed timeline entry')


@shared_task
def notify_students_not_have_lessons_more_week():
    for customer in Customer.objects.all():
        if not customer.check_have_classes_last_week():
            owl = Owl(
                template='mail/not_have_classes_more_week.html',
                ctx={
                    'c': customer,
                },
                to=[customer.user.email],
                timezone=customer.timezone,
            )
            owl.send()
