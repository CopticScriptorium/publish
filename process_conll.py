"""Script to get fresh gold parses from UD_Coptic repo"""

import io, sys, os, re, shutil
from paths import ud_dir
from depedit import DepEdit
from collections import defaultdict

script_dir = os.path.dirname(os.path.realpath(__file__))
PY3 = sys.version_info[0] == 3

treebank_docs = [
    "a22.YA421-428",
    "AP.023.isaac-cells.07",
    "AP.024.isaac-cells.07",
    "AP.025.isaac-cells.12",
    "AP.026.cassian.07",
    "1Cor_01",
    "1Cor_02",
    "1Cor_03",
    "1Cor_04",
    "1Cor_05",
    "1Cor_06",
    "on_vigilance",
    "on_lack_of_food",
    "martyrdom.victor.01",
    "XL93-94",
    "YA518-520",
    "AP.027.pistamon.01",
    "AP.028.serapion.02",
    "AP.029.syncletica.05",
    "AP.030.hyperechios.06",
    "AP.031.philagrios.01",
    "AP.032.benjamin.05",
    "Mark_01",
    "Mark_02",
    "Mark_03",
    "Mark_04",
    "Mark_05",
    "Mark_06",
    "Mark_07",
    "Mark_08",
    "Mark_09",
    "to_thieving_nuns",
    "exhortations",
    "life.cyrus.01",
    "XH204-216",
    "GF31-32",
    "AP.001.n135.mother",
    "AP.002.n136.account",
    "AP.003.n138.blame",
    "AP.004.poemen.65",
    "AP.005.unid.senses",
    "AP.006.n196.worms",
    "AP.018.n372.anger",
    "AP.019.n161.presbyter",
    "AP.114.theophilus.02",
    "AP.116.pistus.01",
    "AP.117.Sisoes.09",
    "AP.118.Sisoes.11",
    "AP.119.Sisoes.16",
    "AP.120.sisoes.13",
    "AP.121.syncletica.26",
    "AP.122.n667.humility",
    "AP.123.syncletica.11",
    "AP.124.orsisius.01",
    "AP.125.orsisius.01",
    "AP.126.n132.pigs",
    "AP.127.n298.demon",
    "AP.128.n299.arrogance",
    "AP.129.n331.humility",
    "AP.130.n300.glory",
    "AP.131.n301.joshua",
    "AP.132.n302.armor",
    "AP.133.n303.words",
    "AP.134.n304.humility",
    "AP.135.n305.blame",
    "AP.136.unid.humility",
    "AP.137.p.263",
    "AP.138.unid.soil",
    "AP.139.n306.dog",
    "to_aphthonia",
    "life.onnophrius.01",
    "psephrem.letter",
    "psflavianus.encomium.01",
    "dormition.john.mercad",
    "mercy_judgment",
    "Ruth_01",
    "Ruth_02",
    "Ruth_03",
    "Ruth_04",
    "proclus.13.easter"
]


