"""
test_assets.py
Unit tests verifying application static assets and logo availability.
Ensures no broken images or missing local assets exist in GeoFoundation.
"""

import os
from PIL import Image


def test_logo_png_exists_and_is_valid():
    """Verify local logo.png exists and is a valid readable image."""
    logo_path = os.path.join("assets", "logo.png")
    assert os.path.exists(logo_path), "assets/logo.png must exist locally"
    assert os.path.getsize(logo_path) > 1000, "assets/logo.png must not be empty"

    # Verify PNG magic number
    with open(logo_path, "rb") as f:
        header = f.read(8)
    assert header == b"\x89PNG\r\n\x1a\n", "assets/logo.png must be a valid PNG file"

    # Open with PIL to confirm image validity
    with Image.open(logo_path) as img:
        assert img.format == "PNG"
        width, height = img.size
        assert width >= 128 and height >= 128, "Logo dimensions must be high resolution"


def test_foundation_png_alias_exists():
    """Verify assets/foundation.png alias exists locally."""
    foundation_path = os.path.join("assets", "foundation.png")
    assert os.path.exists(foundation_path), "assets/foundation.png must exist locally"
    assert os.path.getsize(foundation_path) > 1000, "assets/foundation.png must not be empty"


def test_app_py_references_local_logo():
    """Verify app.py does not use external URL for sidebar logo."""
    with open("app.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Must not contain external http/https URL for sidebar logo
    assert "https://img.icons8.com" not in content, "Sidebar logo must not use external URL"
    assert "assets" in content and "logo.png" in content, "app.py must reference local assets/logo.png"
