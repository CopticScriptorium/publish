"""
Script to fix common namespace conversion inconsistencies in Pepper relANNIS output
"""

import io, re, os
from shutil import move


def process_file(fname, outname, reps):
    with io.open(fname, encoding="utf8") as f:
        lines = f.readlines()
        with io.open(outname, "w", encoding="utf8", newline="\n") as o:
            for line in lines:
                line = line.strip() + "\n"
                for rep in reps:
                    line = line.replace(rep[0], rep[1])
                if line.endswith("\ttranslation\n"):
                    if re.match("[0-9]+\tscriptorium\ttranslation", line) is not None:
                        continue
                o.write(line)


def process_dir(dirname, corpus=None, test=False):
    ext = "annis"

    reps = {
        "node_anno": [
            ("\tdefault_ns\tentity", "\tcoref\tentity"),
            ("\tdefault_ns\ttype", "\tcoref\ttype"),
            ("\tsalt\t", "\tscriptorium\t"),
            ("\tdefault_ns\t", "\tscriptorium\t"),
        ],
        "component": [("scriptorium\tdep", "dep\tdep")],
    }

    if not dirname.endswith(os.sep):
        dirname += os.sep

    process_file(dirname + "node_annotation." + ext, dirname + "node_annotation_fixed." + ext, reps["node_anno"])
    process_file(dirname + "component." + ext, dirname + "component_fixed." + ext, reps["component"])
    os.remove(dirname + "component." + ext)
    os.remove(dirname + "node_annotation." + ext)
    move(dirname + "component_fixed." + ext, dirname + "component." + ext)
    move(dirname + "node_annotation_fixed." + ext, dirname + "node_annotation." + ext)

    if test:
        reps = [(corpus + "\t", corpus + "_test" + "\t")]
        process_file(dirname + "corpus." + ext, dirname + "corpus_fixed." + ext, reps)
        process_file(dirname + "resolver_vis_map." + ext, dirname + "resolver_vis_map_fixed." + ext, reps)
        os.remove(dirname + "resolver_vis_map." + ext)
        os.remove(dirname + "corpus." + ext)
        move(dirname + "corpus_fixed." + ext, dirname + "corpus." + ext)
        move(dirname + "resolver_vis_map_fixed." + ext, dirname + "resolver_vis_map." + ext)


if __name__ == "__main__":

    ext = "annis"

    reps = {
        "node_anno": [("\tsalt\t", "\tscriptorium\t"), ("\tdefault_ns\t", "\tscriptorium\t")],
        "component": [("scriptorium\tdep", "dep\tdep")],
    }

    process_file("node_annotation." + ext, "node_annotation_fixed." + ext, reps["node_anno"])
    process_file("component." + ext, "component_fixed." + ext, reps["component"])
