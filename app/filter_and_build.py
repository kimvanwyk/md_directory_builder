''' Filter out undesired LaTeX elements and build a PDF
'''

import docker
import os

CONTAINER_NAME = 'pandoc'
IMAGE_NAME = 'kimvanwyk/pandoc:latest'
# PDF_CONTAINER_NAME = 'latex'
# PDF_IMAGE_NAME = 'kimvanwyk/latex:latest'
TEMPLATE='no_frills_latex.txt'
FILE_IN='output.txt'
client = docker.from_env()

volumes = {}
workdir = os.getcwd()
volumes[workdir] = {'bind':'/io', 'mode':'rw'}
client.containers.run(IMAGE_NAME, command=f'-s -o output.tex --template={TEMPLATE} {FILE_IN}', name=CONTAINER_NAME,
                      volumes=volumes, auto_remove=True, stdin_open=True, stream=True, tty=True)

client.containers.run(IMAGE_NAME, command=f'output.tex', name=CONTAINER_NAME, entrypoint='pdflatex',
                      volumes=volumes, auto_remove=True, stdin_open=True, stream=True, tty=True)
