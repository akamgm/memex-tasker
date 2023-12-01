import os
import signal
from time import sleep
from flask import Flask, render_template, request
import subprocess
import psutil

app = Flask(__name__)

# Function to list available programs
def list_programs(directory):
    programs = {}
    for filename in os.listdir(directory):
        if filename.endswith('.py'):  # Assuming all programs are Python scripts
            name, _ = os.path.splitext(filename)
            programs[name] = os.path.join(directory, filename)
    return programs

def find_running_program(programs):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if the process command line matches any of our program scripts
            for name, path in programs.items():
                if path in proc.info['cmdline']:
                    return proc, name
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None, None

# Directory containing the programs
apps_dir = 'apps/'
programs = list_programs(apps_dir)

# Keep track of the currently running process
current_process, current_program = find_running_program(programs)

@app.route('/')
def index():
    return render_template('index.html', programs=programs.keys())

@app.route('/start', methods=['POST'])
def start_program():
    global current_process

    data = request.get_json()
    program_name = data['program']

    # Stop the currently running program, if any
    if current_process:
        # Kill the entire process group that was started
        os.killpg(os.getpgid(current_process.pid), signal.SIGKILL)

    # Start the new program
    if program_name in programs:
        current_process = subprocess.Popen(programs[program_name], shell=True, preexec_fn=os.setsid)

    return 'Started ' + program_name


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
