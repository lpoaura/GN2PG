#!/bin/sh

chown -R xfer:xfer /home/xfer/.gn2pg
exec runuser -u xfer "$@"
