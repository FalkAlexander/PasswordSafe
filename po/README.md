## Update pot files from source files:

```bash
cd po  
intltool-update --maintain  
cd ..  
find secrets -iname "*.py" | xargs xgettext --from-code=UTF-8 --output=po/secrets-python.pot  
find data -iname "*.ui" | xargs xgettext --from-code=UTF-8 --output=po/secrets-glade.pot -L Glade  
msgcat --use-first po/secrets-glade.pot po/secrets-python.pot > po/secrets.pot  
rm po/secrets-glade.pot po/secrets-python.pot  
```

## Generate po file for language

```bash
cd po  
msginit --locale=xx --input=secrets.pot
```
