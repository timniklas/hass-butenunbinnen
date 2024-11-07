from __future__ import annotations

from haffmpeg.camera import CameraMjpeg
from haffmpeg.tools import IMAGE_JPEG

from homeassistant.config_entries import ConfigEntry

from homeassistant.components import ffmpeg
from homeassistant.components.camera import (
    Camera,
    CameraEntityFeature,
)
from homeassistant.components.ffmpeg import get_ffmpeg_manager
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_aiohttp_proxy_stream
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up a Camera."""
    
    async_add_entities([LivestreamCamera(hass)], True)


class LivestreamCamera(Camera):

    _attr_has_entity_name = True
    _attr_is_streaming = True
    _attr_icon = "mdi:television-classic"
    _attr_supported_features = CameraEntityFeature.STREAM
    _attr_unique_id = "livestream"
    _options = "-pred 1"
    _video = "https://rbhlslive.akamaized.net/hls/live/2020435/rbfs/master.m3u8"
    _logo = "https://www.butenunbinnen.de/bilder/livestreambild102~_v-1280x720_c-1729068391658.jpg"

    def __init__(self, hass):
        """Initialize."""
        super().__init__()
        self._manager = get_ffmpeg_manager(hass)

    @property
    def is_streaming(self) -> bool:
        """Return the state of the sensor."""
        return True

    async def stream_source(self) -> str:
        """Return the stream source."""
        return self._video.split(" ")[-1]

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a still image response from the camera."""
        if self._logo == None:
            return None

        return await ffmpeg.async_get_image(
            self.hass,
            self._logo,
            output_format=IMAGE_JPEG,
            extra_cmd=self._options,
        )

    async def handle_async_mjpeg_stream(self, request):
        """Generate an HTTP MJPEG stream from the camera."""
        
        stream = CameraMjpeg(self._manager.binary)
        await stream.open_camera(self._video, extra_cmd=self._options)
        try:
            stream_reader = await stream.get_reader()
            return await async_aiohttp_proxy_stream(
                self.hass,
                request,
                stream_reader,
                self._manager.ffmpeg_stream_content_type,
            )
        finally:
            await stream.close()