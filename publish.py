from argparse import ArgumentParser
from shutil import copy, rmtree, copytree
from collections import defaultdict
from glob import glob
import requests, sys, io, os, re, shutil
from zipfile import ZipFile, ZIP_DEFLATED
from pepper_runner import run_pepper
from fix_scriptorium_annis_corpus import process_dir as fix_annis_ns
from reorder_sgml import reorder
from process_conll import get_gold_parses, sgml2conll, treebank_docs
from config import aliases, multi_aliases, pub_corpora, default_vis, no_chapter_corpora

# from hotfixes import apply_hotfixes
from paths import coptic_nlp_path, ud_dir, gitdox_url, gitdox_user, gitdox_pass, gitdox_cookie

PY3 = sys.version_info[0] == 3

script_dir = os.path.dirname(os.path.realpath(__file__)) + os.sep
data_dir = script_dir + "data" + os.sep

sys.path = [script_dir + os.sep + ".." + os.sep + "coptic-nlp"] + sys.path

if not os.path.exists(data_dir):
    os.makedirs(data_dir)

if not coptic_nlp_path.endswith(os.sep):
    coptic_nlp_path += os.sep

sys.path.insert(0, coptic_nlp_path)
sys.path.insert(0, coptic_nlp_path + "lib" + os.sep)
from coptic_nlp import nlp_coptic
from mwe import add_mwe_to_sgml


class Token:

    def __init__(self, xml_id, word, pos, func, parent):
        self.xml_id = xml_id
        self.word = word
        self.pos = pos
        self.func = func
        self.parent = int(parent.replace("u",""))

    def __repr__(self):
        return self.word + " (" + self.pos + "/" + self.func + ") <- " + str(self.parent)


class Entity:

    def __init__(self,tokens,ent_type):
        tokens.sort(key=lambda x: int(x.xml_id.replace("u","")))
        self.tokens = tokens
        self.type = ent_type
        self.start = int(tokens[0].xml_id.replace("u",""))
        self.end = int(tokens[-1].xml_id.replace("u",""))
        self.length = self.end - self.start + 1
        self.text = " ".join([t.word for t in tokens])
        self.head_token = None

    def __repr__(self):
        return self.text + " (" + str(self.start) + "-" + str(self.end) + ")"


def write_temp_files(zipfile, corpus, ext, suffix, meta, folder="_tmp"):

    if not ext.startswith("."):
        ext = "." + ext
    if not suffix.endswith(os.sep):
        suffix = suffix + os.sep

    if not os.path.exists(folder):
        os.makedirs(folder)

    files = [f for f in zipfile.namelist()]
    for filename in files:
        docname = filename
        if filename.endswith(".tt"):
            docname = filename[:-3]
        elif filename.endswith(".xml"):
            docname = filename[:-4]
        elif filename.endswith(".sgml"):
            docname = filename[:-5]

        if PY3:
            contents = io.TextIOWrapper(zipfile.open(filename), encoding="utf8").read()
        else:
            contents = zipfile.open(filename).read()

        if filename.startswith("_meta"):
            meta[corpus] = contents
        else:
            if not os.path.exists(folder + os.sep + corpus + suffix):
                os.makedirs(folder + os.sep + corpus + suffix)
            with io.open(folder + os.sep + corpus + suffix + docname + ext, "w", encoding="utf8", newline="\n") as f:
                f.write(contents)


def validate_sgml(sgml, docname):
    err = False
    if "pb_xml:id" in sgml:
        sys.stderr.write(" ! Found pb_xml:id in doc " + docname + "!\n")
        err = True
    if "xml:lang" in sgml:
        sys.stderr.write(" ! Found xml:lang in doc " + docname + "!\n")
        err = True
    if "<TEI" in sgml:
        sys.stderr.write(" ! Found <TEI> tag" + docname + "!\n")
        err = True
    if err:
        sys.stderr.write(" ! Aborting...")
        sys.exit()


def get(attr, line):
    return re.search(" " + attr + '="([^"]*)"', line).group(1)


