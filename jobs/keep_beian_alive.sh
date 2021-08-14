#! /bin/bash

# 维持备案服务器日活
curl -A 'github' -v $BEIAN_URI > /dev/null