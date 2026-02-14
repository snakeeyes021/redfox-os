# Tilix VTE Integration for Fish
# Emits OSC 7 sequences to tell the terminal the current directory

# Only run if we are inside Tilix
if set -q TILIX_ID || set -q VTE_VERSION
    # Function to emit the OSC 7 code with the current hostname and path
    # Triggered automatically whenever $PWD changes
    function __vte_osc7 --on-variable PWD
        printf "\033]7;file://%s%s\033" (hostname) (string escape --style=url $PWD)
    end

    # Run it once immediately so the initial directory is tracked
    __vte_osc7
end
