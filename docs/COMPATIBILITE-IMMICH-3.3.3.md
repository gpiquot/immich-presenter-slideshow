# Compatibilité Immich 3.3.3

Vérifications du 17 octobre 2026.

## Presenter

Code de référence : commit 0e9d1aa (branche compat-immich-3). Aucune nouvelle modification du code Presenter n'a été nécessaire lors du passage de 3.1.0 à 3.3.3.

Contrôles réalisés sur l'installation mise à jour :

- API annonce 3.3.3 ; serveur et machine learning sains.
- 58 albums accessibles ; lecture d'un album de 307 images par Presenter.
- Accès à un original JPEG et une miniature WebP : HTTP 200.
- Service Presenter réel : page HTML et liste des images via partage HTTP 200.
- Aucun ERROR ni Error: dans les journaux serveur et machine learning contrôlés après démarrage.
- L'utilisateur confirme que Presenter et son diaporama semblent très bien fonctionner.

L'édition des descriptions et leur persistance après rechargement n'ont pas encore fait l'objet d'un test dédié sur 3.3.3. La priorité donnée aux descriptions XMP et le cache constituent des comportements préexistants à surveiller.

## Patch du tri web Immich

Les fichiers de [maintenance/immich/3.3.3](../maintenance/immich/3.3.3/) concernent le code d'Immich, pas celui de Presenter. Le patch conserve les jours du plus récent au plus ancien et trie les photos du matin au soir à l'intérieur de chaque journée, uniquement sur /photos. Les applications mobiles ne sont pas modifiées.

Le patch a été adapté au contexte des sources officielles v3.3.3. Application vérifiée et image complète construite avec server/Dockerfile. Quatre fichiers modifiés : 20 insertions, 8 suppressions. L'image personnalisée a été déployée ; la validation visuelle finale du tri reste à confirmer par l'utilisateur.

Placer le script et le patch ensemble dans un dossier de travail neuf puis lancer :

```bash
bash build-immich-3.3.3.sh
```

Le script clone v3.3.3 dans un dossier séparé et construit immich-server:3.3.3-day-asc. Il s'arrête si son dossier de construction ou l'image existent déjà ; il ne modifie aucun conteneur ni fichier Compose. La construction nécessite Docker avec BuildKit, Git, Internet et de l'espace libre. Le fichier .sh peut être lancé avec bash sans permission exécutable.

## Déploiement et prochaines versions

1. Examiner les notes de toutes les versions intermédiaires.
2. Sauvegarder la VM, la base PostgreSQL et les configurations ; les médias externes demandent une sauvegarde séparée.
3. Vérifier l'application du patch puis construire l'image sans toucher à la production.
4. Précharger le machine learning de la même version.
5. Configurer IMMICH_VERSION=v3.3.3 et la surcharge Compose avec l'image personnalisée correspondante et pull_policy: never. Changer seulement IMMICH_VERSION ne suffit pas si cette surcharge fixe l'image serveur.
6. Basculer serveur et machine learning ensemble. Ne changer les images PostgreSQL/Valkey que si requis par les notes de version.
7. Contrôler santé, API, médias, partage Presenter, grille, diaporama, descriptions et tri /photos (chargement initial, défilement et navigation).

Un redémarrage de l'ancienne image sur une base migrée ne constitue pas un retour arrière : prévoir la restauration cohérente de la sauvegarde. Le catalogue de l'archive PostgreSQL a été vérifié ; aucune restauration d'essai n'a été réalisée lors de cette intervention.

Aucun secret, .env réel ni lien de partage personnel ne doit être publié dans ce dépôt.

Sources : [mise à jour](https://docs.immich.app/install/upgrading/), [sauvegarde](https://docs.immich.app/administration/backup-and-restore/).
