from unittest.mock import patch

from django.core import mail
from freezegun import freeze_time

from accounting.tasks import notify_students_not_have_lessons_more_week
from elk.utils.testing import ClassIntegrationTestCase


class TestStudentsNotHaveLessonsMoreWeekEmail(ClassIntegrationTestCase):
    @patch('market.signals.Owl')
    def test_single_class_pre_start_notification(self, Owl):
        entry = self._create_entry()
        c = self._buy_a_lesson()
        self._schedule(c, entry)
        c.is_fully_used = True
        c.save()

        with freeze_time('2032-09-15 16:30:00+00:00'):   # 2 days after the class
            check_have_classes_last_week = self.customer.check_have_classes_last_week()
            notify_students_not_have_lessons_more_week()

        out_emails = [outbox.to[0] for outbox in mail.outbox]
        self.assertEqual(self.customer.classes.first().is_fully_used, True)

        self.assertEqual(check_have_classes_last_week, True)
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(self.host.user.email, out_emails)
        self.assertNotIn(self.customer.user.email, out_emails)
