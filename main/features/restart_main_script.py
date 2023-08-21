import subprocess
import sys

def restart_main_script(channel):
    subprocess.Popen(['lxterminal', '-e', 'python3', 'main.py'])
    sys.exit()