def assign_entity_heads(sgml):
    def light_head_search(ent,head_position):
        light_heads = ["ⲛⲟϭ","ϩⲁϩ"]
        if ent.tokens[head_position].word in light_heads:
            light_head = ent.tokens[head_position]
            for tok in ent.tokens:
                if tok.func=="nmod" and tok.parent == int(light_head.xml_id.replace("u","")):
                    return tok
        return ent.tokens[head_position]

    def get_entity_head(ent,minimal_covering):
        head = ent.tokens[0]  # Default response
        for tok in ent.tokens:  # First minimally covered proper noun is the head
            if tok.pos == "NPROP":
                if tok in minimal_covering:
                    if minimal_covering[tok] == ent:
                        return tok
        for i, tok in enumerate(ent.tokens):
            if tok.func=="punct":
                continue
            # Non punct root or token dominated from outside the span is the head
            elif tok.parent == 0 or (tok.parent>0 and (tok.parent < ent.start or tok.parent > ent.end)):
                return light_head_search(ent,i)  # Check for ⲛⲟϭ, ϩⲁϩ etc.
        return head

    lines = sgml.strip().split("\n")
    words = {}
    entity_stack = []
    entities = []
    covering = defaultdict(set)
    minimal_covering = {}
    lines2ents = {}
    counter = 0
    norm = pos = func = xml_id = parent = ""

    # Pass 1 - collect data
    for l, line in enumerate(lines):
        if ' norm=' in line:
            norm = get("norm",line)
        if ' pos=' in line:
            pos = get("pos",line)
        if ' func=' in line:
            func = get("func",line)
        if ' xml:id=' in line:
            xml_id = get("xml:id",line)
        if ' head=' in line:
            parent = get("head",line).replace("#","")
        if "</norm>" in line:
            if func == "root" or func == "punct":
                parent = "0"
            words[xml_id] = Token(xml_id,norm,pos,func,parent)
            counter += 1
        if ' entity="' in line:
            ent_type = get("entity",line)
            #entity_starts[counter + 1].append(ent_type)
            entity_stack.append((ent_type,counter+1,l))
        if '</entity>' in line:
            ent_type, ent_start, start_line = entity_stack.pop()
            ids = ["u" + str(i) for i in list(range(ent_start,counter+1))]
            tokens = [words[i] for i in ids]
            ent = Entity(tokens, ent_type)
            entities.append(ent)
            lines2ents[start_line] = ent
            for tok in tokens:
                covering[tok].add(ent)

    # Identify semantic heads
    for tid in words:
        tok = words[tid]
        if tok in covering:
            minimal_covering[tok] = min(covering[tok],key=lambda x: x.length)

    for ent in entities:
        ent.head_token = get_entity_head(ent,minimal_covering)

    # Pass 2: assign heads
    output = []
    for l, line in enumerate(lines):
        if l in lines2ents:
            ent = lines2ents[l]
            head = "#" + ent.head_token.xml_id
            text = ent.text
            insertion = ' head_tok="'+head+'" text="'+ text + '"'
            if not "head_tok=" in line:
                line = line.replace(" entity",insertion + " entity")
        output.append(line)

    return "\n".join(output).strip() + "\n"


p = ArgumentParser()
p.add_argument("corpora", help="comma separated list of corpus names")
p.add_argument("-s", "--status", default=None, help="restrict documents by comma separated list of statuses")
p.add_argument("-n", dest="no_pepper", action="store_true", help="No pepper conversion, just download TT and TEI")
p.add_argument("-m", "--multiword", action="store_true", help="Add multiword expressions")
p.add_argument("-p", "--parse", action="store_true", help="Add parse")
p.add_argument("-t", "--test", action="store_true", help="Name ANNIS corpus *_test for pre-release test")
p.add_argument("-c", "--cache", action="store_true", help="Use cached zips instead of downloading from GitDox")
p.add_argument("-z", "--zip", action="store_true", help="Create zip of ANNIS corpora to upload / import in ANNIS")
p.add_argument("-v", "--verbose", action="store_true", help="Verbose Pepper output (for debugging)")
p.add_argument("--vis", default="generic", choices=["generic", "coref", "bible", "budge"], help="ANNIS vis")
p.add_argument("--gold_dir", default="gold_parses", help="Directory to store gold parses in")

