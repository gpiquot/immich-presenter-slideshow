# Presenter : compatibilité Immich 3.3.3

Vérifications du 17 octobre 2026.

Presenter est une application autonome qui utilise l'API Immich. Sa grille et son diaporama possèdent leur propre logique d'ordre dans le code Presenter. Le patch de tri quotidien de la page /photos d'Immich ne fait pas partie de Presenter.

## Version et contrôles

Code de référence : commit 0e9d1aa, adaptation des albums Immich 3.1.0 déjà publiée dans compat-immich-3. Aucune nouvelle modification du code Presenter n'a été nécessaire pendant le passage de 3.1.0 à 3.3.3.

- API Immich annonce 3.3.3 ; serveur et machine learning sains.
- 58 albums accessibles ; lecture d'un album de 307 images par Presenter.
- Original JPEG et miniature WebP : HTTP 200.
- Service Presenter réel : page HTML et liste d'images via partage HTTP 200.
- Aucun ERROR ni Error: dans les journaux serveur et machine learning contrôlés après démarrage.
- L'utilisateur confirme que Presenter et son diaporama semblent très bien fonctionner.

L'édition des descriptions et leur persistance après rechargement restent à vérifier par un test dédié sur 3.3.3. La priorité des descriptions XMP et le cache sont des comportements préexistants à surveiller.

## À chaque mise à jour Immich

1. Conserver le code et la configuration privée de Presenter ; ne jamais publier .env, clés API, tokens ou liens de partage personnels.
2. Vérifier les endpoints de lecture d'albums, recherche de médias, partages, originaux, miniatures et modification des descriptions.
3. Tester la pagination d'un album, puis un lien de partage réel sans afficher sa clé dans les journaux.
4. Vérifier grille, ordre propre au diaporama, pause, navigation et affichage des descriptions.
5. Vérifier une édition et sa persistance sur une photo de test.

Le script slideshow.html distinct reste une référence historique dont l'utilisation actuelle n'est pas établie. Le diaporama intégré à Presenter est celui validé par l'utilisateur.

## Patch quotidien séparé

Le patch Immich /photos et sa construction doivent être maintenus dans le dépôt distinct gpiquot/chronologie-quotidienne-naturelle. Ils ont été retirés de cette PR pour éviter toute confusion entre les deux fonctionnalités.
