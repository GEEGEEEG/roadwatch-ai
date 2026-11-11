"""Ghim kéo thả cho bản đồ chọn vị trí: thả ghim ở đâu thì gửi tọa độ mới về Streamlit.

streamlit-folium chỉ báo lại sự kiện bấm lên bản đồ (last_clicked). Vì vậy khi người dùng
thả ghim (sự kiện dragend), ta phát một sự kiện 'click' giả tại vị trí ghim để cơ chế sẵn có
đưa tọa độ về app, không cần viết thêm component.
"""
import folium
from branca.element import MacroElement
from jinja2 import Template


class _DragToClick(MacroElement):
    _template = Template("""
        {% macro script(this, kwargs) %}
        {{ this.marker_name }}.on('dragend', function (e) {
            {{ this.map_name }}.fire('click', {latlng: e.target.getLatLng()});
        });
        {% endmacro %}
    """)

    def __init__(self, marker_name: str, map_name: str):
        super().__init__()
        self._name = 'DragToClick'
        self.marker_name = marker_name
        self.map_name = map_name


def add_draggable_marker(fmap: folium.Map, lat: float, lon: float, tooltip: str = '', popup: str = ''):
    marker = folium.Marker([lat, lon], tooltip=tooltip or None, popup=popup or None, draggable=True,
                           icon=folium.Icon(color='red', icon='info-sign'))
    marker.add_to(fmap)
    _DragToClick(marker.get_name(), fmap.get_name()).add_to(fmap)
    return marker
