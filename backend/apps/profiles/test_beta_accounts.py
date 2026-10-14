from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.profiles.management.commands.seed_beta_accounts import ACCOUNTS, Command


class BetaAccountsTests(TestCase):
    def test_confirmation_required_without_creating_accounts(self):
        with self.assertRaises(CommandError):
            call_command("seed_beta_accounts", stdout=StringIO())
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_four_ordinary_accounts_and_repeat_preserves_password(self):
        password = "LocalFixture!72-NeverDeploy"
        with patch.object(Command, "_prompt_valid_password", return_value=password):
            call_command("seed_beta_accounts", confirm_local_preproduction=True, stdout=StringIO())
        User = get_user_model()
        self.assertEqual(User.objects.count(), 4)
        for account in ACCOUNTS:
            user = User.objects.get(email=account.email)
            self.assertTrue(user.check_password(password))
            self.assertFalse(user.is_staff)
            self.assertFalse(user.is_superuser)
            self.assertTrue(user.is_email_verified)
            self.assertTrue(user.profile.is_discoverable)
        original_hash = User.objects.get(email=ACCOUNTS[0].email).password
        with patch.object(Command, "_prompt_valid_password") as prompt:
            with self.assertRaises(CommandError):
                call_command("seed_beta_accounts", confirm_local_preproduction=True, stdout=StringIO())
            prompt.assert_not_called()
        self.assertEqual(User.objects.get(email=ACCOUNTS[0].email).password, original_hash)
        self.assertEqual(User.objects.count(), 4)