opts = p.parse_args()

use_cache = opts.cache

# Step 1 - download corpora as TT SGML and TEI from GitDox

corpora = opts.corpora
if corpora in multi_aliases:
    corpora = multi_aliases[corpora]

corpora = corpora.split(",")
resolved = []
for corpus in corpora:
    if corpus.lower() in aliases:
        resolved.append(aliases[corpus.lower()])
    else:
        resolved.append(corpus)
corpora = resolved

for corpus in corpora:
    if corpus not in pub_corpora:
        sys.stderr.write("! corpus not listed in config.py/pub_corpora: " + corpus + "\n")
        sys.exit(0)

# Clean out _tmp directory
if os.path.exists("_tmp"):
    rmtree("_tmp")

meta = {}  # Dictionary from corpus name to tab delimited corpus metadata key-value pairs string
no_tei = False

if not use_cache:
    gitdox = gitdox_url

    params = {"login": "loginnojs", "username": gitdox_user, "pass": gitdox_pass, "action": "EMPTY_VAL_MJF"}
    tt_params = {"extension": "tt", "stylesheet": "tt_sgml", "docs": "--ALL--"}
    tei_params = {"extension": "xml", "stylesheet": "scriptorium_tei", "docs": "--ALL--"}

    if opts.status is not None:
        params["status"] = opts.status
    else:
        params["status"] = "--ALL--"

    if len(corpora) > 1:
        sys.stderr.write("Downloading corpora from GitDox:\n")
    else:
        sys.stderr.write("Downloading corpus from GitDox:\n")

    sess_cookie = gitdox_cookie

    # Start a session so we can have persistant cookies
    session = requests.session()  # config={'verbose': sys.stderr}

    for corpus in corpora:
        if corpus == "sahidica.nt" or corpus == "sahidic.ot":
            sys.stderr.write("! Attempted to publish "+corpus+" but not from cache!")
            quit()
        current_params = params

        sys.stderr.write(" o " + corpus + "... ")

        # Get TT
        current_params.update(tt_params)

        if "treebank" in corpus:
            current_params["docs"] = ",".join(treebank_docs)
            current_params["no_corpus_name"] = True
        else:
            current_params["corpus"] = corpus

        zip_tt = session.get(gitdox + "export.py", params=current_params, cookies=sess_cookie, stream=True)#, verify=False)
        with io.open(data_dir + corpus + "_tt.zip", "wb") as f:
            for chunk in zip_tt.iter_content(chunk_size=512):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)

        sys.stderr.write("Got TT ")

        # Get TEI
        if corpus in no_chapter_corpora:
            tei_params["stylesheet"] = "scriptorium_tei_p"
        else:
            tei_params["stylesheet"] = "scriptorium_tei"

        current_params.update(tei_params)
        if "treebank" in corpus:
            current_params["docs"] = ",".join(treebank_docs)
            current_params["no_corpus_name"] = True
        else:
            current_params["corpus"] = corpus

        zip_tei = session.get(gitdox + "export.py", params=current_params, cookies=sess_cookie, stream=True)#, verify=False)
        with io.open(data_dir + corpus + "_tei.zip", "wb") as f:
            for chunk in zip_tei.iter_content(chunk_size=512):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)

        sys.stderr.write("+ TEI\n")

        # Open zip file handles
        zip_tt = ZipFile(data_dir + corpus + "_tt.zip")
        zip_tei = ZipFile(data_dir + corpus + "_tei.zip")

        # Step 2 - copy releasable TT and TEI files to temp folder

        write_temp_files(zip_tt, corpus, ".tt", "_TT", meta)
        write_temp_files(zip_tei, corpus, ".xml", "_TEI", meta)

        zip_tt.close()
        zip_tei.close()

