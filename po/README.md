## Update pot files from source files:

```bash
cd po  
intltool-update --maintain  
cd ..  
find passwordsafe -iname "*.py" | xargs xgettext --from-code=UTF-8 --output=po/passwordsafe-python.pot  
find data -iname "*.ui" | xargs xgettext --from-code=UTF-8 --output=po/passwordsafe-glade.pot -L Glade  
msgcat --use-first po/passwordsafe-glade.pot po/passwordsafe-python.pot > po/passwordsafe.pot  
rm po/passwordsafe-glade.pot po/passwordsafe-python.pot  
```

## Generate po file for language

```bash
cd po  
msginit --locale=xx --input=passwordsafe.pot
```
