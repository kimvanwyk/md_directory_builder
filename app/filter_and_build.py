""" Filter out undesired LaTeX elements and build a PDF
"""

import docker

import os, os.path
import re

IMAGE_NAME = "kimvanwyk/pandoc:latest"
# IMAGE_NAME = "registry.gitlab.com/kimvanwyk/document-containers/pandoc"
TEMPLATE = "no_frills_latex.txt"


def build_pdf(file_in, title, compiled, template=TEMPLATE, image=IMAGE_NAME):
    client = docker.from_env()
    volumes = {}
    workdir = os.getcwd()
    volumes[workdir] = {"bind": "/io", "mode": "rw"}
    (fn, ext) = os.path.splitext(file_in)
    tex_file = f"{fn}_orig.tex"

    client.containers.run(
        IMAGE_NAME,
        command=f'-s -o {tex_file} -V title="{title}" -V compiled="{compiled}" --toc --template={template} {file_in}',
        volumes=volumes,
        auto_remove=True,
        stdin_open=True,
        stream=True,
        tty=False,
    )

    out = []
    with open(tex_file, "r") as fh:
        text = fh.read()
        for (pat, rep) in (
            (r"\begin{longtable}[c]", r"\begin{longtable}[l]"),
            ("\\toprule\n", ""),
            ("xxSI", "Served In"),
            ("~", r"\ "),
            ("\\bottomrule\n", ""),
            ("\\hspace*{0.333em}\n", ""),
            (r"\strut\end{minipage}", ""),
            (r"\\" + "\n\n", "\n\n"),
        ):

            text = text.replace(pat, rep)

        for (pat, rep) in (
            (r"\\addcontentsline.*?" + "\n", ""),
            (r"\\begin\{minipage\}.*?\\strut" + "\n", ""),
        ):
            (text, count) = re.subn(pat, rep, text)

    tex_file_mod = f"{fn}.tex"
    with open(tex_file_mod, "w") as fh:
        fh.write(text)

    for _ in range(3):
        client.containers.run(
            IMAGE_NAME,
            command=f"{tex_file_mod}",
            entrypoint="pdflatex",
            volumes=volumes,
            auto_remove=True,
            stdin_open=True,
            stream=True,
            tty=False,
        )


if __name__ == "__main__":
    build_pdf("output.txt")