else:

    if len(corpora) > 1:
        sys.stderr.write("Getting corpora from cache:\n")
    else:
        sys.stderr.write("Getting corpus from cache:\n")

    for corpus in corpora:
        sys.stderr.write(" o " + corpus + "... ")

        # Get TT
        zip_tt = ZipFile(data_dir + corpus + "_tt.zip")
        sys.stderr.write("Got TT ")

        # Get TEI
        try:
            zip_tei = ZipFile(data_dir + corpus + "_tei.zip")
            sys.stderr.write("+ TEI\n")
        except FileNotFoundError:
            sys.stderr.write("! No TEI data in cache, skipping TEI\n")
            no_tei = True

        # Step 2 - copy releasable TT and TEI files to temp folder

        write_temp_files(zip_tt, corpus, ".tt", "_TT", meta)
        if not no_tei:
            write_temp_files(zip_tei, corpus, ".xml", "_TEI", meta)


# Step 3 - add missing NLP categories

gold_dir = opts.gold_dir
if gold_dir[-1] != os.sep:
    gold_dir += os.sep

if opts.parse:
    get_gold_parses(gold_dir=gold_dir, treebank_dir=ud_dir)

for corpus in corpora:
    tt_files = glob("_tmp" + os.sep + corpus + "_TT" + os.sep + "*.tt")
    if len(tt_files) == 0:
        sys.stderr.write(" ! Found zero files... Aborting\n")
        sys.exit(0)
    sys.stderr.write(" o Running NLP...\n")
    for tt_file in tt_files:
        docname = os.path.basename(tt_file).replace(".tt", "")
        sys.stderr.write("   o Doc: " + docname + " ")
        sgml = io.open(tt_file, encoding="utf8").read()
        validate_sgml(sgml, docname)
        if opts.multiword:
            sys.stderr.write("+mwe ")
            sgml = add_mwe_to_sgml(sgml)
        if opts.parse:
            gold_parse = ""
            gold_file = ""
            if os.path.isdir(gold_dir):
                if os.path.isfile(gold_dir + docname + ".conll10"):
                    gold_file = gold_dir + docname + ".conll10"
                elif os.path.isfile(gold_dir + docname + ".conllu"):
                    gold_file = gold_dir + docname + ".conllu"
                elif os.path.isfile(gold_dir + docname.replace("-", "_") + ".conll10"):
                    gold_file = gold_dir + docname.replace("-", "_") + ".conll10"
                if gold_file != "":
                    gold_parse = io.open(gold_file, encoding="utf8").read()
            sys.stderr.write("+parse ")
            if gold_parse != "":
                sys.stderr.write("(gold) ")
            if "translation=" not in sgml and gold_parse == "":
                sys.stderr.write(
                    "\n! You selected parsing based on translation spans but there are no translation annotations in "
                    + docname
                    + "\n"
                )
                sys.exit()
            sgml = nlp_coptic(
                sgml,
                do_tok=False,
                sgml_mode="sgml",
                sent_tag="translation",
                pos_spans=True,
                merge_parse=True,
                preloaded={"stk": "", "xrenner": "", "parser":None},
                do_milestone=False,
                do_norm=False,
                do_tag=False,
                gold_parse=gold_parse,
                docname=docname
            )

        sgml = reorder(sgml,["meta","p_n","pb_xml_id","cb_n","lb_n","verse_n","translation","orig_group","norm_group","entity","orig","norm","lemma","pos","lang","morph","tok"])
        # Remove old static coref from AP and redundant func elements
        sgml = re.sub(r'</?(coref|func)[^\n]+\n','',sgml,flags=re.MULTILINE)
        # Remove multiple and trailing spaces in translations
        sgml = re.sub(r'(<translation translation="[^\n"]*?)  +',r'\1 ',sgml)
        sgml = re.sub(r'(<translation translation="[^\n"]*?)  +',r'\1 ',sgml)
        sgml = re.sub(r'(<translation translation="[^\n"]*?) +">',r'\1">',sgml)
        sgml = assign_entity_heads(sgml)
        # sgml = apply_hotfixes(sgml)

        processed_dir = "_tmp" + os.sep + corpus + "_processed"
        if not os.path.exists(processed_dir):
            os.makedirs(processed_dir)

        with io.open(processed_dir + os.sep + docname + ".tt", "w", encoding="utf8", newline="\n") as f:
            f.write(sgml.strip() + "\n")
        sys.stderr.write("\n")

# Step 4 - convert TT SGML to PAULA and relANNIS
pepper_home = "pepper" + os.sep
pepper_tmp = pepper_home + "tmp" + os.sep