def sgml2conll(sgml, doc, corpus):
    def lang2iso(lang):
        if lang == "Hebrew":
            return "he"
        elif lang == "Greek":
            return "grc"
        elif lang == "Latin":
            return "la"
        elif lang == "Egyptian":
            return "egy"
        elif lang == "Akkadian":
            return "akk"
        elif lang == "Aramaic":
            return "arc"
        elif lang == "Persian":
            return "peo"
        else:
            raise IOError("Uknnown language code: " + lang + "\n")

    def get(attr, line):
        return re.search(" " + attr + '="([^"]*)"', line).group(1)

    def make_sent(sent, sent_num, text, trans):
        sid = "# sent_id = " + corpus + "-" + doc + "_" + make_sid(sent_num)
        sid = sid.replace(".", "_")
        s_text = "# text = " + " ".join(text)
        trans = trans.replace("&apos;", "'")
        sent = [sid, s_text, "# text_en = " + trans] + sent + [""]
        return sent

    """Take a TT SGML file including parses and create Scriptorium-style CoNLLU"""
    # See if we have sentence spans in treebank
    get_gold_parses()
    norms = sgml.count("</norm>")
    trans = sgml.count("</translation>")
    do_trans = False
    break_indices = set([])

    if os.path.exists(script_dir + "gold_parses" + os.sep + doc + ".conll10"):
        conll10 = io.open(script_dir + "gold_parses" + os.sep + doc + ".conll10", encoding="utf8").read()
        sents = conll10.strip().count("\n\n") + 1
        toks = len(re.findall(r"^[0-9]+\t", conll10, flags=re.MULTILINE))

        if trans == sents:
            do_trans = True
        else:
            debug_trans = "\n".join([line for line in sgml.split("\n") if "translation translation=" in line])
            debug_sents = "\n".join([re.sub(r"[0-9]+\t([^\t]+)[^ ]+",r"\1",re.sub(r"\n"," ",s)) for s in conll10.strip().split("\n\n")])
        if toks == norms:  # Counts match, can use sentence splits from treebank
            counter = 1
            sents = conll10.strip().split("\n\n")
            for sent in sents:
                counter += len(re.findall(r"^[0-9]+\t", sent, flags=re.MULTILINE))
                break_indices.add(counter)
    else:
        sys.stderr.write("WARN: no gold parse for document " + doc + "\n")

    groups = {}
    entity_starts = defaultdict(list)
    entity_ends = defaultdict(list)
    entity_single = {}
    entity_stack = []
    norms = []
    langs = []
    lang = ""
    counter = 0
    start = 1
    ent_start = 1
    lines = sgml.split("\n")
    # First pass - get bound groups and entities
    for l, line in enumerate(lines):
        if "ϩⲁⲣⲙⲁ" in line:
            a = 3
        if " norm_group=" in line:
            start = counter + 1
        if "</norm_group>" in line:
            end = counter
            groups[start] = (end, "".join(norms))
            norms = []
        if ' entity="' in line:
            ent_type = get("entity", line)
            ident = ""
            if " identity=" in line:
                ident = get("identity",line).replace(" ","_").replace("(","%28").replace(")","%29")
            entity_starts[counter + 1].append((ent_type,ident))
            entity_stack.append((ent_type, counter + 1, ident))
        if " lang=" in line:
            lang = get("lang",line)
        if "</norm>" in line:
            langs.append(lang)
            lang = ""
        if "</entity>" in line:
            ent_type, ent_start, ident = entity_stack.pop()
            if ent_start < counter:
                entity_ends[counter].append((ent_type,ident))
            else:
                entity_single[counter] = (ent_type,ident)
                # Now remove a single occurrence of this entity type from entity_starts
                prev_len = len(entity_starts[counter])
                entity_starts[counter].remove((ent_type,ident))
                assert len(entity_starts[counter]) == prev_len - 1
        if " norm=" in line:
            norm = get("norm", line)
            norms.append(norm)
            counter += 1

    # output = ["# newdoc id = " + corpus + ":" + conllize_name(doc)]
    output = ["# newdoc id = " + corpus + ":" + doc]
    sent_tag = "translation" if "</translation>" in sgml else "verse_n"
    tok = xml_id = head = sent_num = 1
    offset = 0
    trans = ""
    orig = word = pos = lemma = func = ""
    sent = []
    morphs = []
    text = []
    for line in lines:
        if ' norm="' in line:
            word = get("norm", line)
        if ' orig="' in line:
            orig = get("orig", line)
        if ' pos="' in line:
            pos = get("pos", line)
        if " lemma=" in line:
            lemma = get("lemma", line)
        if " morph=" in line:
            morphs.append(get("morph", line))
        if " func=" in line:
            func = get("func", line)
            if func == "root":
                head = 0
        if " head=" in line:
            head = int(get("head", line).replace("#", "").replace("u", "")) - offset
        elif " func=" in line:  # item has function but not head -> is a root
            head = 0
        if " xml:id=" in line and ' norm=' in line:  # Avoid other xml:id, e.g. on <pb> element
            xml_id = int(get("xml:id", line).replace("u", ""))
        if "</norm>" in line:
            misc = []
            if len(morphs) > 0:
                misc.append("Morphs=" + "-".join(morphs))
            if orig != word:
                misc.append("Orig=" + orig)
            ent_list = []
            if xml_id in entity_single:
                ent_type, ident = entity_single[xml_id]
                ent_string = ent_type if len(ident) == 0 else "-".join([ent_type,ident])
                ent_list.append("(" + ent_string + ")")
            if xml_id in entity_ends:
                for (ent_type, ident) in entity_ends[xml_id]:
                    ent_string = ent_type if len(ident) == 0 else "-".join([ent_type, ident])
                    ent_list.append(ent_string + ")")
            if xml_id in entity_starts:
                for (ent_type,ident) in entity_starts[xml_id]:
                    ent_string = ent_type if len(ident) == 0 else "-".join([ent_type, ident])
                    ent_list.append("(" + ent_string)
            if len(ent_list) > 0:
                misc.append("Entity=" + "".join(ent_list))
            if langs[tok-1] != "":
                misc.append("OrigLang=" + lang2iso(langs[tok-1]))

            misc = "|".join(sorted(misc))
            if misc == "":
                misc = "_"
            if xml_id in groups:
                end, supertok = groups[xml_id]
                if end > xml_id:
                    sent.append("\t".join([str(xml_id - offset) + "-" + str(end - offset), supertok] + ["_"] * 8))
                text.append(supertok)
            upos = make_upos(pos, func)
            cols = [str(tok - offset), word, lemma, upos, pos, "_", str(head), func, "_", misc]
            sent.append("\t".join(cols))
            tok += 1
            morphs = []
        if "<" + sent_tag in line:
            if " translation=" in line:
                trans = get("translation", line)
            else:
                trans = "..."
        if len(break_indices) > 0:
            if tok in break_indices:  # New sentence
                if trans == "" or not do_trans:
                    trans = "..."
                if len(sent) > 0:
                    sent = make_sent(sent, sent_num, text, trans)
                    output += sent
                    offset = xml_id
                    sent = []
                    text = []
                    sent_num += 1
                    if len(break_indices) > 1:
                        break_indices.remove(tok)
        elif "</" + sent_tag in line:  # No treebank sentence spans, use translation spans
            sent = make_sent(sent, sent_num, text, trans)
            output += sent
            offset = xml_id
            sent = []
            text = []
            sent_num += 1
    conll = "\n".join(output) + "\n\n"
    d = DepEdit(
        io.open("C:\\Uni\\Coptic\\git\\corpora\\treebank-dev\\merge_scripts\\add_ud_morph.ini", encoding="utf8")
        .read()
        .split("\n")
    )
    conllu = d.run_depedit(conll.split("\n"))
    return conllu.strip() + "\n\n"


