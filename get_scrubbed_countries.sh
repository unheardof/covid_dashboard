for f in $(ls ./*.csv | grep -vE '03-2[2-9]|03-3[0-1]'); do cat $f | awk -F ',' '{ print $2 }'; done | sort -u | sed 's/["\*]//g' | sed 's/^ //g' | grep -vE '^[A-Z]{2}$' | uniq > scrubbed_country_list.txt
