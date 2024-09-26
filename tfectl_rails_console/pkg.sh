#!/usr/bin/env bash

WORKING_DIR=$(dirname "$(readlink -f "$0")")
DIST_DIR="$WORKING_DIR/../dist"

RAILS_SCRIPT="$(base64 -i $WORKING_DIR/gather_billable_rum.rb)"
OUT_FILE=$(readlink -f "$DIST_DIR/gather_billable_rum-rb.sh")

# Ensure the dist directory exists
mkdir -p dist

cat << EOF > ${OUT_FILE}
#!/usr/bin/env bash

set -e

# Check if Docker is available and properly configured
if ! docker info > /dev/null 2>&1; then
  echo "Docker is not available or not properly configured. Please ensure Docker is installed and running."
  exit 1
fi

RAILS_SCRIPT="${RAILS_SCRIPT}"

CONTAINER_ID="\$(docker ps --format "{{.ID}} {{.Image}}" | grep "terraform-enterprise" | awk '{print \$1}')"
echo "\$(echo \${RAILS_SCRIPT} | base64 -d)" | docker exec -i \${CONTAINER_ID} dd of=/tmp/gather_billable_rum.rb > /dev/null 2>&1
docker exec -i \${CONTAINER_ID} bin/bash << 'EOS'
source atlas-env
echo "load('/tmp/gather_billable_rum.rb'); File.open('/tmp/output.json', 'w') { |f| GatherBillableRum.new.call(organizations = [], output=f) }" | (wait-for-token -- bash -c 'cd /app && ./bin/rails c -- --nomultiline') > /dev/null 2>&1
cat /tmp/output.json
EOS
EOF

chmod +x ${OUT_FILE}
echo "Script written successfully to ${OUT_FILE}"


