from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient

from suggestions.models import Suggestion


class SuggestionAPITestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.alice = User.objects.create_user(username="alice", email="alice@example.com", password="pass")
        self.bob = User.objects.create_user(username="bob", email="bob@example.com", password="pass")

        # Ensure the approver permission exists and a group
        ct = ContentType.objects.get_for_model(Suggestion)
        perm, _ = Permission.objects.get_or_create(
            codename="can_approve_suggestion",
            content_type=ct,
            defaults={"name": "Can approve suggestions"},
        )
        self.approvers_group, _ = Group.objects.get_or_create(name="approvers")
        # create some suggestions
        self.public = Suggestion.objects.create(
            title="Public suggestion",
            description="Visible to everyone",
            proposer=self.alice,
            is_public=True,
        )
        self.private_alice = Suggestion.objects.create(
            title="Alice private",
            description="Only Alice or staff",
            proposer=self.alice,
            is_public=False,
        )
        self.private_bob = Suggestion.objects.create(
            title="Bob private",
            description="Only Bob or staff",
            proposer=self.bob,
            is_public=False,
        )

        self.client = APIClient()

    def test_anonymous_list_shows_only_public(self):
        resp = self.client.get("/api/suggestions/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        items = data.get("results", data)
        ids = {o.get("id") for o in items}
        self.assertIn(self.public.id, ids)
        self.assertNotIn(self.private_alice.id, ids)
        self.assertNotIn(self.private_bob.id, ids)

    def test_authenticated_user_sees_public_and_own(self):
        self.client.force_authenticate(user=self.alice)
        resp = self.client.get("/api/suggestions/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        items = data.get("results", data)
        ids = {o.get("id") for o in items}
        self.assertIn(self.public.id, ids)
        self.assertIn(self.private_alice.id, ids)
        self.assertNotIn(self.private_bob.id, ids)

    def test_create_requires_authentication(self):
        # anonymous should not be able to create
        resp = self.client.post("/api/suggestions/", {"title": "X", "description": "Y"}, format="json")
        self.assertIn(resp.status_code, (401, 403))

        # authenticated can create
        self.client.force_authenticate(user=self.bob)
        resp = self.client.post(
            "/api/suggestions/",
            {"title": "New", "description": "Created by bob", "is_public": False},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(Suggestion.objects.filter(title="New", proposer=self.bob).exists())

    def test_approve_requires_approver_group(self):
        url = f"/api/suggestions/{self.public.id}/approve/"

        # bob is not approver
        self.client.force_authenticate(user=self.bob)
        resp = self.client.post(url)
        self.assertIn(resp.status_code, (401, 403))

        # make bob an approver
        self.approvers_group.user_set.add(self.bob)
        self.client.force_authenticate(user=self.bob)
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        self.public.refresh_from_db()
        self.assertEqual(self.public.status, Suggestion.STATUS_APPROVED)
