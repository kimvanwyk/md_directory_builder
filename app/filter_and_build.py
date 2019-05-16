''' Filter out undesired LaTeX elements and build a PDF
'''

import docker
import os, os.path

IMAGE_NAME = 'kimvanwyk/pandoc:latest'
TEMPLATE='no_frills_latex.txt'

def build_pdf(file_in, template=TEMPLATE, image=IMAGE_NAME):
    client = docker.from_env()
    volumes = {}
    workdir = os.getcwd()
    volumes[workdir] = {'bind':'/io', 'mode':'rw'}
    (fn, ext) = os.path.splitext(file_in)
    tex_file = f"{fn}_orig.tex" 
    client.containers.run(IMAGE_NAME, command=f'-s -o {tex_file} --template={template} {file_in}',
                          volumes=volumes, auto_remove=True, stdin_open=True, stream=True, tty=True)

    out = []
    with open(tex_file, 'r') as fh:
        for l in fh:
            if "\\addcontentsline{toc}" in l:
                continue
            for (src, rep) in (('\\begin{longtable}[c]', '\\begin{longtable}[l]'),
                               ('\\toprule', ''),
                               ('\\bottomrule', '')):
                l = l.replace(src, rep)
            out.append(l)

    tex_file_mod = f"{fn}.tex"
    with open(tex_file_mod, 'w') as fh:
        fh.write(''.join(out))

    client.containers.run(IMAGE_NAME, command=f'{tex_file_mod}', entrypoint='pdflatex',
                          volumes=volumes, auto_remove=True, stdin_open=True, stream=True, tty=True)

build_pdf("output.txt")
