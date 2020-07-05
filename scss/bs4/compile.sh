#!/bin/bash
css_file=$(echo $1 | sed 's/scss/css/g')
min_file=$(echo $1 | sed 's/scss/min.css/g')
sassc -t expanded -p 6 $1 $css_file
echo "Compiled."
postcss $css_file --replace --use autoprefixer
echo "Prefixed."
echo "Written to $css_file."
cleancss --level 1 --format breakWith=lf --source-map --source-map-inline-sources --output $min_file $css_file
echo "Minified version written to $min_file."
