# Jetson Nano Recovery, Headless Setup & Compute Engine Baseline

**Project:** BiblionOCR  
**Platform:** NVIDIA Jetson Nano Developer Kit 4GB  
**Host development machine:** HP Compaq 6200 Pro MT PC, Ubuntu 24.04.2 LTS  
**Date:** August 2026

---

## 1. Where We Ended Up

The Nano is now successfully booting from the **original 128GB micro-SD card** that previously lived in the Nano.

The earlier attempts to repair/burn other micro-SD cards were abandoned after repeated evidence of write/verification anomalies and a failed boot to the splash screen. We switched to the known-good original card and completed NVIDIA's headless setup successfully.

The Nano is reachable over both:

- USB device/serial networking during setup
- Ethernet on the LAN

Current hostname:

```text
nano
```

Current LAN address:

```text
192.168.2.5
```

It is also discoverable as:

```text
nano.local
```

SSH works:

```bash
ssh max-richey@192.168.2.5
```

The Nano reports:

```text
Ubuntu 18.04.6 LTS
Linux 4.9.253-tegra
aarch64
```

---

## 2. Important Recovery Lesson

We originally spent substantial effort attempting to burn and verify a Jetson image from Ubuntu 24.

The image-writing experiments produced repeatable byte differences, including:

```text
cmp: ... differ: byte 460
```

and earlier comparisons showed differences in other regions.

A repaired 64GB card subsequently failed to boot beyond the splash screen.

At that point the decision was made to stop troubleshooting the image-writing path and use the **known-good original 128GB Nano card**, whose complete image had already been backed up.

This was the correct stopping point: preserve the known-good hardware/image rather than continue experimenting with questionable cards.

### Storage/backups

A complete Nano image backup had previously been created and checksum-verified:

```text
Nano_8-12-26.img
SHA256:
22a742e19483127d998d4875e964b9caa9c8dc03aff9db9bc59a6f0298ef6068
```

The large backup will eventually be copied to the 32TB SSD. The important principle is that the Nano's working SD card is now a known-good booting system, while the original image remains backed up.

---

## 3. Headless Setup

The Nano was connected to the Ubuntu 24 machine by USB and appeared as:

```text
/dev/ttyACM0
```

The NVIDIA setup procedure completed successfully.

A user account was created as:

```text
max-richey
```

The Nano hostname was kept as:

```text
nano
```

The NVIDIA power-mode setup was left at:

```text
MAXN
```

No display was installed; the Nano is being operated headlessly.

---

## 4. Serial/USB Networking

During setup:

```bash
ls /dev/ttyACM*
```

returned:

```text
/dev/ttyACM0
```

`screen` was installed on Ubuntu 24:

```bash
sudo apt install screen
```

An attempt to open:

```bash
sudo screen /dev/ttyACM0 115200
```

terminated, but this was not treated as a setup failure because the NVIDIA setup itself had already completed.

The Nano was successfully reachable through the USB network interface as:

```text
nano.local
192.168.55.1
```

---

## 5. LAN Networking

The Nano's Ethernet interface is:

```text
eth0
```

with:

```text
192.168.2.5/24
```

The Ubuntu 24 host can ping it:

```text
PING nano.local (192.168.55.1)
0% packet loss
```

and can SSH directly to:

```bash
ssh max-richey@192.168.2.5
```

The SSH host-key warning encountered after the Nano was reinstalled was expected because the Nano's host key had changed.

On Ubuntu 24, the stale key was removed with:

```bash
ssh-keygen -f ~/.ssh/known_hosts -R 192.168.2.5
```

The new key was then accepted.

---

## 6. Ubuntu 24 USB Network Lesson

The Ubuntu 24 host briefly produced repetitive:

```text
Connection failed.
Activation of network connection failed.
```

notifications.

Investigation showed:

```text
eno1                 ethernet  connected
enx4a721195e328      ethernet  connected
enx4a721195e32a      ethernet  disconnected
```

The `enx...` interfaces correspond to the Nano's USB networking.

The likely trigger was the Nano's USB connection being attached/detached while Ubuntu 24's NetworkManager attempted to manage the USB Ethernet profiles.