if opts.no_pepper:
    sys.stderr.write("\ni Skipping Pepper conversion\n")
else:
    sys.stderr.write("\nStarting pepper conversion:\n" + "=" * 30 + "\n")

    if os.path.exists(pepper_tmp + os.sep):
        rmtree(pepper_tmp + os.sep)
    os.makedirs(pepper_tmp)

    example_queries = {}
    examples = (
        io.open(pepper_home + "annis_templates" + os.sep + "example_queries_all.txt", encoding="utf8").read().strip()
    )
    all_corpora = examples.split("***")
    for corpus_spec in all_corpora:
        if len(corpus_spec.strip()) > 0:
            name, queries = re.split("===+", corpus_spec)
            example_queries[name.strip()] = queries.strip() + "\n"

    for corpus in corpora:
        # Create Pepper staging area in pepper/tmp/

        if os.path.exists(pepper_tmp + corpus + os.sep):
            rmtree(pepper_tmp + corpus + os.sep)
        os.makedirs(pepper_tmp + corpus)

        sys.stderr.write(" o converting corpus: " + corpus)
        tt_files = glob("_tmp" + os.sep + corpus + "_processed" + os.sep + "*.tt")
        for file_ in tt_files:
            copy(file_, pepper_tmp + corpus + os.sep)

        try:
            pepper_params = (
                io.open("pepper" + os.sep + "convert_scriptorium.pepperparams", encoding="utf8")
                .read()
                .replace("\r", "")
            )
        except:
            sys.__stdout__.write(
                "x Can't find pepper template at: pepper"
                + os.sep
                + "convert_scriptorium.pepperparams"
                + "\n  Aborting..."
            )
            sys.exit()

        # Inject gum_target in pepper_params and replace os.sep with URI slash
        pepper_params = pepper_params.replace("**tt_in**", os.path.abspath(pepper_tmp + corpus).replace(os.sep, "/"))
        pepper_params = pepper_params.replace(
            "**paula_out**", os.path.abspath(pepper_tmp + corpus + "_PAULA").replace(os.sep, "/")
        )
        pepper_params = pepper_params.replace(
            "**annis_out**", os.path.abspath(pepper_tmp + corpus + "_ANNIS").replace(os.sep, "/")
        )

        # Setup corpus metadata file
        if corpus in meta:
            with io.open(
                pepper_tmp + corpus + os.sep + corpus + ".meta", "w", encoding="utf8", newline="\n"
            ) as meta_out:
                meta_out.write(meta[corpus])

        out = run_pepper(pepper_params, full_log=opts.verbose)
        sys.stderr.write(out + "\n")

        # Setup ANNIS visualizations
        if corpus in default_vis:
            vis = default_vis[corpus]
        else:
            vis = opts.vis

        # Generate appropriate resolver_vis_map.annis
        resolver_vis_map = "resolver_vis_map_" + vis + ".annis"
        resolver_vis_map = io.open(pepper_home + "annis_templates" + os.sep + resolver_vis_map, encoding="utf8").read()
        resolver_vis_map = resolver_vis_map.replace("**corpus**", corpus)
        with io.open(
            pepper_tmp + corpus + "_ANNIS" + os.sep + "resolver_vis_map.annis", "w", encoding="utf8", newline="\n"
        ) as f:
            f.write(resolver_vis_map)

        # Generate appropriate HTML visualizers in ExtData
        copytree(
            pepper_home + "annis_templates" + os.sep + "ExtData_" + vis,
            pepper_tmp + corpus + "_ANNIS" + os.sep + "ExtData",
        )

        # Fix default_ns and salt ns in node_annotation.annis and component.annis
        # If --test options is on, append _test to corpus name
        fix_annis_ns(pepper_tmp + corpus + "_ANNIS" + os.sep, corpus=corpus, test=opts.test)

        # Generate example_queries.annis
        if corpus in example_queries:
            with io.open(
                pepper_tmp + corpus + "_ANNIS" + os.sep + "example_queries.annis", "w", encoding="utf8", newline="\n"
            ) as f:
                f.write(example_queries[corpus])
        else:
            sys.stderr.write(
                " ! No example queries found for corpus "
                + corpus
                + " in "
                + pepper_home
                + "annis_templates"
                + os.sep
                + "example_queries_all.txt\n"
            )


