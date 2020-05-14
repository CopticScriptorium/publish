"""Script to get fresh gold parses from UD_Coptic repo"""

import io, sys, os, re, shutil
from paths import ud_dir

script_dir = os.path.dirname(os.path.realpath(__file__))
PY3 = sys.version_info[0] == 3


def adjust_name(doc):
    doc = doc.replace("1Corinthians", "1Cor").replace("MONB_", "")
    doc = re.sub("^(XH|YA|XL|GF)_", r"\1", doc)
    doc = doc.replace("YA421", "a22.YA421")
    return doc


def get_gold_parses(gold_dir=None, treebank_dir=None):
    if treebank_dir is None:
        treebank_dir = ud_dir
    if not treebank_dir.endswith(os.sep):
        treebank_dir += os.sep

    if gold_dir is None:
        gold_dir = script_dir + "gold_parses" + os.sep
    if not os.path.exists(gold_dir):
        os.mkdir(gold_dir)
    else:
        shutil.rmtree(gold_dir)
        os.mkdir(gold_dir)

    files = ["cop_scriptorium-ud-train.conllu", "cop_scriptorium-ud-dev.conllu", "cop_scriptorium-ud-test.conllu"]
    files = [treebank_dir + f for f in files]

    for file_ in files:
        lines = io.open(file_, encoding="utf8").read().replace("\r", "").strip().split("\n")

        outhandle = None
        for line in lines:
            if "newdoc" in line:
                docparts = line.strip().split(":")
                docname = docparts[1]
                docname = adjust_name(docname)
                outhandle = io.open(gold_dir + docname + ".conll10", "w", encoding="utf8", newline="\n")
            elif "\t" in line:
                fields = line.split("\t")
                if "-" in fields[0]:  # Skip supertokens
                    continue
                fields[5] = fields[1]  # Duplicate tok into morph to create norm annotation
                if PY3:
                    outhandle.write("\t".join(fields) + "\n")
                else:
                    outhandle.write(unicode(("\t".join(fields) + "\n")))
            elif len(line) == 0:
                if PY3:
                    outhandle.write("\n")
                else:
                    outhandle.write(unicode("\n"))


if __name__ == "__main__":
    get_gold_parses()
