from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from suggestions.models import Suggestion, SuggestionComment, SuggestionVote
from utils.query_builder import build_filters_from_params, build_search_q, sanitize_ordering


class SuggestionsCommentsVotesTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.alice = User.objects.create_user(username="alice", password="pass")
        self.bob = User.objects.create_user(username="bob", password="pass")
        self.sugg = Suggestion.objects.create(
            title="Hello world",
            description="Contains hello",
            proposer=self.alice,
            is_public=True,
        )
        self.client = APIClient()

    def test_comment_create_requires_auth_and_sets_author(self):
        # anonymous cannot create
        resp = self.client.post("/api/comments/", {"suggestion": self.sugg.id, "content": "Hi"}, format="json")
        self.assertIn(resp.status_code, (401, 403))

        # authenticated can create and author is set
        self.client.force_authenticate(user=self.bob)
        resp = self.client.post("/api/comments/", {"suggestion": self.sugg.id, "content": "Nice"}, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(SuggestionComment.objects.filter(suggestion=self.sugg, author=self.bob, content="Nice").exists())

    def test_vote_increments_and_idempotent(self):
        self.client.force_authenticate(user=self.bob)
        resp = self.client.post("/api/votes/", {"suggestion": self.sugg.id}, format="json")
        self.assertEqual(resp.status_code, 201)
        self.sugg.refresh_from_db()
        self.assertEqual(self.sugg.votes_count, 1)

        # voting again should not increment
        resp2 = self.client.post("/api/votes/", {"suggestion": self.sugg.id}, format="json")
        self.assertEqual(resp2.status_code, 201)
        self.sugg.refresh_from_db()
        self.assertEqual(self.sugg.votes_count, 1)


class QueryBuilderUnitTests(TestCase):
    def test_build_filters_and_search_and_ordering(self):
        allow = {"status": "status", "is_public": "is_public", "proposer": "proposer__id"}

        # basic mapping and boolean
        q, kwargs = build_filters_from_params({"status": "pending", "is_public": "true"}, allow)
        self.assertEqual(kwargs.get("status"), "pending")
        self.assertTrue(kwargs.get("is_public") is True)

        # csv
        q2, kwargs2 = build_filters_from_params({"status": "pending,approved"}, allow)
        self.assertIn("status__in", kwargs2)
        self.assertEqual(kwargs2["status__in"], ["pending", "approved"])

        # negation: create a couple of suggestions and apply q to queryset
        User = get_user_model()
        user = User.objects.create_user(username="qb_user", password="pass")
        s1 = Suggestion.objects.create(
            title="A",
            description="a",
            proposer=user,
            status=Suggestion.STATUS_APPROVED,
            is_public=True,
        )
        s2 = Suggestion.objects.create(
            title="B",
            description="b",
            proposer=user,
            status=Suggestion.STATUS_PENDING,
            is_public=True,
        )
        q_not, kwargs_not = build_filters_from_params({"status_not": "approved"}, allow)
        results = Suggestion.objects.filter(q_not, **kwargs_not)
        self.assertIn(s2, results)
        self.assertNotIn(s1, results)

        # search q
        sq = build_search_q("hello", ["title", "description"])
        s3 = Suggestion.objects.create(title="hello there", description="x", proposer=user, is_public=True)
        found = Suggestion.objects.filter(sq)
        self.assertIn(s3, found)

        # sanitize ordering
        self.assertEqual(sanitize_ordering("-votes_count", ["created_at", "votes_count"]), "-votes_count")
        self.assertIsNone(sanitize_ordering("bad_field", ["created_at"]))
