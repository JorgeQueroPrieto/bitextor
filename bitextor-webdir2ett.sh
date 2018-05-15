#!__BASH__

OUTPUT=/dev/stdout

exit_program()
{
  echo "USAGE: $1 webdir"
  echo "WHERE"
  echo "   webdir   folder downloaded directories"
  exit 1
}

ARGS=$(getopt "h" $*)

set -- $ARGS
for i
do
  case "$i" in
    -h)
      exit_program $(basename $0)
      ;;
    --)
      shift
      break
      ;;
  esac
done

case $# in
  1)
    WEBDIR="$1"
    ;;
  *)
    exit_program $(basename $0)
    ;;
esac

# Código aquí

#
# 1. Eliminar ficheros repetidos -> (log)
# 2. Obtener tipo y codificación de ficheros
# 3. Quedarse solo con los que tengan tipo html
# 4. Convertir [no UTF-8 -> UTF-8], si hay error -> (log)
# 5. Corregir errores HTML usando Tidy y eliminar las cabeceras HTML
# 6. Incluir el contenido del fichero en base64
#
# Formato final del documento:
# encoding	mimetype	url	content(base_64)
#
# Genera .ett -> encoded and typed text
#

# Not empty files are searched in WEBDIR and they are printer together with their mime type and their encoding
find "$WEBDIR" -type f -exec file -N --mime-type --mime-encoding {} + | __GREP__ -E "(text|html|xml)" | \
__GAWK__ '{ print gensub(/([^:]+): ([^;]+); (.+)/, "\\2\t\\3\t\\1", "g", $0) }' | \
__JAVA__ -jar __PREFIX__/share/java/piped-tika.jar | __JAVA__ -jar __PREFIX__/share/java/piped-boilerpipe.jar | \
__PYTHON__ -c 'import sys
import hashlib
import base64

reload(sys)
sys.setdefaultencoding("UTF-8")

seen_md5={}
for i in sys.stdin:
  fields = i.strip().split("\t")
  #e = fields[3]
  try:
    e = base64.b64encode(fields[3])
    #Por último, guardamos los datos en un mismo fichero con el formato: encoding   formato   nombre_fichero   base64
    c = hashlib.md5()
    c.update(e)
    #checking for duplicate content (duplicates are discarded)
    if c.hexdigest() in seen_md5:
      sys.stderr.write("Repeated file:\t"+fields[2]+"\tfirst occurrence\t"+seen_md5[c.hexdigest()]+"\n")
    else:
      seen_md5[c.hexdigest()]=fields[2]
      print "{0}\t{1}\t{2}\t{3}".format(fields[0].strip(),fields[1],fields[2],e)
  except UnicodeDecodeError:
    sys.stderr.write("File "+fields[2]+" produced a character encoding error")
' > $OUTPUT


