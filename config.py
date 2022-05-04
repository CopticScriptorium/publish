import os
from collections import defaultdict

multi_aliases = {"shenoute":"fox,a22,abraham,eagerness,seeks,those,unknown,dirt,night,prince",
				"marcion":"victor,ephrem,athanasius,dormition,proclus,cyrus,onno,pachomius,basil,pisentius,chrysostom,const,mysteries,john,timothy,asketikon,celestinus,flavianus,eustathius",
				"paths":"phib,aphou,tamma,longinus",
				 "bible":"mark,1cor,ruth",
				 "other":"besa,papyri,theophilus,johannes,ap,magic"}

aliases = {"ap":"apophthegmata.patrum",
		   "mark":"sahidica.mark",
		   "1cor":"sahidica.1corinthians",
		   "ruth":"sahidic.ruth",
		   "aof":"shenoute.abraham",
		   "abraham":"shenoute.abraham",
		   "eustathius":"life.eustathius.theopiste",
		   "theopiste":"life.eustathius.theopiste",
		   "fox":"shenoute.fox",
		   "nbfb":"shenoute.fox",
		   "a22":"shenoute.a22",
		   "those":"shenoute.those",
		   "night":"shenoute.night",
		   "seeks":"shenoute.seeks",
		   "unknown":"shenoute.unknown5_1",
		   "eagerness": "shenoute.eagerness",
		   "prince": "shenoute.prince",
		   "besa":"besa.letters",
		   "pistis":"pistis.sophia",
		   "victor":"martyrdom.victor",
		   "johannes":"johannes.canons",
		   "ephraim":"pseudo.ephrem",
		   "ephrem":"pseudo.ephrem",
		   "athanasius":"pseudo.athanasius.discourses",
		   "theophilus":"pseudo.theophilus",
		   "repose":"dormition.john",
		   "dormition":"dormition.john",
		   "pap":"doc.papyri",
		   "papyri":"doc.papyri",
		   "magic":"magical.papyri",
		   "mag":"magical.papyri",
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
		   "constantinople":"john.constantinople",
		   "const":"john.constantinople",
		   "basil":"pseudo.basil",
		   "asketikon":"pseudo.ephrem",
		   "celestinus":"pseudo.celestinus",
		   "flavianus":"pseudo.flavianus",
		   "timothy":"pseudo.timothy",
		   "abatton":"pseudo.timothy",
		   "chrysostom":"pseudo.chrysostom",
		   "chrys": "pseudo.chrysostom",
		   "mysteries":"mysteries.john",
		   "pisentius": "life.pisentius",
		   "john": "life.john.kalybites",
		   "kalybites": "life.john.kalybites",
		   "treebank":"coptic.treebank",
		   "ot":"sahidic.ot",
		   "nt":"sahidica.nt",
		   "sahidica":"sahidica.nt"}

