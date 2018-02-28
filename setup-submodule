#!/bin/sh

# Install git hooks
installHooks() {
    SOURCE_DIR=`dirname $0`/githooks
    HOOKS=`ls ${SOURCE_DIR}`
    HOOK_DIR=`git rev-parse --show-toplevel`/.git/hooks

    for hook in $HOOKS; do
        # If the hook already exists, is executable, and is not a symlink
        # Note: local hook won't be run.
        if [ ! -h $HOOK_DIR/$hook -a -x $HOOK_DIR/$hook ]; then
            mv $HOOK_DIR/$hook $HOOK_DIR/$hook.local
        fi
        # create the symlink, overwriting the file if it exists
        ln -s -f $SOURCE_DIR/$hook $HOOK_DIR/$hook
    done
}


installTool() {
    ln -s -f `dirname $0`/tool ./tool
}

installTornadoToolset() {
    pip3 install -e .
}


read -p "Setup tornado project at $(pwd) ?[y/N]" yn
if [ $yn == 'y' ] || [ $yn == 'Y' ]; then
    installHooks || exit 1
    installTool || exit 1
    installTornadoToolset || exit 1
    echo "success."
else
    echo "quit."
    exit 1
fi
