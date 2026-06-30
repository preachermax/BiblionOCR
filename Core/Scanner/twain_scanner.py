import io
import os

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(MODULE_DIR, "..", ".."))

try:
	import twain
except ImportError:
	twain = None

try:
	from PIL import Image
except ImportError:
	Image = None

from .device import ScannerDevice


class TwainScanner(ScannerDevice):
	backend_name = "TWAIN"
	DSM_CANDIDATES = tuple(
		candidate
		for candidate in (
			os.environ.get("BIBLION_TWAIN_DSM"),
			os.environ.get("TWAINDSM_DLL"),
			os.path.join(REPO_ROOT, "twaindsm.dll"),
			os.path.join(MODULE_DIR, "twaindsm.dll"),
			os.path.join(MODULE_DIR, "bin", "twaindsm.dll"),
			"twaindsm.dll",
			os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "System32", "twaindsm.dll"),
			os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "twaindsm.dll"),
			os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "twain_32.dll"),
			"twain_32.dll",
		)
		if candidate
	)

	@classmethod
	def is_supported_platform(cls, platform_name):
		return platform_name == "windows"

	@classmethod
	def is_available(cls):
		if twain is None or Image is None:
			return False
		for dsm_name in cls.DSM_CANDIDATES:
			try:
				with twain.SourceManager(0, dsm_name=dsm_name):
					return True
			except Exception:
				continue
		return False

	def __init__(self):
		if twain is None or Image is None:
			raise RuntimeError("TWAIN scanning requires pytwain and Pillow on Windows")
		self._dsm_name = self._detect_dsm_name()
		if not self._dsm_name:
			raise RuntimeError("TWAIN is installed, but no usable TWAIN data source manager DLL was found")

	def list_devices(self):
		with self._open_source_manager() as source_manager:
			return list(source_manager.GetSourceList() or [])

	def acquire(self, destination_folder, request=None):
		request = request or {}
		with self._open_source_manager() as source_manager:
			source_names = list(source_manager.GetSourceList() or [])
			if not source_names:
				raise RuntimeError("TWAIN did not report any scanner devices")

			source = self._open_source(source_manager, source_names, request.get("device_name"))
			try:
				self._configure_source(source, request)
				source.request_acquire(show_ui=False, modal_ui=False)
				images = self._transfer_images(source, request)
			finally:
				close_source = getattr(source, "close", None)
				if callable(close_source):
					close_source()

		if not images:
			raise RuntimeError("TWAIN scan did not return any images")

		path = self._save_images(images, destination_folder, request)
		return {
			"path": path,
			"dir": destination_folder,
			"device": request.get("device_name") or source_names[0],
		}

	def _open_source(self, source_manager, source_names, requested_name):
		if requested_name:
			requested_name_lower = str(requested_name).strip().lower()
			for source_name in source_names:
				if str(source_name).strip().lower() == requested_name_lower:
					return source_manager.OpenSource(source_name)
			for source_name in source_names:
				if requested_name_lower in str(source_name).strip().lower():
					return source_manager.OpenSource(source_name)
			raise RuntimeError(f"TWAIN device not found: {requested_name}")

		return source_manager.open_source()

	@classmethod
	def _detect_dsm_name(cls):
		for dsm_name in cls.DSM_CANDIDATES:
			try:
				with twain.SourceManager(0, dsm_name=dsm_name):
					return dsm_name
			except Exception:
				continue
		return None

	def _open_source_manager(self):
		return twain.SourceManager(0, dsm_name=self._dsm_name)

	def _configure_source(self, source, request):
		mode = request.get("mode", "color")
		dpi = int(request.get("dpi", 300))
		source_type = request.get("source_type", "flatbed")
		duplex = bool(request.get("duplex"))

		pixel_type_map = {
			"color": twain.TWPT_RGB,
			"grayscale": twain.TWPT_GRAY,
			"mono": twain.TWPT_BW,
		}
		pixel_type = pixel_type_map.get(mode, twain.TWPT_RGB)

		for capability, value_type, value in (
			(twain.ICAP_PIXELTYPE, twain.TWTY_UINT16, pixel_type),
			(twain.ICAP_XRESOLUTION, twain.TWTY_FIX32, dpi),
			(twain.ICAP_YRESOLUTION, twain.TWTY_FIX32, dpi),
		):
			try:
				source.set_capability(capability, value_type, value)
			except Exception:
				pass

		if source_type == "adf":
			for capability in (twain.CAP_FEEDERENABLED, twain.CAP_AUTOFEED):
				try:
					source.set_capability(capability, twain.TWTY_BOOL, True)
				except Exception:
					pass

		cap_duplexenabled = getattr(twain, "CAP_DUPLEXENABLED", None)
		if duplex and cap_duplexenabled is not None:
			try:
				source.set_capability(cap_duplexenabled, twain.TWTY_BOOL, True)
			except Exception:
				pass

	def _transfer_images(self, source, request):
		use_adf = request.get("source_type") == "adf"
		images = []
		more_pages = True
		while more_pages:
			transfer_result = source.xfer_image_natively()
			if not transfer_result:
				break

			handle, remaining_count = transfer_result
			bmp_bytes = twain.dib_to_bm_file(handle)
			image = Image.open(io.BytesIO(bmp_bytes))
			images.append(self._normalize_image_mode(image, request.get("mode", "color")))
			more_pages = bool(remaining_count) and use_adf

		return images

	def _normalize_image_mode(self, image, mode):
		if mode == "grayscale":
			return image.convert("L")
		if mode == "mono":
			return image.convert("1")
		return image.convert("RGB")

	def _save_images(self, images, destination_folder, request):
		scan_number = 1
		while True:
			filename = f"scan_{scan_number:06d}.tif"
			path = os.path.join(destination_folder, filename)
			if not os.path.exists(path):
				break
			scan_number += 1

		first_image = images[0]
		remaining_images = images[1:]
		if remaining_images:
			first_image.save(path, format="TIFF", save_all=True, append_images=remaining_images)
		else:
			first_image.save(path, format="TIFF")
		return path
