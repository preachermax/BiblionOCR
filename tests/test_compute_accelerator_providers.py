from __future__ import annotations

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


class CUDAProviderTests(unittest.TestCase):
	def test_parse_nvcc_version(self) -> None:
		provider = CUDAProvider()
		output = "Cuda compilation tools, release 12.4, V12.4.131"

		self.assertEqual("12.4", provider._parse_nvcc_version(output))

	def test_parse_nvidia_smi_cuda_version(self) -> None:
		provider = CUDAProvider()
		output = "NVIDIA-SMI 550.54.14    Driver Version: 550.54.14    CUDA Version: 12.4"

		self.assertEqual("12.4", provider._parse_nvidia_smi_cuda_version(output))


if __name__ == "__main__":
	unittest.main()