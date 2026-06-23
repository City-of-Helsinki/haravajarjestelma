from django.conf import settings
from django.contrib.gis.forms import OSMWidget


class HaravaOSMWidget(OSMWidget):
    """OSM map widget centred on Helsinki railway station with 3D geometry support.

    Uses Helsinki city raster tiles (maptiles.api.hel.fi) instead of the
    default tile.openstreetmap.org.  This fixes a Firefox-only 403: OpenLayers'
    ``crossOrigin='anonymous'`` puts Firefox into CORS mode and OSM's CDN
    blocks requests whose ``Origin`` header is a private/localhost domain.
    Helsinki's tile CDN supports CORS for all origins and requires no API key.

    The tile URL is configured via the TILE_URL setting.
    """

    template_name = "gis/harava-osm.html"
    default_lon = 24.941389
    default_lat = 60.171944
    default_zoom = 12.5

    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.attrs["tile_url"] = settings.TILE_URL
