from argparse import ArgumentParser
from shutil import copy, rmtree, copytree
from glob import glob
import requests, sys, io, os, re
from zipfile import ZipFile
from pepper_runner import run_pepper
from fix_scriptorium_annis_corpus import process_dir as fix_annis_ns
from split_conllu2conll10 import get_gold_parses
from config import aliases, pub_corpora, default_vis, no_chapter_corpora

# from hotfixes import apply_hotfixes
from paths import coptic_nlp_path, ud_dir, gitdox_url, gitdox_user, gitdox_pass, gitdox_cookie

PY3 = sys.version_info[0] == 3

script_dir = os.path.dirname(os.path.realpath(__file__)) + os.sep
data_dir = script_dir + "data" + os.sep

if not os.path.exists(data_dir):
    os.makedirs(data_dir)

if not coptic_nlp_path.endswith(os.sep):
    coptic_nlp_path += os.sep

sys.path.insert(0, coptic_nlp_path)
sys.path.insert(0, coptic_nlp_path + "lib" + os.sep)
from coptic_nlp import nlp_coptic
from mwe import add_mwe_to_sgml


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
p.add_argument("--gold_dir", default=None, help="Directory with gold parses to use if available; default is ud_dir from paths.py")

opts = p.parse_args()

use_cache = opts.cache

# Step 1 - download corpora as TT SGML and TEI from GitDox

corpora = opts.corpora.split(",")
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
        current_params = params
        current_params["corpus"] = corpus

        sys.stderr.write(" o " + corpus + "... ")

        # Get TT
        current_params.update(tt_params)

        zip_tt = session.get(gitdox + "export.py", params=current_params, cookies=sess_cookie, stream=True)
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

        zip_tei = session.get(gitdox + "export.py", params=current_params, cookies=sess_cookie, stream=True)
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
        zip_tei = ZipFile(data_dir + corpus + "_tei.zip")
        sys.stderr.write("+ TEI\n")

        # Step 2 - copy releasable TT and TEI files to temp folder

        write_temp_files(zip_tt, corpus, ".tt", "_TT", meta)
        write_temp_files(zip_tei, corpus, ".xml", "_TEI", meta)


# Step 3 - add missing NLP categories

if opts.multiword or opts.parse:

    gold_dir = opts.gold_dir
    if gold_dir is None:
        gold_dir = ud_dir
    if gold_dir[-1] != os.sep:
        gold_dir += os.sep

    if opts.parse:
        get_gold_parses(gold_dir=gold_dir)

    for corpus in corpora:
        tt_files = glob("_tmp" + os.sep + corpus + "_TT" + os.sep + "*.tt")
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
                    preloaded={"stk": None, "xrenner": None},
                    do_milestone=False,
                    do_norm=False,
                    do_tag=False,
                    gold_parse=gold_parse,
                )

            # sgml = apply_hotfixes(sgml)

            processed_dir = "_tmp" + os.sep + corpus + "_processed"
            if not os.path.exists(processed_dir):
                os.makedirs(processed_dir)

            with io.open(processed_dir + os.sep + docname + ".tt", "w", encoding="utf8", newline="\n") as f:
                f.write(sgml.strip() + "\n")
            sys.stderr.write("\n")
else:
    for corpus in corpora:
        processed_dir = "_tmp" + os.sep + corpus + "_processed"
        if os.path.exists(processed_dir):
            rmtree(processed_dir)
        copytree("_tmp" + os.sep + corpus + "_TT", "_tmp" + os.sep + corpus + "_processed")


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
                + "example_queries_all.txt"
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
    if os.path.exists(pub_corpora["base"] + pub_corpora[corpus] + corpus + "_TEI"):
        rmtree(pub_corpora["base"] + pub_corpora[corpus] + corpus + "_TEI")
    copytree("_tmp" + os.sep + corpus + "_TEI", pub_corpora["base"] + pub_corpora[corpus] + corpus + "_TEI")

    if opts.zip:
        rel_annis_path = pub_corpora["base"] + pub_corpora[corpus] + corpus + "_ANNIS"
        files = glob(rel_annis_path + os.sep + "**" + os.sep + "*.*", recursive=True)
        files = [f for f in files if not f.endswith(".zip")]  # Filter out zips in case stale archive file is found
        archive_files = [f.replace(rel_annis_path + os.sep, "") for f in files]
        outzip = ZipFile(rel_annis_path + os.sep + corpus + ".zip", "w")
        for i, f in enumerate(files):
            outzip.write(f, archive_files[i])
        outzip.close()
        sys.stderr.write("\n o created ANNIS zip for import: " + corpus + ".zip\n")
