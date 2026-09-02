import unittest
from app.config import settings
from app.main import app


class TestKrishiXConfigAndRoutes(unittest.TestCase):

    def test_settings_loaded(self):
        """Verify that configuration settings are properly initialized."""
        self.assertGreater(settings.API_PORT, 0)
        self.assertEqual(settings.SARVAM_MODEL, "saaras:v4")
        self.assertGreater(settings.MATCH_RADIUS_KM, 0)

    def test_app_routes(self):
        """Verify that the FastAPI app initializes with expected routes."""
        route_paths = [route.path for route in app.routes]
        self.assertIn("/health", route_paths)
        self.assertIn("/process-voice", route_paths)


if __name__ == "__main__":
    unittest.main()

