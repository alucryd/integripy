import subprocess

from integripy import application

subprocess.run(['npx', 'webpack'])
application.run(port=5000)
