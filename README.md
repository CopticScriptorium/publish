# Publish - Coptic Scriptorium Publication Bot

One stop shop for publishing Coptic Scriptorium data from a GitDox installation to a GitHub repo and ANNIS server.

## Usage

```
usage: publish.py [-h] [-s STATUS] [-n] [-m] [-p] [-t] [-c] [-z] [-v]
                  [--vis {generic,coref,bible,budge}] [--gold_dir GOLD_DIR]
                  corpora

positional arguments:
  corpora               comma separated list of corpus names

optional arguments:
  -h, --help            show this help message and exit
  -s STATUS, --status STATUS
                        restrict documents by comma separated list of statuses
  -n                    No pepper conversion, just download TT and TEI
  -m, --multiword       Add multiword expressions
  -p, --parse           Add parse
  -t, --test            Name ANNIS corpus *_test for pre-release test
  -c, --cache           Use cached zips instead of downloading from GitDox
  -z, --zip             Create zip of ANNIS corpora to upload / import in
                        ANNIS
  -v, --verbose         Verbose Pepper output (for debugging)
  --vis {generic,coref,bible,budge}
                        ANNIS vis
  --gold_dir GOLD_DIR   Directory with gold parses to use if available;
                        default is ud_dir from paths.py
  ```

For example, to verbosely publish all documents with the statuses 'to_publish' and 'published' in apophthegmata.patrum and besa.letters, adding mwes and parses (gold if available), creating a zip for ANNIS use:

`python publish.py -mpvz -s to_publish,published apophthegmata.patrum,besa.letters`

Note that `GOLD_DIR` defaults to `ud_dir`. Corpus names are ideally either ANNIS corpus names (besa.letters), or folder names from CopticScriptorium/Corpora (besa-letters), but the bot is fairly creative in using substrings and some known aliases (e.g. "fox", "nbfb", "shenoute.f" all match `shenoute.fox`, "mark" matches `sahidica.mark`, etc.) - see config.py for some supported aliases.

## Installation

The publication bot requires three further repos to be cloned on an accessible path:

  * https://github.com/CopticScriptorium/corpora - the path to existing publicly published Scriptorium data, referred to as `pub_corpora`
  * https://github.com/CopticScriptorium/Coptic-NLP - the Coptic NLP pipeline referred to as `coptic_nlp_path`
  * https://github.com/UniversalDependencies/UD_Coptic-Scriptorium - the repository for the Coptic Universal Dependencies treebank referred to as `ud_dir`

For these repos, consider using the dev branch for the freshest data, or revert to master if unstable. The publication bot also requires access to a GitDox server, including valid credentials and a browser cookie. This allows it retrieve fresh data directly from GitDox annotations

## Configuration

The bot uses a global path and cookie configuration in `paths.py`. To set up the bot please specify:

  * `coptic_nlp_path` - the path to a clone of the Coptic-NLP repo
  * `ud_dir` - the path to a clone of UD_Coptic-Scriptorium
  * `pub_corpora` - the path to a clone of CopticScriptorium/Corpora

You will also need to set up GitDox credentials, including harvesting a cookie from a browser after a successful login to GitDox:

  * `gitdox_url` - the URL of your GitDox interface
  * `gitdox_user` - a valid user name for that interface
  * `gitdox_pass` - the password for the user
  * `gitdox_cookie` - cookie dictionary containing values for `userid`, `_fbp`, `_ga`. These do not expire, so they only need to be set up once for a GitDox installation.
  