The practical lesson:

> The USB cable is useful for serial/USB networking, but the Nano's normal operational connection should be Ethernet. Disconnecting the USB cable stopped the recurring NetworkManager disturbance.

USB/serial capability should still be retained for maintenance and recovery.

---

# 7. Current Nano Hardware Baseline

All commands in this section were run **on the Nano**, not the Ubuntu 24 host.

Prompt:

```text
max-richey@nano:~$
```

## Identity

```text
Static hostname: nano
Operating System: Ubuntu 18.04.6 LTS
Kernel: Linux 4.9.253-tegra
Architecture: arm64
```

Full kernel:

```text
Linux nano 4.9.253-tegra #1 SMP PREEMPT Sat Feb 19 08:59:22 PST 2022 aarch64
```

## CPU

```text
Architecture:        aarch64
CPU(s):              4
On-line CPU(s):      0-3
Thread(s) per core:  1
Core(s) per socket:  4
Model name:          Cortex-A57
CPU max MHz:         1479.0000
CPU min MHz:         102.0000
```

So the Nano has:

- 4 ARM Cortex-A57 CPU cores
- ARM64 architecture
- Dynamic clock range observed from roughly 102 MHz upward
- Maximum reported CPU frequency: 1.479 GHz

## Memory

```text
Mem:           3.9G total
               474M used
               2.6G free
               3.2G available

Swap:          1.9G total
               0B used
```

This confirms the expected 4GB-class Nano.

## Storage

```text
mmcblk0       119.1G
└─mmcblk0p1   119.1G  /
```

The remaining small partitions are the Jetson boot/firmware partitions.

Root filesystem:

```text
118G total
12G used
101G available
11%
```

This is a very healthy amount of free space for development.

---

# 8. Power Mode

The following was run on the Nano:

```bash
sudo nvpmodel -q
```

Result:

```text
NVPM WARN: fan mode is not set!
NV Power Mode: MAXN
0
```

The Nano is therefore currently configured for:

```text
MAXN
```

This is a **power/performance policy**, not a statement that the Nano is currently consuming maximum power.

While idle, the hardware dynamically clocks down.

No power-mode changes have been made.

---

# 9. tegrastats Baseline

The Nano's older `tegrastats` implementation does not support:

```text
--count
```

Its supported syntax is:

```text
Usage: tegrastats [-option]
--help
--interval <millisec>
--logfile <filename>
--load_cfg <filename>
--save_cfg <filename>
--start
--stop
--verbose
```

A live sample was therefore taken with:

```bash
sudo tegrastats --interval 1000
```

and stopped with:

```text
Ctrl+C
```

### Observed baseline

RAM:

```text
533/3964MB
```

Swap:

```text
0/1982MB
```

CPU:

```text
approximately 0–4% per core
```

CPU clocks during idle:

```text
102–204 MHz
```

GPU:

```text
GR3D_FREQuency: 0%@76
```

Therefore:

- GPU utilization was essentially 0%
- GPU clock was approximately 76 MHz at idle

Temperatures:

```text
CPU     ~35–36 °C
GPU     ~36–37 °C
PMIC    ~50 °C
AO      ~43 °C
thermal ~36 °C
```

Power telemetry was approximately:

```text
POM_5V_IN    ~0.9–1.5
POM_5V_GPU   0
POM_5V_CPU   ~0.08–0.125
```

These are idle observations, not performance measurements.

### Interpretation

The Nano is sitting comfortably at idle:

- very low CPU utilization
- unused swap
- substantial free RAM
- GPU present and monitored
- GPU idle
- temperatures are comfortable
- no obvious thermal or resource problem

This is a good baseline for future Compute Engine profiling.

---

# 10. Compute Engine Significance

The BiblionOCR Compute Engine is intended to:

1. Discover hardware.
2. Profile capabilities.
3. Monitor resources.
4. Allocate workloads appropriately.

The Nano should therefore be treated as a concrete compute provider rather than as an abstract "Linux computer."

The baseline now establishes:

```text
Platform:
    NVIDIA Jetson Nano 4GB
    ARM64 / aarch64
    4× Cortex-A57
    ~4GB RAM
    ~119GB SD storage
    NVIDIA Tegra GPU
    MAXN power policy

Runtime:
    Ubuntu 18.04.6
    Linux 4.9.253-tegra
    Jetson/L4T software stack
```

The Compute Engine should eventually discover these properties programmatically rather than relying on hard-coded assumptions.

---

# 11. Architectural Principle

The Compute Engine should distinguish:

**Known capability**

from

**currently available resource**

and from

**unknown capability**.

For example:

```text
GPU exists
    ≠
GPU currently available
    ≠
CUDA workload actually supported
```

Likewise:

```text
CUDA installed
    ≠
every BiblionOCR workload can use CUDA
```

CUDA should be treated as an optional acceleration provider.

A CPU fallback should remain available whenever practical.

Unknown capabilities should degrade gracefully rather than becoming fatal errors.

The eventual Compute Engine should therefore be able to say something like:

```text
GPU: NVIDIA Tegra
CUDA: available / unavailable / unknown
CPU: available
Memory: available
Storage: available
Current load: ...
Thermal state: ...
Power policy: MAXN
```

rather than simply reporting "Jetson Nano."

---

# 12. What We Are NOT Doing Yet

Do not:

- change the Nano's power mode
- reinstall the OS
- reflash the SD card
- modify boot configuration
- install a newer Ubuntu
- install arbitrary CUDA packages
- assume CUDA versions
- benchmark the Nano prematurely
- turn the Compute Engine into a general distributed-computing framework

The current phase is **discovery and documentation**.

---

# 13. Immediate Next Step

The next three commands should be run on the Nano:

```bash
cat /etc/nv_tegra_release
ls -ld /usr/local/cuda*
which nvcc
```

These are read-only discovery commands.

They will establish:

1. The exact NVIDIA L4T release.
2. Whether a CUDA installation is present.
3. Where CUDA is installed.
4. Whether the CUDA compiler (`nvcc`) is available.

After that, we can inspect the CUDA/runtime stack before making any changes.

---

# 14. Lessons From the Nano Journey

### Lesson 1 — Preserve the known-good image.

The original Nano SD card and its image backup are more valuable than repeated attempts to repair questionable cards.

### Lesson 2 — Verify before modifying.

The failed card experiments demonstrated why block-level verification matters.

### Lesson 3 — Use the platform's intended tooling when practical.

The successful headless setup followed NVIDIA's established Jetson procedure rather than continuing to fight an image-writing path that was producing unexplained byte differences.

### Lesson 4 — Separate host from target.

Ubuntu 24 is the **development/control host**.

The Jetson Nano is the **ARM64 target**.

Commands such as:

```text
nvpmodel
tegrastats
```

belong on the Nano.

### Lesson 5 — USB networking is useful but special.

The USB connection provides valuable recovery/serial/network functionality, but it also creates a NetworkManager-managed Ethernet device on Ubuntu 24.

Ethernet is the normal operational network path.

### Lesson 6 — Patience is a technical strategy.

When hardware behavior becomes ambiguous, stop changing things.

Preserve the known-good state, document it, and continue from a controlled baseline.

---

# 15. Current State

**Nano:** WORKING  
**Headless setup:** COMPLETE  
**SSH:** WORKING  
**Ethernet:** WORKING  
**USB networking/serial:** AVAILABLE  
**Hostname:** `nano`  
**LAN IP:** `192.168.2.5`  
**OS:** Ubuntu 18.04.6 LTS  
**Kernel:** 4.9.253-tegra  
**Architecture:** ARM64  
**Power mode:** MAXN  
**RAM:** ~4GB  
**CPU:** 4× Cortex-A57  
**GPU telemetry:** WORKING  
**Thermal state:** HEALTHY  
**Compute Engine baseline:** ESTABLISHED  
**CUDA discovery:** NEXT

---

## Final Note

The Nano is no longer a recovery problem.

It is now a **known, booting, remotely accessible compute node**.

That changes the nature of the work. From this point forward, the safest strategy is:

> **Observe → document → understand → implement → test.**

Not:

> change → reboot → hope → repair.