def adjust_name(doc):
    doc = doc.replace("1Corinthians", "1Cor").replace("MONB_", "")
    doc = re.sub("^(XH|YA|XL|GF)_", r"\1", doc)
    doc = re.sub("([A-Z]{2}[0-9]{1,3})_", r"\1-", doc)
    if "a22" not in doc:
        doc = doc.replace("YA421", "a22.YA421")
    return doc


def conllize_name(doc):
    doc = doc.replace("1Cor", "1Corinthians")
    if doc[:2] in ["XH", "YA", "XL", "GF"]:
        doc = "MONB_" + doc
    doc = re.sub("_(XH|YA|XL|GF)", r"_\1_", doc)
    doc = doc.replace("a22.YA", "YA")
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


def make_upos(cs_tag, func):
    out_tag = ""
    if cs_tag == "AAOR":
        out_tag = "AUX"
    if cs_tag == "ACAUS":
        out_tag = "VERB"
    if cs_tag == "ACOND":
        out_tag = "SCONJ"
    if cs_tag == "ACONJ":
        out_tag = "AUX"
    if cs_tag == "ADV":
        out_tag = "ADV"
    if cs_tag == "AFUTCONJ":
        out_tag = "AUX"
    if cs_tag == "AJUS":
        out_tag = "AUX"
    if cs_tag == "ALIM":
        out_tag = "SCONJ"
    if cs_tag == "ANEGAOR":
        out_tag = "AUX"
    if cs_tag == "ANEGJUS":
        out_tag = "AUX"
    if cs_tag == "ANEGOPT":
        out_tag = "AUX"
    if cs_tag == "ANEGPST":
        out_tag = "AUX"
    if cs_tag == "ANY":
        out_tag = "AUX"
    if cs_tag == "AOPT":
        out_tag = "AUX"
    if cs_tag == "APREC":
        out_tag = "SCONJ"
    if cs_tag == "APST":
        out_tag = "AUX"
    if cs_tag == "ART":
        out_tag = "DET"
    if cs_tag == "CCIRC":
        out_tag = "SCONJ"
    if cs_tag == "CFOC":
        out_tag = "PART"
    if cs_tag == "CONJ":
        if func == "mark":
            out_tag="SCONJ"
        else:
            out_tag = "CCONJ"
    if cs_tag == "COP":
        out_tag = "PRON"
    if cs_tag == "CPRET":
        out_tag = "AUX"
    if cs_tag == "CREL":
        out_tag = "SCONJ"
    if cs_tag == "EXIST":
        out_tag = "VERB"
    if cs_tag == "FM":
        out_tag = "X"
    if cs_tag == "FUT":
        out_tag = "AUX"
    if cs_tag == "IMOD":
        out_tag = "ADV"
    if cs_tag == "N":
        if func == "amod":
            out_tag = "ADJ"
        else:
            out_tag = "NOUN"
    if cs_tag == "NEG":
        out_tag = "ADV"
    if cs_tag == "NPROP":
        out_tag = "PROPN"
    if cs_tag == "NUM":
        out_tag = "NUM"
    if cs_tag == "PDEM":
        out_tag = "DET"
    if cs_tag == "PINT":
        out_tag = "PRON"
    if cs_tag == "PPERI":
        out_tag = "PRON"
    if cs_tag == "PPERO":
        out_tag = "PRON"
    if cs_tag == "PPERS":
        out_tag = "PRON"
    if cs_tag == "PPOS":
        out_tag = "DET"
    if cs_tag == "PREP":
        if func == "mark":
            out_tag = "PART"
        else:
            out_tag = "ADP"
    if cs_tag == "PTC":
        out_tag = "PART"
    if cs_tag == "PUNCT":
        out_tag = "PUNCT"
    if cs_tag == "UNKNOWN":
        out_tag = "X"
    if cs_tag == "FW":
        out_tag = "X"
    if cs_tag == "V":
        out_tag = "VERB"
    if cs_tag == "VBD":
        out_tag = "VERB"
    if cs_tag == "VIMP":
        out_tag = "VERB"
    if cs_tag == "VSTAT":
        out_tag = "VERB"
    if cs_tag.endswith("_PPERS"):
        out_tag = "PRON"
    if cs_tag.endswith("_PPERO"):
        out_tag = "PRON"
    if cs_tag == "_":  # supertoken
        out_tag = "_"
    if func == "aux":
        out_tag = "AUX"
    if cs_tag == "PINT" and func == "advmod":
        out_tag = "ADV"

    return out_tag


def make_sid(sent_num):
    sid = str(sent_num)
    if len(sid) == 1:
        sid = "s000" + sid
    elif len(sid) == 2:
        sid = "s00" + sid
    elif len(sid) == 3:
        sid = "s0" + sid
    else:
        sid = "s" + sid
    return sid


if __name__ == "__main__":
    # get_gold_parses()
    path = "C:\\Uni\\Coptic\\git\\corpora\\pub_corpora\\AP\\apophthegmata.patrum_TT\\AP.007.n139.laughing.tt"
    sgml = io.open(path, encoding="utf8",).read()
    conll = sgml2conll(sgml, "AP.007.n139.laughing", "apophthegmata.patrum")
    path = "C:\\Uni\\Coptic\\git\\corpora\\pub_corpora\\AP\\apophthegmata.patrum_TT\\AP.025.isaac-cells.12.tt"
    sgml = io.open(path, encoding="utf8",).read()
    # conll = sgml2conll(sgml, 'AP.025.isaac-cells.12', 'apophthegmata.patrum')
    print(conll)
