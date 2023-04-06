import os

#Update Font Directories/FontFiles:
fontfile = "FROMVS.ttf"
forgedir = "~/Documents/MyForge/"
homefontdir = "~/.fonts"
localfontdir = "~/.local/share/fonts"
localsharefontdir = "/usr/local/share/fonts"
systemsharefontdir = "/usr/share/fonts/truetype/FROMVS"

# Hardcoded - it works
'''os.system("cp ~/Documents/MyForge/FROMVS.ttf ~/.local/share/fonts")
os.system("cp ~/Documents/MyForge/FROMVS.ttf ~/.fonts")
os.system("sudo cp ~/Documents/MyForge/FROMVS.ttf /usr/local/share/fonts")
os.system("sudo cp ~/Documents/MyForge/FROMVS.ttf /usr/share/fonts/truetype/FROMVS")'''

# field string coded
os.system(f"cp {forgedir}{fontfile} {homefontdir}")
os.system(f"cp {forgedir}{fontfile} {localfontdir}")
os.system(f"sudo cp {forgedir}{fontfile} {localsharefontdir}")
os.system(f"sudo cp {forgedir}{fontfile} {systemsharefontdir}")

os.system("fc-cache -f -v")