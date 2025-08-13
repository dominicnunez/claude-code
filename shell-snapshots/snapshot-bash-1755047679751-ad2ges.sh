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
  alias rg='/nix/store/rdadzfbkr2dm5nsfgw56x6h3vy4zyw6v-ripgrep-14.1.1/bin/rg'
fi
export PATH=/tmp/tmp.HrJ3J7447B\:/run/user/1000/fnm_multishells/33160_1754968417422/bin\:/run/wrappers/bin\:/run/wrappers/bin\:/home/aural/.nix-profile/bin\:/nix/profile/bin\:/home/aural/.local/state/nix/profile/bin\:/etc/profiles/per-user/aural/bin\:/nix/var/nix/profiles/default/bin\:/run/current-system/sw/bin\:/home/aural/go/bin\:/home/aural/.cargo/bin\:/home/aural/.nix-profile/bin\:/nix/profile/bin\:/home/aural/.local/state/nix/profile/bin\:/etc/profiles/per-user/aural/bin\:/nix/var/nix/profiles/default/bin\:/run/current-system/sw/bin\:/home/aural/go/bin\:/home/aural/.cargo/bin\:/home/aural/.npm-global/bin\:/home/aural/.local/bin
