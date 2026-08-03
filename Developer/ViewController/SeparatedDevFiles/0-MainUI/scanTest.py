from scapy.all import conf, get_if_list, get_working_ifaces

print("Default iface:", conf.iface)

print("\nAll interfaces:")
for iface in get_if_list():
    print(" ", iface)

print("\nWorking interfaces:")
for iface in get_working_ifaces():
    print(" ", iface)