pub_corpora = {}
pub_corpora["base"] = "C:\\uni\\Coptic\\git\\corpora\\pub_corpora\\"
pub_corpora["apophthegmata.patrum"] = "AP" + os.sep
pub_corpora["sahidica.mark"] = "sahidica.mark" + os.sep
pub_corpora["sahidica.nt"] = "sahidica.nt" + os.sep  # From cache!
pub_corpora["sahidic.ot"] = "sahidic.ot" + os.sep  # From cache!
pub_corpora["sahidic.ruth"] = "sahidic.ruth" + os.sep
pub_corpora["sahidica.1corinthians"] = "sahidica.1corinthians" + os.sep
pub_corpora["shenoute.abraham"] = "abraham" + os.sep
pub_corpora["shenoute.a22"] = "shenoute-a22" + os.sep
pub_corpora["shenoute.eagerness"] = "shenoute-eagerness" + os.sep
pub_corpora["shenoute.dirt"] = "shenoute-dirt" + os.sep
pub_corpora["shenoute.fox"] = "shenoute-fox" + os.sep
pub_corpora["shenoute.seeks"] = "shenoute-seeks" + os.sep
pub_corpora["shenoute.those"] = "shenoute-those" + os.sep
pub_corpora["shenoute.prince"] = "shenoute-prince" + os.sep
pub_corpora["besa.letters"] = "besa-letters" + os.sep
pub_corpora["johannes.canons"] = "johannes-canons" + os.sep
pub_corpora["doc.papyri"] = "doc-papyri" + os.sep
pub_corpora["magical.papyri"] = "magical-papyri" + os.sep
pub_corpora["pseudo.ephrem"] = "pseudo-ephrem" + os.sep
pub_corpora["dormition.john"] = "dormition-john" + os.sep
pub_corpora["proclus.homilies"] = "proclus-homilies" + os.sep
pub_corpora["life.cyrus"] = "life-cyrus" + os.sep
pub_corpora["life.onnophrius"] = "life-onnophrius" + os.sep
pub_corpora["life.longinus.lucius"] = "life-longinus-lucius" + os.sep
pub_corpora["life.aphou"] = "life-aphou" + os.sep
pub_corpora["life.phib"] = "life-phib" + os.sep
pub_corpora["life.pisentius"] = "life-pisentius" + os.sep
pub_corpora["life.john.kalybites"] = "life-john-kalybites" + os.sep
pub_corpora["john.constantinople"] = "john-constantinople" + os.sep
pub_corpora["mysteries.john"] = "mysteries-john" + os.sep
pub_corpora["pseudo.timothy"] = "pseudo-timothy" + os.sep
pub_corpora["pseudo.chrysostom"] = "pseudo-chrysostom" + os.sep
pub_corpora["pseudo.basil"] = "pseudo-basil" + os.sep
pub_corpora["pseudo.flavianus"] = "pseudo-flavianus" + os.sep
pub_corpora["pseudo.celestinus"] = "pseudo-celestinus" + os.sep
pub_corpora["pistis.sophia"] = "pistis-sophia" + os.sep
pub_corpora["life.eustathius.theopiste"] = "life-eustathius-theopiste" + os.sep
pub_corpora["life.paul.tamma"] = "life-paul-tamma" + os.sep
pub_corpora["pachomius.instructions"] = "pachomius-instructions" + os.sep
pub_corpora["pseudo.athanasius.discourses"] = "pseudo-athanasius-discourses" + os.sep
pub_corpora["pseudo.theophilus"] = "pseudo-theophilus" + os.sep
pub_corpora["martyrdom.victor"] = "martyrdom-victor" + os.sep
pub_corpora["shenoute.unknown5_1"] = "shenoute-unknown5_1" + os.sep
pub_corpora["shenoute.night"] = "shenoute-night" + os.sep

pub_corpora["coptic.treebank"] = "coptic-treebank" + os.sep

default_vis = defaultdict(lambda: "generic")
#default_vis["apophthegmata.patrum"] = "coref"
default_vis["sahidica.mark"] = "bible"
default_vis["sahidica.1corinthians"] = "bible"
default_vis["sahidic.ruth"] = "bible"
default_vis["pistis.sophia"] = "widepage"
default_vis["sahidica.nt"] = "bible"  # From cache!
default_vis["sahidic.ot"] = "bible"  # From cache!
default_vis["martyrdom.victor"] = "budge"
default_vis["pseudo.ephrem"] = "budge"
default_vis["dormition.john"] = "budge"
default_vis["proclus.homilies"] = "budge"
default_vis["life.cyrus"] = "budge"
default_vis["life.onnophrius"] = "budge"
default_vis["life.pisentius"] = "budge"
default_vis["life.john.kalybites"] = "budge"
default_vis["life.eustathius.theopiste"] = "budge"
default_vis["pseudo.timothy"] = "budge"
default_vis["john.constantinople"] = "budge"
default_vis["mysteries.john"] = "budge"
default_vis["psephrem.asketikon"] = "budge"
default_vis["pseudo.basil"] = "budge"
default_vis["shenoute.night"] = "budge"
default_vis["pseudo.chrysostom"] = "budge"
default_vis["pseudo.flavianus"] = "budge"
default_vis["pseudo.celestinus"] = "budge"
default_vis["besa.letters"] = "besa"
default_vis["shenoute.eagerness"] = "p"
default_vis["life.phib"] = "budge_p"
default_vis["life.aphou"] = "budge_p"
default_vis["life.paul.tamma"] = "budge_p"
default_vis["paul.big"] = "budge_p"
default_vis["pachomius.instructions"] = "budge_p"
default_vis["pseudo.athanasius.discourses"] = "budge_p"
default_vis["life.longinus.lucius"] = "budge_p"

# Corpora to export TEI for with scriptorium_tei_p (since they currently have no chapter_n annotation or they have meaningful p's like besa)
no_chapter_corpora = ["shenoute.eagerness",
					  "life.phib",
					  "life.paul.tamma",
					  "paul.big",
					  "besa.letters",
					  "life.aphou",
					  "life.longinus.lucius"]