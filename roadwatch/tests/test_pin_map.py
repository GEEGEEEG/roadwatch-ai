import re
import subprocess
import tempfile

import pytest
folium = pytest.importorskip('folium')

from core.pin_map import add_draggable_marker


def _html():
    m = folium.Map(location=[16.05, 108.2], zoom_start=17)
    mk = add_draggable_marker(m, 16.05, 108.2, 'Kéo', 'x')
    return m, mk, m.get_root().render()


def test_marker_is_draggable_and_fires_click_on_drop():
    m, mk, html = _html()
    assert '"draggable": true' in html or '"draggable":true' in html
    assert f"{mk.get_name()}.on('dragend'" in html
    assert f"{m.get_name()}.fire('click'" in html and 'e.target.getLatLng()' in html


def test_generated_javascript_is_valid():
    node = subprocess.run(['which', 'node'], capture_output=True).returncode == 0
    if not node:
        pytest.skip('không có node')
    js = '\n'.join(re.findall(r'<script>(.*?)</script>', _html()[2], re.S))
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as f:
        f.write(js)
    assert subprocess.run(['node', '--check', f.name], capture_output=True).returncode == 0