# Step 5 - move everything to git folder for public release

for corpus in corpora:
    if not opts.no_pepper:
        if os.path.exists(pub_corpora["base"] + pub_corpora[corpus] + corpus + "_ANNIS"):
            rmtree(pub_corpora["base"] + pub_corpora[corpus] + corpus + "_ANNIS")
        copytree(pepper_tmp + corpus + "_ANNIS", pub_corpora["base"] + pub_corpora[corpus] + corpus + "_ANNIS")
        if os.path.exists(pub_corpora["base"] + pub_corpora[corpus] + corpus + "_PAULA"):
            rmtree(pub_corpora["base"] + pub_corpora[corpus] + corpus + "_PAULA")
        copytree(
            pepper_tmp + corpus + "_PAULA" + os.sep + corpus,
            pub_corpora["base"] + pub_corpora[corpus] + corpus + "_PAULA",
        )
    if os.path.exists(pub_corpora["base"] + pub_corpora[corpus] + corpus + "_TT"):
        rmtree(pub_corpora["base"] + pub_corpora[corpus] + corpus + "_TT")
    copytree("_tmp" + os.sep + corpus + "_processed", pub_corpora["base"] + pub_corpora[corpus] + corpus + "_TT")
    if not no_tei:
        if os.path.exists(pub_corpora["base"] + pub_corpora[corpus] + corpus + "_TEI"):
            rmtree(pub_corpora["base"] + pub_corpora[corpus] + corpus + "_TEI")
        copytree("_tmp" + os.sep + corpus + "_TEI", pub_corpora["base"] + pub_corpora[corpus] + corpus + "_TEI")
    # Make conllu version
    tt_files = glob(pub_corpora["base"] + pub_corpora[corpus] + corpus + "_TT" + os.sep + "*.tt")
    conll_dir = pub_corpora["base"] + pub_corpora[corpus] + corpus + "_CONLLU"
    if os.path.exists(conll_dir):
        rmtree(conll_dir)
    os.makedirs(conll_dir)
    for file_ in tt_files:
        docname = os.path.basename(file_).replace(".tt","")
        conll = sgml2conll(io.open(file_,encoding="utf8").read(), docname, corpus)
        with io.open(conll_dir + os.sep + docname + ".conllu", 'w', encoding="utf8", newline="\n") as f:
            f.write(conll)

    # Zip PAULA data and remove non-zipped files
    if not opts.no_pepper:
        paula_path = pub_corpora["base"] + pub_corpora[corpus] + corpus + "_PAULA"
        files = glob(paula_path + os.sep + "**" + os.sep + "*.*", recursive=True)
        files = [f for f in files if not f.endswith(".zip")]  # Filter out zips in case stale archive file is found
        archive_files = [f.replace(paula_path + os.sep, corpus + os.sep) for f in files]
        outzip = ZipFile(paula_path + os.sep + corpus + "_PAULA.zip", "w", ZIP_DEFLATED)
        for i, f in enumerate(files):
            outzip.write(f, archive_files[i])
        outzip.close()
        for filename in os.listdir(paula_path):
            file_path = os.path.join(paula_path, filename)
            try:
                if os.path.isfile(file_path) and not file_path.endswith(".zip"):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

    if opts.zip:
        rel_annis_path = pub_corpora["base"] + pub_corpora[corpus] + corpus + "_ANNIS"
        files = glob(rel_annis_path + os.sep + "**" + os.sep + "*.*", recursive=True)
        files = [f for f in files if not f.endswith(".zip")]  # Filter out zips in case stale archive file is found
        archive_files = [f.replace(rel_annis_path + os.sep, "") for f in files]
        outzip = ZipFile(rel_annis_path + os.sep + corpus + ".zip", "w", ZIP_DEFLATED)
        for i, f in enumerate(files):
            outzip.write(f, archive_files[i])
        outzip.close()
        sys.stderr.write("\n o created ANNIS zip for import: " + corpus + ".zip\n")
