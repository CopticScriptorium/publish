import os
from collections import defaultdict

aliases = {"ap":"apophthegmata.patrum",
		   "mark":"sahidica.mark",
		   "1cor":"sahidica.1corinthians",
		   "aof":"shenoute.abraham",
		   "abraham":"shenoute.abraham",
		   "fox":"shenoute.fox",
		   "nbfb":"shenoute.fox",
		   "a22":"shenoute.a22",
		   "those":"shenoute.those",
		   "seeks":"shenoute.seeks",
		   "unknown":"shenoute.unknown5_1",
		   "eagerness": "shenoute.eagerness",
		   "besa":"besa.letters",
		   "victor":"martyrdom.victor",
		   "johannes":"johannes.canons",
		   "ephraim":"pseudo.ephrem",
		   "ephrem":"pseudo.ephrem",
		   "athanasius":"pseudo.athanasius.discourses",
		   "repose":"dormition.john",
		   "dormition":"dormition.john",
		   "pap":"doc.papyri",
		   "papyri":"doc.papyri",
		   "proclus":"proclus.homilies",
		   "cyrus":"life.cyrus",
		   "onno":"life.onnophrius",
		   "onnophrius":"life.onnophrius",
		   "dirt":"shenoute.dirt",
		   "phib":"life.phib",
		   "aphou":"life.aphou",
		   "pachomius":"pachomius.instructions",
		   "tamma":"life.paul.tamma",
		   "big":"paul.big",
		   "longinus":"life.longinus.lucius",
		   "treebank":"coptic.treebank"}

pub_corpora = {}
pub_corpora["base"] = "C:\\uni\\Coptic\\git\\corpora\\pub_corpora\\"
pub_corpora["apophthegmata.patrum"] = "AP" + os.sep
pub_corpora["sahidica.mark"] = "sahidica.mark" + os.sep
pub_corpora["sahidica.1corinthians"] = "sahidica.1corinthians" + os.sep
pub_corpora["shenoute.abraham"] = "abraham" + os.sep
pub_corpora["shenoute.a22"] = "shenoute-a22" + os.sep
pub_corpora["shenoute.eagerness"] = "shenoute-eagerness" + os.sep
pub_corpora["shenoute.dirt"] = "shenoute-dirt" + os.sep
pub_corpora["shenoute.fox"] = "shenoute-fox" + os.sep
pub_corpora["shenoute.seeks"] = "shenoute-seeks" + os.sep
pub_corpora["shenoute.those"] = "shenoute-those" + os.sep
pub_corpora["besa.letters"] = "besa-letters" + os.sep
pub_corpora["johannes.canons"] = "johannes-canons" + os.sep
pub_corpora["doc.papyri"] = "doc-papyri" + os.sep
pub_corpora["pseudo.ephrem"] = "pseudo-ephrem" + os.sep
pub_corpora["dormition.john"] = "dormition-john" + os.sep
pub_corpora["proclus.homilies"] = "proclus-homilies" + os.sep
pub_corpora["life.cyrus"] = "life-cyrus" + os.sep
pub_corpora["life.onnophrius"] = "life-onnophrius" + os.sep
pub_corpora["life.longinus.lucius"] = "life-longinus-lucius" + os.sep
pub_corpora["life.aphou"] = "life-aphou" + os.sep
pub_corpora["life.phib"] = "life-phib" + os.sep
pub_corpora["life.paul.tamma"] = "life-paul-tamma" + os.sep
pub_corpora["pachomius.instructions"] = "pachomius-instructions" + os.sep
pub_corpora["pseudo.athanasius.discourses"] = "pseudo-athanasius-discourses" + os.sep
pub_corpora["martyrdom.victor"] = "martyrdom-victor" + os.sep
pub_corpora["shenoute.unknown5_1"] = "shenoute-unknown5_1" + os.sep

pub_corpora["coptic.treebank"] = "coptic-treebank" + os.sep

default_vis = defaultdict(lambda: "generic")
default_vis["apophthegmata.patrum"] = "coref"
default_vis["sahidica.mark"] = "bible"
default_vis["sahidica.1corinthians"] = "bible"
default_vis["martyrdom.victor"] = "budge"
default_vis["pseudo.ephrem"] = "budge"
default_vis["dormition.john"] = "budge"
default_vis["proclus.homilies"] = "budge"
default_vis["life.cyrus"] = "budge"
default_vis["life.onnophrius"] = "budge"
default_vis["besa.letters"] = "besa"
default_vis["shenoute.eagerness"] = "p"
default_vis["life.phib"] = "budge_p"
default_vis["life.aphou"] = "budge_p"
default_vis["life.paul.tamma"] = "budge_p"
default_vis["paul.big"] = "budge_p"
default_vis["pachomius.instructions"] = "budge_p"
default_vis["pseudo.athanasius.discourses"] = "budge_p"
default_vis["life.longinus.lucius"] = "budge_p"

# Corpora to export TEI for with scriptorium_tei_p (since they currently have no chapter_n annotation)
no_chapter_corpora = ["shenoute.eagerness",
					  "life.phib",
					  "life.paul.tamma",
					  "paul.big",
					  "life.aphou",
					  "life.longinus.lucius"]