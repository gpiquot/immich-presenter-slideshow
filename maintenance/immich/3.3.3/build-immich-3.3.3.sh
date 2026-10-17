#!/usr/bin/env bash
set -euo pipefail
VERSION=v3.3.3
IMAGE=immich-server:3.3.3-day-asc
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PATCH="$HERE/immich-v3.3.3-photos-day-asc.patch"
SOURCE="$HERE/immich-src-v3.3.3-build"
test -f "$PATCH" || { echo 'Patch absent du dossier du script.' >&2; exit 1; }
test ! -e "$SOURCE" || { echo "Dossier déjà présent : $SOURCE. Examiner avant de relancer." >&2; exit 1; }
if docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "Image déjà présente : $IMAGE. Arrêt pour ne pas la remplacer." >&2
  exit 1
fi
git clone --depth 1 --branch "$VERSION" https://github.com/immich-app/immich.git "$SOURCE"
git -C "$SOURCE" apply --check "$PATCH"
git -C "$SOURCE" apply "$PATCH"
git -C "$SOURCE" diff --check
COMMIT="$(git -C "$SOURCE" rev-parse HEAD)"
docker build --platform linux/amd64 \
  --build-arg BUILD_SOURCE_REF="$VERSION" \
  --build-arg BUILD_SOURCE_COMMIT="$COMMIT" \
  --build-arg BUILD_IMAGE="$IMAGE" \
  --label "local.immich.day-asc.patch-sha256=$(sha256sum "$PATCH" | cut -d ' ' -f 1)" \
  -f "$SOURCE/server/Dockerfile" -t "$IMAGE" "$SOURCE"
docker image inspect "$IMAGE" --format '{{.Id}}'
printf '\nImage construite : %s\nAucun conteneur démarré ou modifié.\n' "$IMAGE"
