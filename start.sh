#!/bin/bash
#swannybot
export DENO_INSTALL="/$HOME/.deno"
export PATH="$DENO_INSTALL/bin:$PATH"
cd /swannybot/ && python3 swanny_bot.py