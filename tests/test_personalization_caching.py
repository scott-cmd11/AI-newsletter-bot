import unittest
import shutil
import json
import os
from pathlib import Path
from unittest.mock import patch, ANY
from src.services.personalization_service import PersonalizationService

class TestPersonalizationCaching(unittest.TestCase):
    def setUp(self):
        self.output_dir = Path("output/test_caching")
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True)

    def tearDown(self):
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)

    def _create_review_file(self, filename, content=None):
        if content is None:
            content = {
                "categories": {},
                "selected": [{"title": "A", "source": "S", "category": "C", "score": 1.0}]
            }
        with open(self.output_dir / filename, 'w') as f:
            json.dump(content, f)

    def test_caching_behavior(self):
        # 1. Create initial files
        self._create_review_file("review_1.json")
        self._create_review_file("review_2.json")

        service = PersonalizationService(self.output_dir)

        # Monitor open calls
        # We patch builtins.open to track calls, but pass through to real open
        with patch('builtins.open', side_effect=open) as mock_open:
            # First run
            profile = service.analyze_historical_selections()

            # Check cache created
            self.assertTrue((self.output_dir / "profile_cache.json").exists())
            self.assertEqual(profile.total_selections, 2)

            # Count opens. review_1.json and review_2.json should be opened.
            # Convert call args to string to check
            opened_files = []
            for call in mock_open.mock_calls:
                if call.args and isinstance(call.args[0], (str, Path)):
                    path_str = str(call.args[0])
                    if 'review_' in path_str:
                        opened_files.append(Path(path_str).name)

            self.assertIn('review_1.json', opened_files)
            self.assertIn('review_2.json', opened_files)

        # 2. Second run - Cold start (new service instance)
        service2 = PersonalizationService(self.output_dir)
        with patch('builtins.open', side_effect=open) as mock_open:
            profile2 = service2.analyze_historical_selections()

            self.assertEqual(profile2.total_selections, 2)

            # Should open cache, but NOT review files
            opened_files = []
            for call in mock_open.mock_calls:
                if call.args and isinstance(call.args[0], (str, Path)):
                    path_str = str(call.args[0])
                    if 'review_' in path_str:
                        opened_files.append(Path(path_str).name)

            self.assertEqual(len(opened_files), 0, f"Should not read review files when cache is valid, but read: {opened_files}")

        # 3. Add new file
        self._create_review_file("review_3.json")

        service3 = PersonalizationService(self.output_dir)
        with patch('builtins.open', side_effect=open) as mock_open:
            profile3 = service3.analyze_historical_selections()

            self.assertEqual(profile3.total_selections, 3)

            # Should open ONLY review_3.json
            opened_files = []
            for call in mock_open.mock_calls:
                if call.args and isinstance(call.args[0], (str, Path)):
                    path_str = str(call.args[0])
                    if 'review_' in path_str:
                        opened_files.append(Path(path_str).name)

            self.assertIn('review_3.json', opened_files)
            self.assertNotIn('review_1.json', opened_files)
            self.assertNotIn('review_2.json', opened_files)

        # 4. Delete a file (should trigger rebuild)
        (self.output_dir / "review_1.json").unlink()

        service4 = PersonalizationService(self.output_dir)
        with patch('builtins.open', side_effect=open) as mock_open:
            profile4 = service4.analyze_historical_selections()

            self.assertEqual(profile4.total_selections, 2) # 2 and 3 remain

            # Should re-read remaining files (2 and 3)
            opened_files = []
            for call in mock_open.mock_calls:
                if call.args and isinstance(call.args[0], (str, Path)):
                    path_str = str(call.args[0])
                    if 'review_' in path_str:
                        opened_files.append(Path(path_str).name)

            self.assertIn('review_2.json', opened_files)
            self.assertIn('review_3.json', opened_files)
            self.assertNotIn('review_1.json', opened_files)

if __name__ == '__main__':
    unittest.main()
