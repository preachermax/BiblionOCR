from __future__ import annotations

import json
import unittest

from Developer.hardware.providers.cuda import CUDAProvider
from Developer.hardware.providers.gpu import GPUProvider


class GPUProviderTests(unittest.TestCase):
	def test_lspci_parser_extracts_gpu_devices(self) -> None:
		provider = GPUProvider()
		output = "\n".join(
			[
				"00:02.0 VGA compatible controller: Intel Corporation UHD Graphics 630 (Mobile)",
				"01:00.0 3D controller: NVIDIA Corporation TU117M [GeForce GTX 1650 Mobile / Max-Q]",
			]
		)

		devices = provider._devices_from_lspci_output(output)

		self.assertEqual(2, len(devices))
		self.assertEqual("Intel", devices[0]["vendor"])
		self.assertEqual("NVIDIA", devices[1]["vendor"])
		self.assertEqual("01:00.0", devices[1]["bus_id"])

	def test_windows_json_parser_extracts_gpu_devices(self) -> None:
		provider = GPUProvider()
		output = json.dumps(
			[
				{
					"Name": "NVIDIA GeForce RTX 4060",
					"AdapterCompatibility": "NVIDIA",
					"DriverVersion": "32.0.15.6603",
					"AdapterRAM": 8589934592,
					"PNPDeviceID": "PCI\\VEN_10DE&DEV_2882&SUBSYS_12345678",
				},
				{
					"Name": "Intel(R) UHD Graphics 770",
					"AdapterCompatibility": "Intel Corporation",
					"DriverVersion": "31.0.101.4644",
					"AdapterRAM": 1073741824,
					"PNPDeviceID": "PCI\\VEN_8086&DEV_4680&SUBSYS_87654321",
				},
			]
		)

		devices = provider._devices_from_windows_json(output)

		self.assertEqual(2, len(devices))
		self.assertEqual("NVIDIA", devices[0]["vendor"])
		self.assertEqual(8192, devices[0]["memory_total_mb"])
		self.assertEqual("Intel", devices[1]["vendor"])

	def test_jetson_model_name_uses_name_or_compatible(self) -> None:
		provider = GPUProvider()

		self.assertEqual("gv11b", provider._jetson_model_name("gv11b", ["nvidia,gv11b"]))
		self.assertEqual("gv11b", provider._jetson_model_name(None, ["nvidia,gv11b"]))


class CUDAProviderTests(unittest.TestCase):
	def test_parse_nvcc_version(self) -> None:
		provider = CUDAProvider()
		output = "Cuda compilation tools, release 12.4, V12.4.131"

		self.assertEqual("12.4", provider._parse_nvcc_version(output))

	def test_parse_nvidia_smi_cuda_version(self) -> None:
		provider = CUDAProvider()
		output = "NVIDIA-SMI 550.54.14    Driver Version: 550.54.14    CUDA Version: 12.4"

		self.assertEqual("12.4", provider._parse_nvidia_smi_cuda_version(output))

	def test_cuda_version_from_json_payload(self) -> None:
		provider = CUDAProvider()
		path = "/tmp/cuda-version.json"

		with open(path, "w", encoding="utf-8") as handle:
			handle.write('{"cuda": {"version": "12.2.0"}}')

		try:
			self.assertEqual("12.2.0", provider._cuda_version_from_json(path))
		finally:
			import os
			os.remove(path)

	def test_runtime_library_is_optional(self) -> None:
		provider = CUDAProvider()

		self.assertIn(provider._runtime_library(), (None, provider._runtime_library()))

	def test_parse_jetpack_version(self) -> None:
		provider = CUDAProvider()
		contents = "# R32 (release), REVISION: 7.4, GCID: 33514132, BOARD: t210ref, EABI: aarch64"

		self.assertEqual("L4T R32.7.4", provider._parse_jetpack_version(contents))

	def test_parse_jetpack_version_falls_back_to_raw_text(self) -> None:
		provider = CUDAProvider()
		contents = "jetson-custom-build"

		self.assertEqual("jetson-custom-build", provider._parse_jetpack_version(contents))


if __name__ == "__main__":
	unittest.main()