#!/bin/sh

for i in train/*py; do python $i; done
for i in test/*py; do python $i; done

return 0
