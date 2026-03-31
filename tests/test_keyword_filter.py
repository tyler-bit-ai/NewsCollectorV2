import unittest

from filters.keyword_filter import KeywordFilter


GLOBAL_TREND_RULES = {
    "excluded_domains": [
        "facebook.com",
        "pilotcompany.com",
    ],
    "excluded_url_patterns": [
        "/groups/",
        "/help/",
        "/support/",
    ],
    "excluded_keywords": [
        "dog",
        "pets",
    ],
    "required_keywords": [
        "roaming",
        "esim",
        "connectivity",
        "telecom",
    ],
}


class KeywordFilterTests(unittest.TestCase):
    def setUp(self):
        self.keyword_filter = KeywordFilter(
            blacklist_domains=["search", "category"],
            excluded_keywords=["광고", "coupon"],
            global_trend_rules=GLOBAL_TREND_RULES,
        )

    def test_global_trend_filters_false_positive_social_post(self):
        article = {
            "title": "How should I handle a roaming dog in my neighborhood?",
            "snippet": "Neighbors discuss the roaming dog issue.",
            "link": "https://www.facebook.com/groups/hendersonville/posts/10161439450076546/",
            "query": "roaming business",
            "source_domain": "facebook.com",
        }

        self.assertFalse(self.keyword_filter.validate(article, category="global_trend"))

    def test_global_trend_filters_static_help_page(self):
        article = {
            "title": "International roaming rates for business",
            "snippet": "Business roaming support and rates.",
            "link": "https://www.t-mobile.com/support/coverage/international-roaming-rates-business-and-government",
            "query": "roaming business",
            "source_domain": "www.t-mobile.com",
        }

        self.assertFalse(self.keyword_filter.validate(article, category="global_trend"))

    def test_global_trend_keeps_relevant_telecom_article(self):
        article = {
            "title": "Travel eSIM connectivity demand accelerates for MVNOs",
            "snippet": "Roaming and connectivity demand is growing across travel eSIM providers.",
            "link": "https://www.telna.com/blog/travel-esim-strategy-for-mnos",
            "query": "travel connectivity market",
            "source_domain": "www.telna.com",
        }

        self.assertTrue(self.keyword_filter.validate(article, category="global_trend"))

    def test_non_global_trend_keeps_existing_behavior(self):
        article = {
            "title": "말톡 후기",
            "snippet": "실사용 리뷰입니다.",
            "link": "https://blog.example.com/post/1",
        }

        self.assertTrue(self.keyword_filter.validate(article, category="voc_esim"))


if __name__ == "__main__":
    unittest.main()
