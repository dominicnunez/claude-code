# Snapshot file
# Unset all aliases to avoid conflicts with functions
unalias -a 2>/dev/null || true
# Functions
# Shell Options
shopt -u autocd
shopt -u assoc_expand_once
shopt -u cdable_vars
shopt -u cdspell
shopt -u checkhash
shopt -u checkjobs
shopt -s checkwinsize
shopt -s cmdhist
shopt -u compat31
shopt -u compat32
shopt -u compat40
shopt -u compat41
shopt -u compat42
shopt -u compat43
shopt -u compat44
shopt -s complete_fullquote
shopt -u direxpand
shopt -u dirspell
shopt -u dotglob
shopt -u execfail
shopt -u expand_aliases
shopt -u extdebug
shopt -u extglob
shopt -s extquote
shopt -u failglob
shopt -s force_fignore
shopt -s globasciiranges
shopt -s globskipdots
shopt -u globstar
shopt -u gnu_errfmt
shopt -u histappend
shopt -u histreedit
shopt -u histverify
shopt -s hostcomplete
shopt -u huponexit
shopt -u inherit_errexit
shopt -s interactive_comments
shopt -u lastpipe
shopt -u lithist
shopt -u localvar_inherit
shopt -u localvar_unset
shopt -s login_shell
shopt -u mailwarn
shopt -u no_empty_cmd_completion
shopt -u nocaseglob
shopt -u nocasematch
shopt -u noexpand_translation
shopt -u nullglob
shopt -s patsub_replacement
shopt -s progcomp
shopt -u progcomp_alias
shopt -s promptvars
shopt -u restricted_shell
shopt -u shift_verbose
shopt -s sourcepath
shopt -u varredir_close
shopt -u xpg_echo
set -o braceexpand
set -o hashall
set -o interactive-comments
set -o monitor
set -o onecmd
shopt -s expand_aliases
# Aliases
# Check for rg availability
if ! command -v rg >/dev/null 2>&1; then
  alias rg='/nix/store/fiy0cy0zki3mpxj441584q9hqxmx8p5w-ripgrep-14.1.1/bin/rg'
fi
export PATH=/tmp/tmp.Mp8Zdd8Ggw\:/nix/store/0flj33q30lmzdjagwjqh964qmiyklww2-patchelf-0.15.0/bin\:/nix/store/a0d7m3zn9p2dfa1h7ag9h2wzzr2w25sn-gcc-wrapper-14.2.1.20250322/bin\:/nix/store/6i862vz60awrlsila8vw18rg4d4l66iy-gcc-14.2.1.20250322/bin\:/nix/store/y2xdxp8r4g92q28am6mbxj44rivnyirl-glibc-2.40-66-bin/bin\:/nix/store/mp7ba85zcqdj2sqwa29pql02s6nqpcxy-coreutils-9.7/bin\:/nix/store/2gkh9v7wrzjq6ws312c6z6ajwnjvwcmb-binutils-wrapper-2.44/bin\:/nix/store/mkvc0lnnpmi604rqsjdlv1pmhr638nbd-binutils-2.44/bin\:/nix/store/k4fpgv6wd9gwpbs9fvr7x919243yhf7g-nodejs-22.16.0-dev/bin\:/nix/store/a1kxazxkgw7mjbjgisvah95p1r3n5ykl-nodejs-22.16.0/bin\:/nix/store/mp7ba85zcqdj2sqwa29pql02s6nqpcxy-coreutils-9.7/bin\:/nix/store/7fjnb79r7p38piiyn5xwgcj5w7fpfi02-findutils-4.10.0/bin\:/nix/store/1pi99mlqimxmqm1jvllbcaj8v16w2nbv-diffutils-3.12/bin\:/nix/store/x23s7lcvhf18zz3rj543680jgrj71vil-gnused-4.9/bin\:/nix/store/8b4vn1iyn6kqiisjvlmv67d1c0p3j6wj-gnugrep-3.11/bin\:/nix/store/n8825s8qprf8p70m0hq6pz7rvlnsxdjm-gawk-5.3.2/bin\:/nix/store/7nilh5hvnfbsx3vn020pkjkgx9rgsizb-gnutar-1.35/bin\:/nix/store/gqpd9ax2s6jjf7mjyv1q7bwbsycyaxic-gzip-1.14/bin\:/nix/store/28z6bx9sg0lsr7wra22pbjsk6fzfphy4-bzip2-1.0.8-bin/bin\:/nix/store/8dl5ryfna3hjqhvnkw7srm6wnka6agxl-gnumake-4.4.1/bin\:/nix/store/ih68ar79msmj0496pgld4r3vqfr7bbin-bash-5.2p37/bin\:/nix/store/kc8h52p4dfgajrg3qlgx246hl0znr213-patch-2.7.6/bin\:/nix/store/cmv326slnswzsjm2sqgbz16hzzqvkfjy-xz-5.8.1-bin/bin\:/nix/store/v5skl3bspzhm2y13vcxcrw8w29g6phi0-file-5.45/bin\:/home/aural/Code/bigmeanie/.direnv/bin\:/run/user/1000/fnm_multishells/31191_1754531824712/bin\:/run/wrappers/bin\:/run/wrappers/bin\:/home/aural/.nix-profile/bin\:/nix/profile/bin\:/home/aural/.local/state/nix/profile/bin\:/etc/profiles/per-user/aural/bin\:/nix/var/nix/profiles/default/bin\:/run/current-system/sw/bin\:/home/aural/go/bin\:/home/aural/.cargo/bin\:/home/aural/.nix-profile/bin\:/nix/profile/bin\:/home/aural/.local/state/nix/profile/bin\:/etc/profiles/per-user/aural/bin\:/nix/var/nix/profiles/default/bin\:/run/current-system/sw/bin\:/home/aural/go/bin\:/home/aural/.cargo/bin\:/home/aural/.npm-global/bin\:/home/aural/.local/bin
