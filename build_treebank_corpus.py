import io, os, sys, re, shutil
from paths import ud_dir, pub_corpora_dir
from zipfile import ZipFile
from glob import glob

pub_corpora = {}
pub_corpora["apophthegmata.patrum"] = "AP"
pub_corpora["sahidica.mark"] = "sahidica.mark"
pub_corpora["sahidica.1corinthians"] = "sahidica.1corinthians"
pub_corpora["shenoute.abraham"] = "abraham"
pub_corpora["shenoute.a22"] = "shenoute-a22"
pub_corpora["shenoute.eagerness"] = "shenoute-eagerness"
pub_corpora["shenoute.dirt"] = "shenoute-dirt"
pub_corpora["shenoute.fox"] = "shenoute-fox"
pub_corpora["besa.letters"] = "besa-letters"
pub_corpora["johannes.canons"] = "johannes-canons"
pub_corpora["doc.papyri"] = "doc-papyri"
pub_corpora["pseudo.ephrem"] = "pseudo-ephrem"
pub_corpora["dormition.john"] = "dormition-john"
pub_corpora["proclus.homilies"] = "proclus-homilies"
pub_corpora["life.cyrus"] = "life-cyrus"
pub_corpora["life.onnophrius"] = "life-onnophrius"
pub_corpora["life.longinus.lucius"] = "life-longinus-lucius"
pub_corpora["life.aphou"] = "life-aphou"
pub_corpora["life.phib"] = "life-phib"
pub_corpora["life.paul.tamma"] = "life-paul-tamma"
pub_corpora["instructions.pachomius"] = "instructions-pachomius"
pub_corpora["martyrdom.victor"] = "martyrdom-victor"
pub_corpora["pseudo.athanasius.discourses"] = "pseudo-athanasius-discourses"
pub_corpora["pseudo.flavianus"] = "pseudo-flavianus"

def doc2file(doc):
	doc = doc.replace("1Corinthians","1Cor").replace("MONB_","")
	doc = re.sub("^(XH|YA|XL|GF)_",r'\1',doc)
	doc = re.sub("([0-9])_([0-9])",r'\1-\2',doc)
	if not "a22" in doc:
		doc = doc.replace("YA421","a22.YA421")
	return doc

def resolve_corpus(corpus):
	global pub_corpora
	if corpus in pub_corpora:
		corpus = pub_corpora[corpus]
	return corpus

def unravel_norm(sgml):
	lines = sgml.split("\n")
	key_val = {}
	keep = ['norm','pos','lemma','lang','func']
	output = []
	for line in lines:
		if "<norm " in line:
			key_val = {}
			attrs = re.findall(r'([^\s=]+)="([^"]*)"',line)
			for key, val in attrs:
				if key in keep:
					key_val[key] = val
			for key in sorted(list(key_val.keys())):
				val = key_val[key]
				output.append("<" +key + ' ' + key + '="'+val+'">')
		elif "</norm>" in line:
			for key in sorted(list(key_val.keys()),reverse=True):
				output.append("</" +key +'>')
		else:
			output.append(line)
	return "\n".join(output)


# Get document list
if not ud_dir.endswith(os.sep):
	ud_dir += os.sep
ud_files = ["cop_scriptorium-ud-train.conllu","cop_scriptorium-ud-dev.conllu","cop_scriptorium-ud-test.conllu"]
ud_files = [ud_dir + f for f in ud_files]

tb_text = ""
for f in ud_files:
	tb_text += io.open(f,encoding="utf8").read()

docnames = re.findall("# newdoc id = (.+):([^\s]+)",tb_text)

# Get SGML for each document
staging_dir = "treebank_staging" + os.sep
if os.path.exists(staging_dir):
	shutil.rmtree(staging_dir)
os.makedirs(staging_dir)

if not pub_corpora_dir.endswith(os.sep):
	pub_corpora_dir += os.sep

data_dir = "data" + os.sep

for corpus, doc in docnames:
	pub_corpus = resolve_corpus(corpus)
	sgml_dir = pub_corpora_dir + pub_corpus + os.sep + corpus + "_TT" + os.sep
	sgml = io.open(sgml_dir + doc2file(doc) + ".tt",encoding="utf8").read()
	sgml = unravel_norm(sgml)
	with io.open(staging_dir+doc2file(doc) + ".tt",'w',encoding="utf8",newline="\n") as f:
		f.write(sgml)

# Created zips
files = glob(staging_dir + os.sep + "*.tt")
archive_files = [f.replace("treebank_staging"+os.sep,"") for f in files]
outzip = ZipFile(data_dir + os.sep + "coptic.treebank_tt.zip",'w')
for i, f in enumerate(files):
	outzip.write(f,archive_files[i])
outzip.close()
shutil.copy(data_dir + os.sep + "coptic.treebank_tt.zip",data_dir + os.sep + "coptic.treebank_tei.zip")
sys.stderr.write("\n o created zip for publishing: coptic-treebank_tt.zip\n")

