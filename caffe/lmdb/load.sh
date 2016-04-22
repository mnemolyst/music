#!/bin/sh

for i in train/*py; do python $i && mv $i train/loaded; done
for i in test/*py; do python $i && mv $i test/loaded; done

return 0
