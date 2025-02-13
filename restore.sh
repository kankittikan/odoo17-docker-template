while getopts d:f: flag
do
    case "${flag}" in
        d) db=${OPTARG};;
        f) file=${OPTARG};;
    esac
done
if [ -z "$db" ] || [ -z "$file"]; then
        echo 'Missing -d or -f flag' >&2
        exit 1
fi

endpath=$(basename $(pwd))

rm -rf .temp_backup 2> /dev/null

unzip $file -d .temp_backup

docker exec -i "$endpath-db-1" psql -U odoo -d postgres -c "CREATE DATABASE $db;"
cat .temp_backup/dump.sql | docker exec -i "$endpath-db-1" psql -U odoo -d $db
cp -r .temp_backup/filestore/. .volume/web/filestore/$db

rm -rf .temp_backup 2> /dev/null