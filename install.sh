#!/bin/bash

cp -vr openeos-print.service /etc/systemd/system/

mkdir -p /var/log/openeos/

sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable openeos-print.service
sudo systemctl start openeos-print.service


