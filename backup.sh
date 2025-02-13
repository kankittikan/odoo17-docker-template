while getopts d: flag
do
    case "${flag}" in
        d) db=${OPTARG};;
    esac
done
if [ -z "$db" ]; then
        echo 'Missing -d flag' >&2
        exit 1
fi

endpath=$(basename $(pwd))

rm -rf .temp_backup 2> /dev/null
mkdir .temp_backup

docker exec "$endpath-db-1" pg_dump -U odoo $db > .temp_backup/dump.sql
cp -r .volume/web/filestore/$db/. .temp_backup/filestore

rm $db.tgz 2> /dev/null

cd .temp_backup && zip -r ../"$db"_$(date -u '+%Y-%m-%d_%H-%M-%S').zip .
cd ..

rm -rf .temp_backup 2> /dev/null