## SCSS

* `bs<4/5>-jf.scss` contains the source for the customizations to bootstrap. To customize the UI, you can make modifications to this file and then compile it.

Note: For BS5, it assumes that bootstrap is installed in `../../node_modules/bootstrap` relative to itself.
For BS4, it assumes that bootstrap is installed in `../../node_modules/bootstrap4` relative to itself. (`npm install bootstrap4@npm:bootstrap`)
* Compilation requires a sass compiler of your choice, and `postcss-cli`, `autoprefixer` + `clean-css-cli` from npm.
* If you're using `sassc`, run `./compile.sh bs<4/5>-jf.scss` in this directory. This will create a .css file, and minified .css file.
* For `node-sass`, replace the `sassc` line in `compile.sh` with 
```
node-sass --output-style expanded --precision 6 $1 $css_file
```
and run as above.
* If you're building from source, copy the minified css to `<jf-accounts git directory>/jellyfin_accounts/data/static/bs<4/5>-jf.css`.
* If you're just customizing your install, set `custom_css` in your config as the path to your minified css.

