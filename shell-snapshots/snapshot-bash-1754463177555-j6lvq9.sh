# Snapshot file
# Unset all aliases to avoid conflicts with functions
unalias -a 2>/dev/null || true
shopt -s expand_aliases
# Check for rg availability
if ! command -v rg >/dev/null 2>&1; then
  alias rg='/nix/store/1ijacjhy42pqx7vfi5mnsqrps2k3b8xf-ripgrep-14.1.1/bin/rg'
fi
export PATH=/tmp/tmp.pXPvIbylAW\:/run/user/1000/fnm_multishells/45277_1754458097963/bin\:/run/wrappers/bin\:/home/aural/.nix-profile/bin\:/nix/profile/bin\:/home/aural/.local/state/nix/profile/bin\:/etc/profiles/per-user/aural/bin\:/nix/var/nix/profiles/default/bin\:/run/current-system/sw/bin
